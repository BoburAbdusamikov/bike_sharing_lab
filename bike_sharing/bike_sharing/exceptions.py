class BikeSharingError(Exception):
    """Base exception class for Bike Sharing System."""
    pass

class DockOccupiedError(BikeSharingError):
    """Raised when attempting to place a bike into an already occupied dock."""
    pass

class RideActiveError(BikeSharingError):
    """Raised when a rider attempts to start a new ride while having an active ride."""
    pass

class NoBikeError(BikeSharingError):
    """Raised when attempting to take a bike from a station with no available bikes."""
    pass

class NoActiveRideError(BikeSharingError):
    """Raised when a rider attempts to return a bike without an active ride."""
    pass

class StationFullError(BikeSharingError):
    """Raised when attempting to return a bike to a full station."""
    def __init__(self, message: str, redirect_station: str = None):
        super().__init__(message)
        self.redirect_station = redirect_station
