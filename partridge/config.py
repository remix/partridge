import networkx as nx
import numpy as np

from partridge.parsers import \
    vparse_bool, \
    vparse_date, \
    vparse_time


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
            'dependencies': {
                'agency_id': 'agency_id',
            },
        }),
        ('calendar.txt', 'trips.txt', {
            'dependencies': {
                'service_id': 'service_id',
            },
        }),
        ('calendar_dates.txt', 'trips.txt', {
            'dependencies': {
                'service_id': 'service_id',
            },
        }),
        ('fare_attributes.txt', 'fare_rules.txt', {
            'dependencies': {
                'fare_id': 'fare_id',
            },
        }),
        ('fare_rules.txt', 'stops.txt', {
            'dependencies': {
                'origin_id': 'zone_id',
                'destination_id': 'zone_id',
                'contains_id': 'zone_id',
            },
        }),
        ('fare_rules.txt', 'routes.txt', {
            'dependencies': {
                'route_id': 'route_id',
            },
        }),
        ('frequencies.txt', 'trips.txt', {
            'dependencies': {
                'trip_id': 'trip_id',
            },
        }),
        ('routes.txt', 'trips.txt', {
            'dependencies': {
                'route_id': 'route_id',
            },
        }),
        ('shapes.txt', 'trips.txt', {
            'dependencies': {
                'shape_id': 'shape_id',
            },
        }),
        ('stops.txt', 'stop_times.txt', {
            'dependencies': {
                'stop_id': 'stop_id',
            },
        }),
        ('stop_times.txt', 'trips.txt', {
            'dependencies': {
                'trip_id': 'trip_id',
            },
        }),
        ('transfers.txt', 'stops.txt', {
            'dependencies': {
                'from_stop_id': 'stop_id',
                'to_stop_id': 'stop_id',
            },
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
                'monday': vparse_bool,
                'tuesday': vparse_bool,
                'wednesday': vparse_bool,
                'thursday': vparse_bool,
                'friday': vparse_bool,
                'saturday': vparse_bool,
                'sunday': vparse_bool,
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
                'exception_type': np.int8,
            },
            'required_columns': (
                'service_id',
                'date',
                'exception_type',
            ),
        }),
        ('fare_attributes.txt', {
            'converters': {
                'price': np.float32,
                'payment_method': np.int8,
                'transfer_duration': np.int64,
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
                'headway_secs': np.int16,
                'exact_times': np.int64,
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
                'route_type': np.int8,
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
                'shape_pt_lat': np.float32,
                'shape_pt_lon': np.float32,
                'shape_pt_sequence': np.int16,
                'shape_dist_traveled': np.float32,
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
                'stop_lat': np.float32,
                'stop_lon': np.float32,
                'location_type': np.int8,
                'wheelchair_boarding': np.int8,
                'pickup_type': np.int8,
                'drop_off_type': np.int8,
                'shape_dist_traveled': np.float32,
                'timepoint': np.int8,
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
                'pickup_type': np.int8,
                'shape_dist_traveled': np.float32,
                'stop_sequence': np.int16,
                'timepoint': np.int8,
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
                'transfer_type': np.int8,
                'min_transfer_time': np.int64,
            },
            'required_columns': (
                'from_stop_id',
                'to_stop_id',
                'transfer_type',
            ),
        }),
        ('trips.txt', {
            'converters': {
                'direction_id': np.int8,
                'wheelchair_accessible': np.int8,
                'bikes_allowed': np.int8,
            },
            'required_columns': (
                'route_id',
                'service_id',
                'trip_id',
            ),
        }),
    ])


'''
Writer configs
'''


def extract_agencies_config():
    G = empty_config()
    add_edge_config(G)

    G.remove_edges_from([
        ('routes.txt', 'trips.txt'),
        ('agency.txt', 'routes.txt'),
    ])

    G.add_edges_from([
        ('trips.txt', 'routes.txt', {
            'dependencies': {
                'route_id': 'route_id',
            },
        }),
        ('routes.txt', 'agency.txt', {
            'dependencies': {
                'agency_id': 'agency_id',
            },
        }),
    ])

    return G


def extract_routes_config():
    G = empty_config()
    add_edge_config(G)
    return G
