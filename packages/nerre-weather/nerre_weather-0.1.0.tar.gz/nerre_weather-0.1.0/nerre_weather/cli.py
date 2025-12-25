from .core import fetch_weather, show_city_table, plot_graph, save_csv
from colorama import Fore, Style

def main():
    print(Fore.YELLOW + "\n=== Nerre Weather Multi-City Tool ===\n" + Style.RESET_ALL)

    api_key = input("Enter WeatherStack API Key: ")

    city_input = input("Enter cities (comma separated): ")
    cities = [c.strip() for c in city_input.split(",")]

    unit = input("Choose Temperature Unit (C/F): ").strip().upper()
    if unit not in ["C", "F"]:
        unit = "C"

    city_temps = []

    for city in cities:
        current, location = fetch_weather(api_key, city)

        if current and location:
            city_temps.append((location["name"], current["temperature"]))
            show_city_table(current, location, unit)

    if not city_temps:
        print(Fore.RED + "\nNo valid cities. Exiting." + Style.RESET_ALL)
        return

    print(Fore.GREEN + "\n=== Temperature Ranking (High → Low) ===" + Style.RESET_ALL)
    sorted_list = sorted(city_temps, key=lambda x: x[1], reverse=True)

    for rank, (city, temp) in enumerate(sorted_list, start=1):
        if unit == "F":
            temp = (temp * 9/5) + 32
        print(f"{rank}. {city}: {round(temp,2)}°{unit}")

    ans = input("\nShow bar graph? (y/n): ").lower()
    if ans == "y":
        plot_graph(city_temps, unit)

    save = input("Export results to CSV? (y/n): ").lower()
    if save == "y":
        save_csv(city_temps, unit=unit)

    print(Fore.CYAN + "\nDone." + Style.RESET_ALL)
