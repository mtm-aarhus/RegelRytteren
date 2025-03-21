import requests
import random
import numpy as np
import matplotlib.pyplot as plt
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# Constants
NUM_LOCATIONS = 50
WORK_HOURS = 7
STOP_TIME = 30  # Minutes per stop
TOTAL_MINUTES = WORK_HOURS * 60
GRAPHHOPPER_URL = "http://localhost:8989/route"

# 🚲🚗 Vehicle Configuration (Depot is fixed)
DEPOT = (56.161147, 10.13455)
vehicles_config = {
    "bikes": [{"name": "Bike 1"}, {"name": "Bike 2"}],
    "cars": [{"name": "Car 1"}]
}

def generate_random_locations():
    """Generate random coordinates within Aarhus, Denmark."""
    return [(random.uniform(56.1, 56.2), random.uniform(10.1, 10.20)) for _ in range(NUM_LOCATIONS)]

def get_travel_time(coord1, coord2, mode):
    """Query GraphHopper API to get travel time (in minutes)."""
    params = {
        "point": [f"{coord1[0]},{coord1[1]}", f"{coord2[0]},{coord2[1]}"],
        "profile": mode,
        "locale": "da",
        "calc_points": "false"
    }

    try:
        response = requests.get(GRAPHHOPPER_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "paths" in data:
            return data["paths"][0]["time"] / 60000  # Convert ms to minutes
    except requests.exceptions.RequestException:
        return float('inf')  # Assign high travel time if request fails

def create_distance_matrix(locations, mode):
    """Creates a travel time matrix for OR-Tools using GraphHopper."""
    size = len(locations)
    matrix = np.zeros((size, size))

    print(f"📌 Generating {mode} distance matrix for {size} locations...")

    for i in range(size):
        for j in range(size):
            if i != j:
                matrix[i][j] = get_travel_time(locations[i], locations[j], mode)

    print(f"✅ {mode.capitalize()} distance matrix completed.")
    return matrix

def solve_vrp(distance_matrix, num_vehicles, depot_index):
    """Solves the VRP for multiple vehicles with time constraints."""
    print(f"🔄 Solving VRP for {num_vehicles} vehicle(s)...")

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def transit_callback(from_index, to_index):
        """Returns travel time between locations including stop time."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] + STOP_TIME)

    transit_callback_index = routing.RegisterTransitCallback(transit_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    routing.AddDimension(
        transit_callback_index,
        0,  # No slack
        TOTAL_MINUTES,  # Work hour limit
        True,  # Start at zero
        "Time"
    )

    time_dimension = routing.GetDimensionOrDie("Time")
    time_dimension.SetGlobalSpanCostCoefficient(100)  # Encourage minimizing total time

    # Ensure depot (start & end) is mandatory
    for vehicle_id in range(num_vehicles):
        routing.SetFixedCostOfAllVehicles(0)  # No extra cost for starting a vehicle

    # 🔍 Allow skipping some locations but not depot
    penalty = 10000
    for node in range(len(distance_matrix)):
        if node != depot_index:  # Depot cannot be skipped
            routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.time_limit.seconds = 30

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
            route.append(depot_index)  # Ensure depot is last stop
            routes[f"Vehicle {vehicle_id + 1}"] = route
        return routes
    else:
        print("❌ No solution found.")
        return {}

def generate_google_maps_link(route, locations):
    """Generate a Google Maps URL for navigation, ensuring the last stop is included."""
    if not route:
        return "No valid route found."
    
    base_url = "https://www.google.com/maps/dir/"
    
    # 🔹 Ensure last stop (depot) is added
    waypoints = "/".join(f"{locations[i][0]},{locations[i][1]}" for i in route) 

    return base_url + waypoints

def plot_routes(routes, locations, label_prefix):
    """Plot optimized routes for multiple vehicles with unique colors (automatically assigned)."""
    for vehicle_name, route in routes.items():
        if route:
            x_route, y_route = zip(*[locations[i] for i in route])
            plt.plot(y_route, x_route, '-o', label=f'{label_prefix} {vehicle_name}')  # No manual color


# 🗺️ Generate locations
random_locations = generate_random_locations()
print(f"🗺️ {len(random_locations)} locations generated.")

# 🚲 **Solve for Bikes First**
bike_locations = [DEPOT] + random_locations
print(f"🚲 Solving for bikes ({len(vehicles_config['bikes'])} vehicles)...")
bike_distance_matrix = create_distance_matrix(bike_locations, "bike")

bike_routes = solve_vrp(
    bike_distance_matrix,
    num_vehicles=len(vehicles_config["bikes"]),
    depot_index=0
)

# 🚲 Debug: How many locations were visited by bikes?
visited_by_bikes = set(sum(bike_routes.values(), []))
print(f"🚲 Bikes visited {len(visited_by_bikes)} locations.")

# Remove visited locations from the list
remaining_locations = [loc for i, loc in enumerate(random_locations) if i + 1 not in visited_by_bikes]

# 🚗 **Solve for Cars with Remaining Locations**
car_locations = [DEPOT] + remaining_locations
print(f"🚗 Solving for cars ({len(vehicles_config['cars'])} vehicles)...")
car_distance_matrix = create_distance_matrix(car_locations, "car")

car_routes = solve_vrp(
    car_distance_matrix,
    num_vehicles=len(vehicles_config["cars"]),
    depot_index=0
)

# 🚗 Debug: How many locations were visited by cars?
visited_by_cars = set(sum(car_routes.values(), []))
print(f"🚗 Cars visited {len(visited_by_cars)} locations.")

# ✅ **Print Google Maps Links**
print("\n🚴 Bike Routes:")
for name, route in bike_routes.items():
    print(f"{name}: {generate_google_maps_link(route, bike_locations)}")

print("\n🚗 Car Routes:")
for name, route in car_routes.items():
    print(f"{name}: {generate_google_maps_link(route, car_locations)}")
    

# 📌 **Plot the Routes**
plt.figure(figsize=(10, 8))

plot_routes(bike_routes, bike_locations, "Bike")
plot_routes(car_routes, car_locations, "Car")

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.legend()
plt.title("Optimized Routes for Bikes and Cars")
plt.show()
print("Finish")