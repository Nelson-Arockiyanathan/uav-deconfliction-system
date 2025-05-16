from datetime import datetime
import numpy as np

def check_temporal_conflict(primary_mission, simulated_flights, safety_buffer=1.0):
    conflicts = []

    # Combine primary mission and simulated flights for all-pairs checking
    all_flights = [
        {
            'drone_id': 'primary',
            'waypoints': primary_mission['waypoints'],
            'time_window': primary_mission['time_window']
        }
    ] + simulated_flights['flights']
    
    # Check conflicts between all pairs of flights
    for i in range(len(all_flights)):
        for j in range(i + 1, len(all_flights)):  # Start from i+1 to avoid checking same pair twice
            flight1 = all_flights[i]
            flight2 = all_flights[j]
            
            # Convert time windows to datetime objects
            flight1_start = datetime.fromisoformat(flight1['time_window']['start']).replace(tzinfo=None)
            flight1_end = datetime.fromisoformat(flight1['time_window']['end']).replace(tzinfo=None)
            flight2_start = datetime.fromisoformat(flight2['time_window']['start']).replace(tzinfo=None)
            flight2_end = datetime.fromisoformat(flight2['time_window']['end']).replace(tzinfo=None)

            # Check for time overlap
            if (flight1_start < flight2_end and flight1_end > flight2_start):
                # Check for spatial conflict during the overlapping time
                for wp1 in flight1['waypoints']:
                    for wp2 in flight2['waypoints']:
                        # Calculate 3D distance between waypoints
                        distance = np.sqrt((wp1['x'] - wp2['x'])**2 + 
                                        (wp1['y'] - wp2['y'])**2 +
                                        (wp1.get('z', 0) - wp2.get('z', 0))**2)
                        
                        if distance < safety_buffer:
                            conflicts.append({
                                'location': f"({wp1['x']}, {wp1['y']}, {wp1.get('z', 0)})",
                                'time': f"{max(flight1_start, flight2_start)} to {min(flight1_end, flight2_end)}",
                                'involved_flights': [flight1['drone_id'], flight2['drone_id']]
                            })

    return conflicts