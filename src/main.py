# filepath: /uav-deconfliction-system/uav-deconfliction-system/src/main.py

import json
import os
from deconfliction.spatial_check import check_spatial_conflict
from deconfliction.temporal_check import check_temporal_conflict
from deconfliction.conflict_explanation import explain_conflicts
from simulation.simulator import run_simulation
from simulation.visualization import plot_missions, animate_conflicts

def load_mission(file_path):
    # Dynamically determine the absolute path of the file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.join(base_dir, file_path)
    with open(absolute_path, 'r') as file:
        return json.load(file)

def load_flight_schedules(file_path):
    # Dynamically determine the absolute path of the file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.join(base_dir, file_path)
    with open(absolute_path, 'r') as file:
        return json.load(file)

def main():
    print("\nLoading missions and checking for conflicts...")
    primary_mission = load_mission('data/primary_mission.json')
    simulated_flights = load_flight_schedules('data/flight_schedules.json')

    print("\nRunning initial conflict detection...")
    conflicts = run_simulation(primary_mission, simulated_flights)

    # Show initial visualization
    print("\nShowing initial mission paths...")
    plot_missions(primary_mission, simulated_flights)

    resolved_mission = None
    if conflicts:
        conflict_details = explain_conflicts(conflicts)
        print("\nConflicts detected:")
        for detail in conflict_details:
            print(detail)
            
        print("\nAnimating conflicts...")
        animate_conflicts(conflicts, primary_mission, simulated_flights)
            
        print("\nGetting AI suggestions for conflict resolution...")
        from deconfliction.conflict_resolver import get_conflict_resolution, create_resolved_mission, save_resolved_mission
        solutions = get_conflict_resolution(conflicts)
        
        if solutions:
            print("\nSuggested solutions to resolve conflicts:")
            for solution in solutions:
                conflict = solution['conflict']
                print(f"\nFor conflict between {', '.join(conflict['involved_flights'])} at {conflict['location']}:")
                print(f"AI Suggestion: {solution['suggestion']}\n")
            
            # Create and save resolved mission
            resolved_mission = create_resolved_mission(primary_mission, solutions)
            if resolved_mission:
                save_resolved_mission(resolved_mission, 'src/data/resolved_mission.json')
                print("\nShowing resolved mission paths...")
                plot_missions(primary_mission, simulated_flights, resolved_mission)
                print("\nAnimating resolved mission conflicts...")
                animate_conflicts(conflicts, primary_mission, simulated_flights, resolved_mission)
    else:
        print("\nNo conflicts detected. Mission is safe to execute.")

if __name__ == "__main__":
    main()