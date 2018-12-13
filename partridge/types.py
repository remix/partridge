import datetime
from typing import Dict, FrozenSet, Iterable, List, Union


CountsByDate = Dict[datetime.date, int]
Dates = List[datetime.date]
Service = FrozenSet[str]
ServicesByDate = Dict[datetime.date, Service]
DatesByService = Dict[Service, FrozenSet[datetime.date]]
Value = Union[str, Iterable]
View = Dict[str, Dict[str, Value]]
