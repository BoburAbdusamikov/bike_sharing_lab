from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime
import math
from typing import Tuple, Optional
from bike_sharing.exceptions import DockOccupiedError

class BikeStatus(Enum):
    AVAILABLE = auto()
    IN_USE = auto()
    REPAIR = auto()

class Bike:
    def __init__(self, bike_id: str):
        self._bike_id = bike_id
        self._status = BikeStatus.AVAILABLE

    @property
    def bike_id(self) -> str:
        return self._bike_id

    @property
    def status(self) -> BikeStatus:
        return self._status

    def mark_in_use(self) -> None:
        if self._status == BikeStatus.REPAIR:
            raise ValueError("Bike under repair cannot be taken.")
        self._status = BikeStatus.IN_USE

    def mark_available(self) -> None:
        self._status = BikeStatus.AVAILABLE

    def send_to_repair(self) -> None:
        if self._status != BikeStatus.AVAILABLE:
            raise ValueError("Only docked free bikes can be sent to repair.")
        self._status = BikeStatus.REPAIR

    def __repr__(self) -> str:
        return f"Bike({self._bike_id!r}, status={self._status.name})"

class Dock:
    def __init__(self, dock_id: int):
        self._dock_id = dock_id
        self._bike: Optional[Bike] = None

    @property
    def dock_id(self) -> int:
        return self._dock_id

    @property
    def bike(self) -> Optional[Bike]:
        return self._bike

    @property
    def is_free(self) -> bool:
        return self._bike is None

    def park_bike(self, bike: Bike) -> None:
        if not self.is_free:
            raise DockOccupiedError(f"Dock {self._dock_id} is already occupied.")
        self._bike = bike

    def release_bike(self) -> Bike:
        if self.is_free:
            raise ValueError("Dock is empty.")
        if self._bike.status == BikeStatus.REPAIR:
            raise ValueError("Bike in repair cannot be taken.")
        bike = self._bike
        self._bike = None
        return bike

    def __repr__(self) -> str:
        return f"Dock({self._dock_id}, bike={self._bike})"

class Station:
    def __init__(self, name: str, capacity: int):
        self._name = name
        self._capacity = capacity
        # Protect mutable state by instantiating individual docks per instance
        self._docks = tuple(Dock(i + 1) for i in range(capacity))

    @property
    def name(self) -> str:
        return self._name

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def docks(self) -> Tuple[Dock, ...]:
        return self._docks

    @property
    def free_docks_count(self) -> int:
        return sum(1 for d in self._docks if d.is_free)

    @property
    def available_bikes_count(self) -> int:
        return sum(1 for d in self._docks if not d.is_free and d.bike.status == BikeStatus.AVAILABLE)

    def get_free_dock(self) -> Optional[Dock]:
        for dock in self._docks:
            if dock.is_free:
                return dock
        return None

    def get_available_bike_dock(self) -> Optional[Dock]:
        for dock in self._docks:
            if not dock.is_free and dock.bike.status == BikeStatus.AVAILABLE:
                return dock
        return None

    def __len__(self) -> int:
        return sum(1 for d in self._docks if not d.is_free)

    def __str__(self) -> str:
        return f"{self._name}: {len(self)}/{self._capacity} bikes"

    def __repr__(self) -> str:
        return f"Station({self._name!r}, capacity={self._capacity}, free={self.free_docks_count})"

    def __lt__(self, other: "Station") -> bool:
        return self.free_docks_count < other.free_docks_count

class User:
    def __init__(self, user_id: str, name: str):
        self._user_id = user_id
        self._name = name
        self._active_ride: Optional["Ride"] = None

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def active_ride(self) -> Optional["Ride"]:
        return self._active_ride

    @active_ride.setter
    def active_ride(self, ride: Optional["Ride"]) -> None:
        self._active_ride = ride

    def __repr__(self) -> str:
        return f"User({self._user_id!r}, name={self._name!r})"

class Ride:
    FREE_MINUTES = 15
    INTERVAL_MINUTES = 5
    RATE_PER_INTERVAL = 500
    MAX_FEE_CAP = 20000

    def __init__(self, user: User, bike: Bike, start_station: Station, start_time: datetime):
        self._user = user
        self._bike = bike
        self._start_station = start_station
        self._start_time = start_time
        self._end_station: Optional[Station] = None
        self._end_time: Optional[datetime] = None
        self._failed_attempts = 0

    @property
    def user(self) -> User:
        return self._user

    @property
    def bike(self) -> Bike:
        return self._bike

    @property
    def start_station(self) -> Station:
        return self._start_station

    @property
    def end_station(self) -> Optional[Station]:
        return self._end_station

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def end_time(self) -> Optional[datetime]:
        return self._end_time

    @property
    def failed_attempts(self) -> int:
        return self._failed_attempts

    def register_failed_attempt(self) -> int:
        self._failed_attempts += 1
        return self._failed_attempts

    def finish_ride(self, end_station: Station, end_time: datetime) -> int:
        if end_time < self._start_time:
            raise ValueError("End time cannot be prior to start time.")
        self._end_station = end_station
        self._end_time = end_time
        return self.calculate_fee()

    def calculate_fee(self) -> int:
        if not self._end_time or self._end_time < self._start_time:
            raise ValueError("Invalid ride duration or unclosed ride.")
        duration_seconds = (self._end_time - self._start_time).total_seconds()
        duration_minutes = duration_seconds / 60.0

        if duration_minutes <= self.FREE_MINUTES:
            return 0

        billable_minutes = duration_minutes - self.FREE_MINUTES
        intervals = math.ceil(billable_minutes / self.INTERVAL_MINUTES)
        fee = intervals * self.RATE_PER_INTERVAL
        return min(fee, self.MAX_FEE_CAP)

    @property
    def duration_minutes(self) -> int:
        if not self._end_time:
            return 0
        return math.ceil((self._end_time - self._start_time).total_seconds() / 60.0)

class ReceiptPrinter:
    @staticmethod
    def print(ride: Ride) -> str:
        fee = ride.calculate_fee()
        receipt = f"{ride.start_station.name} -> {ride.end_station.name}, {ride.duration_minutes} min, {fee:,} sum".replace(',', ' ')
        return receipt
