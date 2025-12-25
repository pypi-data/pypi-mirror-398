"""
Regressions-Test für High-Level API (QuestraData).

Testet die High-Level API systematisch durch:
- Setup: Namespace, Inventory, Items erstellen
- CRUD: Create, Read, Update, Delete Operations
- TimeSeries: Daten schreiben and lesen
- DataFrame: Pandas-Integration testen
- Cleanup: Alles aufräumen

Das Skript ist idempotent and kann wiederholt ausgeführt werden.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.logging import RichHandler

# Rich Logging Setup
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)
logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

from seven2one.questra.authentication import QuestraAuthentication

from seven2one.questra.data import (
    AssignableDataType,
    ConflictAction,
    InventoryProperty,
    Quality,
    QuestraData,
    StringPropertyConfig,
    TimeSeriesValue,
    TimeUnit,
)
from seven2one.questra.data.models.inputs import (
    BoolProperty,
    DateProperty,
    DateTimeOffsetProperty,
    DateTimeProperty,
    DecimalProperty,
    FileProperty,
    GuidProperty,
    IntProperty,
    StringProperty,
    TimeProperty,
    TimeSeriesProperty,
)

# Optionale pandas Integration
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class RegressionTestsHighLevel:
    """High-Level API Regressions-Tests."""

    def __init__(self, client: QuestraData):
        """
        Initialisiert Tests with QuestraData High-Level Client.

        Args:
            client: Konfigurierter QuestraData Client
        """
        self.client = client
        self.error = False
        self.namespace = "TestNamespaceHighLevel"
        self.inventory = "TestUserHighLevel"

    def get_system_info(self):
        """System-Informationen abrufen."""
        print("=== System-Informationen ===")
        try:
            info = self.client.get_system_info()
            print(f"Dyno Version: {info.dynamic_objects_version}")
            print(f"Datenbank: {info.database_version}")
            free_mb = info.memory_info.free_mb if info.memory_info else 0
            print(f"Speicher frei: {free_mb} MB\n")
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def list_namespaces(self):
        """Namespaces auflisten."""
        print("=== Namespaces auflisten ===")
        try:
            namespaces = self.client.list_namespaces()
            print(f"Anzahl Namespaces: {len(namespaces)}")
            for ns in namespaces[:5]:
                print(f"  - {ns.name}: {ns.description or 'Keine Beschreibung'}")
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def list_roles(self):
        """Roles auflisten."""
        print("=== Roles auflisten ===")
        try:
            roles = self.client.list_roles()
            print(f"Anzahl Roles: {len(roles)}")
            for role in roles[:5]:
                print(f"  - {role.name}: {role.description or 'Keine Beschreibung'}")
                print(f"    System Role: {role.is_system}")
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def list_units(self):
        """Units auflisten."""
        print("=== Units auflisten ===")
        try:
            units = self.client.list_units()
            print(f"Anzahl Units: {len(units)}")
            for unit in units[:10]:
                print(f"  - {unit.symbol}: {unit.aggregation}")
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def list_time_zones(self):
        """Zeitzonen auflisten."""
        print("=== Zeitzonen auflisten ===")
        try:
            time_zones = self.client.list_time_zones()
            print(f"Anzahl Zeitzonen: {len(time_zones)}")
            for tz in time_zones[:5]:
                print(
                    f"  - {tz.name}: UTC{tz.base_utc_offset}, DST={tz.supports_daylight_saving_time}"
                )
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def create_namespace(self):
        """Test-Namespace erstellen."""
        print("=== Namespace erstellen ===")
        try:
            result = self.client.create_namespace(
                name=self.namespace,
                description="Test-Namespace für High-Level API Tests",
                if_exists=ConflictAction.IGNORE,
            )
            print(f"Namespace: {result.name}, existierte bereits: {result.existed}\n")
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def create_inventory(self):
        """Test-Inventory with Properties erstellen."""
        print("=== Inventory erstellen ===")
        try:
            properties = [
                InventoryProperty(  # teste legacy InventoryProperty
                    propertyName="username",
                    dataType=AssignableDataType.STRING,
                    isRequired=True,
                    isUnique=True,
                    string=StringPropertyConfig(maxLength=100),
                ),
                StringProperty(
                    propertyName="email", isRequired=True, isUnique=True, maxLength=255
                ),
                IntProperty(
                    propertyName="age",
                    isRequired=False,
                ),
                BoolProperty(
                    propertyName="active",
                    isRequired=True,
                ),
                TimeSeriesProperty(
                    propertyName="sensor_data",
                    isRequired=False,
                    unit="°C",
                    timeUnit=TimeUnit.MINUTE,
                    multiplier=15,
                ),
                DecimalProperty(
                    propertyName="height",
                    isRequired=False,
                ),
                DateTimeProperty(
                    propertyName="last_login",
                    isRequired=False,
                ),
                FileProperty(
                    propertyName="profile_picture",
                    maxLength=1024,
                    isRequired=False,
                ),
                GuidProperty(
                    propertyName="user_guid",
                    isRequired=False,
                ),
                DateTimeOffsetProperty(
                    propertyName="created_at",
                    isRequired=False,
                ),
                DateProperty(
                    propertyName="birth_date",
                    isRequired=False,
                ),
                TimeProperty(
                    propertyName="preferred_contact_time",
                    isRequired=False,
                ),
            ]

            result = self.client.create_inventory(
                name=self.inventory,
                namespace_name=self.namespace,
                properties=properties,
                description="Test-Inventory für High-Level API",
                if_exists=ConflictAction.IGNORE,
            )
            print(f"Inventory: {result.name}, existierte bereits: {result.existed}\n")
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def list_inventories(self):
        """Inventories auflisten."""
        print("=== Inventories auflisten ===")
        try:
            inventories = self.client.list_inventories(namespace_name=self.namespace)
            print(f"Inventories in '{self.namespace}': {len(inventories)}")
            for inv in inventories:
                inv_type = inv.inventory_type.value if inv.inventory_type else "unknown"
                print(f"  - {inv.name} ({inv_type})")
                if inv.properties:
                    print(f"    Properties: {len(inv.properties)}")
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def create_items(self):
        """Items erstellen (mit automatischer TimeSeries-Erstellung)."""
        print("=== Items erstellen ===")
        try:
            items = [
                {
                    "username": "alice",
                    "email": "alice@example.com",
                    "age": 30,
                    "active": True,
                    "sensor_data": None,  # Automatische TimeSeries-Erstellung
                },
                {
                    "username": "bob",
                    "email": "bob@example.com",
                    "age": 25,
                    "active": True,
                    "sensor_data": None,
                },
                {
                    "username": "charlie",
                    "email": "charlie@example.com",
                    "age": 35,
                    "active": False,
                    "sensor_data": None,
                    "created_at": datetime.now().isoformat(),
                },
                {
                    "username": "diana",
                    "email": "diana@example.com",
                    "age": 28,
                    "active": True,
                    "sensor_data": None,
                    "height": 1.65,
                    "birth_date": datetime(1995, 5, 15).date(),
                    "preferred_contact_time": datetime.strptime(
                        "14:30:00", "%H:%M:%S"
                    ).time(),
                    "user_guid": "123e4567-e89b-12d3-a456-426614174000",
                    "created_at": datetime.now(),
                    "last_login": datetime.now(),
                },
            ]

            created = self.client.create_items(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                items=items,
            )
            print(f"Erstellt: {len(created)} Items")
            for item in created:
                # create_items gibt only _id, _rowVersion, _existed zurück
                status = "already vorhanden" if item.get("_existed") else "neu"
                print(
                    f"  - ID {item['_id']}: _rowVersion={item['_rowVersion']} ({status})"
                )
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def list_items(self):
        """Items auflisten."""
        print("=== Items auflisten ===")
        # Absichtlich Username groß geschrieben, um Case-Insensitivity zu testen
        try:
            items = self.client.list_items(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                properties=["_id", "_rowVersion", "Username", "email", "age", "active"],
                limit=100,
            )
            print(f"Anzahl Items: {len(items)}")
            for item in items:
                print(
                    f"  - [{item['_id']}] {item['Username']}: {item['email']}, "
                    f"Age={item.get('age', 'N/A')}, Active={item['active']}"
                )
            print()
            return items
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True
            return []

    def update_items(self, items_to_update):
        """Items aktualisieren."""
        print("=== Items aktualisieren ===")
        try:
            if not items_to_update:
                print("Keine Items zum Aktualisieren\n")
                return

            # Ersten User deaktivieren
            item = items_to_update[0]
            item["active"] = False
            item["age"] = 31

            updated = self.client.update_items(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                items=[item],
            )
            print(f"Aktualisiert: {len(updated)} Items")
            for upd in updated:
                # update_items gibt only _id, _rowVersion, _existed zurück
                print(
                    f"  - ID {upd['_id']}: _rowVersion={upd['_rowVersion']}, existed={upd.get('_existed', 'N/A')}"
                )
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def delete_items(self, items_to_delete):
        """Items löschen."""
        print("=== Items löschen ===")
        try:
            if not items_to_delete:
                print("Keine Items zum Löschen\n")
                return

            # Letzten User löschen
            item = items_to_delete[-1]

            # Reduziere Item auf _id and _rowVersion (only diese Felder sind beim Löschen erlaubt)
            item_to_delete = {"_id": item["_id"], "_rowVersion": item["_rowVersion"]}

            deleted = self.client.delete_items(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                item_ids=[item_to_delete],
            )
            print(f"Gelöscht: {len(deleted)} Items")
            for del_item in deleted:
                print(f"  - ID {del_item['_id']}")
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def save_timeseries_values(self):
        """Zeitreihenvalues speichern (High-Level)."""
        print("=== Zeitreihenvalues speichern (High-Level) ===")
        try:
            # Lade Items with TimeSeries-Property
            items = self.client.list_items(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                properties=["_id", "username", "sensor_data.id"],
                limit=10,
            )

            if not items:
                print("Keine Items zum Speichern of Zeitreihenvaluesn\n")
                return

            # Erstelle Zeitreihenvalues für alle Items
            # Startzeit: 10 Stunden in der Vergangenheit
            start_time = datetime.now() - timedelta(hours=10)
            item_values = {}

            for i, item in enumerate(items):
                # Nur Items with TimeSeries
                if item.get("sensor_data") and item["sensor_data"].get("id"):
                    # Werte in chronologischer Reihenfolge (aufsteigend)
                    values = [
                        TimeSeriesValue(
                            time=start_time + timedelta(hours=j),
                            value=20.0 + i + j * 0.5,
                            quality=Quality.VALID,
                        )
                        for j in range(10)
                    ]
                    item_values[item["_id"]] = values

            if item_values:
                self.client.save_timeseries_values_bulk(
                    inventory_name=self.inventory,
                    namespace_name=self.namespace,
                    timeseries_properties="sensor_data",
                    item_values=item_values,
                    time_unit=TimeUnit.MINUTE,
                    multiplier=15,
                    unit="°C",
                )
                print(f"Zeitreihenvalues für {len(item_values)} Items gespeichert")
                for item_id, values in item_values.items():
                    print(f"  - Item ID {item_id}: {len(values)} Werte")
                print()
            else:
                print("Keine Items with TimeSeries gefunden\n")
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def list_timeseries_values(self):
        """Zeitreihenvalues laden (High-Level)."""
        print("=== Zeitreihenvalues laden (High-Level) ===")
        try:
            result = self.client.list_timeseries_values(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                timeseries_properties="sensor_data",
                from_time=datetime.now() - timedelta(days=1),
                to_time=datetime.now() + timedelta(hours=1),
                properties=["username"],
            )

            print(f"Zeitreihenvalues für {len(result)} Items")
            for item_id, data in result.items():
                item = data["item"]
                ts_data = data["timeseries"].get("sensor_data", {})
                values = ts_data.get("values", [])
                print(f"\n  User: {item.get('username', 'N/A')} (ID {item_id})")
                print(f"  TimeSeries ID: {ts_data.get('timeseries_id', 'N/A')}")
                print(f"  Unit: {ts_data.get('unit', 'N/A')}")
                print(f"  Anzahl Werte: {len(values)}")
                if values:
                    print(f"  Erster Wert: {values[0].time} = {values[0].value}")
                    print(f"  Letzter Wert: {values[-1].time} = {values[-1].value}")
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def test_dataframes(self):
        """Teste DataFrame-Integration (falls pandas verfügbar)."""
        if not PANDAS_AVAILABLE:
            print("=== Pandas nicht verfügbar - DataFrame-Tests übersprungen ===\n")
            return

        print("=== DataFrame-Tests ===")
        try:
            # Items as DataFrame
            df_items = self.client.list_items(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                properties=["_id", "username", "email", "age", "active"],
                limit=100,
            ).to_df()
            print(f"Items DataFrame: {len(df_items)} Zeilen")
            if not df_items.empty:
                print(df_items)
            print()

            # Inventories as DataFrame
            df_inventories = self.client.list_inventories(
                namespace_name=self.namespace
            ).to_df()
            print(f"Inventories DataFrame: {len(df_inventories)} Zeilen")
            if not df_inventories.empty:
                print(df_inventories)
            print()

            # Roles as DataFrame
            df_roles = self.client.list_roles().to_df()
            print(f"Roles DataFrame: {len(df_roles)} Zeilen")
            if not df_roles.empty:
                print(df_roles[["name", "is_system"]].head(5))
            print()

            # Units as DataFrame
            df_units = self.client.list_units().to_df()
            print(f"Units DataFrame: {len(df_units)} Zeilen")
            if not df_units.empty:
                print(df_units.head(10))
                print("\nUnits nach Aggregation:")
                print(df_units.groupby("aggregation", sort=False).size())
            print()

            # Zeitzonen as DataFrame
            df_tz = self.client.list_time_zones().to_df()
            print(f"Zeitzonen DataFrame: {len(df_tz)} Zeilen")
            if not df_tz.empty:
                print(df_tz.head(5))
                europe_tz = df_tz[df_tz["name"].str.contains("Europe")]
                print(f"\nEuropäische Zeitzonen: {len(europe_tz)}")
            print()

            # Zeitreihen as DataFrame
            try:
                ts_result = self.client.list_timeseries_values(
                    inventory_name=self.inventory,
                    namespace_name=self.namespace,
                    timeseries_properties="sensor_data",
                    from_time=datetime.now() - timedelta(days=1),
                    to_time=datetime.now() + timedelta(hours=1),
                    properties=["username"],
                )
                df_ts = ts_result.to_df(include_metadata=True, properties=["username"])
                print(f"Zeitreihen DataFrame: {len(df_ts)} Zeilen")
                if not df_ts.empty:
                    print(df_ts.head(10))
                print()
            except Exception as e:
                print(f"Hinweis at Zeitreihen-DataFrame: {e}\n")

        except Exception as e:
            print(f"Fehler at DataFrame-Tests: {e}\n")
            self.error = True

    def delete_all_items(self):
        """Alle Items löschen (für Cleanup)."""
        print("=== Alle Items löschen ===")
        try:
            items = self.client.list_items(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                properties=["_id", "_rowVersion"],
                limit=1000,
            )

            if items:
                # Reduziere Items auf _id and _rowVersion (only diese Felder sind beim Löschen erlaubt)
                items_to_delete = [
                    {"_id": item["_id"], "_rowVersion": item["_rowVersion"]}
                    for item in items
                ]

                # Type-Cast für Type-Checker
                item_ids: list[int | dict] = items_to_delete  # type: ignore[assignment]
                deleted = self.client.delete_items(
                    inventory_name=self.inventory,
                    namespace_name=self.namespace,
                    item_ids=item_ids,
                )
                print(f"Gelöscht: {len(deleted)} Items")
                for item in deleted:
                    print(f"  - ID {item['_id']}")
                print()
            else:
                print("Keine Items zum Löschen\n")
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def delete_inventory(self):
        """Inventory löschen."""
        print("=== Inventory löschen ===")
        try:
            result = self.client.delete_inventory(
                inventory_name=self.inventory,
                namespace_name=self.namespace,
                if_not_exists=ConflictAction.IGNORE,
            )
            print(f"Inventory: {result.name}, existierte: {result.existed}\n")
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def delete_namespace(self):
        """Namespace löschen."""
        print("=== Namespace löschen ===")
        try:
            result = self.client.delete_namespace(
                name=self.namespace,
                if_not_exists=ConflictAction.IGNORE,
            )
            print(f"Namespace: {result.name}, existierte: {result.existed}\n")
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True

    def test_lowlevel_access(self):
        """Teste Low-Level API Zugriff."""
        print("=== Low-Level API Zugriff ===")
        try:
            result = self.client.lowlevel.execute_raw("""
                query {
                    _timeZones {
                        name
                        baseUtcOffset
                    }
                }
            """)
            print("Erste 3 Zeitzonen (via Low-Level):")
            for tz in result["_timeZones"][:3]:
                print(f"  - {tz['name']}: {tz['baseUtcOffset']}")
            print()
        except Exception as e:
            print(f"Fehler: {e}\n")
            self.error = True


def main():
    """Führt alle High-Level API Tests aus."""
    print("\n" + "=" * 70)
    print("HIGH-LEVEL API REGRESSIONS-TEST")
    print("=" * 70 + "\n")

    load_dotenv(Path(__file__).parent / ".env")
    username = os.getenv("QUESTRA_USERNAME", "")
    password = os.getenv("QUESTRA_SECRET")
    print(f"Username: {'(leer)' if not username else username}")

    # Client initialisieren
    if username:
        auth_client = QuestraAuthentication(
            url="https://authentik.dev.questra.s2o.dev",
            username=username,
            password=password,
        )
    else:
        auth_client = QuestraAuthentication(
            url="https://authentik.dev.questra.s2o.dev",
            interactive=True,
        )

    client = QuestraData(
        graphql_url="https://dev.questra.s2o.dev/data/graphql/",
        auth_client=auth_client,
    )

    logger.info(f"Client initialisiert: {client}")
    logger.info(f"Authentifiziert: {client.is_authenticated()}")

    tests = RegressionTestsHighLevel(client)

    # Phase 1: System-Informationen
    print("\n" + "=" * 70)
    print("PHASE 1: System-Informationen and Basis-Queries")
    print("=" * 70 + "\n")

    tests.get_system_info()
    tests.list_namespaces()
    tests.list_roles()
    tests.list_units()
    tests.list_time_zones()

    # Phase 2: Setup - Namespace and Inventory
    print("\n" + "=" * 70)
    print("PHASE 2: Setup - Namespace and Inventory")
    print("=" * 70 + "\n")

    tests.create_namespace()
    tests.create_inventory()
    tests.list_inventories()

    # Phase 3: CRUD - Items
    print("\n" + "=" * 70)
    print("PHASE 3: CRUD - Inventory Items")
    print("=" * 70 + "\n")

    tests.create_items()
    items = tests.list_items()
    tests.update_items(items[:1] if items else [])
    items_after_update = tests.list_items()
    tests.delete_items(items_after_update[-1:] if items_after_update else [])
    tests.list_items()

    # Phase 4: TimeSeries Operations
    print("\n" + "=" * 70)
    print("PHASE 4: TimeSeries Operations (High-Level)")
    print("=" * 70 + "\n")

    tests.save_timeseries_values()
    tests.list_timeseries_values()

    # Phase 5: DataFrame-Integration
    print("\n" + "=" * 70)
    print("PHASE 5: DataFrame-Integration")
    print("=" * 70 + "\n")

    tests.test_dataframes()

    # Phase 6: Low-Level Access
    print("\n" + "=" * 70)
    print("PHASE 6: Low-Level API Zugriff")
    print("=" * 70 + "\n")

    tests.test_lowlevel_access()

    # Phase 7: Cleanup
    print("\n" + "=" * 70)
    print("PHASE 7: Cleanup")
    print("=" * 70 + "\n")

    tests.delete_all_items()
    tests.delete_inventory()
    tests.delete_namespace()

    # Ergebnis
    print("\n" + "=" * 70)
    if tests.error:
        print("REGRESSION TEST FEHLGESCHLAGEN")
        print("=" * 70 + "\n")
        sys.exit(1)
    else:
        print("REGRESSION TEST ERFOLGREICH ABGESCHLOSSEN")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
