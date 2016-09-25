import pytest
import tarfile

from datetime import date
from onegov.core.utils import module_path
from onegov.election_day.collections import ArchivedResultCollection
from webtest import TestApp as Client
from webtest.forms import Upload


def login(client):
    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def test_upload_election_year_unavailable(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(1990, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    csv = (
        "Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,"
        "Ungültige Wahlzettel,Leere Wahlzettel,Leere Stimmen,Listen-Nr,"
        "Partei-ID,Parteibezeichnung,HLV-Nr,ULV-Nr,Anzahl Sitze Liste,"
        "Unveränderte Wahlzettel Liste,Veränderte Wahlzettel Liste,"
        "Kandidatenstimmen unveränderte Wahlzettel,"
        "Zusatzstimmen unveränderte Wahlzettel,"
        "Kandidatenstimmen veränderte Wahlzettel,"
        "Zusatzstimmen veränderte Wahlzettel,Kandidaten-Nr,Gewählt,Name,"
        "Vorname,Stimmen unveränderte Wahlzettel,"
        "Stimmen veränderte Wahlzettel,Stimmen Total aus Wahlzettel,"
        "01 FDP,02 CVP, Anzahl Gemeinden\n"
    )
    csv = csv.encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Das Jahr 1990 wird noch nicht unterstützt" in upload


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/sesam_majorz.tar.gz'),
])
def test_upload_election_sesam_majorz(election_day_app_gr, tar_file):
    archive = ArchivedResultCollection(election_day_app_gr.session())

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert archive.query().one().progress == (0, 0)

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "125 von 125", "2 von 2", "137'126", "55'291", "40.32 %",
        "48'778", "5'365", "1'148", "84'046",
        # candidates
        "39'608", "35'926"
    )))
    assert archive.query().one().progress == (125, 125)

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "125 von 125", "2 von 2", "137'126", "55'291", "40.32 %",
        "48'778", "5'365", "1'148", "84'046",
        # candidates
        "39'608", "35'926"
    )))


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/sesam_proporz.tar.gz'),
])
def test_upload_election_sesam_proporz(election_day_app_gr, tar_file):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "125 von 125", "5 von 5", "137'126", "63'053", "45.98 %", "145",
        "2'314", "60'594", "300'743",
        # list connections
        "20'610", "33'950", "41'167", "23'673",
        "39'890", "52'992", "76'665",
        # candidates
        "1'788", "1'038", "520"
    )))
    assert archive.query().one().progress == (125, 125)

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "125 von 125", "5 von 5", "137'126", "63'053", "45.98 %", "145",
        "2'314", "60'594", "300'743",
        # list connections
        "20'610", "33'950", "41'167", "23'673",
        "39'890", "52'992", "76'665",
        # candidates
        "1'788", "1'038", "520"
    )))


def test_upload_election_sesam_fail(election_day_app_gr):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    headers = [
        'Anzahl Sitze',
        'Wahlkreis-Nr',
        'Stimmberechtigte',
        'Wahlzettel',
        'Ungültige Wahlzettel',
        'Leere Wahlzettel',
        'Leere Stimmen',
        'Listen-Nr',
        'Partei-ID',
        'Parteibezeichnung',
        'HLV-Nr',
        'ULV-Nr',
        'Anzahl Sitze Liste',
        'Unveränderte Wahlzettel Liste',
        'Veränderte Wahlzettel Liste',
        'Kandidatenstimmen unveränderte Wahlzettel',
        'Zusatzstimmen unveränderte Wahlzettel',
        'Kandidatenstimmen veränderte Wahlzettel',
        'Zusatzstimmen veränderte Wahlzettel',
        'Kandidaten-Nr',
        'Gewählt',
        'Name',
        'Vorname',
        'Stimmen unveränderte Wahlzettel',
        'Stimmen veränderte Wahlzettel',
        'Stimmen Total aus Wahlzettel',
        '01 FDP',
        '02 CVP',
        'Anzahl Gemeinden',
    ]

    # no data
    csv = '{}\r\n'.format(','.join(headers),).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Keine Daten gefunden" in upload
    assert archive.query().one().progress == (0, 0)

    # Invalid data
    csv = '\r\n'.join((
        ','.join(headers),
        ','.join((
            'five',
            '1234',
            '56',
            '32',
            '1',
            '0',
            '1',
            'list one',
            '19',
            'FDP',
            '1',
            '1',
            '0',
            '0',
            '0',
            '0',
            '0',
            'eight',
            '0',
            'zeroone',
            'nicht gewählt',
            'Casanova',
            'Angela',
            '0',
            '0',
            'zero',
            '0',
            '0',
            '1 von 1',
        ))
    )).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ungültige Wahldaten" in upload
    assert "1234 ist unbekannt" in upload
    assert "Ungültige Listendaten" in upload
    assert "Ungültige Listenresultate" in upload
    assert "Ungültige Kandidierendendaten" in upload
    assert "Ungültige Kandidierendenresultate" in upload
    assert archive.query().one().progress == (0, 0)

    csv = '\r\n'.join((
        ','.join(headers),
        ','.join((
            '5',
            'xyzb',
            '56',
            '32',
            '1',
            '0',
            '1',
            '1',
            '19',
            'FDP',
            '1',
            '1',
            '0',
            '0',
            '0',
            '0',
            '0',
            '8',
            '0',
            '101',
            'nicht gewählt',
            'Casanova',
            'Angela',
            '0',
            '0',
            '0',
            '0',
            '0',
            '1/1',
        ))
    )).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ungültige Wahldaten" in upload
    assert "1234 ist unbekannt" not in upload
    assert "Ungültige Listendaten" not in upload
    assert "Ungültige Listenresultate" not in upload
    assert "Ungültige Kandidierendendaten" not in upload
    assert "Ungültige Kandidierendenresultate" not in upload
    assert archive.query().one().progress == (0, 0)

    # Missing headers
    headers.remove('Wahlkreis-Nr')
    csv = '{}\r\n'.format(','.join(headers),).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Fehlende Spalten: Wahlkreis-Nr" in upload
    assert archive.query().one().progress == (0, 0)


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabsti_majorz.tar.gz'),
])
def test_upload_election_wabsti_majorz(election_day_app_sg, tar_file):
    archive = ArchivedResultCollection(election_day_app_sg.session())
    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2011, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "144'529", "942", "223", "145'694",
        # candidates
        "53'308", "36'282", "54'616",
    )))
    assert archive.query().one().progress == (85, 0)

    elected = "ID,Name,Vorname\n3,Rechsteiner,Paul".encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', elected, 'text/plain')
    upload.form['complete'] = True
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "1 von 1", "304'850", "47.79 %", "85 von 85", "144'529", "942", "223",
        "145'694",
        # candidates
        "53'308", "36'282", "54'616",
    )))

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', elected, 'text/plain')
    upload.form['complete'] = True
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "1 von 1", "304'850", "47.79 %", "85 von 85", "144'529", "942", "223",
        "145'694",
        # candidates
        "53'308", "36'282", "54'616",
    )))


def test_upload_election_wabsti_majorz_fail(election_day_app_gr):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    headers_result = [
        'AnzMandate',
        'BFS',
        'StimmBer',
        'StimmAbgegeben',
        'StimmLeer',
        'StimmUngueltig',
        'StimmGueltig',
    ]

    headers_candidate = [
        'kandid_1',
        'kandname_1',
        'kandvorname_1',
        'stimmen_1',
        'kandid_2',
        'kandname_2',
        'kandvorname_2',
        'stimmen_2',
        'kandid_3',
        'kandname_3',
        'kandvorname_3',
        'stimmen_3',
    ]

    headers_elected = [
        'ID',
        'Name',
        'Vorname',
    ]

    # no data
    csv_result = '{}\r\n'.format(','.join(headers_result),).encode('utf-8')
    csv_elected = '{}\r\n'.format(','.join(headers_elected),).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv_result, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', csv_elected, 'text/plain')
    upload = upload.form.submit()

    assert "Keine Daten gefunden" in upload
    assert archive.query().one().progress == (0, 0)

    # Invalid data
    csv_result = '\r\n'.join((
        ','.join(headers_result + headers_candidate),
        ','.join((
            'one',
            'onetwothree',
            '100',
            '90',
            '1',
            '2',
            '80',
            '1',
            'Name',
            'Vorname',
            'zero',
            '2',
            'Leere',
            'Leere',
            '0',
            '3',
            'Ungültige',
            'Ungültige',
            '0',
        )),
        ','.join((
            '1',
            '1234',
            '100',
            '90',
            '1',
            '2',
            '80',
            '1',
            'Name',
            'Vorname',
            '60',
            '2',
            'Leere Zeilen',
            'Leere Zeilen',
            '0',
            '3',
            'Ungültige Stimmen',
            'Ungültige Stimmen',
            '0',
        )),
    )).encode('utf-8')
    csv_elected = '\r\n'.join((
        ','.join(headers_elected),
        ','.join((
            '1',
            'Name',
            'Vorname',
        )),
        ','.join((
            '2',
            'Peterson',
            'Peter',
        ))
    )).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv_result, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', csv_elected, 'text/plain')
    upload = upload.form.submit()

    assert "Ungültige Wahldaten" in upload
    assert "1234 ist unbekannt" in upload
    assert "Ungültige Gemeindedaten" in upload
    assert "Unbekannter Kandidierender" in upload
    assert archive.query().one().progress == (0, 0)

    # Missing headers
    headers_result.remove('AnzMandate')
    headers_elected.remove('ID')
    csv_result = '{}\r\n'.format(','.join(headers_result),).encode('utf-8')
    csv_elected = '{}\r\n'.format(','.join(headers_elected),).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv_result, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', csv_elected, 'text/plain')
    upload = upload.form.submit()

    assert "Fehlende Spalten: AnzMandate" in upload
    assert "Fehlende Spalten: ID" in upload
    assert archive.query().one().progress == (0, 0)


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabsti_proporz.tar.gz'),
])
def test_upload_election_wabsti_proporz(election_day_app, tar_file):
    archive = ArchivedResultCollection(election_day_app.session())
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 3
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()
        connections = f.extractfile(f.next()).read()
        stats = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # candidates
        "3'240", "10'174", "17'034"
    )))
    assert archive.query().one().progress == (11, 0)

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['connections'] = Upload('cons.csv', connections, 'text/plain')
    upload.form['statistics'] = Upload('stats.csv', stats, 'text/plain')
    upload.form['complete'] = True
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')

    assert all((expected in results for expected in (
        # totals
        "11 von 11", "74'803", "40'200", "53.74 %", "39'067", "118", "1'015",
        "116'689",
        # connections
        "30'532", "4'178", "807",
        "25'528", "20'584", "35'543",
        # candidates
        "3'240", "10'174", "17'034"
    )))

    elected = "ID,Name,Vorname\n401,Pfister,Gerhard\n"
    elected = elected + "601,Pezzatti,Bruno\n1501,Aeschi,Thomas\n"
    elected = elected.encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['connections'] = Upload('cons.csv', connections, 'text/plain')
    upload.form['statistics'] = Upload('stats.csv', stats, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', elected, 'text/plain')
    upload.form['complete'] = True
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "11 von 11", "3 von 3", "74'803", "40'200", "53.74 %", "39'067",
        "118", "1'015", "116'689",
        # connections
        "30'532", "4'178", "807",
        # candidates
        "3'240", "10'174", "17'034"
    )))

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['connections'] = Upload('cons.csv', connections, 'text/plain')
    upload.form['statistics'] = Upload('stats.csv', stats, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', elected, 'text/plain')
    upload.form['complete'] = True
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "11 von 11", "3 von 3", "74'803", "40'200", "53.74 %", "39'067",
        "118", "1'015", "116'689",
        # connections
        "30'532", "4'178", "807",
        # candidates
        "3'240", "10'174", "17'034"
    )))


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/sesam_majorz.tar.gz'),
])
def test_upload_election_majorz_roundtrip(election_day_app_gr, tar_file):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    assert archive.query().one().progress == (125, 125)

    export = client.get('/election/election/data-csv').text.encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', export, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    second_export = client.get('/election/election/data-csv').text
    second_export = second_export.encode('utf-8')

    assert export == second_export

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['majority'] = '500'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    export = client.get('/election/election/data-csv').text.encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', export, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    second_export = client.get('/election/election/data-csv').text
    second_export = second_export.encode('utf-8')

    assert export == second_export


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/sesam_proporz.tar.gz'),
])
def test_upload_election_proporz_roundtrip(election_day_app_gr, tar_file):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    assert archive.query().one().progress == (125, 125)

    export = client.get('/election/election/data-csv').text.encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', export, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    second_export = client.get('/election/election/data-csv').text
    second_export = second_export.encode('utf-8')

    assert export == second_export

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', second_export, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    third_export = client.get('/election/election/data-csv').text
    third_export = third_export.encode('utf-8')

    assert export == second_export
    assert second_export == third_export
    assert export == third_export


def test_upload_election_onegov_ballot_fail(election_day_app_gr):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    headers = [
        'election_title',
        'election_date',
        'election_type',
        'election_mandates',
        'election_absolute_majority',
        'election_counted_entities',
        'election_total_entities',
        'entity_name',
        'entity_id',
        'entity_elegible_voters',
        'entity_received_ballots',
        'entity_blank_ballots',
        'entity_invalid_ballots',
        'entity_unaccounted_ballots',
        'entity_accounted_ballots',
        'entity_blank_votes',
        'entity_invalid_votes',
        'entity_accounted_votes',
        'list_name',
        'list_id',
        'list_number_of_mandates',
        'list_votes',
        'list_connection',
        'list_connection_parent',
        'candidate_family_name',
        'candidate_first_name',
        'candidate_id',
        'candidate_elected',
        'candidate_votes',
    ]

    # no data
    csv = '{}\r\n'.format(','.join(headers),).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Keine Daten gefunden" in upload
    assert archive.query().one().progress == (0, 0)

    # Invalid data
    csv = '\r\n'.join((
        ','.join(headers),
        ','.join((
            'Election',
            '2015-03-02',
            'proporz',
            '1',
            '0',
            'one',
            'one',
            'Town',
            '1234',
            '1013',
            '428',
            '2',
            '16',
            '18',
            '410',
            '13',
            '0',
            '2037',
            'Party',
            'x',
            'zero',
            'one',
            'five',
            'one',
            'Muster',
            'Peter',
            'y',
            'False',
            'forty',
        ))
    )).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ungültige Wahldaten" in upload
    assert "1234 ist unbekannt" in upload
    assert "Ungültige Listendaten" in upload
    assert "Ungültige Listenresultate" in upload
    assert "Ungültige Kandidierendendaten" in upload
    assert "Ungültige Kandidierendenresultate" in upload
    assert archive.query().one().progress == (0, 0)

    # Missing headers
    headers.remove('entity_id')
    csv = '{}\r\n'.format(','.join(headers),).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Fehlende Spalten: entity_id" in upload
    assert archive.query().one().progress == (0, 0)


def test_upload_election_invalidate_cache(election_day_app_gr):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # Invalid data
    csv = (
        'election_title,election_date,election_type,election_mandates,'
        'election_absolute_majority,election_counted_entities,'
        'election_total_entities,entity_name,'
        'entity_id,entity_elegible_voters,'
        'entity_received_ballots,entity_blank_ballots,'
        'entity_invalid_ballots,entity_unaccounted_ballots,'
        'entity_accounted_ballots,entity_blank_votes,'
        'entity_invalid_votes,entity_accounted_votes,list_name,'
        'list_id,list_number_of_mandates,list_votes,list_connection,'
        'list_connection_parent,candidate_family_name,candidate_first_name,'
        'candidate_id,candidate_elected,candidate_votes\r\n'
        'Election,2015-03-02,proporz,1,0,1,1,Town,3503,1013,428,2,16,18,410,'
        '13,0,2037,Party,1,0,1,5,1,Muster,Peter,1,False,40'
    )

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    assert archive.query().one().progress == (1, 1)

    anonymous = Client(election_day_app_gr)
    anonymous.get('/locale/de_CH').follow()

    assert "1'013" in anonymous.get('/election/election')

    csv = csv.replace('1013', '1015')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    assert "1'013" not in anonymous.get('/election/election')
    assert "1'015" in anonymous.get('/election/election')


def test_upload_election_temporary_results_majorz(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # SESAM: "Anzahl Gemeinden" + missing lines
    csv = '\n'.join((
        (
            'Anzahl Sitze,Anzahl Gemeinden,Wahlkreis-Nr,Stimmberechtigte,'
            'Wahlzettel,Leere Wahlzettel,Ungültige Wahlzettel,Leere Stimmen,'
            'Ungueltige Stimmen,Kandidaten-Nr,Name,Vorname,Stimmen,Gewaehlt'
        ),
        '7,2 von 11,1701,13567,40,0,0,18,0,1,Hegglin,Peter,36,FALSE',
        '7,2 von 11,1701,13567,40,0,0,18,0,2,Hürlimann,Urs,25,FALSE',
        '7,2 von 11,1702,9620,41,0,1,6,0,1,Hegglin,Peter,34,FALSE',
        '7,2 von 11,1702,9620,41,0,1,6,0,2,Hürlimann,Urs,28,FALSE',
    )).encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_sesam = client.get('/election/election/data-csv').text
    assert 'Baar,1701,13567' in result_sesam
    assert 'Cham,1702,9620' in result_sesam
    assert 'Zug' not in result_sesam

    # Wabsti: form value + (optionally) missing lines
    csv = '\n'.join((
        (
            'AnzMandate,BFS,StimmBer,StimmAbgegeben,StimmLeer,StimmUngueltig,'
            'StimmGueltig,KandID_1,KandName_1,KandVorname_1,Stimmen_1,'
            'KandResultArt_1,KandID_2,KandName_2,KandVorname_2,Stimmen_2,'
            'KandResultArt_2,KandID_3,KandName_3,KandVorname_3,Stimmen_3,'
            'KandResultArt_3,KandID_4,KandName_4,KandVorname_4,Stimmen_4,'
            'KandResultArt_4'
        ),
        (
            '7,1701,13567,40,0,0,40,1,Hegglin,Peter,36,2,2,Hürlimann,Urs,25,'
            '2,1000,Leere Zeilen,,18,9,1001,Ungültige Stimmen,,0,9'
        ),
        (
            '7,1702,9620,41,0,1,40,1,Hegglin,Peter,34,2,2,Hürlimann,Urs,28,2,'
            '1000,Leere Zeilen,,6,9,1001,Ungültige Stimmen,,0,9'
        )
    )).encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 0)

    result_wabsti = client.get('/election/election/data-csv').text
    assert 'Baar,1701,13567' in result_wabsti
    assert 'Cham,1702,9620' in result_wabsti
    assert 'Zug' not in result_wabsti

    upload.form['complete'] = True
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 2)

    result_wabsti = client.get('/election/election/data-csv').text
    assert '2,2,Baar,1701' in result_wabsti

    assert result_sesam == result_wabsti.replace('2,2', '2,11')

    # Onegov internal: misssing and number of municpalities
    csv = '\n'.join((
        (
            'election_title,election_date,election_type,election_mandates,'
            'election_absolute_majority,election_counted_entities,'
            'election_total_entities,entity_name,'
            'entity_id,entity_elegible_voters,'
            'entity_received_ballots,entity_blank_ballots,'
            'entity_invalid_ballots,entity_unaccounted_ballots,'
            'entity_accounted_ballots,entity_blank_votes,'
            'entity_invalid_votes,entity_accounted_votes,'
            'list_name,list_id,list_number_of_mandates,list_votes,'
            'list_connection,list_connection_parent,candidate_family_name,'
            'candidate_first_name,candidate_id,candidate_elected,'
            'candidate_votes'
        ),
        (
            'majorz,2015-01-01,majorz,7,,2,11,Baar,1701,13567,40,0,0,0,40,18,'
            '0,262,,,,0,,,Hegglin,Peter,1,False,36'
        ),
        (
            'majorz,2015-01-01,majorz,7,,2,11,Baar,1701,13567,40,0,0,0,40,18,'
            '0,262,,,,0,,,Hürlimann,Urs,2,False,25'
        ),
        (
            'majorz,2015-01-01,majorz,7,,2,11,Cham,1702,9620,41,0,1,1,40,6,0,'
            '274,,,,0,,,Hegglin,Peter,1,False,34'
        ),
        (
            'majorz,2015-01-01,majorz,7,,2,11,Cham,1702,9620,41,0,1,1,40,6,0,'
            '274,,,,0,,,Hürlimann,Urs,2,False,28'
        ),
    )).encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_onegov = client.get('/election/election/data-csv').text

    assert result_sesam == result_onegov


def test_upload_election_temporary_results_proporz(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # SESAM: "Anzahl Gemeinden" + missing lines
    csv = '\n'.join((
        (
            'Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,'
            'Leere Wahlzettel,Ungültige Wahlzettel,Leere Stimmen,Listen-Nr,'
            'Partei-ID,Parteibezeichnung,HLV-Nr,ULV-Nr,'
            'Kandidatenstimmen unveränderte Wahlzettel,'
            'Kandidatenstimmen veränderte Wahlzettel,'
            'Zusatzstimmen unveränderte Wahlzettel,'
            'Zusatzstimmen veränderte Wahlzettel,Anzahl Sitze Liste,'
            'Kandidaten-Nr,Gewählt,Name,Vorname,'
            'Stimmen Total aus Wahlzettel,Anzahl Gemeinden'
        ),
        (
            '2,1701,14119,7462,77,196,122,1,1,ALG,,,1435,0,0,0,0,101,FALSE,'
            'Lustenberger,Andreas,948,2 von 11'
        ),
        (
            '2,1701,14119,7462,77,196,122,1,1,ALG,,,1435,0,0,0,0,102,FALSE,'
            'Schriber-Neiger,Hanni,208,2 von 11'
        ),
        (
            '2,1702,9926,4863,0,161,50,1,1,ALG,,,533,0,0,0,0,101,FALSE,'
            'Lustenberger,Andreas,290,2 von 11'
        ),
        (
            '2,1702,9926,4863,0,161,50,1,1,ALG,,,533,0,0,0,0,102,FALSE,'
            'Schriber-Neiger,Hanni,105,2 von 11'
        ),
    )).encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_sesam = client.get('/election/election/data-csv').text
    assert 'Baar,1701,14119' in result_sesam
    assert 'Cham,1702,9926' in result_sesam
    assert 'Zug' not in result_sesam

    # Wabsti: form value + (optionally) missing lines
    csv = '\n'.join((
        (
            'Einheit_BFS,Kand_Nachname,Kand_Vorname,Liste_KandID,Liste_ID,'
            'Liste_Code,Kand_StimmenTotal,Liste_ParteistimmenTotal'
        ),
        '1701,Lustenberger,Andreas,101,1,ALG,948,1435',
        '1701,Schriber-Neiger,Hanni,102,1,ALG,208,1435',
        '1702,Lustenberger,Andreas,101,1,ALG,290,533',
        '1702,Schriber-Neiger,Hanni,102,1,ALG,105,533',
    )).encode('utf-8')
    csv_stat = '\n'.join((
        (
            'Einheit_BFS,StimBerTotal,WZEingegangen,WZLeer,WZUngueltig,'
            'StmWZVeraendertLeerAmtlLeer'
        ),
        '1701,14119,7462,77,196,122',
        '1702,9926,4863,0,161,50',
    )).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['statistics'] = Upload('data.csv', csv_stat, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 0)

    result_wabsti = client.get('/election/election/data-csv').text
    assert 'Baar,1701,14119' in result_wabsti
    assert 'Cham,1702,9926' in result_wabsti
    assert 'Zug' not in result_wabsti

    upload.form['complete'] = True
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 2)

    result_wabsti = client.get('/election/election/data-csv').text
    assert '2,2,Baar,1701' in result_wabsti

    assert result_sesam == result_wabsti.replace('2,2', '2,11')

    # Onegov internal: misssing and number of municpalities
    csv = '\n'.join((
        (
            'election_title,election_date,election_type,election_mandates,'
            'election_absolute_majority,election_counted_entities,'
            'election_total_entities,entity_name,'
            'entity_id,entity_elegible_voters,'
            'entity_received_ballots,entity_blank_ballots,'
            'entity_invalid_ballots,entity_unaccounted_ballots,'
            'entity_accounted_ballots,entity_blank_votes,'
            'entity_invalid_votes,entity_accounted_votes,'
            'list_name,list_id,list_number_of_mandates,list_votes,'
            'list_connection,list_connection_parent,candidate_family_name,'
            'candidate_first_name,candidate_id,candidate_elected,'
            'candidate_votes'
        ),
        (
            'election,2015-01-01,proporz,2,0,2,11,Baar,1701,14119,7462,77,196,'
            '273,7189,122,0,14256,ALG,1,0,1435,,,Lustenberger,Andreas,101,'
            'False,948'
        ),
        (
            'election,2015-01-01,proporz,2,0,2,11,Baar,1701,14119,7462,77,196,'
            '273,7189,122,0,14256,ALG,1,0,1435,,,Schriber-Neiger,Hanni,102,'
            'False,208'
        ),
        (
            'election,2015-01-01,proporz,2,0,2,11,Cham,1702,9926,4863,0,161,'
            '161,4702,50,0,9354,ALG,1,0,533,,,Lustenberger,Andreas,101,'
            'False,290'
        ),
        (
            'election,2015-01-01,proporz,2,0,2,11,Cham,1702,9926,4863,0,161,'
            '161,4702,50,0,9354,ALG,1,0,533,,,Schriber-Neiger,Hanni,102,'
            'False,105'
        ),
    )).encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_onegov = client.get('/election/election/data-csv').text

    assert result_sesam == result_onegov


def test_upload_election_available_formats_canton(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    upload = client.get('/election/election/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'internal', 'sesam', 'wabsti'
    ]

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'canton'
    new.form.submit()

    upload = client.get('/election/election/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'internal', 'sesam', 'wabsti'
    ]


def test_upload_election_available_formats_municipality(election_day_app_bern):
    client = Client(election_day_app_bern)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    upload = client.get('/election/election/upload')
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'canton'
    new.form.submit()

    upload = client.get('/election/election/upload')
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'municipality'
    new.form.submit()

    upload = client.get('/election/election/upload')
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']


def test_upload_communal_election(election_day_app_kriens):
    archive = ArchivedResultCollection(election_day_app_kriens.session())
    client = Client(election_day_app_kriens)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'municipality'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    headers = [
        'election_absolute_majority',
        'election_counted_entities',
        'election_total_entities',
        'entity_id',
        'entity_elegible_voters',
        'entity_received_ballots',
        'entity_blank_ballots',
        'entity_invalid_ballots',
        'entity_blank_votes',
        'entity_invalid_votes',
        'list_name',
        'list_id',
        'list_number_of_mandates',
        'list_votes',
        'list_connection',
        'list_connection_parent',
        'candidate_family_name',
        'candidate_first_name',
        'candidate_id',
        'candidate_elected',
        'candidate_vote'
    ]

    csv = '{}\r\n'.format(','.join(headers),).encode('utf-8')

    csv = '\r\n'.join((
        ','.join(headers),
        '3294,1,1,1059,18699,6761,124,51,0,0,,,,,,,Koch,Patrick,1,False,1621',
        '3294,1,1,1059,18699,6761,124,51,0,0,,,,,,,Konrad,Simon,2,False,1707',
        '3294,1,1,1059,18699,6761,124,51,0,0,,,,,,,Faé,Franco,3,False,3176',
        '3294,1,1,1059,18699,6761,124,51,0,0,,,,,,,Vereinzelte,,4,False,82',
    )).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert "erfolgreich hochgeladen" in upload.form.submit()
    assert archive.query().one().progress == (1, 1)

    result = client.get('/election/election')
    assert '36.16' in result
    assert 'Wahlkreise' not in result
    assert '<td>Total' not in result


def test_upload_communal_election_districts(election_day_app_bern):
    archive = ArchivedResultCollection(election_day_app_bern.session())
    client = Client(election_day_app_bern)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'municipality'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    headers = [
        'election_absolute_majority',
        'election_counted_entities',
        'election_total_entities',
        'entity_id',
        'entity_elegible_voters',
        'entity_received_ballots',
        'entity_blank_ballots',
        'entity_invalid_ballots',
        'entity_blank_votes',
        'entity_invalid_votes',
        'list_name',
        'list_id',
        'list_number_of_mandates',
        'list_votes',
        'list_connection',
        'list_connection_parent',
        'candidate_family_name',
        'candidate_first_name',
        'candidate_id',
        'candidate_elected',
        'candidate_vote'
    ]

    csv = '{}\r\n'.format(','.join(headers),).encode('utf-8')

    csv = '\r\n'.join((
        ','.join(headers),
        '12606,6,6,1,15159,5522,265,503,0,0,,,,,,,V1,N1,1,True,3596',
        '12606,6,6,2,9399,3342,161,333,0,0,,,,,,,V1,N1,1,True,2139',
        '12606,6,6,3,12599,4439,184,441,0,0,,,,,,,V1,N1,1,True,2827',
        '12606,6,6,4,18461,6487,289,624,0,0,,,,,,,V1,N1,1,True,3647',
        '12606,6,6,5,13880,4985,205,466,0,0,,,,,,,V1,N1,1,True,3192',
        '12606,6,6,6,12999,4506,170,430,0,0,,,,,,,V1,N1,1,True,2227',
        '12606,6,6,1,15159,5522,265,503,0,0,,,,,,,V2,N2,2,False,608',
        '12606,6,6,2,9399,3342,161,333,0,0,,,,,,,V2,N2,2,False,352',
        '12606,6,6,3,12599,4439,184,441,0,0,,,,,,,V2,N2,2,False,466',
        '12606,6,6,4,18461,6487,289,624,0,0,,,,,,,V2,N2,2,False,943',
        '12606,6,6,5,13880,4985,205,466,0,0,,,,,,,V2,N2,2,False,489',
        '12606,6,6,6,12999,4506,170,430,0,0,,,,,,,V2,N2,2,False,489',
        '12606,6,6,1,15159,5522,265,503,0,0,,,,,,,V3,N3,3,False,550',
        '12606,6,6,2,9399,3342,161,333,0,0,,,,,,,V3,N3,3,False,357',
        '12606,6,6,3,12599,4439,184,441,0,0,,,,,,,V3,N3,3,False,521',
        '12606,6,6,4,18461,6487,289,624,0,0,,,,,,,V3,N3,3,False,984',
        '12606,6,6,5,13880,4985,205,466,0,0,,,,,,,V3,N3,3,False,633',
        '12606,6,6,6,12999,4506,170,430,0,0,,,,,,,V3,N3,3,False,1190',
    )).encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert "erfolgreich hochgeladen" in upload.form.submit()
    assert archive.query().one().progress == (6, 6)

    result = client.get('/election/election')
    assert '35.49' in result
    assert 'Wahlkreise' in result
    assert '<td>Total' in result
