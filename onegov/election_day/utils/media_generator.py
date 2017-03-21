from babel.dates import format_date
from base64 import b64decode
from copy import deepcopy
from datetime import date
from io import BytesIO, StringIO
from json import loads
from onegov.ballot import Ballot, Election, Vote
from onegov.core.utils import groupbylist
from onegov.core.utils import module_path
from onegov.election_day import _
from onegov.election_day.utils import pdf_filename, svg_filename
from onegov.election_day.utils.pdf import Pdf
from onegov.election_day.views.election import get_candidates_results
from onegov.election_day.views.election import get_connection_results
from onegov.election_day.views.election.candidates import (
    view_election_candidates_data
)
from onegov.election_day.views.election.connections import (
    view_election_connections_data
)
from onegov.election_day.views.election.lists import view_election_lists_data
from onegov.election_day.views.election.panachage import (
    view_election_panachage_data
)
from onegov.election_day.views.election.parties import (
    view_election_parties_data,
    get_party_results,
    get_party_deltas
)
from pdfdocument.document import MarkupParagraph
from reportlab.lib.units import cm
from requests import post
from rjsmin import jsmin
from shutil import copyfileobj
from textwrap import shorten, wrap
from onegov.election_day import log


class MediaGenerator():

    def __init__(self, app, force, cleanup):
        self.app = app
        self.force = force
        self.cleanup = cleanup
        self.pdf_dir = self.app.configuration.get('pdf_directory', 'pdf')
        self.svg_dir = self.app.configuration.get('svg_directory', 'svg')
        self.renderer = app.configuration.get('d3_renderer').rstrip('/')
        self.session = self.app.session()

        self.supported_charts = {
            'bar': {
                'main': 'barChart',
                'scripts': ('d3.chart.bar.js',),
            },
            'grouped': {
                'main': 'groupedChart',
                'scripts': ('d3.chart.grouped.js',),
            },
            'sankey': {
                'main': 'sankeyChart',
                'scripts': ('d3.sankey.js', 'd3.chart.sankey.js'),
            },
            'map': {
                'main': 'ballotMap',
                'scripts': ('underscore.js', 'topojson.js', 'd3.chart.map.js'),
            }
        }

        # Read and minify the javascript sources
        self.scripts = {}
        for chart in self.supported_charts:
            self.scripts[chart] = []
            for script in self.supported_charts[chart]['scripts']:
                path = module_path(
                    'onegov.election_day', 'assets/js/{}'.format(script)
                )
                with open(path, 'r') as f:
                    self.scripts[chart].append(jsmin(f.read()))

    def translate(self, text, locale):
        """ Translates the given string. """

        translator = self.app.translations.get(locale)
        return text.interpolate(translator.gettext(text))

    def get_chart(self, chart, fmt, data, width=1000, params=None):
        """ Returns the requested chart from the d3-render service as a
        PNG/PDF/SVG.

        """

        assert chart in self.supported_charts
        assert fmt in ('pdf', 'svg')

        params = params or {}
        params.update({
            'data': data,
            'width': width,
            'viewport_width': width  # only used for PDF and PNG
        })

        response = post('{}/d3/{}'.format(self.renderer, fmt), json={
            'scripts': self.scripts[chart],
            'main': self.supported_charts[chart]['main'],
            'params': params
        })

        response.raise_for_status()

        if fmt == 'svg':
            return StringIO(response.text)
        else:
            return BytesIO(b64decode(response.text))

    def get_map(self, fmt, data, year, width=1000, params=None):
        """ Returns the request chart from the d3-render service as a
        PNG/PDF/SVG.

        """
        mapdata = None
        path = module_path(
            'onegov.election_day',
            'static/mapdata/{}/{}.json'.format(year, self.app.principal.id)
        )
        with open(path, 'r') as f:
            mapdata = loads(f.read())

        params = params or {}
        params.update({
            'mapdata': mapdata,
            'canton': self.app.principal.canton
        })

        return self.get_chart('map', fmt, data, width, params)

    def generate_pdf(self, item, path, locale):
        """ Generates the PDF for an election or a vote. """

        with self.app.filestorage.open(path, 'wb') as f:

            def translate(content):
                return self.translate(content, locale)

            def draw_footer(canvas, doc):
                canvas.saveState()
                canvas.setFont('Helvetica', 9)
                canvas.drawString(
                    doc.leftMargin,
                    doc.bottomMargin / 2,
                    '© {} {}'.format(
                        date.today().year,
                        self.app.principal.name
                    )
                )
                canvas.drawRightString(
                    doc.pagesize[0] - doc.rightMargin,
                    doc.bottomMargin / 2,
                    '{}'.format(canvas._pageNumber)
                )
                canvas.restoreState()

            def draw_header_and_footer(canvas, doc):
                draw_footer(canvas, doc)

                canvas.saveState()
                title = item.title_translations.get(locale) or item.title
                lines = wrap(title, 110)[:2]
                if len(lines) > 1:
                    lines[1] = shorten(lines[1], 100)
                text = canvas.beginText()
                text.setFont('Helvetica', 9)
                text.setTextOrigin(
                    doc.leftMargin,
                    doc.pagesize[1] - doc.topMargin * 2 / 3
                )
                text.textLines(lines)
                canvas.drawText(text)
                canvas.restoreState()

            pdf = Pdf(f)
            pdf.init_a4_portrait(
                page_fn=draw_footer,
                page_fn_later=draw_header_and_footer
            )

            def table_style_results(columns):
                return pdf.style.tableHead + (
                    ('ALIGN', (0, 0), (columns - 1, -1), 'LEFT'),
                    ('ALIGN', (columns, 0), (-1, -1), 'RIGHT'),
                )

            table_style_factoids = pdf.style.table + (
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
            )

            def indent_style(level):
                style = deepcopy(pdf.style.normal)
                style.leftIndent = level * style.fontSize
                return style

            # Add Header
            pdf.h1(item.title_translations.get(locale) or item.title)
            pdf.p(format_date(item.date, format='long', locale=locale))
            pdf.spacer()

            # Election
            if isinstance(item, Election):
                majorz = item.type == 'majorz'

                # Factoids
                pdf.table(
                    [
                        [
                            translate(_('Turnout')),
                            translate(_('Elegible Voters')),
                            translate(_('Received Ballots')),
                        ], [
                            '{0:.2f}%'.format(item.turnout),
                            item.elegible_voters,
                            item.received_ballots,
                        ]
                    ],
                    'even',
                    style=table_style_factoids
                )
                pdf.spacer()
                pdf.table(
                    [
                        [
                            translate(_('Mandates')),
                            translate(_('Absolute majority')) if majorz
                            else '',
                            '',
                        ], [
                            translate(_(
                                '${counted} of ${total}',
                                mapping={
                                    'counted': item.allocated_mandates,
                                    'total': item.number_of_mandates}
                            )),
                            item.absolute_majority if majorz else ''
                            ''
                        ],
                    ],
                    'even',
                    style=table_style_factoids
                )
                pdf.spacer()
                pdf.spacer()

                # Lists
                data = view_election_lists_data(item, None)
                if data and data.get('results'):
                    pdf.h2(translate(_('Lists')))
                    pdf.pdf(self.get_chart('bar', 'pdf', data))
                    pdf.spacer()
                    pdf.table(
                        [[
                            translate(_('List')),
                            translate(_('Mandates')),
                            translate(_('single_votes')),
                        ]] + [[
                            r['text'],
                            r['value2'],
                            r['value'],
                        ] for r in data['results']],
                        [None, 2 * cm, 2 * cm],
                        style=table_style_results(1)
                    )
                    pdf.pagebreak()

                # Candidates
                data = view_election_candidates_data(item, None)
                if data and data.get('results'):
                    pdf.h2(translate(_('Candidates')))
                    pdf.pdf(self.get_chart('bar', 'pdf', data))
                    pdf.spacer()
                    if majorz:
                        pdf.table(
                            [[
                                translate(_('Candidate')),
                                translate(_('Elected')),
                                translate(_('single_votes')),
                            ]] + [[
                                '{} {}'.format(r[0], r[1]),
                                translate(_('Yes')) if r[2] else '',
                                r[3],
                            ] for r in get_candidates_results(
                                item, self.session
                            )],
                            [None, 2 * cm, 2 * cm],
                            style=table_style_results(2)
                        )
                    else:
                        pdf.table(
                            [[
                                translate(_('Candidate')),
                                translate(_('List')),
                                translate(_('Elected')),
                                translate(_('single_votes')),
                            ]] + [[
                                '{} {}'.format(r[0], r[1]),
                                r[4],
                                translate(_('Yes')) if r[2] else '',
                                r[3],
                            ] for r in get_candidates_results(
                                item, self.session
                            )],
                            [None, None, 2.3 * cm, 2 * cm],
                            style=table_style_results(3)
                        )
                    pdf.pagebreak()

                # Connections
                data = view_election_connections_data(item, None)
                if data and data.get('links') and data.get('nodes'):
                    pdf.h2(translate(_('List connections')))
                    pdf.pdf(self.get_chart('sankey', 'pdf', data,
                                           params={'inverse': True}))
                    pdf.figcaption(translate(_('figcaption_connections')))
                    pdf.spacer()

                    connections = get_connection_results(item, self.session)
                    spacers = []
                    table = [[
                        '{} / {} / {}'.format(
                            translate(_('List connection')),
                            translate(_('Sublist connection')),
                            translate(_('Party'))
                        ),
                        translate(_('single_votes'))
                    ]]
                    for connection in connections:
                        table += [[
                            MarkupParagraph('{} {}'.format(
                                translate(_('List connection')),
                                connection[0]
                            ), indent_style(0)),
                            connection[1]
                        ]]
                        for sc in connection[3]:
                            table += [[
                                MarkupParagraph('{} {}'.format(
                                    translate(_('Sublist connection')),
                                    sc[0]
                                ), indent_style(1)),
                                sc[1]
                            ]]
                            table += [[
                                MarkupParagraph(l[0], indent_style(2)),
                                l[1]
                            ] for l in sc[2]]
                        table += [[
                            MarkupParagraph(l[0], indent_style(1)),
                            l[1]
                        ] for l in connection[2]]
                        spacers.append(len(table))

                    pdf.table(
                        table,
                        [None, 2 * cm, 2 * cm],
                        style=table_style_results(1) + tuple([
                            ('TOPPADDING', (0, row), (-1, row), 15)
                            for row in spacers[:-1]
                        ])
                    )
                    pdf.pagebreak()

                # Parties
                data = view_election_parties_data(item, None)
                if data and data.get('results'):
                    pdf.h2(translate(_('Parties')))
                    pdf.pdf(self.get_chart('grouped', 'pdf', data))
                    pdf.figcaption(translate(_('figcaption_parties')))
                    pdf.spacer()
                    years, parties = get_party_results(item)
                    deltas, results = get_party_deltas(item, years, parties)
                    if deltas:
                        pdf.table(
                            [[
                                translate(_('Party')),
                                translate(_('Mandates')),
                                translate(_('single_votes')),
                                translate(_('single_votes')),
                                'Δ {}'.format(years[0]),
                            ]] + [[
                                r[0],
                                r[-4],
                                r[-2],
                                r[-3],
                                r[-1],
                            ] for r in results],
                            [None, 2 * cm, 2 * cm, 2 * cm, 2 * cm],
                            style=table_style_results(1)
                        )
                    else:
                        pdf.table(
                            [[
                                translate(_('Party')),
                                translate(_('Mandates')),
                                translate(_('single_votes')),
                                translate(_('single_votes')),
                            ]] + [[
                                r[0],
                                r[1],
                                r[3],
                                r[2],
                            ] for r in results],
                            [None, 2 * cm, 2 * cm, 2 * cm],
                            style=table_style_results(1)
                        )
                    pdf.pagebreak()

                # Panachage
                data = view_election_panachage_data(item, None)
                if data and data.get('links') and data.get('nodes'):
                    pdf.h2(translate(_('Panachage')))
                    pdf.pdf(self.get_chart('sankey', 'pdf', data))
                    pdf.figcaption(translate(_('figcaption_panachage')))
                    pdf.spacer()
                    pdf.pagebreak()

                # Statistics
                summarize = item.total_entities != 1

                pdf.h2(translate(_('Election statistics')))
                if not summarize:
                    res = item.results.first()
                    pdf.table(
                        [[
                            translate(_('Turnout')),
                            '{0:.2f} %'.format(res.turnout)
                        ], [
                            translate(_('Elegible Voters')),
                            res.elegible_voters
                        ], [
                            translate(_('Accounted Votes')),
                            res.accounted_votes
                        ], [
                            translate(_('Received Ballots')),
                            res.received_ballots or '0'
                        ], [
                            translate(_('Accounted Ballots')),
                            res.accounted_ballots or '0'
                        ], [
                            translate(_('Blank Ballots')),
                            res.blank_ballots or '0'
                        ], [
                            translate(_('Invalid Ballots')),
                            res.invalid_ballots or '0']
                        ],
                        'even'
                    )

                else:
                    pdf.table(
                        [[
                            translate(_('Electoral District')),
                            translate(_('Turnout')),
                            translate(_('Elegible Voters')),
                            translate(_('Accounted Votes')),
                        ]] + [[
                            result.group,
                            '{0:.2f} %'.format(result.turnout),
                            result.elegible_voters,
                            result.accounted_votes,
                        ] for result in item.results] + [[
                            translate(_('Total')),
                            '{0:.2f} %'.format(item.turnout),
                            item.elegible_voters,
                            item.accounted_votes,
                        ]],
                        [None, 2.8 * cm, 2.8 * cm, 2.8 * cm],
                        style=table_style_results(1)
                    )
                    pdf.spacer()
                    pdf.table(
                        [[
                            translate(_('Electoral District')),
                            translate(_('Received Ballots')),
                            translate(_('Accounted Ballots')),
                            translate(_('Blank Ballots')),
                            translate(_('Invalid Ballots')),

                        ]] + [[
                            result.group,
                            result.received_ballots or '0',
                            result.accounted_ballots or '0',
                            result.blank_ballots or '0',
                            result.invalid_ballots or '0',
                        ] for result in item.results] + [[
                            translate(_('Total')),
                            item.received_ballots or '0',
                            item.accounted_ballots or '0',
                            item.blank_ballots or '0',
                            item.invalid_ballots or '0',
                        ]],
                        [None, 2.8 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm],
                        style=table_style_results(1)
                    )
                pdf.pagebreak()

            if isinstance(item, Vote):
                summarize = item.proposal.results.count() != 1

                # Answer
                answer = _('Rejected')
                if item.answer == 'accepted':
                    answer = _('Accepted')
                if item.counter_proposal:
                    proposal = item.proposal.accepted
                    counter_proposal = item.counter_proposal.accepted
                    if not proposal and not counter_proposal:
                        answer = _('Proposal and counter proposal rejected')
                    if proposal and not counter_proposal:
                        answer = _('Proposal accepted')
                    if not proposal and counter_proposal:
                        answer = _('Counter proposal accepted')
                    if proposal and counter_proposal:
                        if item.tie_breaker.accepted:
                            answer = _('Tie breaker in favor of the proposal')
                        else:
                            answer = _(
                                'Tie breaker in favor of the counter proposal'
                            )
                pdf.p(translate(answer))
                pdf.spacer()

                ballots = ((None, item.proposal),)
                if item.counter_proposal:
                    ballots = (
                        (_('Proposal'), item.proposal),
                        (_('Counter Proposal'), item.counter_proposal),
                        (_('Tie-Breaker'), item.tie_breaker),
                    )

                for title, ballot in ballots:
                    if title:
                        pdf.h2(translate(title))

                    # Factoids
                    pdf.table(
                        [
                            [
                                translate(_('turnout_vote')),
                                translate(_('elegible_voters_vote')),
                                translate(_('Cast Ballots')),
                            ], [
                                '{0:.2f}%'.format(ballot.turnout),
                                ballot.elegible_voters,
                                ballot.cast_ballots,
                            ]
                        ],
                        'even',
                        style=table_style_factoids
                    )
                    pdf.spacer()
                    if summarize:
                        pdf.spacer()

                    # Results
                    if not summarize:
                        res = ballot.results.first()
                        pdf.table(
                            [[
                                translate(_('Yes %')).replace('%', '').strip(),
                                translate(_('No %')).replace('%', '').strip(),
                                '{} / {}'.format(
                                    translate(_('Empty')),
                                    translate(_('Invalid'))
                                ),
                            ], [
                                '{} / {:.2f}%'.format(
                                    res.yeas or '0',
                                    res.yeas_percentage
                                ),
                                '{} / {:.2f}%'.format(
                                    res.nays or '0',
                                    res.nays_percentage
                                ),
                                '{} / {}'.format(
                                    res.empty or '0',
                                    res.invalid or '0',
                                )
                            ]],
                            'even',
                            style=table_style_factoids
                        )
                        pdf.spacer()

                    if summarize:
                        pdf.table(
                            [[
                                translate(_('Electoral District')),
                                translate(_('Result')),
                                translate(_('Yes %')),
                                translate(_('No %')),
                            ]] + [[
                                result.group,
                                translate(_('Accepted')) if result.accepted
                                else translate(_('Rejected')),
                                '{0:.2f}%'.format(result.yeas_percentage),
                                '{0:.2f}%'.format(result.nays_percentage),
                            ] for result in ballot.results] + [[
                                translate(_('Total')),
                                translate(_('Accepted')) if ballot.accepted
                                else translate(_('Rejected')),
                                '{0:.2f}%'.format(ballot.yeas_percentage),
                                '{0:.2f}%'.format(ballot.nays_percentage),
                            ]],
                            [None, 2.3 * cm, 2 * cm, 2 * cm],
                            style=table_style_results(2)
                        )

                    # Map
                    if self.app.principal.use_maps:
                        pdf.pagebreak()
                        data = ballot.percentage_by_entity()
                        params = {
                            'yay': translate(_('Yay')),
                            'nay': translate(_('Nay')),
                        }
                        year = item.date.year
                        pdf.pdf(
                            self.get_map('pdf', data, year, params=params),
                            0.8
                        )
                        pdf.pagebreak()
                    else:
                        pdf.spacer()

                    if summarize:
                        pdf.table(
                            [[
                                translate(_('Electoral District')),
                                translate(_('Empty')),
                                translate(_('Invalid')),
                                translate(_('Yes %')).replace('%', '').strip(),
                                translate(_('No %')).replace('%', '').strip(),
                            ]] + [[
                                result.group,
                                result.empty or '0',
                                result.invalid or '0',
                                result.yeas or '0',
                                result.nays or '0',
                            ] for result in ballot.results] + [[
                                translate(_('Total')),
                                ballot.empty or '0',
                                ballot.invalid or '0',
                                ballot.yeas or '0',
                                ballot.nays or '0',
                            ]],
                            [None, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm],
                            style=table_style_results(1)
                        )
                        pdf.pagebreak()

            # Add related link
            link = (item.meta or {}).get('related_link', '')
            if link:
                pdf.h2(translate(_('Related link')))
                pdf.p_markup('<a href="{link}">{link}</a>'.format(link=link))

            pdf.generate()

    def create_pdfs(self):
        """ Generates all PDFs for the given application.

        Only generates PDFs if not already generated since the last change of
        the election or vote. Allows to force the re-creation of the PDF.

        Optionally cleans up unused PDFs.

        """

        # Get all elections and votes
        items = self.session.query(Election).all()
        items.extend(self.session.query(Vote).all())

        # Read existing PDFs
        if not self.app.filestorage.exists(self.pdf_dir):
            self.app.filestorage.makedir(self.pdf_dir)
        existing = self.app.filestorage.listdir(self.pdf_dir)

        # Generate the PDFs
        for locale in self.app.locales:
            for item in items:
                filename = pdf_filename(item, locale)
                if (self.force or filename not in existing) and item.counted:
                    path = '{}/{}'.format(self.pdf_dir, filename)
                    if self.app.filestorage.exists(path):
                        self.app.filestorage.remove(path)
                    try:
                        self.generate_pdf(item, path, locale)
                        log.info("{} created".format(filename))
                    except Exception as ex:
                        # Don't leave probably broken PDFs laying around
                        if self.app.filestorage.exists(path):
                            self.app.filestorage.remove(path)
                        raise ex

        # Delete old PDFs
        if self.cleanup:
            existing = self.app.filestorage.listdir(self.pdf_dir)
            existing = dict(groupbylist(
                existing,
                key=lambda a: a.split('.')[0]
            ))

            # Delete orphaned files
            created = [
                pdf_filename(item, '').split('.')[0] for item in items
            ]
            for id in set(existing.keys()) - set(created):
                for name in existing[id]:
                    self.app.filestorage.remove(
                        '{}/{}'.format(self.pdf_dir, name)
                    )

            # Delete old files
            for files in existing.values():
                files = sorted(files, reverse=True)
                for name in files[len(self.app.locales):]:
                    self.app.filestorage.remove(
                        '{}/{}'.format(self.pdf_dir, name)
                    )

    def generate_svg(self, item, type_, locale=None):
        """ Creates the requested SVG. """

        assert type_ in (
            'lists', 'candidates', 'connections', 'parties', 'panachage', 'map'
        )

        existing = self.app.filestorage.listdir(self.svg_dir)
        filename = svg_filename(item, type_, locale)

        if not (self.force or filename not in existing):
            return None

        path = '{}/{}'.format(self.svg_dir, filename)
        if self.app.filestorage.exists(path):
            self.app.filestorage.remove(path)

        chart = None
        if type_ == 'lists':
            data = view_election_lists_data(item, None)
            if data and data.get('results'):
                chart = self.get_chart('bar', 'svg', data)

        if type_ == 'candidates':
            data = view_election_candidates_data(item, None)
            if data and data.get('results'):
                chart = self.get_chart('bar', 'svg', data)

        if type_ == 'connections':
            data = view_election_connections_data(item, None)
            if data and data.get('links') and data.get('nodes'):
                chart = self.get_chart('sankey', 'svg', data,
                                       params={'inverse': True})

        if type_ == 'parties':
            data = view_election_parties_data(item, None)
            if data and data.get('results'):
                chart = self.get_chart('grouped', 'svg', data)

        if type_ == 'panachage':
            data = view_election_panachage_data(item, None)
            if data and data.get('links') and data.get('nodes'):
                chart = self.get_chart('sankey', 'svg', data)

        if type_ == 'map':
            data = item.percentage_by_entity()
            params = {
                'yay': self.translate(_('Yay'), locale),
                'nay': self.translate(_('Nay'), locale),
            }
            year = item.vote.date.year
            chart = self.get_map('svg', data, year, params=params)

        if chart:
            with self.app.filestorage.open(path, 'w') as f:
                copyfileobj(chart, f)
            log.info("{} created".format(filename))

        return filename

    def create_svgs(self):
        """ Generates all SVGs for the given application.

        Only generates SVGs if not already generated since the last change of
        the election or vote. Allows to force the re-creation of the SVG.

        Optionally cleans up unused SVGs.

        """

        # Read existing SVGs
        if not self.app.filestorage.exists(self.svg_dir):
            self.app.filestorage.makedir(self.svg_dir)

        # Generate the SVGs
        for election in self.session.query(Election):
            self.generate_svg(election, 'candidates')
            if election.type == 'proporz':
                self.generate_svg(election, 'lists')
                self.generate_svg(election, 'connections')
                self.generate_svg(election, 'parties')
                self.generate_svg(election, 'panachage')
        if self.app.principal.use_maps:
            for vote in self.session.query(Vote):
                for locale in self.app.locales:
                    self.generate_svg(
                        vote.proposal, 'map', locale
                    )
                    if vote.counter_proposal:
                        self.generate_svg(vote.counter_proposal, 'map', locale)
                        self.generate_svg(vote.tie_breaker, 'map', locale)

        # Delete old SVGs
        if self.cleanup:
            existing = self.app.filestorage.listdir(self.svg_dir)
            existing = dict(groupbylist(
                existing,
                key=lambda a: a.split('.')[0]
            ))

            # Delete orphaned files
            created = [
                svg_filename(item, '', '').split('.')[0]
                for item in
                self.session.query(Election).all() +
                self.session.query(Ballot).all() +
                self.session.query(Vote).all()
            ]
            for id in set(existing.keys()) - set(created):
                for name in existing[id]:
                    self.app.filestorage.remove(
                        '{}/{}'.format(self.svg_dir, name)
                    )

            # Delete old files
            for files in existing.values():
                if len(files):
                    files = sorted(files, reverse=True)
                    ts = files[0].split('.')[1]
                    for name in [f for f in files if ts not in f]:
                        self.app.filestorage.remove(
                            '{}/{}'.format(self.svg_dir, name)
                        )