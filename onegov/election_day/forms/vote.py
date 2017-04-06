from datetime import date
from onegov.election_day import _
from onegov.form import Form
from wtforms import RadioField, StringField
from wtforms.fields.html5 import DateField, URLField
from wtforms.validators import InputRequired


class VoteForm(Form):
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

    upload_type = RadioField(
        _("Upload"),
        choices=[
            ('manual', _("Manual")),
            ('wabsti', _("Automatic (Wabsti)")),
        ],
        validators=[
            InputRequired()
        ],
        default='manual'
    )

    upload_wabsti_district = StringField(
        label=_("Automatic upload (Wabsti): 'SortWahlkreis'"),
        validators=[
            InputRequired()
        ],
        render_kw=dict(force_simple=True),
        depends_on=('upload_type', 'wabsti'),
    )

    upload_wabsti_number = StringField(
        label=_("Automatic upload (Wabsti): 'SortGeschaeft'"),
        validators=[
            InputRequired()
        ],
        render_kw=dict(force_simple=True),
        depends_on=('upload_type', 'wabsti'),
    )

    upload_wabsti_folder = StringField(
        label=_("Automatic upload (Wabsti): Folder"),
        validators=[
            InputRequired()
        ],
        render_kw=dict(force_simple=True),
        depends_on=('upload_type', 'wabsti')
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

        model.title_translations = {}
        model.title_translations['de_CH'] = self.vote_de.data

        if self.vote_fr.data:
            model.title_translations['fr_CH'] = self.vote_fr.data

        if self.vote_it.data:
            model.title_translations['it_CH'] = self.vote_it.data

        if self.vote_rm.data:
            model.title_translations['rm_CH'] = self.vote_rm.data

        if not model.meta:
            model.meta = {}
        model.meta['related_link'] = self.related_link.data
        model.meta['upload_type'] = self.upload_type.data
        model.meta['upload_wabsti_district'] = self.upload_wabsti_district.data
        model.meta['upload_wabsti_number'] = self.upload_wabsti_number.data
        model.meta['upload_wabsti_folder'] = self.upload_wabsti_folder.data

    def apply_model(self, model):
        self.vote_de.data = model.title_translations['de_CH']
        self.vote_fr.data = model.title_translations.get('fr_CH')
        self.vote_it.data = model.title_translations.get('it_CH')
        self.vote_rm.data = model.title_translations.get('rm_CH')

        self.date.data = model.date
        self.domain.data = model.domain
        self.shortcode.data = model.shortcode

        meta_data = model.meta or {}
        self.related_link.data = meta_data.get('related_link', '')
        self.upload_type.data = meta_data.get('upload_type', 'manual')
        self.upload_wabsti_district.data = meta_data.get(
            'upload_wabsti_district', ''
        )
        self.upload_wabsti_number.data = meta_data.get(
            'upload_wabsti_number', ''
        )
        self.upload_wabsti_folder.data = meta_data.get(
            'upload_wabsti_folder', ''
        )
