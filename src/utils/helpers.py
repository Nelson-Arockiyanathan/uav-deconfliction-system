def calculate_distance(point1, point2):
    """Calculate the Euclidean distance between two points in 2D space."""
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

def is_within_time_window(start_time, end_time, time_window):
    """Check if a given time window overlaps with the specified start and end times."""
    return not (end_time < time_window[0] or start_time > time_window[1])

def format_conflict_details(conflict):
    """Format the details of a conflict for better readability."""
    return f"Conflict detected at location {conflict['location']} during time {conflict['time']} with flight {conflict['flight_id']}."