from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.formats.common import STATI
from sqlalchemy.orm import object_session
from uuid import uuid4


HEADERS = [
    'election_absolute_majority',
    'election_status',
    'entity_id',
    'entity_counted',
    'entity_eligible_voters',
    'entity_received_ballots',
    'entity_blank_ballots',
    'entity_invalid_ballots',
    'entity_blank_votes',
    'entity_invalid_votes',
    'candidate_family_name',
    'candidate_first_name',
    'candidate_id',
    'candidate_elected',
    'candidate_votes',
    'candidate_party',
]


def parse_election(line, errors):
    majority = None
    status = None
    try:
        if line.election_absolute_majority:
            majority = int(line.election_absolute_majority or 0)
            majority = majority if majority else None
        status = line.election_status or 'unknown'
    except ValueError:
        errors.append(_("Invalid election values"))
    if status not in STATI:
        errors.append(_("Invalid status"))
    return majority, status


def parse_election_result(line, errors, entities, election_id):
    try:
        entity_id = int(line.entity_id or 0)
        counted = line.entity_counted.strip().lower() == 'true'
        eligible_voters = int(line.entity_eligible_voters or 0)
        received_ballots = int(line.entity_received_ballots or 0)
        blank_ballots = int(line.entity_blank_ballots or 0)
        invalid_ballots = int(line.entity_invalid_ballots or 0)
        blank_votes = int(line.entity_blank_votes or 0)
        invalid_votes = int(line.entity_invalid_votes or 0)

    except ValueError:
        errors.append(_("Invalid entity values"))
    else:
        if entity_id not in entities and entity_id in EXPATS:
            entity_id = 0

        if entity_id and entity_id not in entities:
            errors.append(_(
                "${name} is unknown",
                mapping={'name': entity_id}
            ))
        else:
            entity = entities.get(entity_id, {})
            return dict(
                id=uuid4(),
                election_id=election_id,
                name=entity.get('name', ''),
                district=entity.get('district', ''),
                entity_id=entity_id,
                counted=counted,
                eligible_voters=eligible_voters,
                received_ballots=received_ballots,
                blank_ballots=blank_ballots,
                invalid_ballots=invalid_ballots,
                blank_votes=blank_votes,
                invalid_votes=invalid_votes,
            )


def parse_candidate(line, errors, election_id):
    try:
        id = int(line.candidate_id or 0)
        family_name = line.candidate_family_name
        first_name = line.candidate_first_name
        elected = str(line.candidate_elected or '').lower() == 'true'
        party = line.candidate_party

    except ValueError:
        errors.append(_("Invalid candidate values"))
    else:
        return dict(
            id=uuid4(),
            candidate_id=id,
            election_id=election_id,
            family_name=family_name,
            first_name=first_name,
            elected=elected,
            party=party
        )


def parse_candidate_result(line, errors):
    try:
        votes = int(line.candidate_votes or 0)
    except ValueError:
        errors.append(_("Invalid candidate results"))
    else:
        return dict(
            id=uuid4(),
            votes=votes,
        )


def import_election_internal_majorz(election, principal, file, mimetype):
    """ Tries to import the given file (internal format).

    This is the format used by onegov.ballot.Election.export().

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A list containing errors.

    """
    filename = _("Results")
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS, filename=filename,
        dialect='excel'
    )
    if error:
        return [error]

    errors = []
    candidates = {}
    candidate_results = []
    results = {}
    entities = principal.entities[election.date.year]
    election_id = election.id

    # This format has one candiate per entity per line
    absolute_majority = None
    status = None
    for line in csv.lines:
        line_errors = []

        # Parse the line
        absolute_majority, status = parse_election(line, line_errors)
        result = parse_election_result(
            line, line_errors, entities, election_id
        )
        candidate = parse_candidate(line, line_errors, election_id)
        candidate_result = parse_candidate_result(line, line_errors)

        # Skip expats if not enabled
        if result and result['entity_id'] == 0 and not election.expats:
            continue

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename=filename
                )
                for err in line_errors
            )
            continue

        # Add the data
        result = results.setdefault(result['entity_id'], result)

        candidate = candidates.setdefault(candidate['candidate_id'], candidate)
        candidate_result['candidate_id'] = candidate['id']
        candidate_result['election_result_id'] = result['id']
        candidate_results.append(candidate_result)

    if not errors and not results:
        errors.append(FileImportError(_("No data found")))

    # Check if all results are from the same district if regional election
    districts = set([result['district'] for result in results.values()])
    if election.domain == 'region' and election.distinct:
        if principal.has_districts:
            if len(districts) != 1:
                errors.append(FileImportError(_("No clear district")))
        else:
            if len(results) != 1:
                errors.append(FileImportError(_("No clear district")))

    if errors:
        return errors

    # Add the missing entities
    remaining = set(entities.keys())
    if election.expats:
        remaining.add(0)
    remaining -= set(results.keys())
    for entity_id in remaining:
        entity = entities.get(entity_id, {})
        district = entity.get('district', '')
        if election.domain == 'region':
            if not election.distinct:
                continue
            if not principal.has_districts:
                continue
            if district not in districts:
                continue
        results[entity_id] = dict(
            id=uuid4(),
            election_id=election_id,
            name=entity.get('name', ''),
            district=district,
            entity_id=entity_id,
            counted=False
        )

    # Add the results to the DB
    election.clear_results()
    election.absolute_majority = absolute_majority
    election.status = status

    session = object_session(election)
    session.bulk_insert_mappings(Candidate, candidates.values())
    session.bulk_insert_mappings(ElectionResult, results.values())
    session.bulk_insert_mappings(CandidateResult, candidate_results)

    return []
