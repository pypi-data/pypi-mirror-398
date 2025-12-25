import requests
import csv
from tabulate import tabulate
import matplotlib.pyplot as plt
from colorama import Fore, Style

API_URL = "http://api.weatherstack.com/current"


def fetch_weather(api_key, city):
    params = {"access_key": api_key, "query": city}

    try:
        res = requests.get(API_URL, params=params)
        data = res.json()

        if "error" in data:
            print(Fore.RED + f"[{city}] API Error: {data['error']['info']}" + Style.RESET_ALL)
            return None, None
        
        return data["current"], data["location"]

    except Exception as e:
        print(Fore.RED + f"[{city}] Request Error: {e}" + Style.RESET_ALL)
        return None, None


def show_city_table(current, location, unit="C"):
    temp = current["temperature"]
    if unit.upper() == "F":
        temp = (temp * 9/5) + 32

    print(Fore.CYAN + f"\n=== Weather in {location['name']} ({location['country']}) ===" + Style.RESET_ALL)
    
    table = [
        [f"Temperature (°{unit})", round(temp, 2)],
        ["Wind (km/h)", current["wind_speed"]],
        ["Humidity (%)", current["humidity"]],
        ["Pressure (mb)", current["pressure"]],
        ["UV Index", current["uv_index"]],
    ]
    
    print(tabulate(table, headers=["Metric", "Value"], tablefmt="grid"))


def plot_graph(city_temps, unit="C"):
    cities = [item[0] for item in city_temps]
    temps = [item[1] for item in city_temps]

    if unit.upper() == "F":
        temps = [(t * 9/5) + 32 for t in temps]

    plt.bar(cities, temps)
    plt.title(f"Temperature Comparison (°{unit})")
    plt.ylabel(f"Temp °{unit}")
    plt.grid(True)
    plt.show()


def save_csv(city_temps, file_path="weather_report.csv", unit="C"):
    rows = []
    for city, temp in city_temps:
        if unit.upper() == "F":
            temp = (temp * 9/5) + 32
        rows.append({"City": city, f"Temp (°{unit})": round(temp, 2)})

    with open(file_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(Fore.GREEN + f"\nResults saved to {file_path}" + Style.RESET_ALL)
