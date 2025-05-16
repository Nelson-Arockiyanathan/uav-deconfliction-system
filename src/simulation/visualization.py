import matplotlib
import platform

# Configure matplotlib backend based on platform
if platform.system() == 'Windows':
    matplotlib.use('TkAgg')
else:
    matplotlib.use('Agg')

from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import numpy as np
from scipy.interpolate import interp1d
import time
import threading

def debug_print(msg):
    """Print debug messages with timestamp"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def interpolate_path(waypoints, num_points=100):
    """Create a smooth path between waypoints using appropriate interpolation"""
    points = np.array(waypoints)
    
    # If we have too few points for cubic interpolation, use linear
    if len(points) < 4:
        # Create parameter t for interpolation (0 to 1)
        t = np.linspace(0, 1, len(points))
        t_new = np.linspace(0, 1, num_points)
        
        # Create interpolation functions for each dimension
        fx = interp1d(t, points[:, 0], kind='linear')
        fy = interp1d(t, points[:, 1], kind='linear')
        fz = interp1d(t, points[:, 2], kind='linear')
    else:
        # Use cubic interpolation for 4 or more points
        t = np.linspace(0, 1, len(points))
        t_new = np.linspace(0, 1, num_points)
        
        # Create interpolation functions for each dimension
        fx = interp1d(t, points[:, 0], kind='cubic')
        fy = interp1d(t, points[:, 1], kind='cubic')
        fz = interp1d(t, points[:, 2], kind='cubic')
    
    # Generate smooth path
    smooth_path = np.vstack([fx(t_new), fy(t_new), fz(t_new)]).T
    
    return smooth_path

def plot_missions(primary_mission, simulated_flights, resolved_mission=None):
    """Plot the flight paths in 3D space. If resolved_mission is provided, show it alongside original paths."""
    try:
        debug_print("Starting mission path plotting...")
        plt.ioff()  # Turn off interactive mode
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Convert waypoints to numpy arrays and interpolate paths
        primary_waypoints = np.array([(wp['x'], wp['y'], wp.get('z', 0)) for wp in primary_mission['waypoints']])
        primary_smooth_path = interpolate_path(primary_waypoints)
        
        # If we have a resolved mission, prepare its path too
        if resolved_mission:
            resolved_waypoints = np.array([(wp['x'], wp['y'], wp.get('z', 0)) for wp in resolved_mission['waypoints']])
            resolved_smooth_path = interpolate_path(resolved_waypoints)
        
        # Plot primary mission path
        ax.plot(primary_smooth_path[:, 0], primary_smooth_path[:, 1], primary_smooth_path[:, 2], 
                color='blue', linestyle='-', alpha=0.5, label='Original Primary Path')
        
        # Plot resolved mission path if provided
        if resolved_mission:
            ax.plot(resolved_smooth_path[:, 0], resolved_smooth_path[:, 1], resolved_smooth_path[:, 2],
                    color='green', linestyle='-', alpha=0.8, label='Resolved Primary Path')
        
        # Plot simulated flight paths
        colors = ['red', 'orange', 'purple']
        for idx, flight in enumerate(simulated_flights['flights']):
            waypoints = np.array([(wp['x'], wp['y'], wp.get('z', 0)) for wp in flight['waypoints']])
            smooth_path = interpolate_path(waypoints)
            ax.plot(smooth_path[:, 0], smooth_path[:, 1], smooth_path[:, 2], 
                    color=colors[idx % len(colors)], linestyle='--', alpha=0.5,
                    label=f'Flight {flight["drone_id"]} Path')
        
        # Set plot properties
        ax.set_title('3D Flight Paths')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_zlabel('Altitude (Z)')
        
        # Calculate plot limits
        all_paths = [primary_smooth_path]
        for flight in simulated_flights['flights']:
            waypoints = np.array([(wp['x'], wp['y'], wp.get('z', 0)) for wp in flight['waypoints']])
            all_paths.append(interpolate_path(waypoints))
        all_points = np.vstack(all_paths)
        
        padding = 2.0
        ax.set_xlim(all_points[:, 0].min() - padding, all_points[:, 0].max() + padding)
        ax.set_ylim(all_points[:, 1].min() - padding, all_points[:, 1].max() + padding)
        ax.set_zlim(all_points[:, 2].min() - padding, all_points[:, 2].max() + padding)
        
        ax.grid(True)
        ax.legend(bbox_to_anchor=(1.15, 1), loc='upper right')
        
        plt.subplots_adjust(right=0.85)
        plt.ion()  # Enable interactive mode
        plt.show(block=True)  # Show plot and block until window is closed
        plt.close(fig)  # Clean up figure after window is closed
    except Exception as e:
        debug_print(f"Error in plot_missions: {str(e)}")
        raise

# Global variable to store the animation object
anim = None

def animate_conflicts(conflicts, primary_mission, simulated_flights, resolved_mission=None):
    """Animate the drone paths and conflicts, optionally showing the resolved path."""
    global anim  # Use the global variable to persist the animation object

    if not conflicts:
        print("No conflicts to animate.")
        return

    plt.ioff()  # Turn off interactive mode
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Convert waypoints and create smooth paths
    primary_waypoints = np.array([(wp['x'], wp['y'], wp.get('z', 0)) for wp in primary_mission['waypoints']])
    primary_smooth_path = interpolate_path(primary_waypoints)
    
    # Initialize primary drone visualization
    primary_path, = ax.plot([], [], [], color='blue', linestyle='-', alpha=0.5, label='Original Primary Path')
    primary_drone = ax.scatter([], [], [], color='blue', marker='o', s=100, label='Original Primary')
    
    # Initialize resolved mission visualization if provided
    resolved_path = None
    resolved_drone = None
    if resolved_mission:
        resolved_waypoints = np.array([(wp['x'], wp['y'], wp.get('z', 0)) for wp in resolved_mission['waypoints']])
        resolved_smooth_path = interpolate_path(resolved_waypoints)
        resolved_path, = ax.plot([], [], [], color='green', linestyle='-', alpha=0.8, label='Resolved Path')
        resolved_drone = ax.scatter([], [], [], color='green', marker='o', s=100, label='Resolved Primary')
    
    # Initialize simulated flights
    flight_paths = []
    flight_drones = []
    colors = ['red', 'orange', 'purple']
    
    for idx, flight in enumerate(simulated_flights['flights']):
        waypoints = np.array([(wp['x'], wp['y'], wp.get('z', 0)) for wp in flight['waypoints']])
        smooth_path = interpolate_path(waypoints)
        
        path, = ax.plot([], [], [], color=colors[idx % len(colors)], linestyle='--', alpha=0.5,
                       label=f'Flight {flight["drone_id"]} Path')
        drone = ax.scatter([], [], [], color=colors[idx % len(colors)], marker='o', s=100,
                          label=f'Flight {flight["drone_id"]}')
        
        flight_paths.append((path, smooth_path))
        flight_drones.append(drone)
    
    # Initialize conflict visualization
    conflict_marker = ax.scatter([], [], [], color='red', s=200, marker='*', label='Conflict')
    conflict_sphere = None  # Will be initialized in update function
    time_text = ax.text2D(0.02, 0.95, '', transform=ax.transAxes)
    
    # Setup axis limits and labels
    all_paths = [primary_smooth_path] + [path[1] for path in flight_paths]
    all_points = np.vstack(all_paths)
    padding = 2.0
    ax.set_xlim(all_points[:, 0].min() - padding, all_points[:, 0].max() + padding)
    ax.set_ylim(all_points[:, 1].min() - padding, all_points[:, 1].max() + padding)
    ax.set_zlim(all_points[:, 2].min() - padding, all_points[:, 2].max() + padding)
    
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_zlabel('Altitude (Z)')
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.15, 1), loc='upper right')
    plt.subplots_adjust(right=0.85)

    def init():
        artists = []
        primary_path.set_data_3d([], [], [])
        artists.append(primary_path)
        primary_drone._offsets3d = ([], [], [])
        artists.append(primary_drone)
        
        for path, _ in flight_paths:
            path.set_data_3d([], [], [])
            artists.append(path)
        for drone in flight_drones:
            drone._offsets3d = ([], [], [])
            artists.append(drone)
            
        conflict_marker._offsets3d = ([], [], [])
        artists.append(conflict_marker)
        time_text.set_text('')
        artists.append(time_text)
        return artists

    # Initialize a threading lock for synchronization
    lock = threading.Lock()

    def update(frame):
        with lock:
            artists = []
            base_progress = (frame % 100) / 100
            conflict_idx = (frame // 100) % len(conflicts)
            
            # Update primary mission
            points_to_show = int(len(primary_smooth_path) * base_progress)
            if points_to_show > 0:
                primary_path.set_data_3d(
                    primary_smooth_path[:points_to_show, 0],
                    primary_smooth_path[:points_to_show, 1],
                    primary_smooth_path[:points_to_show, 2]
                )
                current_pos = primary_smooth_path[min(points_to_show - 1, len(primary_smooth_path) - 1)]
                primary_drone._offsets3d = ([current_pos[0]], [current_pos[1]], [current_pos[2]])
            artists.extend([primary_path, primary_drone])
            
            # Update resolved mission if available
            if resolved_mission:
                points_to_show = int(len(resolved_smooth_path) * base_progress)
                if points_to_show > 0:
                    resolved_path.set_data_3d(
                        resolved_smooth_path[:points_to_show, 0],
                        resolved_smooth_path[:points_to_show, 1],
                        resolved_smooth_path[:points_to_show, 2]
                    )
                    current_pos = resolved_smooth_path[min(points_to_show - 1, len(resolved_smooth_path) - 1)]
                    resolved_drone._offsets3d = ([current_pos[0]], [current_pos[1]], [current_pos[2]])
                artists.extend([resolved_path, resolved_drone])
            
            # Update simulated flights
            for (path, smooth_path), drone in zip(flight_paths, flight_drones):
                points_to_show = int(len(smooth_path) * base_progress)
                if points_to_show > 0:
                    path.set_data_3d(
                        smooth_path[:points_to_show, 0],
                        smooth_path[:points_to_show, 1],
                        smooth_path[:points_to_show, 2]
                    )
                    current_pos = smooth_path[min(points_to_show - 1, len(smooth_path) - 1)]
                    drone._offsets3d = ([current_pos[0]], [current_pos[1]], [current_pos[2]])
                artists.extend([path, drone])
            
            # Update conflict visualization
            conflict = conflicts[conflict_idx]
            location = eval(conflict['location'])
            conflict_marker._offsets3d = ([location[0]], [location[1]], [location[2]])
            size = 200 + 100 * np.sin(frame * 0.1)
            conflict_marker.set_sizes([size])
            artists.append(conflict_marker)
            
            time_text.set_text(f'Time: {conflict["time"]}\n'
                              f'Flight: {conflict["involved_flights"][0]}\n')
            artists.append(time_text)
            
            ax.view_init(elev=20, azim=frame % 360)
            return artists

    # Assign the animation to the global variable
    anim = FuncAnimation(fig, update, init_func=init, frames=range(1000), interval=50, blit=False)

    plt.show()  # Show the animation

    # Keep the animation object in scope
    return anim