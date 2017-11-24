from datetime import date
from onegov.election_day import _
from onegov.form import Form
from wtforms import RadioField
from wtforms import StringField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import URLField
from wtforms.validators import InputRequired


class VoteForm(Form):

    vote_type = RadioField(
        _("Type"),
        choices=[
            ('simple', _("Simple Vote")),
            ('complex', _("Vote with Counter-Proposal")),
        ],
        validators=[
            InputRequired()
        ],
        default='simple'
    )

    vote_de = StringField(
        label=_("Vote (German)"),
        validators=[
            InputRequired()
        ]
    )
    vote_fr = StringField(
        label=_("Vote (French)")
    )
    vote_it = StringField(
        label=_("Vote (Italian)")
    )
    vote_rm = StringField(
        label=_("Vote (Romansh)")
    )

    shortcode = StringField(
        label=_("Shortcode")
    )

    date = DateField(
        label=_("Date"),
        validators=[InputRequired()],
        default=date.today
    )

    domain = RadioField(
        label=_("Type"),
        validators=[
            InputRequired()
        ]
    )

    related_link = URLField(
        label=_("Related link")
    )

    def set_domain(self, principal):
        self.domain.choices = [
            (key, text)
            for key, text in principal.available_domains.items()
        ]

    def update_model(self, model):
        model.date = self.date.data
        model.domain = self.domain.data
        model.shortcode = self.shortcode.data
        model.related_link = self.related_link.data

        model.title_translations = {}
        model.title_translations['de_CH'] = self.vote_de.data
        if self.vote_fr.data:
            model.title_translations['fr_CH'] = self.vote_fr.data
        if self.vote_it.data:
            model.title_translations['it_CH'] = self.vote_it.data
        if self.vote_rm.data:
            model.title_translations['rm_CH'] = self.vote_rm.data

    def apply_model(self, model):
        self.vote_de.data = model.title_translations['de_CH']
        self.vote_fr.data = model.title_translations.get('fr_CH')
        self.vote_it.data = model.title_translations.get('it_CH')
        self.vote_rm.data = model.title_translations.get('rm_CH')

        self.date.data = model.date
        self.domain.data = model.domain
        self.shortcode.data = model.shortcode
        self.related_link.data = model.related_link
        if model.type == 'complex':
            self.vote_type.choices = [
                ('complex', _("Vote with Counter-Proposal"))
            ]
            self.vote_type.data = 'complex'
        else:
            self.vote_type.choices = [('simple', _("Simple Vote"))]
            self.vote_type.data = 'simple'
