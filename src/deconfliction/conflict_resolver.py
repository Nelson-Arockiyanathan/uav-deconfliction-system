import requests
import json
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

def get_conflict_resolution(conflicts):
    """
    Use Hugging Face API to get suggestions for resolving drone conflicts.
    
    Parameters:
    conflicts (list): List of detected conflicts, each containing location and timing information
    
    Returns:
    list: List of suggested solutions for each conflict
    """
    # Get API token from environment
    api_token = os.getenv('HUGGINGFACE_API_KEY')
    if not api_token:
        print("Error: HUGGINGFACE_API_KEY not found in environment variables")
        return None

    # Configure API headers
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # We'll use the Mixtral model which is good at reasoning tasks
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    
    try:
        solutions = []
        for conflict in conflicts:
            other_drone = [f for f in conflict['involved_flights'] if f != 'primary'][0]
              # Format the conflict information for the prompt
            example_response = (
                "ALTITUDE: 120\n"
                "DELAY: 0\n"
                "PATH: 15.5,25.5\n"
                "REASON: Increasing altitude by 20m provides safe vertical separation while maintaining original timing."
            )
            
            prompt = f"""<s>[INST] As a UAV deconfliction expert, analyze this conflict and provide recommendations to modify ONLY the primary mission's path to avoid the conflict:
Location: {conflict['location']}
Time: {conflict['time']}
Primary Mission vs {other_drone}

Your task is to suggest ONE specific change that will resolve this conflict. Choose the most effective option:
1. Vertical separation: Increase or decrease altitude (must be at least 20 meters different from conflict point)
2. Temporal separation: Add a time delay (must be at least 5 minutes to ensure separation)
3. Path modification: Change x,y coordinates (must be at least 10 meters away from conflict point)

Format your response using EXACTLY these labels and numerical values only:
ALTITUDE: [number only, in meters]
DELAY: [number only, in minutes]
PATH: [x,y coordinates as numbers only]
REASON: [one brief sentence explaining why this is the best option]

Example response:
{example_response}
[/INST]</s>"""
            
            print(f"\nSending request to Hugging Face API for conflict at {conflict['location']}...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Call Hugging Face API
                    response = requests.post(
                        API_URL,
                        headers=headers,
                        json={"inputs": prompt, "parameters": {"max_new_tokens": 500}},
                        timeout=30
                    )
                    
                    print(f"Received response with status code: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, list):
                            raw_suggestion = result[0].get('generated_text', '')
                        else:
                            raw_suggestion = result.get('generated_text', '')
                            
                        print("Successfully parsed response")

                        # Extract the structured parts from the response
                        suggestion = {}
                        for line in raw_suggestion.split('\n'):
                            if line.startswith('ALTITUDE:'):
                                suggestion['altitude'] = line.replace('ALTITUDE:', '').strip()
                            elif line.startswith('DELAY:'):
                                suggestion['delay'] = line.replace('DELAY:', '').strip()
                            elif line.startswith('PATH:'):
                                suggestion['path'] = line.replace('PATH:', '').strip()
                            elif line.startswith('REASON:'):
                                suggestion['reason'] = line.replace('REASON:', '').strip()
                        
                        solution = {
                            'conflict': conflict,
                            'suggestion': suggestion
                        }
                        solutions.append(solution)
                        break  # Success, exit retry loop
                    elif response.status_code == 503:
                        # Model is loading
                        print("Model is loading, waiting before retry...")
                        time.sleep(20)  # Wait longer for model loading
                    else:
                        print(f"Error from Hugging Face API: {response.status_code}")
                        print(f"Response content: {response.text}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            
                except requests.exceptions.ConnectionError:
                    print(f"Could not connect to Hugging Face API (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        print("Retrying in a few seconds...")
                        time.sleep(2 ** attempt)
                except requests.exceptions.Timeout:
                    print(f"Request timed out (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        print("Retrying...")
                        time.sleep(2 ** attempt)
                except Exception as e:
                    print(f"Unexpected error: {str(e)}")
                    print(f"Error type: {type(e)}")
                    if attempt < max_retries - 1:
                        print("Retrying...")
                        time.sleep(2 ** attempt)
                
        return solutions
    except Exception as e:
        print(f"Error getting conflict resolution suggestions: {str(e)}")
        return None

def parse_coordinates(coord_str):
    """Parse coordinates from a string, handling various formats."""
    try:
        # Remove any parentheses, brackets, and extra whitespace
        clean_str = coord_str.strip('[]()').replace(' ', '')
        coords = clean_str.split(',')
        if len(coords) >= 2:
            return float(coords[0]), float(coords[1])
    except (ValueError, IndexError) as e:
        print(f"Could not parse coordinates from: {coord_str}")
        return None
    return None

def create_resolved_mission(primary_mission, solutions):
    """
    Create a new mission file incorporating the LLM's suggested changes.
    
    Parameters:
    primary_mission (dict): Original primary mission data
    solutions (list): List of solutions from the LLM
    
    Returns:
    dict: Modified mission data
    """
    # Create a deep copy of the primary mission
    resolved_mission = json.loads(json.dumps(primary_mission))
    
    # Sort solutions by timestamp to apply changes in chronological order
    solutions.sort(key=lambda x: x['conflict'].get('time', ''))
    
    # Keep track of modified waypoints to avoid double-applying changes
    modified_waypoints = set()
    
    for solution in solutions:
        suggestion = solution['suggestion']
        conflict_location = eval(solution['conflict']['location'])  # Convert string "(x, y, z)" to tuple
        
        # Find ALL waypoints near the conflict that might need adjustment
        affected_waypoints = []
        safety_radius = 5.0  # Consider waypoints within this radius of the conflict
        
        for idx, wp in enumerate(resolved_mission['waypoints']):
            if idx in modified_waypoints:
                continue  # Skip already modified waypoints
                
            dist = ((wp['x'] - conflict_location[0])**2 + 
                   (wp['y'] - conflict_location[1])**2 + 
                   (wp['z'] - conflict_location[2])**2)**0.5
            if dist < safety_radius:
                affected_waypoints.append((idx, dist))
        
        # Sort affected waypoints by distance to conflict
        affected_waypoints.sort(key=lambda x: x[1])
        
        for wp_idx, _ in affected_waypoints:
            print(f"\nApplying changes to waypoint {wp_idx}:")
            print(f"Original waypoint: x={resolved_mission['waypoints'][wp_idx]['x']}, "
                  f"y={resolved_mission['waypoints'][wp_idx]['y']}, "
                  f"z={resolved_mission['waypoints'][wp_idx]['z']}")
            
            # Apply altitude change if specified
            if 'altitude' in suggestion and suggestion['altitude']:
                try:
                    new_altitude = float(suggestion['altitude'].replace('meters', '').strip())
                    if abs(new_altitude - conflict_location[2]) >= 20:  # Enforce minimum vertical separation
                        resolved_mission['waypoints'][wp_idx]['z'] = new_altitude
                        print(f"Updated altitude to: {new_altitude} meters")
                    else:
                        # If altitude difference is too small, add an extra 20m separation
                        new_altitude = conflict_location[2] + (20 if new_altitude > conflict_location[2] else -20)
                        resolved_mission['waypoints'][wp_idx]['z'] = new_altitude
                        print(f"Enforced minimum vertical separation, new altitude: {new_altitude} meters")
                except ValueError:
                    print(f"Could not parse altitude value: {suggestion['altitude']}")
                    
            # Apply path modification if specified
            if 'path' in suggestion and suggestion['path']:
                coords = parse_coordinates(suggestion['path'])
                if coords:
                    new_x, new_y = coords
                    # Check if new position provides enough separation
                    dist_to_conflict = ((new_x - conflict_location[0])**2 + 
                                      (new_y - conflict_location[1])**2)**0.5
                    if dist_to_conflict >= 10:  # Enforce minimum horizontal separation
                        resolved_mission['waypoints'][wp_idx]['x'] = new_x
                        resolved_mission['waypoints'][wp_idx]['y'] = new_y
                        print(f"Updated path to: x={new_x}, y={new_y}")
                    else:
                        # Scale the offset to ensure minimum separation
                        scale = 10 / dist_to_conflict
                        offset_x = (new_x - conflict_location[0]) * scale
                        offset_y = (new_y - conflict_location[1]) * scale
                        resolved_mission['waypoints'][wp_idx]['x'] = conflict_location[0] + offset_x
                        resolved_mission['waypoints'][wp_idx]['y'] = conflict_location[1] + offset_y
                        print(f"Enforced minimum horizontal separation, new path: " 
                              f"x={resolved_mission['waypoints'][wp_idx]['x']}, "
                              f"y={resolved_mission['waypoints'][wp_idx]['y']}")
            
            # Apply time delay if specified
            if 'delay' in suggestion and suggestion['delay']:
                try:
                    delay_min = float(suggestion['delay'].replace('minutes', '').strip())
                    if delay_min < 5:  # Enforce minimum time separation
                        delay_min = 5
                    
                    # Convert timestamps to datetime, add delay, and convert back to string
                    timestamp = datetime.fromisoformat(resolved_mission['waypoints'][wp_idx]['timestamp'].replace('Z', ''))
                    new_timestamp = timestamp + timedelta(minutes=delay_min)
                    resolved_mission['waypoints'][wp_idx]['timestamp'] = new_timestamp.isoformat() + 'Z'
                    
                    # Update time window only if this is the first delayed waypoint
                    if not modified_waypoints:
                        start_time = datetime.fromisoformat(resolved_mission['time_window']['start'].replace('Z', ''))
                        end_time = datetime.fromisoformat(resolved_mission['time_window']['end'].replace('Z', ''))
                        resolved_mission['time_window']['start'] = (start_time + timedelta(minutes=delay_min)).isoformat() + 'Z'
                        resolved_mission['time_window']['end'] = (end_time + timedelta(minutes=delay_min)).isoformat() + 'Z'
                        print(f"Applied delay of {delay_min} minutes")
                except ValueError:
                    print(f"Could not parse delay value: {suggestion['delay']}")
            
            modified_waypoints.add(wp_idx)
            
        # If no changes were applied to any waypoint, forcefully apply altitude separation
        if not affected_waypoints:
            # Find closest waypoint as fallback
            closest_wp_idx = min(range(len(resolved_mission['waypoints'])), 
                               key=lambda i: ((resolved_mission['waypoints'][i]['x'] - conflict_location[0])**2 + 
                                            (resolved_mission['waypoints'][i]['y'] - conflict_location[1])**2 + 
                                            (resolved_mission['waypoints'][i]['z'] - conflict_location[2])**2))
            if closest_wp_idx not in modified_waypoints:
                wp = resolved_mission['waypoints'][closest_wp_idx]
                new_altitude = wp['z'] + 25  # Add 25m vertical separation as fallback
                wp['z'] = new_altitude
                print(f"Applied fallback vertical separation to waypoint {closest_wp_idx}, new altitude: {new_altitude}m")
                modified_waypoints.add(closest_wp_idx)
    
    # Interpolate changes to intermediate waypoints for smoother transitions
    for i in range(len(resolved_mission['waypoints']) - 1):
        if i in modified_waypoints and i + 1 not in modified_waypoints:
            # Smoothly transition changes to next waypoint
            curr_wp = resolved_mission['waypoints'][i]
            next_wp = resolved_mission['waypoints'][i + 1]
            
            # Apply partial changes (50%) to next waypoint for smoother transition
            if abs(curr_wp['z'] - next_wp['z']) > 10:
                next_wp['z'] = (curr_wp['z'] + next_wp['z']) / 2
            
    return resolved_mission

def save_resolved_mission(resolved_mission, output_path):
    """Save the resolved mission to a JSON file."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(resolved_mission, f, indent=2)
