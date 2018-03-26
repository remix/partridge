# flake8: noqa E501

import networkx as nx

from partridge.parsers import \
    vparse_date, \
    vparse_time, \
    vparse_numeric


def empty_config():
    return nx.DiGraph()


'''
Default configs
'''


def default_config():
    G = empty_config()
    add_edge_config(G)
    add_node_config(G)
    return G


def add_edge_config(g):
    g.add_edges_from([
        ('agency.txt', 'routes.txt', {
            'dependencies': [
                {'agency.txt': 'agency_id', 'routes.txt': 'agency_id'},
            ],
        }),
        ('calendar.txt', 'trips.txt', {
            'dependencies': [
                {'calendar.txt': 'service_id', 'trips.txt': 'service_id'},
            ],
        }),
        ('calendar_dates.txt', 'trips.txt', {
            'dependencies': [
                {'calendar_dates.txt': 'service_id', 'trips.txt': 'service_id'},
            ],
        }),
        ('fare_attributes.txt', 'fare_rules.txt', {
            'dependencies': [
                {'fare_attributes.txt': 'fare_id', 'fare_rules.txt': 'fare_id'},
            ],
        }),
        ('fare_rules.txt', 'stops.txt', {
            'dependencies': [
                {'fare_rules.txt': 'origin_id', 'stops.txt': 'zone_id'},
                {'fare_rules.txt': 'destination_id', 'stops.txt': 'zone_id'},
                {'fare_rules.txt': 'contains_id', 'stops.txt': 'zone_id'},
            ],
        }),
        ('fare_rules.txt', 'routes.txt', {
            'dependencies': [
                {'fare_rules.txt': 'route_id', 'routes.txt': 'route_id'},
            ],
        }),
        ('frequencies.txt', 'trips.txt', {
            'dependencies': [
                {'frequencies.txt': 'trip_id', 'trips.txt': 'trip_id'},
            ],
        }),
        ('routes.txt', 'trips.txt', {
            'dependencies': [
                {'routes.txt': 'route_id', 'trips.txt': 'route_id'},
            ],
        }),
        ('shapes.txt', 'trips.txt', {
            'dependencies': [
                {'shapes.txt': 'shape_id', 'trips.txt': 'shape_id'},
            ],
        }),
        ('stops.txt', 'stop_times.txt', {
            'dependencies': [
                {'stops.txt': 'stop_id', 'stop_times.txt': 'stop_id'},
            ],
        }),
        ('stop_times.txt', 'trips.txt', {
            'dependencies': [
                {'stop_times.txt': 'trip_id', 'trips.txt': 'trip_id'},
            ],
        }),
        ('transfers.txt', 'stops.txt', {
            'dependencies': [
                {'transfers.txt': 'from_stop_id', 'stops.txt': 'stop_id'},
                {'transfers.txt': 'to_stop_id', 'stops.txt': 'stop_id'},
            ],
        }),
    ])


def add_node_config(g):
    g.add_nodes_from([
        ('agency.txt', {
            'required_columns': (
                'agency_name',
                'agency_url',
                'agency_timezone',
            ),
        }),
        ('calendar.txt', {
            'converters': {
                'start_date': vparse_date,
                'end_date': vparse_date,
                'monday': vparse_numeric,
                'tuesday': vparse_numeric,
                'wednesday': vparse_numeric,
                'thursday': vparse_numeric,
                'friday': vparse_numeric,
                'saturday': vparse_numeric,
                'sunday': vparse_numeric,
            },
            'required_columns': (
                'service_id',
                'monday',
                'tuesday',
                'wednesday',
                'thursday',
                'friday',
                'saturday',
                'sunday',
                'start_date',
                'end_date',
            ),
        }),
        ('calendar_dates.txt', {
            'converters': {
                'date': vparse_date,
                'exception_type': vparse_numeric,
            },
            'required_columns': (
                'service_id',
                'date',
                'exception_type',
            ),
        }),
        ('fare_attributes.txt', {
            'converters': {
                'price': vparse_numeric,
                'payment_method': vparse_numeric,
                'transfer_duration': vparse_numeric,
            },
            'required_columns': (
                'fare_id',
                'price',
                'currency_type',
                'payment_method',
                'transfers',
            ),
        }),
        ('fare_rules.txt', {
            'required_columns': (
                'fare_id',
            ),
        }),
        ('feed_info.txt', {
            'converters': {
                'feed_start_date': vparse_date,
                'feed_end_date': vparse_date,
            },
            'required_columns': (
                'feed_publisher_name',
                'feed_publisher_url',
                'feed_lang',
            ),
        }),
        ('frequencies.txt', {
            'converters': {
                'headway_secs': vparse_numeric,
                'exact_times': vparse_numeric,
                'start_time': vparse_time,
                'end_time': vparse_time,
            },
            'required_columns': (
                'trip_id',
                'start_time',
                'end_time',
                'headway_secs',
            ),
        }),
        ('routes.txt', {
            'converters': {
                'route_type': vparse_numeric,
            },
            'required_columns': (
                'route_id',
                'route_short_name',
                'route_long_name',
                'route_type',
            ),
        }),
        ('shapes.txt', {
            'converters': {
                'shape_pt_lat': vparse_numeric,
                'shape_pt_lon': vparse_numeric,
                'shape_pt_sequence': vparse_numeric,
                'shape_dist_traveled': vparse_numeric,
            },
            'required_columns': (
                'shape_id',
                'shape_pt_lat',
                'shape_pt_lon',
                'shape_pt_sequence',
            ),
        }),
        ('stops.txt', {
            'converters': {
                'stop_lat': vparse_numeric,
                'stop_lon': vparse_numeric,
                'location_type': vparse_numeric,
                'wheelchair_boarding': vparse_numeric,
                'pickup_type': vparse_numeric,
                'drop_off_type': vparse_numeric,
                'shape_dist_traveled': vparse_numeric,
                'timepoint': vparse_numeric,
            },
            'required_columns': (
                'stop_id',
                'stop_name',
                'stop_lat',
                'stop_lon',
            ),
        }),
        ('stop_times.txt', {
            'converters': {
                'arrival_time': vparse_time,
                'departure_time': vparse_time,
                'pickup_type': vparse_numeric,
                'shape_dist_traveled': vparse_numeric,
                'stop_sequence': vparse_numeric,
                'timepoint': vparse_numeric,
            },
            'required_columns': (
                'trip_id',
                'arrival_time',
                'departure_time',
                'stop_id',
                'stop_sequence',
            ),
        }),
        ('transfers.txt', {
            'converters': {
                'transfer_type': vparse_numeric,
                'min_transfer_time': vparse_numeric,
            },
            'required_columns': (
                'from_stop_id',
                'to_stop_id',
                'transfer_type',
            ),
        }),
        ('trips.txt', {
            'converters': {
                'direction_id': vparse_numeric,
                'wheelchair_accessible': vparse_numeric,
                'bikes_allowed': vparse_numeric,
            },
            'required_columns': (
                'route_id',
                'service_id',
                'trip_id',
            ),
        }),
    ])


def reroot_graph(G, node):
    '''Return a copy of the graph rooted at the given node'''
    G = G.copy()
    to_add, to_remove = [], []
    for n, successors in nx.bfs_successors(G, source=node):
        for s in successors:
            to_add.append([s, n, G.edges[n, s]])
            to_remove.append([n, s])
    G.remove_edges_from(to_remove)
    G.add_edges_from(to_add)
    return G
