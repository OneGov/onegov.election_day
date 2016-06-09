from onegov.ballot import Ballot, BallotResult
from onegov.election_day import _
from onegov.election_day.formats import FileImportError, load_csv
from onegov.election_day.formats.vote import BALLOT_TYPES
from sqlalchemy.orm import object_session


HEADERS = [
    # 'domain',
    'type',
    # 'group',
    'municipality_id',
    'counted',
    'yeas',
    'nays',
    'invalid',
    'empty',
    'elegible_voters',
]


def import_file(municipalities, vote, file, mimetype):
    """ Tries to import the given csv, xls or xlsx file.

    :return: A dictionary of dictionaries containing the status and a list of
    errors if any.

    For example::

        {'proposal': {'status': 'ok', 'errors': []}}

    """
    csv, error = load_csv(file, mimetype, expected_headers=HEADERS)
    if error:
        return {'status': 'error', 'errors': [error]}

    ballot_results = {}
    errors = {}
    added_municipality_ids = {}
    added_groups = {}
    ballot_types = set()

    for line in csv.lines:

        line_errors = []

        ballot_type = line.type
        if ballot_type not in BALLOT_TYPES:
            line_errors.append(_("Invalid ballot type"))
        ballot_types.add(ballot_type)
        errors.setdefault(ballot_type, [])
        added_municipality_ids.setdefault(ballot_type, set())
        added_groups.setdefault(ballot_type, set())
        ballot_results.setdefault(ballot_type, [])

        # the name of the municipality
        group = line.group.strip()
        if not group:
            line_errors.append(_("Missing municipality"))
        if group in added_groups[ballot_type]:
            line_errors.append(_("${group} was found twice", mapping={
                'group': group
            }))
        added_groups[ballot_type].add(group)

        # the id of the municipality
        try:
            municipality_id = int(line.municipality_id or 0)
        except ValueError:
            line_errors.append(_("Invalid municipality id"))
        else:
            if municipality_id in added_municipality_ids[ballot_type]:
                line_errors.append(
                    _("municipality id ${id} was found twice", mapping={
                        'id': municipality_id
                    }))

            if municipality_id not in municipalities:
                line_errors.append(
                    _("municipality id ${id} is unknown", mapping={
                        'id': municipality_id
                    }))
            else:
                added_municipality_ids[ballot_type].add(municipality_id)

        # the yeas
        try:
            yeas = int(line.yeas or 0)
        except ValueError:
            line_errors.append(_("Could not read yeas"))

        # the nays
        try:
            nays = int(line.nays or 0)
        except ValueError:
            line_errors.append(_("Could not read nays"))

        # the elegible voters
        try:
            elegible_voters = int(line.elegible_voters or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))

        # the empty votes
        try:
            empty = int(line.empty or 0)
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # the invalid votes
        try:
            invalid = int(line.invalid or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

        # now let's do some sanity checks
        try:
            if not elegible_voters:
                line_errors.append(_("No elegible voters"))
            if (yeas + nays + empty + invalid) > elegible_voters:
                line_errors.append(_("More cast votes than elegible voters"))
        except UnboundLocalError:
            pass

        # pass the errors
        if line_errors:
            errors[ballot_type].extend(
                FileImportError(error=err, line=line.rownumber)
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors[ballot_type]:
            ballot_results[ballot_type].append(
                BallotResult(
                    group=group,
                    counted=True,
                    yeas=yeas,
                    nays=nays,
                    elegible_voters=elegible_voters,
                    municipality_id=municipality_id,
                    empty=empty,
                    invalid=invalid
                )
            )

    if any((len(results) for results in errors.values())):
        return {
            ballot_type: {
                'status': 'fail',
                'errors': errors[ballot_type],
                'records': 0
            } for ballot_type in ballot_types
        }

    if not any((len(results) for results in ballot_results.values())):
        return {
            'proposal': {
                'status': 'fail',
                'errors': [FileImportError(_("No data found"))],
                'records': 0
            }
        }

    for ballot_type in ballot_types:
        remaining = (
            municipalities.keys() - added_municipality_ids[ballot_type]
        )
        for id in remaining:
            municipality = municipalities[id]
            ballot_results[ballot_type].append(
                BallotResult(
                    group='/'.join(p for p in (
                        municipality.get('district'),
                        municipality['name']
                    ) if p is not None),
                    counted=False,
                    municipality_id=id
                )
            )

        if ballot_results[ballot_type]:
            ballot = next(
                (b for b in vote.ballots if b.type == ballot_type), None
            )
            if not ballot:
                ballot = Ballot(type=ballot_type)
                vote.ballots.append(ballot)
            session = object_session(vote)
            for result in ballot.results:
                session.delete(result)
            for result in ballot_results[ballot_type]:
                ballot.results.append(result)

    return {
        ballot_type: {
            'status': 'ok',
            'errors': errors[ballot_type],
            'records': len(added_municipality_ids[ballot_type])
        } for ballot_type in ballot_types
    }
