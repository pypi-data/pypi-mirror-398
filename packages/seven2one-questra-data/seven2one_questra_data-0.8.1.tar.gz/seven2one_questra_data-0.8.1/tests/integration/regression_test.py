"""
Script für Questra Data zum Testen auf Regression.
"""

from __future__ import annotations

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
from datetime import datetime

from seven2one.questra.authentication import QuestraAuthentication

from seven2one.questra.data import (
    AssignableDataType,
    ConflictAction,
    Namespace,
    QuestraDataCore,
)
from seven2one.questra.data.models.inputs import (
    CreateTimeSeriesInput,
    IntervalConfig,
    InventoryProperty,
    StringPropertyConfig,
    TimeSeriesPropertyConfig,
)
from seven2one.questra.data.models.inventory import Inventory
from seven2one.questra.data.models.rest import SetTimeSeriesDataInput
from seven2one.questra.data.models.timeseries import TimeSeriesValue, TimeUnit


class RegressionTests:
    def __init__(self, client: QuestraDataCore, error: bool = False):
        self.client = client
        self.error = error

    def get_sysinfo(self):
        # 2. System-Informationen abrufen
        print("=== System-Informationen ===")
        system_info = self.client.queries.get_system_info()
        print(f"Dyno Version: {system_info.dynamic_objects_version}")
        print(f"Datenbank Version: {system_info.database_version}")
        free_mb = system_info.memory_info.free_mb if system_info.memory_info else 0
        print(f"Speicher frei: {free_mb} MB\n")

    def get_namespaces(self) -> list[Namespace]:
        # 3. Namespaces abfragen
        print("=== Namespaces abfragen ===")
        namespaces = self.client.queries.get_namespaces()
        for namespace in namespaces:
            print(
                f"  - {namespace.name}: {namespace.description or 'Keine Beschreibung'}"
            )
        print(f"Anzahl Namespaces: {len(namespaces)}\n")
        return namespaces

    def get_inventories(self) -> list[Inventory]:
        # 4. Inventories abfragen
        print("=== Inventories abfragen ===")
        inventories = self.client.queries.get_inventories(order={"by": "NAME"})
        for inventory in inventories:
            inv_type = (
                inventory.inventory_type.DATA if inventory.inventory_type else "unknown"
            )
            print(f"  - {inventory.name} ({inv_type})")
            namespace_name = inventory.namespace.name if inventory.namespace else None
            print(f"    Namespace: {namespace_name}")
            print(f"    Audit: {inventory.audit_enabled}")
            if inventory.properties:
                print(f"    Properties: {len(inventory.properties)}")
        print()
        return inventories

    def create_namespace(self):
        # 5. Namespace erstellen
        print("=== Namespace erstellen ===")
        try:
            result = self.client.mutations.create_namespace(
                namespace_name="TestNamespace",
                description="Ein Test-Namespace",
                if_exists=ConflictAction.IGNORE,
            )
            print(
                f"Namespace erstellt: {result.name}, existierte bereits: {result.existed}\n"
            )
        except Exception as e:
            print(f"Fehler beim Erstellen: {e}\n")
            self.error = True

    def rename_namespace(self):
        print("=== Namespace umbenennen ===")
        try:
            result = self.client.mutations.alter_namespace(
                namespace_name="TestNamespace",
                new_namespace_name="TestNamespaceRenamed",
            )
            print(
                f"Namespace umbenannt: {result.name}, existierte bereits: {result.existed}\n"
            )
        except Exception as e:
            print(f"Fehler beim Umbenennen: {e}\n")
            self.error = True

    def delete_namespace(self):
        print("=== Namespace löschen ===")
        try:
            result = self.client.mutations.drop_namespace(
                namespace_name="TestNamespaceRenamed",
                if_not_exists=ConflictAction.IGNORE,
            )
            print(f"Namespace gelöscht: {result.name}, existierte: {result.existed}\n")
        except Exception as e:
            print(f"Fehler beim Löschen: {e}\n")
            self.error = True

    def create_inventory(self, namespace: str | None):
        print("=== Inventory in Namespace erstellen ===")
        try:
            properties = [
                InventoryProperty(
                    propertyName="Name",
                    dataType=AssignableDataType.STRING,
                    string=StringPropertyConfig(maxLength=255),
                    isRequired=True,
                    isUnique=False,
                    isArray=False,
                ),
                InventoryProperty(
                    propertyName="Email",
                    dataType=AssignableDataType.STRING,
                    string=StringPropertyConfig(maxLength=255),
                    isRequired=True,
                    isUnique=True,
                    isArray=False,
                ),
                InventoryProperty(
                    propertyName="Age",
                    dataType=AssignableDataType.INT,
                    isRequired=False,
                    isUnique=False,
                    isArray=False,
                ),
                InventoryProperty(
                    propertyName="IsActive",
                    dataType=AssignableDataType.BOOLEAN,
                    isRequired=True,
                    isUnique=False,
                    isArray=False,
                ),
                InventoryProperty(
                    propertyName="BodyBattery",
                    dataType=AssignableDataType.TIME_SERIES,
                    isRequired=False,
                    timeSeries=TimeSeriesPropertyConfig(
                        unit="kW",
                        interval=IntervalConfig(
                            multiplier=15, timeUnit=TimeUnit.MINUTE
                        ),
                    ),
                ),
            ]

            result = self.client.mutations.create_inventory(
                inventory_name="TestUser",
                namespace_name=namespace,
                properties=properties,
                description="Test-Inventory für Benutzer",
                enable_audit=True,
                if_exists=ConflictAction.IGNORE,
            )
            print(
                f"Inventory erstellt: {result.name}, existierte bereits: {result.existed}\n"
            )
        except Exception as e:
            print(f"Fehler beim Erstellen: {e}\n")
            self.error = True

    def delete_inventory_func(self, namespace: str | None):
        print("=== Inventory löschen ===")
        try:
            result = self.client.mutations.delete_inventory(
                inventory_name="TestUser",
                namespace_name=namespace,
                if_not_exists=ConflictAction.IGNORE,
            )
            print(f"Inventory gelöscht: {result.name}, existierte: {result.existed}\n")
        except Exception as e:
            print(f"Fehler beim Löschen: {e}\n")
            self.error = True

    def execute_query(self):
        # 10. Rohe GraphQL-Query ausführen
        print("=== Rohe GraphQL-Query ===")
        try:
            result = self.client.execute_raw("""
                query {
                    _timeZones {
                        name
                        baseUtcOffset
                    }
                }
            """)
            print(f"Anzahl Zeitzonen: {len(result['_timeZones'])}")
            print(f"Erste Zeitzone: {result['_timeZones'][0]['name']}\n")
        except Exception as e:
            print(f"Fehler at roher Query: {e}\n")
            self.error = True

    def get_roles(self):
        print("=== Roles abfragen ===")
        try:
            roles = self.client.queries.get_roles()
            for role in roles:
                print(f"  - {role.name}: {role.description or 'Keine Beschreibung'}")
                print(f"    System Role: {role.is_system}")
            print(f"Anzahl Roles: {len(roles)}\n")
        except Exception as e:
            print(f"Fehler beim Abfragen der Roles: {e}\n")
            self.error = True

    def get_units(self):
        print("=== Units abfragen ===")
        try:
            units = self.client.queries.get_units()
            for unit in units:
                print(f"  - {unit.symbol}: Aggregation={unit.aggregation}")
            print(f"Anzahl Units: {len(units)}\n")
        except Exception as e:
            print(f"Fehler beim Abfragen der Units: {e}\n")
            self.error = True

    def get_time_zones(self):
        print("=== Zeitzonen abfragen ===")
        try:
            time_zones = self.client.queries.get_time_zones()
            for tz in time_zones[:5]:  # Nur die ersten 5 anzeigen
                print(
                    f"  - {tz.name}: UTC{tz.base_utc_offset}, DST={tz.supports_daylight_saving_time}"
                )
            print(f"Anzahl Zeitzonen: {len(time_zones)}\n")
        except Exception as e:
            print(f"Fehler beim Abfragen der Zeitzonen: {e}\n")
            self.error = True

    def create_test_unit(self):
        print("=== Test-Unit erstellen ===")
        try:
            result = self.client.mutations.create_unit(
                symbol="TestkW", aggregation="AVERAGE", if_exists=ConflictAction.IGNORE
            )
            print(
                f"Unit erstellt: {result.name}, existierte bereits: {result.existed}\n"
            )
        except Exception as e:
            print(f"Fehler beim Erstellen der Unit: {e}\n")
            self.error = True

    def delete_test_unit(self):
        print("=== Test-Unit löschen ===")
        try:
            result = self.client.mutations.delete_unit(
                symbol="TestkW", if_not_exists=ConflictAction.IGNORE
            )
            print(f"Unit gelöscht: {result.name}, existierte: {result.existed}\n")
        except Exception as e:
            print(f"Fehler beim Löschen der Unit: {e}\n")
            self.error = True

    def deny_permissions(self):
        print("=== Permissions verweigern ===")
        try:
            self.client.mutations.deny_inventory_permissions(
                inventory_name="TestUser",
                role_name="TestRole",
                privileges=["DELETE"],
                namespace_name="TestNamespace",
            )
            print("Permissions erfolgreich verweigert\n")
        except Exception as e:
            print(f"Fehler beim Verweigern: {e}\n")
            self.error = True

    def revoke_permissions(self):
        print("=== Permissions widerrufen ===")
        try:
            self.client.mutations.revoke_inventory_permissions(
                inventory_name="TestUser",
                role_name="TestRole",
                privileges=["SELECT", "INSERT", "UPDATE"],
                namespace_name="TestNamespace",
            )
            print("Permissions erfolgreich widerrufen\n")
        except Exception as e:
            print(f"Fehler beim Widerrufen: {e}\n")
            self.error = True

    def create_inventory_policy(self):
        print("=== Inventory Policy erstellen ===")
        try:
            result = self.client.mutations.create_inventory_policy(
                policy_name="TestPolicy",
                role_name="TestRole",
                inventory_name="TestUser",
                property_name="Age",
                filter_value=30,
                namespace_name="TestNamespace",
                description="Test-Policy für 30-jährige Benutzer",
                if_exists=ConflictAction.IGNORE,
            )
            print(
                f"Policy erstellt: {result.name}, existierte bereits: {result.existed}\n"
            )
        except Exception as e:
            print(f"Fehler beim Erstellen der Policy: {e}\n")
            self.error = True

    def delete_inventory_policy(self):
        print("=== Inventory Policy löschen ===")
        try:
            result = self.client.mutations.delete_inventory_policy(
                policy_name="TestPolicy",
                inventory_name="TestUser",
                namespace_name="TestNamespace",
                if_not_exists=ConflictAction.IGNORE,
            )
            print(f"Policy gelöscht: {result.name}, existierte: {result.existed}\n")
        except Exception as e:
            print(f"Fehler beim Löschen der Policy: {e}\n")
            self.error = True

    def create_role(self):
        print("=== Role erstellen ===")
        try:
            result = self.client.mutations.create_role(
                role_name="TestRole",
                description="Eine Test-Rolle",
                if_exists=ConflictAction.IGNORE,
            )
            print(
                f"Role erstellt: {result.name}, existierte bereits: {result.existed}\n"
            )
        except Exception as e:
            print(f"Fehler beim Erstellen: {e}\n")
            self.error = True

    def grant_permissions(self):
        # 8. Permissions gewähren
        print("=== Permissions gewähren ===")
        try:
            self.client.mutations.grant_inventory_permissions(
                inventory_name="TestUser",
                role_name="TestRole",
                privileges=["SELECT", "INSERT", "UPDATE"],
                namespace_name="TestNamespace",
            )
            print("Permissions erfolgreich gewährt\n")
        except Exception as e:
            print(f"Fehler beim Gewähren: {e}\n")
            self.error = True

    def insert_user(self):
        # Dynamische Inventory-Operationen: Items einfügen
        print("=== Items in TestUser erstellen ===")
        try:
            items = self.client.inventory.create(
                inventory_name="TestUser",
                namespace_name="TestNamespace",
                items=[
                    {
                        "Name": "John Doe",
                        "Email": "john.doe@example.com",
                        "Age": 30,
                        "IsActive": True,
                    },
                    {
                        "Name": "Jane Smith",
                        "Email": "jane.smith@example.com",
                        "Age": 28,
                        "IsActive": True,
                    },
                    {
                        "Name": "Bob Wilson",
                        "Email": "bob.wilson@example.com",
                        "Age": 35,
                        "IsActive": False,
                    },
                ],
            )
            for item in items:
                status = "already vorhanden" if item["_existed"] else "neu erstellt"
                print(f"  - ID={item['_id']}: {status}")
            print()
        except Exception as e:
            print(f"Fehler beim Einfügen: {e}\n")
            self.error = True

    def query_users(self, namespace: str | None):
        # Dynamische Inventory-Operationen: Items abfragen
        print("=== Items from TestUser abfragen ===")
        try:
            result = self.client.inventory.list(
                inventory_name="TestUser",
                namespace_name=namespace,
                properties=[
                    "_id",
                    "_rowVersion",
                    "Name",
                    "Email",
                    "Age",
                    "IsActive",
                    "BodyBattery.id",
                ],
                first=10,
            )
            print(f"Anzahl Items: {len(result['nodes'])}")
            for item in result["nodes"]:
                print(
                    f"  - [{item['_id']}] {item['name']}: "
                    f"{item['email']}, Age={item.get('age', 'N/A')}, "
                    f"Active={item['isActive']}, BodyBattery={item.get('bodyBattery', 'N/A')}"
                )
            print(f"Hat weitere Seiten: {result['pageInfo']['hasNextPage']}\n")
        except Exception as e:
            print(f"Fehler beim Abfragen: {e}\n")
            self.error = True

    def update_user(self, namespace: str | None, ts_id: int):
        # Dynamische Inventory-Operationen: Items aktualisieren
        print("=== Items in TestUser aktualisieren ===")
        try:
            # Zuerst Items abrufen um ID and RowVersion to bekommen
            result = self.client.inventory.list(
                inventory_name="TestUser",
                namespace_name=namespace,
                properties=["_id", "_rowVersion", "Name", "Email"],
                first=1,
            )

            if result["nodes"]:
                item = result["nodes"][0]
                print(f"Aktualisiere User: {item['name']}")

                updated = self.client.inventory.update(
                    inventory_name="TestUser",
                    namespace_name=namespace,
                    items=[
                        {
                            "_id": item["_id"],
                            "_rowVersion": item["_rowVersion"],
                            "IsActive": False,  # Aktivitätsstatus ändern
                            "BodyBattery": f"{ts_id}",  # Zeitreihe zuweisen
                        }
                    ],
                )
                for upd_item in updated:
                    status = (
                        "gefunden and aktualisiert"
                        if upd_item["_existed"]
                        else "nicht gefunden"
                    )
                    print(f"  - ID {upd_item['_id']}: {status}\n")
            else:
                print("Keine Items zum Aktualisieren gefunden\n")
        except Exception as e:
            print(f"Fehler beim Aktualisieren: {e}\n")
            self.error = True

    def delete_users(self, namespace: str | None):
        # Dynamische Inventory-Operationen: Items löschen
        print("=== Items from TestUser löschen ===")
        try:
            # Zuerst Items abrufen um ID and RowVersion to bekommen
            result = self.client.inventory.list(
                inventory_name="TestUser",
                namespace_name=namespace,
                properties=["_id", "_rowVersion", "Name"],
                first=1,
            )

            if result["nodes"]:
                item = result["nodes"][0]
                print(f"Lösche User: {item['name']}")

                deleted = self.client.inventory.delete(
                    inventory_name="TestUser",
                    namespace_name="TestNamespace",
                    items=[{"_id": item["_id"], "_rowVersion": item["_rowVersion"]}],
                )
                for del_item in deleted:
                    status = (
                        "gefunden and gelöscht"
                        if del_item["_existed"]
                        else "nicht gefunden"
                    )
                    print(f"  - ID {del_item['_id']}: {status}\n")
            else:
                print("Keine Items zum Löschen gefunden\n")
        except Exception as e:
            print(f"Fehler beim Löschen: {e}\n")
            self.error = True

    def delete_all_users(self):
        # Alle Items löschen (Vorsicht!)
        print("=== Alle Items from TestUser löschen ===")
        try:
            result = self.client.inventory.list(
                inventory_name="TestUser",
                namespace_name="TestNamespace",
                properties=["_id", "_rowVersion", "Name"],
                first=1000,
            )
            if result["nodes"]:
                for item in result["nodes"]:
                    print(f"Lösche User: {item['name']}")
                    deleted = self.client.inventory.delete(
                        inventory_name="TestUser",
                        namespace_name="TestNamespace",
                        items=[
                            {"_id": item["_id"], "_rowVersion": item["_rowVersion"]}
                        ],
                    )
                    for del_item in deleted:
                        status = (
                            "gefunden and gelöscht"
                            if del_item["_existed"]
                            else "nicht gefunden"
                        )
                        print(f"  - ID {del_item['_id']}: {status}\n")
            else:
                print("Keine Items zum Löschen gefunden\n")
        except Exception as e:
            print(f"Fehler beim Löschen aller Items: {e}\n")
            self.error = True

    def create_timeseries(self) -> int:
        print("=== Zeitreihe erstellen ===")
        try:
            result = self.client.mutations.create_timeseries(
                time_series_inputs=[
                    CreateTimeSeriesInput(
                        namespaceName="TestNamespace",
                        inventoryName="TestUser",
                        propertyName="BodyBattery",
                    )
                ]
            )
            for ts in result:
                print(f"Zeitreihe erstellt: ID={ts.id}")
                return int(ts.id)
        except Exception as e:
            print(f"Fehler beim Erstellen der Zeitreihe: {e}\n")
            self.error = True
        return -1

    def set_timeseries_data(self, time_series_id: int):
        print("=== Zeitreihen-Daten setzen ===")
        try:
            self.client.timeseries.set_data(
                data_inputs=[
                    SetTimeSeriesDataInput(  # type: ignore[call-arg]
                        timeSeriesId=time_series_id,
                        values=[
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 0, 00), value=0.0
                            ),
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 0, 15), value=0.25
                            ),
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 0, 30), value=0.5
                            ),
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 0, 45), value=0.75
                            ),
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 1, 00), value=1.0
                            ),
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 1, 15), value=1.25
                            ),
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 1, 30), value=1.5
                            ),
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 1, 45), value=1.75
                            ),
                            TimeSeriesValue(
                                time=datetime(2025, 10, 10, 2, 00), value=2.0
                            ),
                        ],
                    )
                ]
            )
            print("Zeitreihen-Daten erfolgreich gesetzt\n")
        except Exception as e:
            print(f"Fehler beim Setzen der Zeitreihen-Daten: {e}\n")
            self.error = True

    def get_timeseries_data(self, time_series_id: int):
        print("=== Zeitreihen-Daten abfragen ===")
        try:
            result = self.client.timeseries.get_data(
                time_series_ids=[time_series_id],
                from_time=datetime(2025, 10, 10, 0, 0),
                to_time=datetime(2025, 10, 10, 2, 15),
            )
            print(f"Anzahl Datenpunkte: {len(result.data)}")
            for entry in result.data:
                print(f"  - Zeitreihe ID: {entry.time_series_id}")
                if entry.values:
                    for value in entry.values:
                        print(f"  - {value.time.isoformat()}: {value.value}")
            print()
        except Exception as e:
            print(f"Fehler beim Abfragen der Zeitreihen-Daten: {e}\n")
            self.error = True


def main():
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

    client = QuestraDataCore(
        graphql_url="https://dev.questra.s2o.dev/data/graphql/",
        auth_client=auth_client,
    )

    logger.info(f"Client initialisiert: {client}")
    logger.info(f"Authentifiziert: {client.is_authenticated()}")

    namespace = "TestNamespace"
    regtest = RegressionTests(client)

    # Phase 1: System-Informationen and Basisabfragen
    print("\n" + "=" * 60)
    print("PHASE 1: System-Informationen and Basis-Queries")
    print("=" * 60 + "\n")

    regtest.get_sysinfo()
    regtest.get_time_zones()
    regtest.get_units()

    # Phase 2: Namespace and Inventory Setup
    print("\n" + "=" * 60)
    print("PHASE 2: Namespace and Inventory Setup")
    print("=" * 60 + "\n")

    regtest.create_namespace()  # Namespace wird in Phase 12 umbenannt and gelöscht.

    namespaces = regtest.get_namespaces()
    assert any(ns.name == namespace for ns in namespaces), f"{namespace} nicht gefunden"

    # Phase 3: Test-Unit erstellen (für TimeSeries)
    print("\n" + "=" * 60)
    print("PHASE 3: Unit Management")
    print("=" * 60 + "\n")

    regtest.create_test_unit()
    regtest.get_units()  # Überprüfen, dass TestkW dabei ist

    # Phase 4: Inventories erstellen
    print("\n" + "=" * 60)
    print("PHASE 4: Inventory Erstellung")
    print("=" * 60 + "\n")

    regtest.create_inventory(namespace)
    regtest.create_inventory(namespace=None)

    inventories = regtest.get_inventories()
    assert any(inv.name == "TestUser" for inv in inventories), (
        "TestUser Inventory nicht gefunden"
    )

    # Phase 5: TimeSeries Operations
    print("\n" + "=" * 60)
    print("PHASE 5: TimeSeries Operations")
    print("=" * 60 + "\n")

    ts_id = regtest.create_timeseries()
    assert ts_id != -1, "Fehler beim Erstellen der Zeitreihe"

    regtest.set_timeseries_data(ts_id)
    regtest.get_timeseries_data(ts_id)

    # Phase 6: Inventory Items Operations
    print("\n" + "=" * 60)
    print("PHASE 6: Inventory Items CRUD")
    print("=" * 60 + "\n")

    regtest.insert_user()

    regtest.update_user(namespace, ts_id)
    regtest.update_user(None, ts_id)

    regtest.query_users(namespace)
    regtest.query_users(None)

    regtest.delete_users(namespace)

    # Phase 7: Permissions and Policies
    print("\n" + "=" * 60)
    print("PHASE 7: Permissions & Policy Management")
    print("=" * 60 + "\n")

    regtest.create_role()
    regtest.get_roles()  # Alle Roles inkl. TestRole anzeigen

    regtest.grant_permissions()
    regtest.deny_permissions()

    # regtest.create_inventory_policy()

    # Phase 8: Rohe GraphQL-Query
    print("\n" + "=" * 60)
    print("PHASE 8: Raw GraphQL Query")
    print("=" * 60 + "\n")

    regtest.execute_query()

    # Phase 9: Cleanup - Policy and Permissions
    print("\n" + "=" * 60)
    print("PHASE 9: Cleanup - Policies & Permissions")
    print("=" * 60 + "\n")

    # regtest.delete_inventory_policy()
    regtest.revoke_permissions()

    # Phase 10: Cleanup - Inventories
    print("\n" + "=" * 60)
    print("PHASE 10: Cleanup - Inventories")
    print("=" * 60 + "\n")

    # Alle User Items löschen bevor Inventory gelöscht wird
    regtest.delete_all_users()

    regtest.delete_inventory_func(namespace)
    regtest.delete_inventory_func(namespace=None)

    # Phase 11: Cleanup - Units
    print("\n" + "=" * 60)
    print("PHASE 11: Cleanup - Units")
    print("=" * 60 + "\n")

    regtest.delete_test_unit()

    # Phase 12: Namespace umbenennen and löschen
    print("\n" + "=" * 60)
    print("PHASE 12: Namespace Rename & Delete")
    print("=" * 60 + "\n")

    regtest.rename_namespace()
    namespaces = regtest.get_namespaces()
    assert any(ns.name == "TestNamespaceRenamed" for ns in namespaces), (
        "TestNamespaceRenamed nicht gefunden"
    )

    regtest.delete_namespace()
    namespaces = regtest.get_namespaces()
    assert not any(ns.name == "TestNamespaceRenamed" for ns in namespaces), (
        "TestNamespaceRenamed was nicht gelöscht"
    )

    print("\n" + "=" * 60)
    if regtest.error:
        print("REGRESSION TEST FEHLGESCHLAGEN")
        print("=" * 60 + "\n")
        sys.exit(1)
    else:
        print("REGRESSION TEST ERFOLGREICH ABGESCHLOSSEN")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
