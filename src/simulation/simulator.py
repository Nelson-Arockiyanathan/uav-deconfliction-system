from deconfliction.spatial_check import check_spatial_conflict
from deconfliction.temporal_check import check_temporal_conflict

def deduplicate_conflicts(conflicts):
    """
    Deduplicate conflicts based on location and involved flights.
    If the same conflict is detected with both spatial and temporal checks,
    prefer the one with timing information.
    """
    unique_conflicts = {}
    
    for conflict in conflicts:
        # Create a key based on location and involved flights
        key = (conflict['location'], tuple(sorted(conflict['involved_flights'])))
        
        # If we haven't seen this conflict before, or if this one has timing info and the previous one doesn't
        if key not in unique_conflicts or (conflict['time'] is not None and unique_conflicts[key]['time'] is None):
            unique_conflicts[key] = conflict
    
    return list(unique_conflicts.values())

def run_simulation(primary_mission, simulated_flights):
    """
    Simulates the flight paths of the primary drone and other simulated drones,
    checking for conflicts in both space and time.

    Parameters:
    primary_mission (dict): The primary drone's mission data including waypoints and time window.
    simulated_flights (list): A list of simulated flight paths, each containing waypoints and timings.

    Returns:
    dict: A dictionary containing the simulation results, including any detected conflicts.
    """
    conflicts = []

    # Perform spatial conflict checks
    spatial_conflicts = check_spatial_conflict(primary_mission, simulated_flights)
    if spatial_conflicts:
        conflicts.extend(spatial_conflicts)

    # Perform temporal conflict checks
    temporal_conflicts = check_temporal_conflict(primary_mission, simulated_flights)
    if temporal_conflicts:
        conflicts.extend(temporal_conflicts)

    # Deduplicate conflicts, preferring ones with timing information
    return deduplicate_conflicts(conflicts)