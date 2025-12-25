"""
Generiert Testdaten für das Questra Data Datenmodell.

Creates CSV-Dateien mit:
- Gebäude (10 Stück)
- Räume (50 Stück, verknüpft with Gebäuden)
- Sensoren (150 Stück = 3 pro Raum: Temperatur + Luftfeuchtigkeit + CO2)
- Zeitreihenwerte (15-Minuten-Intervalle über 1 Jahr)
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_buildings_csv(filepath: Path, count: int = 10):
    """Generiert CSV with Gebäude-Daten."""
    print(f"Generiere {count} Gebäude...")

    building_types = [
        "Bürogebäude",
        "Produktionshalle",
        "Lagerhaus",
        "Rechenzentrum",
        "Verwaltung",
    ]
    cities = [
        "Berlin",
        "Hamburg",
        "München",
        "Köln",
        "Frankfurt",
        "Stuttgart",
        "Düsseldorf",
        "Leipzig",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["gebaeudename", "typ", "standort", "baujahr", "flaeche_m2"]
        )
        writer.writeheader()

        for i in range(1, count + 1):
            writer.writerow(
                {
                    "gebaeudename": f"Gebäude-{i:03d}",
                    "typ": random.choice(building_types),
                    "standort": random.choice(cities),
                    "baujahr": random.randint(1980, 2024),
                    "flaeche_m2": random.randint(500, 5000),
                }
            )

    print(f"  - {filepath} erstellt")


def generate_rooms_csv(filepath: Path, count: int = 50, building_count: int = 10):
    """Generiert CSV with Raum-Daten."""
    print(f"Generiere {count} Räume...")

    room_types = [
        "Büro",
        "Besprechungsraum",
        "Labor",
        "Lager",
        "Serverraum",
        "Werkstatt",
        "Kantine",
        "Empfang",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["raumnummer", "gebaeudenummer", "typ", "etage", "flaeche_m2"]
        )
        writer.writeheader()

        for i in range(1, count + 1):
            building_num = ((i - 1) % building_count) + 1
            writer.writerow(
                {
                    "raumnummer": f"R-{i:03d}",
                    "gebaeudenummer": f"Gebäude-{building_num:03d}",
                    "typ": random.choice(room_types),
                    "etage": random.randint(0, 8),
                    "flaeche_m2": random.randint(15, 200),
                }
            )

    print(f"  - {filepath} erstellt")


def generate_sensors_csv(filepath: Path, room_count: int = 50):
    """
    Generiert CSV with Sensor-Daten.

    Jeder Raum bekommt genau 3 Sensoren: Temperatur, Luftfeuchtigkeit, CO2.
    """
    sensor_types = ["Temperatur", "Luftfeuchtigkeit", "CO2"]
    manufacturers = [
        "Siemens",
        "ABB",
        "Schneider Electric",
        "Honeywell",
        "Bosch",
        "Phoenix Contact",
    ]

    total_sensors = room_count * 3
    print(f"Generiere {total_sensors} Sensoren ({room_count} Räume × 3 Typen)...")

    ranges = {
        "Temperatur": ("°C", 15.0, 30.0),
        "Luftfeuchtigkeit": ("%", 30.0, 70.0),
        "CO2": ("ppm", 400.0, 1500.0),
    }

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sensornummer",
                "raumnummer",
                "typ",
                "hersteller",
                "einheit",
                "min_wert",
                "max_wert",
            ],
        )
        writer.writeheader()

        sensor_id = 1
        for room_num in range(1, room_count + 1):
            # Jeder Raum bekommt alle 3 Sensor-Typen
            for sensor_type in sensor_types:
                unit, min_val, max_val = ranges[sensor_type]

                writer.writerow(
                    {
                        "sensornummer": f"SENS-{sensor_id:04d}",
                        "raumnummer": f"R-{room_num:03d}",
                        "typ": sensor_type,
                        "hersteller": random.choice(manufacturers),
                        "einheit": unit,
                        "min_wert": min_val,
                        "max_wert": max_val,
                    }
                )
                sensor_id += 1

    print(f"  - {filepath} erstellt")


def generate_timeseries_csv(filepath: Path, room_count: int = 50, days: int = 365):
    """
    Generiert CSV with Zeitreihendaten.

    Creates 15-Minuten-Intervalle über den angegebenen Zeitraum.
    Jeder Raum hat 3 Sensoren (Temperatur, Luftfeuchtigkeit, CO2).
    """
    sensor_count = room_count * 3
    print(f"Generiere Zeitreihendaten für {sensor_count} Sensoren über {days} Tage...")

    # Start: 1. Januar 2024
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    interval_minutes = 15

    # Berechne Anzahl der Zeitpunkte
    total_intervals = (days * 24 * 60) // interval_minutes
    print(f"  - {total_intervals} Zeitpunkte pro Sensor")
    print(f"  - {total_intervals * sensor_count:,} Gesamtwerte")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["sensornummer", "timestamp", "value", "quality"]
        )
        writer.writeheader()

        # Sensor-Typen für realistische Werte
        # Sensoren sind gruppiert: Raum 1 hat SENS-0001 (Temp), SENS-0002 (Luft), SENS-0003 (CO2)
        sensor_configs = {}
        sensor_types = ["Temperatur", "Luftfeuchtigkeit", "CO2"]

        sensor_id = 1
        for room_num in range(1, room_count + 1):
            for sensor_type in sensor_types:
                sensor_configs[f"SENS-{sensor_id:04d}"] = sensor_type
                sensor_id += 1

        # Generiere Werte
        for sensor_num in range(1, sensor_count + 1):
            sensor_id = f"SENS-{sensor_num:04d}"
            sensor_type = sensor_configs[sensor_id]

            # Basisvalues je nach Typ
            if sensor_type == "Temperatur":
                base_value = 21.0
                variation = 2.0
                daily_cycle = 2.0
                min_value = 15.0
                max_value = 30.0
            elif sensor_type == "Luftfeuchtigkeit":
                base_value = 50.0
                variation = 5.0
                daily_cycle = 5.0
                min_value = 30.0
                max_value = 70.0
            elif sensor_type == "CO2":
                base_value = 800.0
                variation = 100.0
                daily_cycle = 200.0
                min_value = 400.0
                max_value = 1500.0
            else:
                base_value = 20.0
                variation = 5.0
                daily_cycle = 2.0
                min_value = 0.0
                max_value = 100.0

            current_time = start_time

            for interval in range(total_intervals):
                # Simuliere Tageszyklen and zufällige Variation
                hour = current_time.hour

                # Tageszyklen (Cosinus-Kurve)
                import math

                daily_factor = math.cos((hour - 12) * math.pi / 12) * daily_cycle

                # Zufällige Variation
                random_variation = random.uniform(-variation, variation)

                # Berechne Wert
                value = base_value + daily_factor + random_variation

                # Begrenze Wert auf Min/Max
                value = max(min_value, min(max_value, value))

                # Qualität: 98% VALID, 2% FAULTY
                quality = "VALID" if random.random() > 0.02 else "FAULTY"

                writer.writerow(
                    {
                        "sensornummer": sensor_id,
                        "timestamp": current_time.isoformat(),
                        "value": round(value, 2),
                        "quality": quality,
                    }
                )

                current_time += timedelta(minutes=interval_minutes)

            if (sensor_num % 10) == 0:
                print(f"  -{sensor_num}/{sensor_count} Sensoren abgeschlossen")

    print(f"  - {filepath} erstellt")


def main():
    """Hauptfunktion zum Generieren aller Testdaten."""
    print("=" * 60)
    print("Generiere Testdaten für Questra Data")
    print("=" * 60)
    print()

    # Erstelle test_data Verzeichnis
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    # Generiere CSV-Dateien
    generate_buildings_csv(test_data_dir / "buildings.csv", count=10)
    generate_rooms_csv(test_data_dir / "rooms.csv", count=50, building_count=10)
    generate_sensors_csv(test_data_dir / "sensors.csv", room_count=50)
    generate_timeseries_csv(test_data_dir / "timeseries.csv", room_count=50, days=365)

    print()
    print("=" * 60)
    print("Testdaten erfolgreich generiert!")
    print("=" * 60)
    print(f"Verzeichnis: {test_data_dir}")
    print()


if __name__ == "__main__":
    main()
