from onegov.election_day.models import ArchivedResult
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms.fields.html5 import DateField
from wtforms import StringField
from onegov.election_day import _


class ArchiveSearchForm(Form):

    term = StringField(
        label=_("Text Retrieval"),
        render_kw={'size': 4, 'clear': True},
        description=_(
            "Searches the title of the election/vote and the short code."
            "Use Wilcards (*) to find not exact results, e.g Nationalrat*."
        ),
    )

    from_date = DateField(
        label=_("From date"),
        render_kw={'size': 4}
    )

    to_date = DateField(
        label=_("To date"),
        render_kw={'size': 4, 'clear': False}
    )

    result = MultiCheckboxField(
        label=_("Voting result"),
        choices=ArchivedResult.types_of_answers,
        render_kw={'size': 4},
        description=_(
            "Has effect if votes is checked."
        ),

    )

    type_ = MultiCheckboxField(
        label=_("Type"),
        render_kw={'size': 4, 'clear': False},
        choices=ArchivedResult.types_of_results
    )

    domain = MultiCheckboxField(
        label=_("Domain"),
        render_kw={'size': 4, 'clear': False},
        choices=ArchivedResult.types_of_domains
    )

    def on_request(self):
        # Roves crf token from query params
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

    def select_all(self, name):
        field = getattr(self, name)
        if not field.data:
            field.data = list(next(zip(*field.choices)))

    def apply_model(self, model):

        self.term.data = model.term
        self.from_date.data = model.from_date
        self.to_date.data = model.to_date
        self.result.data = model.answer
        self.type_.data = model.type
        self.domain.data = model.domain

        self.select_all('domain')
        self.select_all('type_')
        self.select_all('result')
