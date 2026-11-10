from datetime import datetime
from typing import Dict, List, Optional
from bike_sharing.models import Station, User, Bike, Ride, BikeStatus, ReceiptPrinter
from bike_sharing.exceptions import (
    RideActiveError,
    NoBikeError,
    NoActiveRideError,
    StationFullError
)

class Network:
    def __init__(self):
        self._stations: Dict[str, Station] = {}
        self._users: Dict[str, User] = {}

    def add_station(self, station: Station) -> None:
        self._stations[station.name] = station

    def register_user(self, user: User) -> None:
        self._users[user.user_id] = user

    def take_bike(self, user: User, station: Station, current_time: datetime) -> Ride:
        if user.active_ride is not None:
            raise RideActiveError(f"User {user.user_id} already has an active ride.")

        dock = station.get_available_bike_dock()
        if dock is None:
            raise NoBikeError(f"Station {station.name} has no available bikes.")

        bike = dock.release_bike()
        bike.mark_in_use()

        ride = Ride(user=user, bike=bike, start_station=station, start_time=current_time)
        user.active_ride = ride
        return ride

    def get_redirect_station((self) -> Station:
        return max(
            sorted(self._stations.values(), key=lambda s: s.name),
            key=lambda s: s.free_docks_count
        )

    def return_bike(self, user: User, station: Station, current_time: datetime) -> str:
        ride = user.active_ride
        if ride is None:
            raise NoActiveRideError(f"User {user.user_id} does not have an active ride.")

        dock = station.get_free_dock()
        if dock is None:
            attempts = ride.register_failed_attempt()
            redirect_name = None
            if attempts >= 2:
                redirect_station = self.get_redirect_station()
                redirect_name = redirect_station.name
                raise StationFullError(
                    f"Station {station.name} is full. Redirected to {redirect_name}.",
                    redirect_station=redirect_name
                )
            raise StationFullError(f"Station {station.name} is full.")

        dock.park_bike(ride.bike)
        ride.bike.mark_available()
        ride.finish_ride(end_station=station, end_time=current_time)
        user.active_ride = None

        return ReceiptPrinter.print(ride)

    def report(self) -> List[Station]:
        return sorted(self._stations.values(), key=lambda s: s.free_docks_count, reverse=True)
