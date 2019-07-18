import re

from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import load_csv
from sqlalchemy.orm import object_session
from uuid import uuid4


HEADERS_WP_WAHL = (
    'sortgeschaeft',  # provides the link to the election
    'ausmittlungsstand',  # complete
)
HEADERS_WPSTATIC_GEMEINDEN = (
    'sortwahlkreis',  # provides the link to the election
    'sortgeschaeft',  # provides the link to the election
    'bfsnrgemeinde',  # BFS
    'stimmberechtigte',  # eligible votes
)
HEADERS_WP_GEMEINDEN = (
    'bfsnrgemeinde',  # BFS
    'stimmberechtigte',  # eligible votes
    'sperrung',  # counted
    'stmabgegeben',  # received ballots
    'stmleer',  # blank ballots
    'stmungueltig',  # invalid ballots
    'anzwzamtleer',  # blank ballots
)
HEADERS_WP_LISTEN = (
    'sortgeschaeft',  # provides the link to the election
    'listnr',
    'listcode',
    'sitze',
    'listverb',
    'listuntverb',
)
HEADERS_WP_LISTENGDE = (
    'bfsnrgemeinde',  # BFS
    'listnr',
    'stimmentotal',
)
HEADERS_WPSTATIC_KANDIDATEN = (
    'sortgeschaeft',  # provides the link to the election
    'knr',  # candidate id
    'nachname',  # familiy name
    'vorname',  # first name
)
HEADERS_WP_KANDIDATEN = (
    'sortgeschaeft',  # provides the link to the election
    'knr',  # candidate id
    'gewahlt',  # elected
)
HEADERS_WP_KANDIDATENGDE = (
    'bfsnrgemeinde',  # BFS
    'knr',  # candidate id
    'stimmen',  # votes
)


def line_is_relevant(line, number, district=None):
    if district:
        return line.sortwahlkreis == district and line.sortgeschaeft == number
    else:
        return line.sortgeschaeft == number


def get_entity_id(line, entities):
    entity_id = int(line.bfsnrgemeinde or 0)
    return 0 if entity_id in EXPATS else entity_id


def get_list_id_from_knr(line):
    """
    Takes a line with a candidate number (knr) in it and
    return the abstracted listnr for this candidate
    """
    if not hasattr(line, 'knr'):
        raise ValueError(_('Line does not contain candidate number knr.'))
    if '.' in line.knr:
        return line.knr.split('.')[0]
    return line.knr[0:-2]


def get_list_id(line):
    # FIXME: Adapt to WabstiCExport-Version 2.30e (2018)
    if hasattr(line, 'listnr'):
        number = line.listnr or '0'
    number = '999' if number == '99' else number  # blank list
    return number


def import_election_wabstic_proporz(
    election, principal, number, district,
    file_wp_wahl, mimetype_wp_wahl,
    file_wpstatic_gemeinden, mimetype_wpstatic_gemeinden,
    file_wp_gemeinden, mimetype_wp_gemeinden,
    file_wp_listen, mimetype_wp_listen,
    file_wp_listengde, mimetype_wp_listengde,
    file_wpstatic_kandidaten, mimetype_wpstatic_kandidaten,
    file_wp_kandidaten, mimetype_wp_kandidaten,
    file_wp_kandidatengde, mimetype_wp_kandidatengde
):
    """ Tries to import the given CSV files from a WabstiCExport.

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A list containing errors.

    """

    errors = []
    entities = principal.entities[election.date.year]
    election_id = election.id

    # Read the files
    wp_wahl, error = load_csv(
        file_wp_wahl, mimetype_wp_wahl,
        expected_headers=HEADERS_WP_WAHL,
        filename='wp_wahl'
    )
    if error:
        errors.append(error)

    wpstatic_gemeinden, error = load_csv(
        file_wpstatic_gemeinden, mimetype_wpstatic_gemeinden,
        expected_headers=HEADERS_WPSTATIC_GEMEINDEN,
        filename='wpstatic_gemeinden'
    )
    if error:
        errors.append(error)

    wp_gemeinden, error = load_csv(
        file_wp_gemeinden, mimetype_wp_gemeinden,
        expected_headers=HEADERS_WP_GEMEINDEN,
        filename='wp_gemeinden'
    )
    if error:
        errors.append(error)

    wp_listen, error = load_csv(
        file_wp_listen, mimetype_wp_listen,
        expected_headers=HEADERS_WP_LISTEN,
        filename='wp_listen'
    )
    if error:
        errors.append(error)

    wp_listengde, error = load_csv(
        file_wp_listengde, mimetype_wp_listengde,
        expected_headers=HEADERS_WP_LISTENGDE,
        filename='wp_listengde'
    )
    if error:
        errors.append(error)

    wpstatic_kandidaten, error = load_csv(
        file_wpstatic_kandidaten, mimetype_wpstatic_kandidaten,
        expected_headers=HEADERS_WPSTATIC_KANDIDATEN,
        filename='wpstatic_kandidaten'
    )
    if error:
        errors.append(error)

    wp_kandidaten, error = load_csv(
        file_wp_kandidaten, mimetype_wp_kandidaten,
        expected_headers=HEADERS_WP_KANDIDATEN,
        filename='wp_kandidaten'
    )
    if error:
        errors.append(error)

    wp_kandidatengde, error = load_csv(
        file_wp_kandidatengde, mimetype_wp_kandidatengde,
        expected_headers=HEADERS_WP_KANDIDATENGDE,
        filename='wp_kandidatengde'
    )
    if error:
        errors.append(error)

    if errors:
        return errors

    # Parse the election
    complete = 0
    for line in wp_wahl.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            complete = int(line.ausmittlungsstand or 0)
            assert 0 <= complete <= 3
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid values"))

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wp_wahl'
                )
                for err in line_errors
            )
            continue

    # Parse the entities
    added_entities = {}
    for line in wpstatic_gemeinden.lines:
        line_errors = []

        if not line_is_relevant(line, number, district=district):
            continue

        # Parse the id of the entity
        try:
            entity_id = get_entity_id(line, entities)
            if entity_id == 3251:
                pass
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id and entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id}))

            if entity_id in added_entities:
                line_errors.append(
                    _("${name} was found twice", mapping={'name': entity_id}))

        # Parse the eligible voters
        try:
            eligible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the eligible voters"))

        # Skip expats if not enabled
        if entity_id == 0 and not election.expats:
            continue

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wpstatic_gemeinden'
                )
                for err in line_errors
            )
            continue

        entity = entities.get(entity_id, {})
        added_entities[entity_id] = {
            'name': entity.get('name', ''),
            'district': entity.get('district', ''),
            'eligible_voters': eligible_voters
        }

    for line in wp_gemeinden.lines:
        line_errors = []

        # Parse the id of the entity
        try:
            entity_id = get_entity_id(line, entities)
        except ValueError:
            line_errors.append(_("Invalid id"))
        else:
            if entity_id and entity_id not in entities:
                line_errors.append(
                    _("${name} is unknown", mapping={'name': entity_id}))

            if entity_id not in added_entities:
                # Only add it if present (there is there no SortGeschaeft)
                # .. this also skips expats if not enabled
                continue

        entity = added_entities[entity_id]

        # Check if the entity is counted
        try:
            entity['counted'] = False if int(line.sperrung or 0) == 0 else True
        except ValueError:
            line_errors.append(_("Invalid entity values"))

        # Parse the eligible voters
        try:
            eligible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Invalid entity values"))
        else:
            eligible_voters = (
                eligible_voters
                or added_entities.get(entity_id, {}).get('eligible_voters', 0)
            )
            entity['eligible_voters'] = eligible_voters

        # Parse the ballots and votes
        try:
            received_ballots = int(line.stmabgegeben or 0)
            blank_ballots = int(line.stmleer or 0)
            invalid_ballots = int(line.stmungueltig or 0)
        except ValueError:
            line_errors.append(_("Invalid entity values"))
        else:
            entity['received_ballots'] = received_ballots
            entity['blank_ballots'] = blank_ballots
            entity['invalid_ballots'] = invalid_ballots
            entity['blank_votes'] = 0  # they are in the list results

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wp_gemeinden'
                )
                for err in line_errors
            )
            continue

    # Parse the lists
    added_lists = {}
    added_connections = {}
    for line in wp_listen.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            list_id = get_list_id(line)
            name = line.listcode
            number_of_mandates = int(line.sitze or 0)
            connection = line.listverb or None
            subconnection = line.listuntverb or None
            if subconnection:
                assert connection
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid list values"))
        else:
            if list_id in added_lists:
                line_errors.append(
                    _("${name} was found twice", mapping={'name': list_id}))

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wp_listen')
                for err in line_errors
            )
            continue

        connection_id = None
        if connection:
            parent_id = None
            if subconnection:
                parent_id = added_connections.setdefault(
                    (connection, None),
                    dict(
                        id=uuid4(),
                        election_id=election_id,
                        connection_id=connection
                    )
                )['id']

            connection_id = added_connections.setdefault(
                (connection, subconnection),
                dict(
                    id=uuid4(),
                    election_id=election_id,
                    parent_id=parent_id,
                    connection_id=subconnection or connection,
                )
            )['id']

        added_lists[list_id] = dict(
            id=uuid4(),
            election_id=election_id,
            list_id=list_id,
            name=name,
            number_of_mandates=number_of_mandates,
            connection_id=connection_id
        )

    # Parse the list results
    added_list_results = {}
    for line in wp_listengde.lines:
        line_errors = []

        try:
            entity_id = get_entity_id(line, entities)
            list_id = get_list_id(line)
            votes = int(line.stimmentotal)
        except ValueError:
            line_errors.append(_("Invalid list results"))
        else:
            if entity_id not in added_entities:
                # Only add the list result if the entity is present (there is
                # no SortGeschaeft in this file)
                # .. this also skips expats if not enabled
                continue

            if entity_id not in added_entities:
                line_errors.append(_("Invalid entity values"))

            if list_id in added_list_results.get(entity_id, {}):
                line_errors.append(
                    _(
                        "${name} was found twice",
                        mapping={
                            'name': '{}/{}'.format(entity_id, list_id)
                        }
                    )
                )

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber, filename='wp_listengde')
                for err in line_errors
            )
            continue

        if list_id == '999':
            added_entities[entity_id]['blank_votes'] = votes

        if entity_id not in added_list_results:
            added_list_results[entity_id] = {}
        added_list_results[entity_id][list_id] = votes

    # Parse the candidates
    added_candidates = {}
    for line in wpstatic_kandidaten.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            candidate_id = line.knr
            list_id = get_list_id_from_knr(line)
            family_name = line.nachname
            first_name = line.vorname
        except ValueError:
            line_errors.append(_("Invalid candidate values"))
        else:
            if candidate_id in added_candidates:
                line_errors.append(
                    _("${name} was found twice",
                      mapping={'name': candidate_id}))

            if list_id not in added_lists:
                line_errors.append(_("Invalid list values"))

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wpstatic_kandidaten'
                )
                for err in line_errors
            )
            continue

        added_candidates[candidate_id] = dict(
            id=uuid4(),
            election_id=election_id,
            candidate_id=candidate_id,
            family_name=family_name,
            first_name=first_name,
            list_id=added_lists[list_id]['id']
        )

    for line in wp_kandidaten.lines:
        line_errors = []

        if not line_is_relevant(line, number):
            continue

        try:
            candidate_id = line.knr
            assert candidate_id in added_candidates
            elected = True if line.gewahlt == '1' else False
        except (ValueError, AssertionError):
            line_errors.append(_("Invalid candidate values"))
        else:
            added_candidates[candidate_id]['elected'] = elected

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wpstatic_kandidaten'
                )
                for err in line_errors
            )
            continue

    added_results = {}
    for line in wp_kandidatengde.lines:
        line_errors = []

        try:
            entity_id = get_entity_id(line, entities)
            candidate_id = line.knr
            votes = int(line.stimmen)
        except ValueError:
            line_errors.append(_("Invalid candidate results"))
        else:
            if (
                entity_id not in added_entities
                or candidate_id not in added_candidates
            ):
                # Only add the candidate result if the entity and the candidate
                # are present (there is no SortGeschaeft in this file)
                # .. this also skips expats if not enabled
                continue

            if candidate_id in added_results.get(entity_id, {}):
                line_errors.append(
                    _(
                        "${name} was found twice",
                        mapping={
                            'name': '{}/{}'.format(entity_id, candidate_id)
                        }
                    )
                )

        # Pass the errors and continue to next line
        if line_errors:
            errors.extend(
                FileImportError(
                    error=err, line=line.rownumber,
                    filename='wp_kandidatengde'
                )
                for err in line_errors
            )
            continue

        if entity_id not in added_results:
            added_results[entity_id] = {}
        added_results[entity_id][candidate_id] = votes

    # Check if all results are from the same district if regional election
    districts = set([result['district'] for result in added_entities.values()])
    if election.domain == 'region' and districts and election.distinct:
        if principal.has_districts:
            if len(districts) != 1:
                errors.append(FileImportError(_("No clear district")))
        else:
            if len(added_results) != 1:
                errors.append(FileImportError(_("No clear district")))

    if errors:
        return errors

    # Add the results to the DB
    election.clear_results()
    election.status = 'unknown'
    if complete == 1:
        election.status = 'interim'
    if complete == 2:
        election.status = 'final'

    result_uids = {entity_id: uuid4() for entity_id in added_results}

    session = object_session(election)
    session.bulk_insert_mappings(
        ListConnection,
        (
            added_connections[key]
            for key in sorted(added_connections, key=lambda x: x[1] or '')
        )
    )
    session.bulk_insert_mappings(
        List,
        (
            added_lists[key]
            for key in filter(lambda x: x != '999', added_lists)
        )
    )
    session.bulk_insert_mappings(Candidate, added_candidates.values())
    session.bulk_insert_mappings(
        ElectionResult,
        (
            dict(
                id=result_uids[entity_id],
                election_id=election_id,
                name=added_entities[entity_id]['name'],
                district=added_entities[entity_id]['district'],
                entity_id=entity_id,
                counted=added_entities[entity_id]['counted'],
                eligible_voters=added_entities[entity_id]['eligible_voters'],
                received_ballots=added_entities[entity_id]['received_ballots'],
                blank_ballots=added_entities[entity_id]['blank_ballots'],
                invalid_ballots=added_entities[entity_id]['invalid_ballots'],
                blank_votes=added_entities[entity_id]['blank_votes'],
            )
            for entity_id in added_results
        )
    )
    session.bulk_insert_mappings(
        CandidateResult,
        (
            dict(
                id=uuid4(),
                election_result_id=result_uids[entity_id],
                votes=votes,
                candidate_id=added_candidates[candidate_id]['id']
            )
            for entity_id in added_results
            for candidate_id, votes in added_results[entity_id].items()
        )
    )
    session.bulk_insert_mappings(
        ListResult,
        (
            dict(
                id=uuid4(),
                election_result_id=result_uids[entity_id],
                votes=votes,
                list_id=added_lists[list_id]['id']
            )
            for entity_id in added_results
            for list_id, votes in added_list_results[entity_id].items()
            if list_id != '999'
        )
    )

    # Add the missing entities
    result_inserts = []
    remaining = set(entities.keys())
    if election.expats:
        remaining.add(0)
    remaining -= set(added_results.keys())
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
        result_inserts.append(
            dict(
                id=uuid4(),
                election_id=election_id,
                name=entity.get('name', ''),
                district=district,
                entity_id=entity_id,
                counted=False
            )
        )
    session.bulk_insert_mappings(ElectionResult, result_inserts)

    return []
