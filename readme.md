
# 🚴‍♂️ Route Optimization with GraphHopper + OR-Tools

This project uses **GraphHopper** and **Google OR-Tools** to generate optimal routes for bikes and cars across Aarhus, Denmark — all while respecting time constraints like an 8-hour workday and 30-minute stops per location.

---

## 📦 Prerequisites

1. **Java** (required to run GraphHopper), we used [adoptium](https://adoptium.net/)
2. **Python** and `pip` (for the optimizer)
3. Python packages:
   ```bash
   pip install requests numpy matplotlib ortools
   ```

---

## 🗺️ Setup GraphHopper

1. **Download GraphHopper Web JAR**  
   👉 [https://github.com/graphhopper/graphhopper/releases](https://github.com/graphhopper/graphhopper/releases)  
   Example file: `graphhopper-web-10.0.jar`

2. **Download Denmark Map**  
   👉 [https://download.geofabrik.de/europe/denmark-latest.osm.pbf](https://download.geofabrik.de/europe/denmark-latest.osm.pbf)

3. **Save configuration YAML** (name it `config-example.yml`)  
   Use the `config-example.yml` content in this repository, which includes elevation and custom profiles.

---

## 🚀 Start GraphHopper

Open **PowerShell** (in the folder where GraphHopper + config live) and run:

```bash
java -D"dw.graphhopper.datareader.file=denmark-latest.osm.pbf" -jar graphhopper-web-10.0.jar server config-example.yml
```

This starts GraphHopper locally on port **8989**. You can open it in the browser to verify that it's running, and to test if it works by visiting http://localhost:8989/

---

## 🧠 How It Works

1. **Generate 50 random locations** in Aarhus
2. **Solve for bikes first** using OR-Tools VRP with:
   - Shared depot (same start/end)
   - Time constraints (7 hours max, 30 min per stop)
   - Elevation-aware travel times (via GraphHopper)
3. **Remove visited stops** from the location list
4. **Solve for cars** using remaining locations
5. **Display Google Maps links** for each route
6. **Plot the routes** using Matplotlib

---

## 🔍 Elevation Support

GraphHopper uses SRTM elevation data thanks to:

```yaml
graph.elevation.provider: srtm
graph.encoded_values: ..., average_slope, surface
```

So biking uphill is automatically more expensive in travel time.

---

## ✅ Output

- Google Maps URLs for visualizing routes
- Matplotlib plot showing routes for:
  - All Bikes
  - All Cars
  - Remaining (unvisited) stops (if any)

---
