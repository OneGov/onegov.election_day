from morepath.request import Response
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election import get_connection_results
from onegov.election_day.utils.election import get_connections_data
from sqlalchemy.orm import object_session


@ElectionDayApp.json(
    model=Election,
    name='connections-data',
    permission=Public
)
def view_election_connections_data(self, request):

    """" View the list connections as JSON.

    Used to for the connection sankey chart.

    """

    return get_connections_data(self, request)


@ElectionDayApp.html(
    model=Election,
    name='connections-chart',
    template='embed.pt',
    permission=Public
)
def view_election_connections_chart(self, request):

    """" View the connections as sankey chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'type': 'sankey',
        'inverse': 'true',
        'data_url': request.link(self, name='connections-data'),
    }


@ElectionDayApp.html(
    model=Election,
    name='connections',
    template='election/connections.pt',
    permission=Public
)
def view_election_connections(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'connections')

    return {
        'election': self,
        'layout': layout,
        'connections': get_connection_results(self, object_session(self)),
    }


@ElectionDayApp.view(
    model=Election,
    name='connections-svg',
    permission=Public
)
def view_election_connections_svg(self, request):

    """ View the connections as SVG. """

    layout = ElectionLayout(self, request, 'connections')
    if not layout.svg_path:
        return Response(status='503 Service Unavailable')

    content = None
    with request.app.filestorage.open(layout.svg_path, 'r') as f:
        content = f.read()

    return Response(
        content,
        content_type='application/svg; charset=utf-8',
        content_disposition='inline; filename={}'.format(layout.svg_name)
    )
