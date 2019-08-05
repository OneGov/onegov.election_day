from datetime import date

from onegov.ballot import Vote
from onegov.election_day.models import ArchivedResult


class TestSearchableCollection:

    available_types = [t[0] for t in ArchivedResult.types_of_results]
    available_domains = [d[0] for d in ArchivedResult.types_of_domains]
    available_answers = [0, 1]

    def test_initial_config(self, searchable_archive):
        # Test to_date is always filled in and is type date
        assert searchable_archive.to_date
        assert searchable_archive.from_date is None
        assert isinstance(searchable_archive.to_date, date)

    def test_initial_query(self, searchable_archive):
        # Test initial query without params
        assert len(searchable_archive.query().all()) == 12

    def test_default_values_of_form(self, searchable_archive):
        # Set values like you would when going to search form first time
        archive = searchable_archive
        archive.domain = self.available_domains
        archive.type = self.available_types
        archive.answer = self.available_answers
        archive.term = ''

        sql_query = str(archive.query())
        assert 'WHERE archived_results.date' not in sql_query

    def test_from_date_to_date(self, searchable_archive):
        archive = searchable_archive
        # Test to_date is neglected if from_date is not given
        assert not archive.from_date
        assert 'WHERE archived_results.date' not in str(archive.query())

        # Test if from_date > to_date
        # archive.from_date = date(2019, 1, 1)
        # archive.to_date = date(2018, 1, 1)
        # assert len(archive.query().all()) == 0

        # Test query and results with a value of to_date and from_date
        archive.from_date = date(2009, 1, 1)
        assert 'WHERE archived_results.date' in str(archive.query())
        assert len(archive.query().all()) == 11

    def test_query_with_types(self, searchable_archive):
        # Check if type is queried correctly
        searchable_archive.type = ['vote']
        assert len(searchable_archive.query().all()) == 3

        searchable_archive.type = ['election']
        assert len(searchable_archive.query().all()) == 6

        searchable_archive.type = ['vote', 'election', 'election_compound']
        assert len(searchable_archive.query().all()) == 12

    def test_query_with_domains(self, searchable_archive):
        archive = searchable_archive
        archive.domain = ['federation']
        assert len(archive.query().all()) == 9

        archive.domain = ['canton']
        assert len(archive.query().all()) == 1

        archive.domain = ['region']
        assert len(archive.query().all()) == 1

        archive.domain = ['municipality']
        assert len(archive.query().all()) == 1

    def test_query_with_voting_result(self, session, searchable_archive):
        query = session.query(ArchivedResult)
        results = query.all()
        count = query.count()
        print(count)
        for item in results:
            assert not item.answer
            item.answer = 'accepted'
            # assert item.answer is None      # fails since it has also ''
            print(f'{item.id} - answer: {item.answer}')



    def test_with_with_all_params(self):
        pass
