def explain_conflicts(conflicts):
    """
    Generate detailed explanations for detected conflicts.

    Parameters:
    conflicts (list): A list of conflict objects, each containing information about
                      the conflict's location, time, and involved flights.

    Returns:
    list: A list of strings, each providing a detailed explanation of a conflict.
    """
    explanations = []
    
    for conflict in conflicts:
        location = conflict.get('location')
        time = conflict.get('time')
        involved_flights = conflict.get('involved_flights')
        
        explanation = f"Conflict detected at location {location} during time {time}. "
        explanation += f"Involved flights: {', '.join(involved_flights)}."
        
        explanations.append(explanation)
    
    return explanations