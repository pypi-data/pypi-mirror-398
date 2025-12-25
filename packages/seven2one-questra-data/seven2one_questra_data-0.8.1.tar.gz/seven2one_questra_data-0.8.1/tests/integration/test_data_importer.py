"""
Importiert Testdaten in Questra Data.

Verwendet die High-Level API, um:
1. Namespace and Inventories with Relationen to erstellen
2. Items from CSV-Dateien to importieren
3. Zeitreihendaten from CSV to importieren
"""

from __future__ import annotations

import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from seven2one.questra.authentication import QuestraAuthentication

from seven2one.questra.data import (
    ConflictAction,
    CreateTimeSeriesInput,
    DecimalProperty,
    IntProperty,
    InventoryRelation,
    Quality,
    QuestraData,
    QuestraDataCore,
    RelationType,
    StringProperty,
    TimeSeriesProperty,
    TimeSeriesValue,
    TimeUnit,
    ValueAlignment,
    ValueAvailability,
)

logging.basicConfig(
    level=logging.INFO,
    format="\033[32m%(asctime)s\033[0m | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


class TestDataImporter:
    """Importiert Testdaten in Questra Data."""

    def __init__(
        self,
        graphql_url: str,
        auth_url: str,
        username: str,
        password: str,
        namespace: str = "TestDaten",
    ):
        """
        Initialisiert den Importer.

        Args:
            graphql_url: URL des GraphQL-Endpunkts
            auth_url: URL des Authentifizierungs-Endpunkts
            username: Benutzername
            password: Passwort
            namespace: Name des Namespaces (Standard: "TestDaten")
        """
        self.namespace = namespace
        self.test_data_dir = Path(__file__).parent / "test_data"

        # Authentifizierung
        logger.info("Initialisiere Authentifizierung...")
        auth_client = QuestraAuthentication(
            url=auth_url,
            username=username,
            password=password,
        )

        # Client initialisieren
        logger.info("Initialisiere Questra Data Client...")
        self.client = QuestraData(
            graphql_url=graphql_url,
            auth_client=auth_client,
        )
        self.core_client = QuestraDataCore(
            graphql_url=graphql_url,
            auth_client=auth_client,
        )

        logger.info(f"Client initialisiert: {self.client.is_authenticated()}")

    def create_schema(self):
        """Creates Namespace and Inventories with Relationen."""
        logger.info("=" * 60)
        logger.info("Erstelle Schema (Namespace and Inventories)")
        logger.info("=" * 60)

        # 1. Namespace erstellen
        logger.info(f"Erstelle Namespace '{self.namespace}'...")
        ns_result = self.client.create_namespace(
            name=self.namespace,
            description="Namespace für Testdaten with Gebäuden, Räumen and Sensoren",
            if_exists=ConflictAction.IGNORE,
        )
        logger.info(
            f"  → Namespace '{ns_result.name}' "
            f"{'already vorhanden' if ns_result.existed else 'erstellt'}"
        )

        # 2. Gebäude-Inventory erstellen
        logger.info("Erstelle Inventory 'Gebaeude'...")
        building_properties = [
            StringProperty(
                propertyName="gebaeudename",
                maxLength=100,
                isRequired=True,
                isUnique=True,
            ),
            StringProperty(
                propertyName="typ",
                maxLength=50,
                isRequired=False,
            ),
            StringProperty(
                propertyName="standort",
                maxLength=100,
                isRequired=False,
            ),
            IntProperty(
                propertyName="baujahr",
                isRequired=False,
            ),
            IntProperty(
                propertyName="flaeche_m2",
                isRequired=False,
            ),
        ]

        building_result = self.client.create_inventory(
            name="Gebaeude",
            namespace_name=self.namespace,
            properties=building_properties,
            description="Inventory für Gebäude",
            if_exists=ConflictAction.IGNORE,
        )
        logger.info(
            f"  → Inventory 'Gebaeude' "
            f"{'already vorhanden' if building_result.existed else 'erstellt'}"
        )

        # 3. Räume-Inventory with Relation to Gebäude erstellen
        logger.info("Erstelle Inventory 'Raeume' with Gebäude-Relation...")
        room_properties = [
            StringProperty(
                propertyName="raumnummer",
                maxLength=50,
                isRequired=True,
                isUnique=True,
            ),
            StringProperty(
                propertyName="typ",
                maxLength=50,
                isRequired=False,
            ),
            IntProperty(
                propertyName="etage",
                isRequired=False,
            ),
            IntProperty(
                propertyName="flaeche_m2",
                isRequired=False,
            ),
        ]

        # Relation: Viele Räume gehören to einem Gebäude
        # Im Schema: ONE_TO_MANY (vom Parent Gebäude from gesehen)
        # propertyName ist der Name im Child (Raeume), parentPropertyName im Parent (Gebaeude)
        room_relations = [
            InventoryRelation(
                propertyName="Gebaeude",  # Property im Child (Raeume)
                relationType=RelationType.ONE_TO_MANY,  # Ein Gebäude hat viele Räume
                parentInventoryName="Gebaeude",
                parentPropertyName="Raeume",  # Property im Parent (Gebaeude)
                parentNamespaceName=self.namespace,  # Namespace des Parent-Inventorys
            )
        ]

        room_result = self.client.create_inventory(
            name="Raeume",
            namespace_name=self.namespace,
            properties=room_properties,
            relations=room_relations,
            description="Inventory für Räume with Gebäude-Relation",
            if_exists=ConflictAction.IGNORE,
        )
        logger.info(
            f"  → Inventory 'Raeume' "
            f"{'already vorhanden' if room_result.existed else 'erstellt'}"
        )

        # 4. Sensoren-Inventory with Relation to Räumen and TimeSeries erstellen
        logger.info(
            "Erstelle Inventory 'Sensoren' with Raum-Relation and TimeSeries..."
        )
        sensor_properties = [
            StringProperty(
                propertyName="sensornummer",
                maxLength=50,
                isRequired=True,
                isUnique=True,
            ),
            StringProperty(
                propertyName="typ",
                maxLength=50,
                isRequired=False,
            ),
            StringProperty(
                propertyName="hersteller",
                maxLength=100,
                isRequired=False,
            ),
            StringProperty(
                propertyName="einheit",
                maxLength=20,
                isRequired=False,
            ),
            DecimalProperty(
                propertyName="min_wert",
                isRequired=False,
            ),
            DecimalProperty(
                propertyName="max_wert",
                isRequired=False,
            ),
            # Separate TimeSeries-Properties für verschiedene Sensortypen
            TimeSeriesProperty(
                propertyName="messwerte_temperatur",
                timeUnit=TimeUnit.MINUTE,
                multiplier=15,
                unit="°C",  # Temperatur in Grad Celsius
                valueAlignment=ValueAlignment.LEFT,
                valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
                timeZone="Europe/Berlin",
                isRequired=False,
            ),
            TimeSeriesProperty(
                propertyName="messwerte_luftfeuchtigkeit",
                timeUnit=TimeUnit.MINUTE,
                multiplier=15,
                unit="%",  # Luftfeuchtigkeit in Prozent
                valueAlignment=ValueAlignment.LEFT,
                valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
                timeZone="Europe/Berlin",
                isRequired=False,
            ),
            TimeSeriesProperty(
                propertyName="messwerte_co2",
                timeUnit=TimeUnit.MINUTE,
                multiplier=15,
                unit="[1]",  # CO2 as dimensionslose Einheit (ppm nicht verfügbar)
                valueAlignment=ValueAlignment.LEFT,
                valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
                timeZone="Europe/Berlin",
                isRequired=False,
            ),
        ]

        # Relation: Viele Sensoren gehören to einem Raum
        # Im Schema: ONE_TO_MANY (vom Parent Raum from gesehen)
        sensor_relations = [
            InventoryRelation(
                propertyName="Raum",  # Property im Child (Sensoren)
                relationType=RelationType.ONE_TO_MANY,  # Ein Raum hat viele Sensoren
                parentInventoryName="Raeume",
                parentPropertyName="Sensoren",  # Property im Parent (Raeume)
                parentNamespaceName=self.namespace,  # Namespace des Parent-Inventorys
            )
        ]

        sensor_result = self.client.create_inventory(
            name="Sensoren",
            namespace_name=self.namespace,
            properties=sensor_properties,
            relations=sensor_relations,
            description="Inventory für Sensoren with Raum-Relation and Messwerten",
            if_exists=ConflictAction.IGNORE,
        )
        logger.info(
            f"  → Inventory 'Sensoren' "
            f"{'already vorhanden' if sensor_result.existed else 'erstellt'}"
        )

        logger.info("Schema erfolgreich erstellt!")

    def import_buildings(self) -> dict[str, str | None]:
        """
        Importiert Gebäude from CSV.

        Returns:
            Mapping of Gebäudename to Item-ID
        """
        logger.info("=" * 60)
        logger.info("Importiere Gebäude from CSV")
        logger.info("=" * 60)

        csv_path = self.test_data_dir / "buildings.csv"
        logger.info(f"Lese CSV: {csv_path}")

        items = []
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(
                    {
                        "gebaeudename": row["gebaeudename"],
                        "typ": row["typ"],
                        "standort": row["standort"],
                        "baujahr": int(row["baujahr"]),
                        "flaeche_m2": int(row["flaeche_m2"]),
                    }
                )

        logger.info(f"Erstelle {len(items)} Gebäude...")
        created_items = self.client.create_items(
            inventory_name="Gebaeude",
            namespace_name=self.namespace,
            items=items,
        )

        # Erstelle Mapping: Die zurückgegebenen Items enthalten only _id, _rowVersion, _existed
        # Wir müssen die ursprünglichen Daten with den IDs kombinieren
        building_mapping = {}
        new_count = 0
        existing_count = 0
        for original_item, created_item in zip(items, created_items):
            building_name = original_item["gebaeudename"]
            building_mapping[building_name] = created_item["_id"]
            if created_item.get("_existed"):
                existing_count += 1
            else:
                new_count += 1
            logger.debug(
                f"  → {building_name}: {'already vorhanden' if created_item.get('_existed') else 'neu erstellt'}"
            )

        logger.info(
            f"  → {new_count} neue Gebäude erstellt, {existing_count} already vorhanden"
        )
        logger.info(f"{len(created_items)} Gebäude erfolgreich importiert!")
        return building_mapping

    def import_rooms(
        self, building_mapping: dict[str, str | None]
    ) -> dict[str, str | None]:
        """
        Importiert Räume from CSV with Relation to Gebäuden.

        Args:
            building_mapping: Mapping of Gebäudename to Item-ID

        Returns:
            Mapping of Raumnummer to Item-ID
        """
        logger.info("=" * 60)
        logger.info("Importiere Räume from CSV")
        logger.info("=" * 60)

        csv_path = self.test_data_dir / "rooms.csv"
        logger.info(f"Lese CSV: {csv_path}")

        items = []
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Finde Gebäude-ID
                building_id = building_mapping.get(row["gebaeudenummer"])
                if not building_id:
                    logger.warning(
                        f"Gebäude '{row['gebaeudenummer']}' nicht gefunden, "
                        f"überspringe Raum '{row['raumnummer']}'"
                    )
                    continue

                items.append(
                    {
                        "raumnummer": row["raumnummer"],
                        "typ": row["typ"],
                        "etage": int(row["etage"]),
                        "flaeche_m2": int(row["flaeche_m2"]),
                        "_gebaeudeId": building_id,  # Relation: _{propertyName}Id (lowercase erster Buchstabe)
                    }
                )

        logger.info(f"Erstelle {len(items)} Räume...")
        created_items = self.client.create_items(
            inventory_name="Raeume",
            namespace_name=self.namespace,
            items=items,
        )

        # Erstelle Mapping: Die zurückgegebenen Items enthalten only _id, _rowVersion, _existed
        # Wir müssen die ursprünglichen Daten with den IDs kombinieren
        room_mapping = {}
        new_count = 0
        existing_count = 0
        for original_item, created_item in zip(items, created_items):
            room_number = original_item["raumnummer"]
            room_mapping[room_number] = created_item["_id"]
            if created_item.get("_existed"):
                existing_count += 1
            else:
                new_count += 1
            logger.debug(
                f"  → {room_number}: {'already vorhanden' if created_item.get('_existed') else 'neu erstellt'}"
            )

        logger.info(
            f"  → {new_count} neue Räume erstellt, {existing_count} already vorhanden"
        )
        logger.info(f"{len(created_items)} Räume erfolgreich importiert!")
        return room_mapping

    def import_sensors(
        self, room_mapping: dict[str, str | None]
    ) -> tuple[dict[str, str], dict[str, str], dict[str, dict[str, int]]]:
        """
        Importiert Sensoren from CSV with Relation to Räumen.
        Creates auch TimeSeries für jeden Sensor basierend auf Typ.

        Args:
            room_mapping: Mapping of Raumnummer to Item-ID

        Returns:
            Tuple of (
                Mapping of Sensornummer to Item-ID,
                Mapping of Sensornummer to Typ,
                Mapping of Sensornummer to {property_name: timeseries_id}
            )
        """
        logger.info("=" * 60)
        logger.info("Importiere Sensoren from CSV")
        logger.info("=" * 60)

        csv_path = self.test_data_dir / "sensors.csv"
        logger.info(f"Lese CSV: {csv_path}")

        # Mapping of Sensor-Typ to TimeSeries-Property-Name
        type_to_property = {
            "Temperatur": "messwerte_temperatur",
            "Luftfeuchtigkeit": "messwerte_luftfeuchtigkeit",
            "CO2": "messwerte_co2",
        }

        # Schritt 1: Lese CSV and sammle Sensor-Daten
        sensor_data = []  # Liste of (row, room_id, sensor_type, property_name)

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Finde Raum-ID
                room_id = room_mapping.get(row["raumnummer"])
                if not room_id:
                    logger.warning(
                        f"Raum '{row['raumnummer']}' nicht gefunden, "
                        f"überspringe Sensor '{row['sensornummer']}'"
                    )
                    continue

                sensor_type = row["typ"]
                property_name = type_to_property.get(sensor_type)

                if not property_name:
                    logger.warning(
                        f"Kein Property-Mapping für Sensor-Typ '{sensor_type}', überspringe..."
                    )
                    continue

                sensor_data.append((row, room_id, sensor_type, property_name))

        logger.info(f"Gelesene Sensoren: {len(sensor_data)}")

        # Schritt 2: Erstelle TimeSeries ZUERST für jeden Sensor (in Batches of max. 100)
        logger.info("Erstelle TimeSeries für Sensoren...")
        timeseries_inputs = []

        for row, room_id, sensor_type, property_name in sensor_data:
            ts_input = CreateTimeSeriesInput(
                inventoryName="Sensoren",
                propertyName=property_name,
                namespaceName=self.namespace,
                # No specifics nötig, da already im Schema definiert
            )
            timeseries_inputs.append(ts_input)

        logger.info(f"Erstelle {len(timeseries_inputs)} TimeSeries via GraphQL...")

        # API-Limit: Max. 100 TimeSeries pro Call
        batch_size = 100
        ts_results = []
        total_batches = (len(timeseries_inputs) + batch_size - 1) // batch_size

        for i in range(0, len(timeseries_inputs), batch_size):
            batch = timeseries_inputs[i : i + batch_size]
            batch_num = i // batch_size + 1
            logger.info(
                f"  → Batch {batch_num}/{total_batches} ({len(batch)} TimeSeries)..."
            )
            batch_results = self.core_client.mutations.create_timeseries(batch)
            ts_results.extend(batch_results)

        logger.info(f"  → {len(ts_results)} TimeSeries erfolgreich erstellt")

        # Schritt 3: Erstelle Sensor-Items MIT TimeSeries-Verknüpfung
        logger.info(
            f"Erstelle {len(sensor_data)} Sensoren with TimeSeries-Verknüpfung..."
        )
        items = []
        sensor_timeseries = {}  # Mapping: sensor_number -> {property_name: timeseries_id}

        for (row, room_id, sensor_type, property_name), ts_result in zip(
            sensor_data, ts_results
        ):
            ts_id = ts_result.id
            sensor_number = row["sensornummer"]

            # Speichere TimeSeries-ID für späteren Gebrauch
            if sensor_number not in sensor_timeseries:
                sensor_timeseries[sensor_number] = {}
            sensor_timeseries[sensor_number][property_name] = ts_id

            item = {
                "sensornummer": sensor_number,
                "typ": sensor_type,
                "hersteller": row["hersteller"],
                "einheit": row["einheit"],
                "min_wert": float(row["min_wert"]),
                "max_wert": float(row["max_wert"]),
                "_raumId": room_id,  # Relation: _{propertyName}Id (lowercase erster Buchstabe)
                property_name: ts_id,  # Direktzuweisung der TimeSeries-ID
            }
            items.append(item)
            logger.debug(
                f"  → {sensor_number} ({sensor_type}): TimeSeries {ts_id} für {property_name} erstellt"
            )

        created_items = self.client.create_items(
            inventory_name="Sensoren",
            namespace_name=self.namespace,
            items=items,
        )

        # Erstelle Mappings
        sensor_mapping = {}
        sensor_types = {}

        new_count = 0
        existing_count = 0
        for original_item, created_item in zip(items, created_items):
            sensor_number = original_item["sensornummer"]
            sensor_type = original_item["typ"]
            sensor_id = created_item["_id"]
            sensor_mapping[sensor_number] = sensor_id
            sensor_types[sensor_number] = sensor_type
            if created_item.get("_existed"):
                existing_count += 1
            else:
                new_count += 1
            logger.debug(
                f"  → {sensor_number} ({sensor_type}): {'already vorhanden' if created_item.get('_existed') else 'neu erstellt'}"
            )

        logger.info(
            f"  → {new_count} neue Sensoren erstellt, {existing_count} already vorhanden"
        )
        logger.info(f"{len(created_items)} Sensoren erfolgreich importiert!")
        return sensor_mapping, sensor_types, sensor_timeseries

    def import_timeseries(
        self,
        sensor_mapping: dict[str, str],
        sensor_types: dict[str, str],
        sensor_timeseries: dict[str, dict[str, int]],
    ) -> None:
        """
        Importiert Zeitreihendaten from CSV über REST API.

        Args:
            sensor_mapping: Mapping of Sensornummer to Item-ID
            sensor_types: Mapping of Sensornummer to Sensor-Typ
            sensor_timeseries: Mapping of Sensornummer to {property_name: timeseries_id}
        """
        logger.info("=" * 60)
        logger.info("Importiere Zeitreihendaten from CSV")
        logger.info("=" * 60)

        csv_path = self.test_data_dir / "timeseries.csv"
        logger.info(f"Lese CSV: {csv_path}")

        # Mapping of Sensor-Typ to TimeSeries-Property-Name
        type_to_property = {
            "Temperatur": "messwerte_temperatur",
            "Luftfeuchtigkeit": "messwerte_luftfeuchtigkeit",
            "CO2": "messwerte_co2",
        }

        # Gruppiere Werte nach Property-Name and Item-ID (nicht Sensor-Nummer!)
        # Structure: {property_name: {item_id: [TimeSeriesValue, ...]}}
        property_sensor_values: dict[str, dict[str, list[TimeSeriesValue]]] = {
            prop: {} for prop in type_to_property.values()
        }

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row_count = 0

            for row in reader:
                sensor_num = row["sensornummer"]

                # Überspringe wenn Sensor nicht gefunden
                if sensor_num not in sensor_mapping:
                    continue

                sensor_id = sensor_mapping[sensor_num]
                sensor_type = sensor_types.get(sensor_num)

                # Überspringe wenn Sensor-Typ nicht gefunden
                if not sensor_type:
                    logger.warning(
                        f"Kein Sensor-Typ für Sensor {sensor_num}, überspringe..."
                    )
                    continue

                # Bestimme Property-Name basierend auf Sensor-Typ
                property_name = type_to_property.get(sensor_type)
                if not property_name:
                    logger.warning(
                        f"Unbekannter Sensor-Typ '{sensor_type}' für Sensor {sensor_num}, überspringe..."
                    )
                    continue

                # Erstelle TimeSeriesValue
                ts_value = TimeSeriesValue(
                    time=datetime.fromisoformat(row["timestamp"]),
                    value=float(row["value"]),
                    quality=Quality[row["quality"]],
                )

                # Füge to Property-Sensorvaluesn hinzu
                if sensor_id not in property_sensor_values[property_name]:
                    property_sensor_values[property_name][sensor_id] = []

                property_sensor_values[property_name][sensor_id].append(ts_value)
                row_count += 1

                if row_count % 10000 == 0:
                    logger.info(f"  → {row_count:,} Werte gelesen...")

        logger.info(f"Insgesamt {row_count:,} Werte gelesen")

        # Zeige Verteilung nach Sensor-Typ
        for property_name, sensor_values in property_sensor_values.items():
            sensor_count = len(sensor_values)
            if sensor_count > 0:
                logger.info(f"  → {property_name}: {sensor_count} Sensoren")

        # Speichere Werte für jede Property separat über High-Level API
        logger.info("Speichere Zeitreihendaten...")

        batch_size = 10
        total_saved = 0

        for property_name, sensor_values in property_sensor_values.items():
            if not sensor_values:
                continue

            logger.info(f"Speichere Daten für Property '{property_name}'...")

            # Speichere in Batches (um nicht to viel auf einmal to senden)
            sensor_ids = list(sensor_values.keys())
            total_batches = (len(sensor_ids) + batch_size - 1) // batch_size
            property_total = sum(len(vals) for vals in sensor_values.values())

            for i in range(0, len(sensor_ids), batch_size):
                batch_ids = sensor_ids[i : i + batch_size]
                batch_values = {sid: sensor_values[sid] for sid in batch_ids}
                batch_num = i // batch_size + 1

                logger.info(
                    f"  → Batch {batch_num}/{total_batches} "
                    f"({len(batch_ids)} Sensoren)..."
                )

                self.client.save_timeseries_values_bulk(
                    inventory_name="Sensoren",
                    namespace_name=self.namespace,
                    timeseries_properties=property_name,
                    item_values=batch_values,
                    time_unit=TimeUnit.MINUTE,
                    multiplier=15,
                )

            logger.info(
                f"  → {property_total:,} Werte für '{property_name}' gespeichert"
            )
            total_saved += property_total

        logger.info(
            f"Zeitreihendaten erfolgreich importiert! ({total_saved:,} Werte gesamt)"
        )

    def run(self):
        """Führt den kompletten Import durch."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("Questra Data - Test Daten Import")
        logger.info("=" * 60)
        logger.info("")

        # 1. Schema erstellen
        self.create_schema()
        logger.info("")

        # 2. Gebäude importieren
        building_mapping = self.import_buildings()
        logger.info("")

        # 3. Räume importieren
        room_mapping = self.import_rooms(building_mapping)
        logger.info("")

        # 4. Sensoren importieren (inkl. TimeSeries-Erstellung)
        sensor_mapping, sensor_types, sensor_timeseries = self.import_sensors(
            room_mapping
        )
        logger.info("")

        # 5. Zeitreihendaten importieren
        self.import_timeseries(sensor_mapping, sensor_types, sensor_timeseries)
        logger.info("")

        logger.info("=" * 60)
        logger.info("Import erfolgreich abgeschlossen!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Zusammenfassung:")
        logger.info(f"  - Namespace: {self.namespace}")
        logger.info(f"  - Gebäude: {len(building_mapping)}")
        logger.info(f"  - Räume: {len(room_mapping)}")
        logger.info(f"  - Sensoren: {len(sensor_mapping)}")
        logger.info("")


def main():
    """Hauptfunktion."""
    # Konfiguration from Umgebungsvariablen
    graphql_url = os.getenv(
        "QUESTRA_GRAPHQL_URL",
        "https://dev.techstack.s2o.dev/dynamic-objects-v2/graphql",
    )
    auth_url = os.getenv(
        "QUESTRA_AUTH_URL",
        "https://authentik.dev.techstack.s2o.dev",
    )
    username = os.getenv("DYNO_USERNAME", "ServiceUser")
    password = os.getenv("DYNO_PASSWORD", "secret")

    # Importer erstellen and ausführen
    importer = TestDataImporter(
        graphql_url=graphql_url,
        auth_url=auth_url,
        username=username,
        password=password,
        namespace="TestDaten",
    )

    importer.run()


if __name__ == "__main__":
    main()
