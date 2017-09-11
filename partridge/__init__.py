from partridge.gtfs import feed, raw_feed


def read_service_ids_by_date(path):
	return feed(path).service_ids_by_date


def read_dates_by_service_ids(path):
	return feed(path).dates_by_service_ids


def read_trip_counts_by_date(path):
	return feed(path).trip_counts_by_date
