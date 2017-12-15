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
