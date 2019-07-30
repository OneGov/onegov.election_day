from onegov.core.converters import extended_date_encode
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from sedate import utcnow
from wtforms.fields.html5 import DateField
from wtforms import StringField
from onegov.election_day import _


class ArchiveSearchForm(Form):

    term = StringField(
        label=_("Text Retrieval"),
        render_kw={'size': 4, 'clear': True},
        description=_(
            "Searches the title of the election/vote and the short code."
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
        coerce=int,
        choices=(
            (1, _("Yes")),
            (0, _("No")),
        ),
        render_kw={'size': 4},
        description=_(
            "Has effect if votes is checked."
        ),

    )

    type_ = MultiCheckboxField(
        label=_("Type"),
        render_kw={'size': 4, 'clear': False},
        choices=(
            ('vote', _("Vote")),
            ('election', _("Election")),
            ('election_compound', _("Compounds of elections"))
        )
    )

    domain = MultiCheckboxField(
        label=_("Domain"),
        render_kw={'size': 4, 'clear': False},
        choices=(
            ('federation', _("Federal")),
            ('canton', _("Cantonal")),
            ('region', _("Regional")),
            ('municipality', _("Municipality"))
        )
    )

    def on_request(self):
        # Roves crf token from query params
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

    def select_all(self, name):
        field = getattr(self, name)
        field.data = list(next(zip(*field.choices)))

    def apply_model(self):
        self.select_all('domain')
        self.select_all('type_')
        self.select_all('result')
        self.to_date.data = utcnow()

