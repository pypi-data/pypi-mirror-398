"""
Global pytest fixtures für alle Tests.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Pfad to GraphQL Response Fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "graphql_responses"
MUTATIONS_FIXTURES_DIR = FIXTURES_DIR / "mutations"

# Pfad to REST Response Fixtures
REST_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "rest_responses"


def load_graphql_response(filename: str) -> dict:
    """
    Lädt eine GraphQL Response from einer JSON-Datei.

    Args:
        filename: Name der JSON-Datei (z.B. "namespaces_response.json")

    Returns:
        dict: Deserialisierte GraphQL Response
    """
    filepath = FIXTURES_DIR / filename
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def load_mutation_response(filename: str) -> dict:
    """
    Lädt eine GraphQL Mutation Response from einer JSON-Datei.

    Args:
        filename: Name der JSON-Datei (z.B. "create_inventory_success.json")

    Returns:
        dict: Deserialisierte GraphQL Mutation Response
    """
    filepath = MUTATIONS_FIXTURES_DIR / filename
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def load_rest_response(category: str, filename: str) -> dict | list:
    """
    Lädt eine REST Response from einer JSON-Datei.

    NDJSON-Support: Wenn die Datei mehrere JSON-Objekte (durch Newlines getrennt)
    enthält, werden diese as Liste zurückgegeben (simuliert RESTTransport-Verhalten).

    Args:
        category: Kategorie (z.B. "timeseries", "file", "audit")
        filename: Name der JSON-Datei (z.B. "get_data_success.json")

    Returns:
        dict | list: Deserialisierte REST Response
    """
    filepath = REST_FIXTURES_DIR / category / filename
    with open(filepath, encoding="utf-8") as f:
        content = f.read().strip()

        # Versuche NDJSON to parsen (mehrere JSON-Objekte durch Newlines)
        try:
            # Versuche zuerst Standard-JSON
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Falls "Extra data" Error -> NDJSON (mehrere Objekte)
            if "Extra data" in str(e):
                # Split at }{ Pattern (mit optionalem Whitespace)
                objects_str = re.split(r"\}\s*\{", content)

                if len(objects_str) > 1:
                    # Re-add geschweifte Klammern
                    objects_str[0] += "}"
                    for i in range(1, len(objects_str) - 1):
                        objects_str[i] = "{" + objects_str[i] + "}"
                    objects_str[-1] = "{" + objects_str[-1]

                    return [json.loads(obj) for obj in objects_str]
            raise


@pytest.fixture
def mock_auth_client():
    """Mock für QuestraAuthentication Client."""
    mock = MagicMock()
    mock.is_authenticated.return_value = True
    mock.get_access_token.return_value = "mock_token_12345"
    return mock


@pytest.fixture
def mock_graphql_execute():
    """Mock für GraphQL Execute-Funktion."""
    return MagicMock()


@pytest.fixture
def mock_rest_get():
    """Mock für REST GET-Funktion."""
    return MagicMock()


@pytest.fixture
def mock_rest_post():
    """Mock für REST POST-Funktion."""
    return MagicMock()


@pytest.fixture
def sample_inventory_response():
    """GraphQL Response für _inventories Query (aus JSON-Datei)."""
    return load_graphql_response("inventories_response.json")


@pytest.fixture
def sample_namespace_response():
    """GraphQL Response für _namespaces Query (aus JSON-Datei)."""
    return load_graphql_response("namespaces_response.json")


@pytest.fixture
def sample_role_response():
    """GraphQL Response für _roles Query (aus JSON-Datei)."""
    return load_graphql_response("roles_response.json")


@pytest.fixture
def sample_system_info_response():
    """GraphQL Response für _systemInfo Query (aus JSON-Datei)."""
    return load_graphql_response("system_info_response.json")


@pytest.fixture
def sample_system_info_wo_message_response():
    """GraphQL Response für _systemInfo Query (aus JSON-Datei)."""
    return load_graphql_response("system_info_response_wo_message.json")


@pytest.fixture
def sample_units_response():
    """GraphQL Response für _units Query (aus JSON-Datei)."""
    return load_graphql_response("units_response.json")


@pytest.fixture
def sample_time_zones_response():
    """GraphQL Response für _timeZones Query (aus JSON-Datei)."""
    return load_graphql_response("time_zones_response.json")


@pytest.fixture
def sample_timeseries_response():
    """GraphQL Response für _timeSeries Query (einzelne TimeSeries)."""
    return load_graphql_response("timeseries_response.json")


@pytest.fixture
def sample_timeseries_multiple_response():
    """GraphQL Response für _timeSeries Query (mehrere TimeSeries)."""
    return load_graphql_response("timeseries_multiple_response.json")


# ========== Mutation Fixtures ==========


@pytest.fixture
def create_inventory_success_response():
    """GraphQL Response für _createInventory Mutation (erfolgreiche Erstellung)."""
    return load_mutation_response("create_inventory_success.json")


@pytest.fixture
def create_inventory_conflict_response():
    """GraphQL Response für _createInventory Mutation (Konflikt - already vorhanden)."""
    return load_mutation_response("create_inventory_conflict.json")


@pytest.fixture
def delete_inventory_success_response():
    """GraphQL Response für _deleteInventory Mutation."""
    return load_mutation_response("delete_inventory_success.json")


@pytest.fixture
def create_namespace_success_response():
    """GraphQL Response für _createNamespace Mutation."""
    return load_mutation_response("create_namespace_success.json")


@pytest.fixture
def create_role_success_response():
    """GraphQL Response für _createRole Mutation."""
    return load_mutation_response("create_role_success.json")


@pytest.fixture
def grant_permissions_success_response():
    """GraphQL Response für _grantInventoryPermissions Mutation."""
    return load_mutation_response("grant_permissions_success.json")


@pytest.fixture
def create_unit_success_response():
    """GraphQL Response für _createUnit Mutation."""
    return load_mutation_response("create_unit_success.json")


@pytest.fixture
def create_timeseries_success_response():
    """GraphQL Response für _createTimeSeries Mutation."""
    return load_mutation_response("create_timeseries_success.json")


@pytest.fixture
def create_inventory_error_duplicate_response():
    """GraphQL Error Response für _createInventory Mutation (Duplicate)."""
    return load_mutation_response("create_inventory_error_duplicate.json")


@pytest.fixture
def deny_permissions_success_response():
    """GraphQL Response für _denyInventoryPermissions Mutation."""
    return load_mutation_response("deny_permissions_success.json")


@pytest.fixture
def revoke_permissions_success_response():
    """GraphQL Response für _revokeInventoryPermissions Mutation."""
    return load_mutation_response("revoke_permissions_success.json")


@pytest.fixture
def create_inventory_policy_success_response():
    """GraphQL Response für _createInventoryPolicy Mutation (erfolgreiche Erstellung)."""
    return load_mutation_response("create_inventory_policy_success.json")


@pytest.fixture
def create_inventory_policy_conflict_response():
    """GraphQL Response für _createInventoryPolicy Mutation (Konflikt - already vorhanden)."""
    return load_mutation_response("create_inventory_policy_conflict.json")


@pytest.fixture
def delete_inventory_policy_success_response():
    """GraphQL Response für _dropInventoryPolicy Mutation."""
    return load_mutation_response("delete_inventory_policy_success.json")


@pytest.fixture
def delete_unit_success_response():
    """GraphQL Response für _dropUnit Mutation."""
    return load_mutation_response("delete_unit_success.json")


@pytest.fixture
def start_alter_inventory_success_response():
    """GraphQL Response für _startAlterInventory Mutation."""
    return load_mutation_response("start_alter_inventory_success.json")


# ========== REST Fixtures ==========


@pytest.fixture
def rest_timeseries_get_data_success():
    """REST Response für GET /timeseries/data (erfolgreiche Abfrage)."""
    return load_rest_response("timeseries", "get_data_success.json")


@pytest.fixture
def rest_timeseries_get_data_with_missing():
    """REST Response für GET /timeseries/data (mit MISSING Quality)."""
    return load_rest_response("timeseries", "get_data_with_missing_quality.json")


@pytest.fixture
def rest_timeseries_get_quotations_success():
    """REST Response für GET /timeseries/quotations (einzelne Zeitreihe)."""
    return load_rest_response("timeseries", "get_quotations_success.json")


@pytest.fixture
def rest_timeseries_get_quotations_multiple_success():
    """REST Response für GET /timeseries/quotations (mehrere Zeitreihen - NDJSON)."""
    return load_rest_response("timeseries", "get_quotations_multiple_success.json")


@pytest.fixture
def rest_file_upload_success():
    """REST Response für POST /file/upload (einzelne Datei)."""
    return load_rest_response("file", "upload_success.json")


@pytest.fixture
def rest_file_upload_multiple_success():
    """REST Response für POST /file/upload (mehrere Dateien)."""
    return load_rest_response("file", "upload_multiple_success.json")


@pytest.fixture
def rest_audit_get_timeseries_success():
    """REST Response für GET /audit/timeseries (Metadaten)."""
    return load_rest_response("audit", "get_timeseries_success.json")


@pytest.fixture
def rest_audit_get_timeseries_data_success():
    """REST Response für GET /audit/timeseries/data (einzelne TimeSeries)."""
    return load_rest_response("audit", "get_timeseries_data_success.json")


@pytest.fixture
def rest_audit_get_timeseries_data_multiple_success():
    """REST Response für GET /audit/timeseries/data (mehrere TimeSeries - NDJSON)."""
    return load_rest_response("audit", "get_timeseries_data_multiple_success.json")


@pytest.fixture
def rest_timeseries_error_unknown():
    """REST Error Response für GET /timeseries/data (unbekannte TimeSeries IDs)."""
    return load_rest_response("timeseries", "get_data_error_unknown_timeseries.json")


@pytest.fixture
def rest_timeseries_quotations_error_no_quotation():
    """REST Error Response für GET /timeseries/quotations (keine Quotierung aktiviert)."""
    return load_rest_response("timeseries", "get_quotations_error_no_quotation.json")
