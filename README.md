# UAV Deconfliction System

## Overview
The UAV Deconfliction System is designed to ensure safe operation of drones in shared airspace by verifying that a primary drone's planned waypoint mission does not conflict with the flight paths of other drones. The system performs spatial and temporal checks to identify potential conflicts and provides detailed explanations for any detected issues.

## Features
- **Spatial Conflict Check**: Validates that the primary drone's path does not intersect with other drones' trajectories within a defined safety buffer.
- **Temporal Conflict Check**: Ensures that no other drone is present in the same spatial area during overlapping time segments within the primary mission's overall time window.
- **Conflict Explanation**: Provides detailed information about detected conflicts, including locations, times, and involved simulated flights.
- **Simulation and Visualization**: Simulates drone flight paths and generates visual representations of missions and conflicts.

## Project Structure
```
uav-deconfliction-system
├── src
│   ├── main.py
│   ├── deconfliction
│   │   ├── spatial_check.py
│   │   ├── temporal_check.py
│   │   └── conflict_explanation.py
│   ├── simulation
│   │   ├── simulator.py
│   │   └── visualization.py
│   ├── data
│   │   ├── flight_schedules.json
│   │   └── primary_mission.json
│   └── utils
│       └── helpers.py
├── tests
│   ├── test_spatial_check.py
│   ├── test_temporal_check.py
│   └── test_conflict_explanation.py
├── docs
│   └── reflection_and_justification.md
├── README.md
└── requirements.txt
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd uav-deconfliction-system
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Prepare the data files:
   - Ensure that `flight_schedules.json` and `primary_mission.json` are correctly populated in the `src/data` directory.

## Execution
To run the UAV Deconfliction System, execute the following command:
```
python src/main.py
```

## Testing
Unit tests are provided to ensure the functionality of the spatial and temporal checks, as well as conflict explanations. To run the tests, use:
```
pytest tests/
```

## Documentation
For detailed design decisions, architectural choices, and scalability considerations, refer to the `docs/reflection_and_justification.md` file.

## Acknowledgments
This project leverages various AI-assisted tools to enhance development efficiency and accuracy.