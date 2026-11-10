import pytest
from datetime import datetime, timedelta
from bike_sharing.models import Bike, Dock, Station, User, Ride, BikeStatus, ReceiptPrinter
from bike_sharing.network import Network
from bike_sharing.exceptions import (
    DockOccupiedError,
    RideActiveError,
    NoBikeError,
    NoActiveRideError,
    StationFullError
)

def test_bike_in_exact_one_place_rule():
    station_a = Station("Chilonzor", 2)
    station_b = Station("Yunusobod", 2)
    bike = Bike("B001")
    
    station_a.docks[0].park_bike(bike)
    assert station_a.docks[0].bike == bike
    
    with pytest.raises(DockOccupiedError):
        station_a.docks[0].park_bike(Bike("B002"))
        
    with pytest.raises(TypeError):
        station_a.docks.append(Dock(3))  

def test_dock_occupied_error():
    dock = Dock(1)
    bike1 = Bike("B1")
    bike2 = Bike("B2")
    dock.park_bike(bike1)
    with pytest.raises(DockOccupiedError):
        dock.park_bike(bike2)

def test_bike_repair_status():
    station = Station("Chilonzor", 1)
    bike = Bike("B1")
    station.docks[0].park_bike(bike)
    
    bike.send_to_repair()
    assert bike.status == BikeStatus.REPAIR
    assert station.get_available_bike_dock() is None

def test_fee_calculation():
    user = User("U1", "Ali")
    bike = Bike("B1")
    s1 = Station("Chilonzor", 5)
    start_time = datetime(2026, 11, 10, 10, 0, 0)
    
    ride1 = Ride(user, bike, s1, start_time)
    ride1.finish_ride(s1, start_time + timedelta(minutes=15))
    assert ride1.calculate_fee() == 0

    ride2 = Ride(user, bike, s1, start_time)
    ride2.finish_ride(s1, start_time + timedelta(minutes=15, seconds=1))
    assert ride2.calculate_fee() == 500

    ride3 = Ride(user, bike, s1, start_time)
    ride3.finish_ride(s1, start_time + timedelta(minutes=20))
    assert ride3.calculate_fee() == 500

    ride4 = Ride(user, bike, s1, start_time)
    ride4.finish_ride(s1, start_time + timedelta(minutes=20, seconds=1))
    assert ride4.calculate_fee() == 1000

    ride5 = Ride(user, bike, s1, start_time)
    ride5.finish_ride(s1, start_time + timedelta(hours=10))
    assert ride5.calculate_fee() == 20000

def test_happy_path_take_return():
    net = Network()
    chilonzor = Station("Chilonzor", 2)
    yunusobod = Station("Yunusobod", 2)
    net.add_station(chilonzor)
    net.add_station(yunusobod)
    
    bike = Bike("B100")
    chilonzor.docks[0].park_bike(bike)
    
    user = User("U1", "Jasur")
    net.register_user(user)
    
    t0 = datetime(2026, 11, 10, 12, 0)
    ride = net.take_bike(user, chilonzor, t0)
    assert bike.status == BikeStatus.IN_USE
    assert user.active_ride == ride
    
    t1 = t0 + timedelta(minutes=23)
    receipt = net.return_bike(user, yunusobod, t1)
    assert receipt == "Chilonzor -> Yunusobod, 23 min, 1 000 sum"
    assert user.active_ride is None
    assert bike.status == BikeStatus.AVAILABLE

def test_failure_and_recovery_path():
    net = Network()
    start_st = Station("Chilonzor", 2)
    full_st = Station("Yunusobod", 1)
    backup_st = Station("Buyuk Ipak Yoli", 3)
    
    net.add_station(start_st)
    net.add_station(full_st)
    net.add_station(backup_st)
    
    b_occupant = Bike("B_OCC")
    full_st.docks[0].park_bike(b_occupant)
    
    b_user = Bike("B_USER")
    start_st.docks[0].park_bike(b_user)
    
    user = User("U2", "Malika")
    net.register_user(user)
    
    t0 = datetime(2026, 11, 10, 14, 0)
    net.take_bike(user, start_st, t0)
    
    with pytest.raises(StationFullError):
        net.return_bike(user, full_st, t0 + timedelta(minutes=10))
        
    with pytest.raises(StationFullError) as exc_info:
        net.return_bike(user, full_st, t0 + timedelta(minutes=12))
    assert exc_info.value.redirect_station == "Buyuk Ipak Yoli"
    
    t_final = t0 + timedelta(minutes=18)
    receipt = net.return_bike(user, backup_st, t_final)
    assert "Buyuk Ipak Yoli" in receipt
    assert user.active_ride is None
