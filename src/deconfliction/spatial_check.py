from datetime import datetime, timedelta

def check_spatial_conflict(primary_mission, simulated_flights, safety_buffer=2.0):
    """
    Check for spatial conflicts between the primary drone mission and simulated flights.

    Parameters:
    - primary_mission: A dictionary containing the primary drone's waypoints and time window.
    - simulated_flights: A list of dictionaries, each representing a simulated drone's waypoints and time window.
    - safety_buffer: Minimum distance threshold to consider for conflict detection.

    Returns:
    - conflicts: A list of conflicts detected, each represented as a dictionary with details.
    """
    conflicts = []
    print(f"Checking spatial conflicts with safety buffer: {safety_buffer}")

    # Combine primary mission and simulated flights for all-pairs checking
    all_flights = [{'drone_id': 'primary', 'waypoints': primary_mission['waypoints'],
                   'time_window': primary_mission['time_window']}] + simulated_flights['flights']
    
    # Check conflicts between all pairs of flights
    for i in range(len(all_flights)):
        for j in range(i + 1, len(all_flights)):  # Start from i+1 to avoid checking same pair twice
            flight1 = all_flights[i]
            flight2 = all_flights[j]
            
            print(f"Checking between {flight1['drone_id']} and {flight2['drone_id']}")
            
            # Check for intersection between waypoints
            for wp1 in flight1['waypoints']:
                for wp2 in flight2['waypoints']:
                    # Use full 3D coordinates for conflict detection
                    point1 = (wp1['x'], wp1['y'], wp1.get('z', 0))
                    point2 = (wp2['x'], wp2['y'], wp2.get('z', 0))
                    distance = calculate_distance(point1, point2)
                    print(f"Distance between {point1} and {point2}: {distance}")
                    
                    if distance < safety_buffer:
                        # Calculate the time of conflict based on waypoint timestamps
                        time1 = wp1.get('time', None)
                        time2 = wp2.get('time', None)
                        
                        if time1 is not None and time2 is not None:
                            # Get the time windows for both flights
                            flight1_start = datetime.fromisoformat(flight1['time_window']['start']).replace(tzinfo=None)
                            flight2_start = datetime.fromisoformat(flight2['time_window']['start']).replace(tzinfo=None)
                            
                            # Calculate actual timestamps for the conflict
                            conflict_time1 = flight1_start + timedelta(minutes=time1*10)  # Assuming time units are in 10-minute intervals
                            conflict_time2 = flight2_start + timedelta(minutes=time2*10)
                            
                            conflict_time = f"{min(conflict_time1, conflict_time2)} to {max(conflict_time1, conflict_time2)}"
                        else:
                            conflict_time = None
                            
                        conflict = {
                            'location': f"({wp1['x']}, {wp1['y']}, {wp1.get('z', 0)})",
                            'time': conflict_time,
                            'involved_flights': [flight1['drone_id'], flight2['drone_id']]
                        }
                        print(f"Found conflict: {conflict}")
                        conflicts.append(conflict)

    print(f"Total conflicts found: {len(conflicts)}")
    return conflicts

def calculate_distance(point1, point2):
    """
    Calculate the Euclidean distance between two points.

    Parameters:
    - point1: A tuple (x1, y1) or (x1, y1, z1) representing the first point.
    - point2: A tuple (x2, y2) or (x2, y2, z2) representing the second point.

    Returns:
    - distance: The Euclidean distance between the two points.
    """
    if len(point1) == 2 and len(point2) == 2:  # 2D points
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5
    elif len(point1) == 3 and len(point2) == 3:  # 3D points
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2 + (point1[2] - point2[2]) ** 2) ** 0.5
    else:
        raise ValueError("Points must be 2D or 3D")