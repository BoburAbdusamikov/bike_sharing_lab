# Bike Sharing System Design

## Class Discovery & CRC Cards

Nouns extracted from requirements:
- **Station**: System entity with docks and location. (Class)
- **Dock**: Fixed slot at a station holding at most one bike. (Class)
- **Bike**: Bicycle that can be taken, returned, or under repair. (Class)
- **Rider / User**: Customer using the system. (Class)
- **Ride**: Event representing a single rental transaction with start/end details and fee rules. (Class)
- **Network**: System orchestrator managing overall operations, riders, and stations. (Class)
- **Fee**: Value/attribute owned by Ride.
- **Dock capacity / Free dock count**: Attributes.
- **Manager**: Actor outside system scope.

### CRC Cards Table

| Class | Responsibilities | Collaborators |
| :--- | :--- | :--- |
| **Bike** | - Maintain unique ID and status (AVAILABLE, IN_USE, REPAIR)<br>- Protect status transition rules | Dock |
| **Dock** | - Hold at most one bike<br>- Enforce single-occupancy and repair status constraints | Bike |
| **Station** | - Manage fixed collection of docks<br>- Provide free dock count, bike availability, and station sorting | Dock, Bike |
| **User (Rider)** | - Hold user identity and track current active ride (at most 1) | Ride |
| **Ride** | - Record start station, end station, start time, end time<br>- Calculate rental fee (15-min free, 500 UZS/5 min, capped at 20,000 UZS)<br>- Track failed return attempts and suggest redirect station | Station, User |
| **Network** | - Coordinate ride start/return flows<br>- Handle error handling & redirection routing<br>- Generate manager reports | Station, User, Ride |

## Scenario: Rider returns bike to a full station
1. **User** requests **Network** to return bike to Target **Station**.
2. **Network** checks **User**'s active **Ride**.
3. **Network** asks Target **Station** for a free **Dock**.
4. Target **Station** reports no free docks available.
5. Target **Station** raises `StationFullError`.
6. **Ride** records the failure attempt count ($n = 1$).
7. **User** attempts second return to Target **Station**; failure count reaches $n = 2$.
8. **Ride** triggers redirection request; **Network** identifies alternative **Station** with the most free docks (using Information Expert).
9. **User** returns bike to Redirected **Station**, closing the **Ride** and releasing the **Bike** into an available **Dock**.
