from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.forms import ArchiveSearchForm
from datetime import date


def test_apply_model_archive_search_form(session):
    archive = SearchableArchivedResultCollection(session)
    archive.term = 'xxx'
    archive.from_date = date(2222, 1, 1)
    archive.to_date = date(2222, 1, 1)
    archive.answer = ['accepted']
    archive.type = ['election', 'vote']
    archive.domain = ['region', 'municipality']

    form = ArchiveSearchForm()
    # form.request = DummyRequest()
    form.apply_model(archive)
    assert form.term.data == archive.term
    assert form.from_date.data == archive.from_date
    assert form.to_date.data == archive.to_date
    assert form.answer.data == archive.answer
    assert form.type.data == archive.type
    assert form.domain == archive.domain
