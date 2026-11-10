# Bike Sharing System - Laboratory 4.2

## Relationships Table

| Pair | Relationship | Multiplicity (End 1 : End 2) | File:Line |
| :--- | :--- | :--- | :--- |
| Network - Station | Aggregation | 1 : 0..* | `network.py:11` |
| Network - User | Aggregation | 1 : 0..* | `network.py:12` |
| Station - Dock | Composition | 1 : 1..* | `models.py:53` |
| Dock - Bike | Association | 0..1 : 0..1 | `models.py:32` |
| User - Ride | Association | 1 : 0..1 | `models.py:91` |
| Ride - Station | Dependency | * : 1 | `models.py:108` |
| ReceiptPrinter - Ride | Dependency | 1 : 1 | `models.py:160` |

### Lifetime Tests (Aggregation vs Composition)
- **Station / Dock (Composition)**: "If I delete `Station`, do `Dock` objects disappear?" **Yes**. `Dock` instances are created strictly inside `Station.__init__` and managed bound to its lifecycle.
- **Network / Station (Aggregation)**: "If I delete `Network`, do `Station` objects disappear?" **No**. `Station` instances exist independently and are passed into `Network` via `add_station()`.

---

## How "A Bike is in Exactly One Place" is Handled

```python
# Encapsulation & Single Occupancy Enforcement in models.py & network.py

class Dock:
    def park_bike(self, bike: Bike) -> None:
        if not self.is_free:
            raise DockOccupiedError("Dock occupied")
        self._bike = bike

class Station:
    def __init__(self, name: str, capacity: int):
        # Docks are stored in a read-only tuple to prevent external array mutations (station.docks.append)
        self._docks = tuple(Dock(i + 1) for i in range(capacity))

    @property
    def docks(self) -> Tuple[Dock, ...]:
        return self._docks
```

1. **State Isolation**: A `Bike` cannot be directly assigned to multiple docks because `Dock._bike` holds a single reference, protected behind `park_bike()` which asserts `is_free`.
2. **Immutable Dock Collection**: `Station.docks` exposes a read-only `tuple`. Any attempt by outside code to append or replace dock elements raises an error.
3. **Atomic Ownership Transfers**: When `Network.take_bike()` is called, `dock.release_bike()` unsets the reference from the dock before assigning the bike to `User.active_ride`.
