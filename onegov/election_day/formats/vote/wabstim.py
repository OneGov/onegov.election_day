from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.election_day import _
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from onegov.election_day.utils import clear_vote
from onegov.election_day.utils import guessed_group


HEADERS = (
    'freigegeben',
    'stileer',
    'stiungueltig',
    'stijahg',
    'stineinhg',
    'stiohneawhg',
    'stijan1',
    'stineinn1',
    'stiohneawN1',
    'stijan2',
    'stineinn2',
    'stiohneawN2',
    'stimmberechtigte',
    'bfs',
)


def import_vote_wabstim(vote, entities, complex, file, mimetype):
    """ Tries to import the given csv, xls or xlsx file.

    This is the format used by Wabsti for municipalities. Since there is no
    format description, importing these files is somewhat experimental.

    :return:
        A list containing errors.

    """
    csv, error = load_csv(
        file, mimetype, expected_headers=HEADERS,
        rename_duplicate_column_names=True
    )
    if error:
        # Wabsti files are sometimes UTF-16
        csv, utf16_error = load_csv(
            file, mimetype, expected_headers=HEADERS, encoding='utf-16-le',
            rename_duplicate_column_names=True
        )
        if utf16_error:
            return [error]

    used_ballot_types = ['proposal']
    if complex:
        used_ballot_types.extend(['counter-proposal', 'tie-breaker'])

    ballot_results = {key: [] for key in used_ballot_types}
    added_entity_ids = set()
    errors = []
    skipped = 0

    for line in csv.lines:
        line_errors = []

        # the id of the entity
        entity_id = None
        try:
            entity_id = int(line.bfs or 0)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id in added_entity_ids:
                line_errors.append(
                    _("${name} was found twice", mapping={
                        'name': entity_id
                    }))

            if entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={
                        'name': entity_id
                    }))
            else:
                added_entity_ids.add(entity_id)

        try:
            counted = True if line.freigegeben else False
        except ValueError:
            line_errors.append(_("Invalid values"))

        # the yeas
        yeas = {}
        try:
            yeas['proposal'] = int(line.stijahg or 0)
            yeas['counter-proposal'] = int(line.stijan1 or 0)
            yeas['tie-breaker'] = int(line.stijan2 or 0)
        except ValueError:
            line_errors.append(_("Could not read yeas"))

        # the nays
        nays = {}
        try:
            nays['proposal'] = int(line.stineinhg or 0)
            nays['counter-proposal'] = int(line.stineinn1 or 0)
            nays['tie-breaker'] = int(line.stineinn2 or 0)
        except ValueError:
            line_errors.append(_("Could not read nays"))

        # the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))

        # the empty votes
        empty = {}
        try:
            e_ballots = int(line.stileer or 0)
            empty['proposal'] = int(line.stiohneawhg or 0) + e_ballots
            empty['counter-proposal'] = int(line.stiohneawn1 or 0) + e_ballots
            empty['tie-breaker'] = int(line.stiohneawn2 or 0) + e_ballots
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # the invalid votes
        try:
            invalid = int(line.stiungueltig or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

        # pass the errors
        if line_errors:
            errors.extend(
                FileImportError(error=err, line=line.rownumber)
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            for ballot_type in used_ballot_types:
                ballot_results[ballot_type].append(
                    BallotResult(
                        group=entities.get(entity_id, {}).get('name', ''),
                        counted=counted,
                        yeas=yeas[ballot_type],
                        nays=nays[ballot_type],
                        elegible_voters=elegible_voters,
                        entity_id=entity_id,
                        empty=empty[ballot_type],
                        invalid=invalid
                    )
                )

    if errors:
        return errors

    if (
        not any((len(results) for results in ballot_results.values())) and not
        skipped
    ):
        return [FileImportError(_("No data found"))]

    clear_vote(vote)

    for ballot_type in used_ballot_types:
        remaining = (
            entities.keys() - added_entity_ids
        )
        for id in remaining:
            entity = entities[id]
            ballot_results[ballot_type].append(
                BallotResult(
                    group=guessed_group(entity, ballot_results[ballot_type]),
                    counted=False,
                    entity_id=id
                )
            )

        if ballot_results[ballot_type]:
            ballot = next(
                (b for b in vote.ballots if b.type == ballot_type), None
            )
            if not ballot:
                ballot = Ballot(type=ballot_type)
                vote.ballots.append(ballot)

            for result in ballot_results[ballot_type]:
                ballot.results.append(result)

    return []