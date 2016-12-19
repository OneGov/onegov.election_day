from collections import OrderedDict
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout, ElectionsLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import handle_headerless_params


@ElectionDayApp.json(model=Election, permission=Public, name='panachage-data')
def view_election_panachage_data(self, request):
    """" View the panachage data as JSON. Used to for the panachage sankey
    chart.

    Returns for every list: The number of votes from other lists. The modified
    xplus remaining votes from the own list.
    """

    if self.type == 'majorz':
        return {}

    if not self.has_panachage_data:
        return {}

    nodes = OrderedDict()
    nodes['left.999'] = {'name': '-'}
    for list_ in self.lists:
        nodes['left.{}'.format(list_.list_id)] = {'name': list_.name}
    for list_ in self.lists:
        nodes['right.{}'.format(list_.list_id)] = {'name': list_.name}
    node_keys = list(nodes.keys())

    links = []
    for list_target in self.lists:
        target = node_keys.index('right.{}'.format(list_target.list_id))
        remaining = list_target.votes - sum(
            [r.votes for r in list_target.panachage_results]
        )
        for result in list_target.panachage_results:
            source_list_id = result.source_list_id
            source = node_keys.index('left.{}'.format(source_list_id))
            votes = result.votes
            if list_target.list_id == result.source_list_id:
                votes += remaining
            links.append({
                'source': source,
                'target': target,
                'value': votes
            })

    count = 0
    for key in nodes.keys():
        count = count + 1
        nodes[key]['id'] = count

    return {
        'nodes': list(nodes.values()),
        'links': links,
        'title': self.title
    }


@ElectionDayApp.html(model=Election, permission=Public,
                     name='panachage-chart', template='embed.pt')
def view_election_panachage_chart(self, request):
    """" View the panachage data as sankey chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    request.include('sankey_chart')
    request.include('frame_resizer')

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'sankey': request.link(self, name='panachage-data')
        }
    }


@ElectionDayApp.html(model=Election, template='election/panachage.pt',
                     name='panachage', permission=Public)
def view_election_panachage(self, request):
    """" The main view. """

    request.include('sankey_chart')
    request.include('tablesorter')

    handle_headerless_params(request)

    return {
        'election': self,
        'layout': ElectionsLayout(self, request, 'panachage')
    }