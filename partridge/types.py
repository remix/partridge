import datetime
from typing import FrozenSet, Iterable, List, Mapping, NewType, Union


CountsByDate = Mapping[datetime.date, int]
Dates = List[datetime.date]
ServiceID = NewType("ServiceID", str)
Service = FrozenSet[ServiceID]
ServicesByDate = Mapping[datetime.date, Service]
DatesByService = Mapping[Service, FrozenSet[datetime.date]]
Value = Union[str, Iterable]
View = Mapping[str, Mapping[str, Value]]
