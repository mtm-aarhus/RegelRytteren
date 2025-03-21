
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

3. **Add an empty srtmprovider folder in the project directory**  
   Graphhopper will automatically fill it with the required files when launching.

---

## 🚀 Start GraphHopper

Open **PowerShell** (in the folder where GraphHopper + config live) and run:

```bash
java -D"dw.graphhopper.datareader.file=denmark-latest.osm.pbf" -jar graphhopper-web-10.0.jar server config-example.yml
```

This starts GraphHopper locally on port **8989**. You can open it in the browser to verify that it's running, and to test if it works by visiting http://localhost:8989/

---

## Run main.py

Run main.py which will call GraphHopper and calculate the optimal routes. You can config variables in main.py, including multiple vehicles, work hours, stop time and so on. 

```python
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
```
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

```
🗺️ 50 locations generated.
🚲 Solving for bikes (2 vehicles)...
📌 Generating bike distance matrix for 51 locations...
✅ Bike distance matrix completed.
🔄 Solving VRP for 2 vehicle(s)...
🔎 Running OR-Tools VRP Solver...
✅ VRP Solved Successfully!
🚲 Bikes visited 23 locations.
🚗 Solving for cars (1 vehicles)...
📌 Generating car distance matrix for 29 locations...
✅ Car distance matrix completed.
🔄 Solving VRP for 1 vehicle(s)...
🔎 Running OR-Tools VRP Solver...
✅ VRP Solved Successfully!
🚗 Cars visited 13 locations.

🚴 Bike Routes:
Vehicle 1: https://www.google.com/maps/dir/56.161147,10.13455/56.1650445126152,10.145599383694863/56.17328331524722,10.159267900510665/56.17090764371608,10.16570600042246/56.16796655654246,10.180533868382767/56.16422129404255,10.184257351756433/56.16669178051126,10.183092380663814/56.171897143701074,10.19591138074191/56.1567347929189,10.177785254479895/56.15517841967556,10.170473079747081/56.1477394075875,10.171870324146163/56.16171927742466,10.15019501342694/56.161147,10.13455
Vehicle 2: https://www.google.com/maps/dir/56.161147,10.13455/56.16300004921837,10.121466048887592/56.16474846862127,10.107551813323827/56.173504246470024,10.104166696920158/56.179782475049294,10.10593509000983/56.17904938742202,10.115409733253333/56.1860389044953,10.122190165704724/56.19299291478618,10.133769522453568/56.18849036816077,10.138559907381305/56.188724368658995,10.129037006675718/56.1836383Vehicle 1: https://www.google.com/maps/dir/56.161147,10.13455/56.13626604100466,10.149857437499584/56.12561606949042,10.147398701678656/56.123479415305475,10.156018890701317/56.122472676742156,10.163589663794008/56.12455389477675,10.165913000078039/56.13731638069797,10.159629290091834/56.14336090014644,10.150154179655333/56.144619744282934,10.12630075839402/56.14955811760693,10.110223085530862/56.15285102665583,10.116841767091318/56.15412970784213,10.12431106546826/56.167331033274245,10.131223784886606/56.161147,10.13455

🚗 Car Routes:
Vehicle 1: https://www.google.com/maps/dir/56.161147,10.13455/56.152665218157125,10.113377799908578/56.15584790329262,10.101406579291714/56.16157757885512,10.108607927756152/56.144239159077536,10.101938558828893/56.140901874878836,10.128800462497464/56.133966041051806,10.119146850054765/56.11049935047961,10.163208097081714/56.10743679918988,10.166544220092387/56.1015786760406,10.167904637773079/56.112276966262066,10.155306900231475/56.1074001788128,10.145848364758107/56.14042666447572,10.150539327146362/56.161147,10.13455

```
<img width="485" alt="image" src="https://github.com/user-attachments/assets/020203ca-d70f-47c9-aaa5-fa01ea71c109" />

---
