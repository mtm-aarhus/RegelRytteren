import requests
import random
import numpy as np
import matplotlib.pyplot as plt
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# Constants
NUM_LOCATIONS = 45
WORK_HOURS = 8
STOP_TIME = 30  # Minutes per stop
TOTAL_MINUTES = WORK_HOURS * 60

GRAPHHOPPER_URL = "http://localhost:8989/route"

# Fixed start and end locations for vehicles
vehicles_config = {
    "bikes": [{"name": "Bike 1", "start": [56.161147,10.13455], "end": [56.152891,10.203396]}],
    "cars": [{"name": "Car 1", "start": [56.161147,10.13455], "end": [56.152891,10.203396]}]
  }


def generate_random_locations():
    """Generate random coordinates within Aarhus, Denmark."""
    return [(random.uniform(56.1, 56.2), random.uniform(10.1, 10.20)) for _ in range(NUM_LOCATIONS)]


def get_travel_time(coord1, coord2, mode, max_retries=1):
    """Query GraphHopper API to get travel time, retry once if it fails."""
    params = {
        "point": [f"{coord1[0]},{coord1[1]}", f"{coord2[0]},{coord2[1]}"],
        "profile": mode,
        "locale": "da",
        "calc_points": "false"
    }

    for attempt in range(max_retries + 1):  # Try once + 1 retry
        try:
            response = requests.get(GRAPHHOPPER_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "paths" in data:
                travel_time = data["paths"][0]["time"] / 60000  # Convert ms to minutes
                return travel_time

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            print(f"⚠️ Timeout or Connection Error ({attempt + 1}/{max_retries + 1}) for {mode} route: {coord1} -> {coord2}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed for {mode} route: {coord1} -> {coord2} | Error: {e}")

    print(f"❌ Failed to fetch {mode} route after {max_retries + 1} attempts. Assigning high travel time.")
    return float('inf')  # Assign high value if all retries fail


def create_distance_matrix(locations, mode):
    """Creates a travel time matrix for OR-Tools using GraphHopper"""
    size = len(locations)
    matrix = np.zeros((size, size))
    print(f"📌 Generating distance matrix for {mode} ({size} locations)...")

    for i in range(size):
        for j in range(size):
            if i != j:
                matrix[i][j] = get_travel_time(locations[i], locations[j], mode)

    print(f"✅ Distance matrix for {mode} completed.")
    return matrix


def solve_vrp(distance_matrix, num_vehicles, start_indices, end_indices):
    """Solves the Vehicle Routing Problem (VRP) with OR-Tools for multiple vehicles (optional stops)"""
    print(f"🔄 Solving VRP for {num_vehicles} vehicle(s)...")

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, start_indices, end_indices)
    routing = pywrapcp.RoutingModel(manager)

    def transit_callback(from_index, to_index):
        """Returns travel time between locations."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] + STOP_TIME)  # Add stop time

    transit_callback_index = routing.RegisterTransitCallback(transit_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # ✅ Add time constraints
    routing.AddDimension(
        transit_callback_index,
        0,  # No slack
        TOTAL_MINUTES,  # Max work time (8 hours)
        True,  # Start at zero
        "Time"
    )

    # ✅ Now safely get the time dimension
    time_dimension = routing.GetDimensionOrDie("Time")
    time_dimension.SetGlobalSpanCostCoefficient(100)  # Encourage minimizing total time

    # ✅ Make all stops optional except start & end
    penalty = 100000  # High penalty for skipping stops
    for node in range(len(distance_matrix)):
        if node not in start_indices and node not in end_indices:
            routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.time_limit.seconds = 30  # Stop solver if it takes too long

    print("🔎 Running OR-Tools VRP Solver...")
    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        print(f"✅ VRP Solved Successfully!")
        routes = {}
        for vehicle_id in range(num_vehicles):
            route = []
            index = routing.Start(vehicle_id)
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))  # Append end location
            routes[f"Vehicle {vehicle_id + 1}"] = route
        return routes
    else:
        print("❌ No solution found.")
        return None



def generate_google_maps_link(route, locations):
    """Generate a Google Maps URL for navigation."""
    if not route:
        return "No valid route found."

    base_url = "https://www.google.com/maps/dir/"
    waypoints = "/".join(f"{locations[i][0]},{locations[i][1]}" for i in route)
    return base_url + waypoints


def plot_routes(bike_routes, car_routes, bike_locations, car_locations, remaining_locations):
    """Plot the routes for bikes, cars, and remaining stops separately."""
    plt.figure(figsize=(8, 6))

    # 🚴 **Plot bike routes**
    colors = ["blue", "cyan"]
    for idx, (name, route) in enumerate(bike_routes.items()):
        if route:
            x_route, y_route = zip(*[bike_locations[i] for i in route])
            plt.plot(y_route, x_route, '-o', label=f'bike {name}', color=colors[idx % len(colors)])

    # 🚗 **Plot car routes**
    colors = ["red", "orange"]
    for idx, (name, route) in enumerate(car_routes.items()):
        if route:
            x_route, y_route = zip(*[car_locations[i] for i in route])
            plt.plot(y_route, x_route, '-o', label=f'car {name}', color=colors[idx % len(colors)])

    # ❌ **Plot remaining stops separately**
    if remaining_locations:
        x_remaining, y_remaining = zip(*remaining_locations)
        plt.scatter(y_remaining, x_remaining, c='gray', label='Remaining Stops', alpha=0.7, marker="x")

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend()
    plt.title("🚀 Optimized Routes for Vehicles with Remaining Stops")
    plt.show()
    print("✅ Plotting complete.")
    
def generate_remaining_stops_link(remaining_locations):
    """Generate a Google Maps URL to visualize remaining stops."""
    if not remaining_locations:
        return "All stops were assigned!"
    
    base_url = "https://www.google.com/maps/dir/"
    waypoints = "/".join(f"{lat},{lon}" for lat, lon in remaining_locations)
    return base_url + waypoints

# 🗺️ Generate random locations
random_locations = generate_random_locations()

print(f'Random locations: {random_locations}')
# 🚴 **Bikes First**
bike_start = tuple(vehicles_config["bikes"][0]["start"])
bike_end = tuple(vehicles_config["bikes"][0]["end"])
bike_locations = [bike_start] + random_locations + [bike_end]
bike_distance_matrix = create_distance_matrix(bike_locations, "bike")

bike_routes = solve_vrp(bike_distance_matrix, num_vehicles=1, start_indices=[0], end_indices=[len(bike_locations) - 1]) or {}
print(f'Bike routes: {bike_routes}')
# ❌ Remove stops taken by bikes
bike_stops = set(sum(bike_routes.values(), [])) if bike_routes else set()
bike_stop_locations = {bike_locations[idx] for idx in bike_stops}  # Convert indices to actual coordinates
remaining_locations = [loc for loc in random_locations if loc not in bike_stop_locations]
# 🚗 **Now Assign Remaining Stops to Cars**
car_start = tuple(vehicles_config["cars"][0]["start"])
car_end = tuple(vehicles_config["cars"][0]["end"])
car_locations = [car_start] + remaining_locations + [car_end]
car_distance_matrix = create_distance_matrix(car_locations, "car")

car_routes = solve_vrp(car_distance_matrix, num_vehicles=1, start_indices=[0], end_indices=[len(car_locations) - 1]) or {}

# ✅ **Generate Google Maps Links Separately**
print("\n🚴 Bike Routes:")
for name, route in bike_routes.items():
    print(f"{name}: {generate_google_maps_link(route, bike_locations)}")

print("\n🚗 Car Routes:")
for name, route in car_routes.items():
    print(f"{name}: {generate_google_maps_link(route, car_locations)}")

# 🔗 **Generate and print Google Maps links**
print("\n🔗 Google Maps for Remaining Stops:")
print(generate_remaining_stops_link(remaining_locations))

# 📊 **Plot Routes with Remaining Stops**
plot_routes(bike_routes, car_routes, bike_locations, car_locations, remaining_locations)
