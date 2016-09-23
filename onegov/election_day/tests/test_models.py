import json
import textwrap
import pytest

from datetime import date, datetime, timezone
from freezegun import freeze_time
from onegov.ballot import Election, Vote
from onegov.election_day.models import Archive
from onegov.election_day.models import Notification
from onegov.election_day.models import Principal
from onegov.election_day.models import WebhookNotification
from onegov.election_day.models.principal import cantons
from onegov.election_day.tests import DummyRequest
from time import sleep
from unittest.mock import patch


def test_load_principal():
    principal = Principal.from_yaml(textwrap.dedent("""
        name: Foobar
        logo:
        canton: zg
        color: '#000'
    """))

    assert principal.name == 'Foobar'
    assert principal.name == 'Foobar'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.webhooks == []

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Foobar
        logo:
        canton: zg
        color: '#000'
        base: 'http://www.zg.ch'
        analytics: "<script type=\\"text/javascript\\"></script>"
        webhooks:
          - 'http://abc.com/1'
          - 'http://abc.com/2'
    """))

    assert principal.name == 'Foobar'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.color == '#000'
    assert principal.base == 'http://www.zg.ch'
    assert principal.base_domain == 'zg.ch'
    assert principal.analytics == '<script type="text/javascript"></script>'
    assert principal.webhooks == ['http://abc.com/1', 'http://abc.com/2']


def test_municipalities():
    principal = Principal(name='Zug', canton='zg', logo=None, color=None)

    municipalities = {
        1701: {'name': 'Baar'},
        1702: {'name': 'Cham'},
        1703: {'name': 'Hünenberg'},
        1704: {'name': 'Menzingen'},
        1705: {'name': 'Neuheim'},
        1706: {'name': 'Oberägeri'},
        1707: {'name': 'Risch'},
        1708: {'name': 'Steinhausen'},
        1709: {'name': 'Unterägeri'},
        1710: {'name': 'Walchwil'},
        1711: {'name': 'Zug'},
    }

    assert principal.municipalities == {
        2009: municipalities,
        2010: municipalities,
        2011: municipalities,
        2012: municipalities,
        2013: municipalities,
        2014: municipalities,
        2015: municipalities,
        2016: municipalities,
    }

    for year in range(2009, 2013):
        assert not principal.is_year_available(year)
    for year in range(2013, 2017):
        assert principal.is_year_available(year)
    for year in range(2009, 2017):
        assert principal.is_year_available(year, map_required=False)

    for canton in cantons:
        principal = Principal(
            name=canton, canton=canton, logo=None, color=None
        )

        assert principal.municipalities[2009]
        assert principal.municipalities[2010]
        assert principal.municipalities[2011]
        assert principal.municipalities[2012]
        assert principal.municipalities[2013]
        assert principal.municipalities[2014]
        assert principal.municipalities[2015]


def test_archive(session):
    archive = Archive(session)

    assert archive.for_date(2015).date == 2015

    assert archive.get_years() == []
    assert archive.latest() is None

    for year in (2009, 2011, 2014, 2016):
        session.add(
            Election(
                title="Election {}".format(year),
                domain='federation',
                type='majorz',
                date=date(year, 1, 1),
            )
        )
    for year in (2007, 2011, 2015, 2016):
        session.add(
            Vote(
                title="Vote {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )

    session.flush()

    assert archive.get_years() == [2016, 2015, 2014, 2011, 2009, 2007]

    assert archive.latest() == archive.for_date(2016).by_date()
    assert archive.latest() == archive.for_date('2016').by_date()
    assert archive.latest() == archive.for_date('2016-01-01').by_date()

    assert archive.for_date('2016-02-02').by_date() is None

    for year in (2009, 2011, 2014, 2016):
        assert (
            ('election', 'federation', date(year, 1, 1)),
            [session.query(Election).filter_by(date=date(year, 1, 1)).one()]
        ) in archive.for_date(year).by_date()

    for year in (2007, 2011, 2015, 2016):
        assert (
            ('vote', 'federation', date(year, 1, 1)),
            [session.query(Vote).filter_by(date=date(year, 1, 1)).one()]
        ) in archive.for_date(year).by_date()


def test_notification(session):
    notification = Notification()
    notification.action = 'action'
    notification.last_change = datetime(2007, 1, 1, 0, 0, tzinfo=timezone.utc)

    session.add(notification)
    session.flush()

    notification = session.query(Notification).one()
    assert notification.id
    assert notification.action == 'action'
    assert notification.last_change == datetime(2007, 1, 1, 0, 0,
                                                tzinfo=timezone.utc)
    assert notification.election_id is None
    assert notification.vote_id is None

    with freeze_time("2008-01-01 00:00"):
        session.add(
            Election(
                title="Election",
                domain='federation',
                type='majorz',
                date=date(2011, 1, 1)
            )
        )
        session.flush()
        election = session.query(Election).one()

        notification = Notification()
        notification.update_from_model(election)
        assert notification.election_id == election.id
        assert notification.vote_id == None
        assert notification.last_change == datetime(2008, 1, 1, 0, 0,
                                                    tzinfo=timezone.utc)

    with freeze_time("2009-01-01 00:00"):
        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        session.flush()
        vote = session.query(Vote).one()

        notification = Notification()
        notification.update_from_model(vote)
        assert notification.election_id == None
        assert notification.vote_id == vote.id
        assert notification.last_change == datetime(2009, 1, 1, 0, 0,
                                                    tzinfo=timezone.utc)

    with pytest.raises(NotImplementedError):
        notification.trigger(DummyRequest(), election)
    with pytest.raises(NotImplementedError):
        notification.trigger(DummyRequest(), vote)


def test_webhook_notification(session):
    with freeze_time("2008-01-01 00:00"):
        session.add(
            Election(
                title="Election",
                domain='federation',
                type='majorz',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        notification = WebhookNotification()
        notification.trigger(DummyRequest(), election)

        assert notification.action == 'webhooks'
        assert notification.election_id == election.id
        assert notification.last_change == datetime(2008, 1, 1, 0, 0,
                                                    tzinfo=timezone.utc)

        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        notification.trigger(DummyRequest(), vote)

        assert notification.action == 'webhooks'
        assert notification.vote_id == vote.id
        assert notification.last_change == datetime(2008, 1, 1, 0, 0,
                                                    tzinfo=timezone.utc)

        with patch('urllib.request.urlopen') as urlopen:
            request = DummyRequest()
            request.app.principal.webhooks = ['http://abc.com/1']

            notification.trigger(DummyRequest(), election)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == len(data)

            assert json.loads(data.decode('utf-8')) == {
                'date': '2011-01-01',
                'domain': 'federation',
                'last_modified': '2008-01-01T00:00:00+00:00',
                'progress': {'counted': 0, 'total': 0},
                'title': {'de_CH': 'Election'},
                'type': 'election',
                'url': 'Election/election'
            }

            notification.trigger(DummyRequest(), vote)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == len(data)

            assert json.loads(data.decode('utf-8')) == {
                'answer': '',
                'date': '2011-01-01',
                'domain': 'federation',
                'last_modified': '2008-01-01T00:00:00+00:00',
                'nays_percentage': 100.0,
                'progress': {'counted': 0.0, 'total': 0.0},
                'title': {'de_CH': 'Vote'},
                'type': 'vote',
                'url': 'Vote/vote',
                'yeas_percentage': 0.0
            }
