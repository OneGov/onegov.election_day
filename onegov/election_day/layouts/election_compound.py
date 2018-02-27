from cached_property import cached_property
from onegov.election_day import _
from onegov.election_day.layouts.default import DefaultLayout
from onegov.election_day.utils import pdf_filename


class ElectionCompoundLayout(DefaultLayout):

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab

    @cached_property
    def all_tabs(self):
        return (
            'districts',
            'parties',
            'candidates',
            'data'
        )

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'districts':
            return self.request.app.principal.label('districts')
        if tab == 'candidates':
            return _("Elected candidates")
        if tab == 'parties':
            return _("Parties")
        if tab == 'data':
            return _("Downloads")

        return ''

    def visible(self, tab=None):
        if not self.model.has_results:
            return False

        tab = self.tab if tab is None else tab

        if tab == 'parties':
            return False
            # todo: self.model.party_results.first()

        return True

    @cached_property
    def main_view(self):
        return self.request.link(self.model, 'districts')

    @cached_property
    def menu(self):
        return [
            (
                self.title(tab),
                self.request.link(self.model, tab),
                'active' if self.tab == tab else ''
            ) for tab in self.all_tabs if self.visible(tab)
        ]

    # todo:
    # @cached_property
    # def pdf_path(self):
    #     """ Returns the path to the PDF file or None, if it is not available.
    #     """
    #
    #     path = 'pdf/{}'.format(pdf_filename(self.model, self.request.locale))
    #     if self.request.app.filestorage.exists(path):
    #         return path
    #
    #     return None

    @cached_property
    def majorz(self):
        return not self.proporz

    @cached_property
    def proporz(self):
        election = self.model.elections.first()
        if election and election.type == 'proporz':
            return True
        return False