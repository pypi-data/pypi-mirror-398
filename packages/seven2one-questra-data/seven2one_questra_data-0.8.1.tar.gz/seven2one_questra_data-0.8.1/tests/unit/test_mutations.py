"""
Unit-Tests für MutationOperations (Low-Level API).

Testet alle Mutation-Methoden with gemockten GraphQL-Responses
und Schema-/Input-Validierung.
"""

from __future__ import annotations

import pytest
from helpers.mutation_validators import MutationInputValidator, MutationQueryValidator

from seven2one.questra.data.exceptions import QuestraGraphQLError
from seven2one.questra.data.models import (
    AssignableDataType,
    ConflictAction,
    NamedItemResult,
)
from seven2one.questra.data.models.inputs import InventoryProperty, StringPropertyConfig
from seven2one.questra.data.operations.mutations import MutationOperations


@pytest.mark.unit
class TestMutationOperationsCreateInventory:
    """Tests für create_inventory() Methode with Schema-Validierung."""

    def test_create_inventory_success(
        self, mock_graphql_execute, create_inventory_success_response
    ):
        """Test create_inventory - erfolgreich erstellt."""
        mock_graphql_execute.return_value = create_inventory_success_response

        mutations = MutationOperations(mock_graphql_execute)
        properties = [
            InventoryProperty(
                propertyName="Name",
                dataType=AssignableDataType.STRING,
                isRequired=True,
                string=StringPropertyConfig(maxLength=255),
            ),
            InventoryProperty(
                propertyName="Age",
                dataType=AssignableDataType.INT,
                isRequired=False,
            ),
        ]

        result = mutations.create_inventory(
            inventory_name="TestInventory",
            properties=properties,
            namespace_name="TestNamespace",
            description="Test Description",
        )

        # Response validieren
        assert isinstance(result, NamedItemResult)
        assert result.name == "TestInventory"
        assert result.existed is False

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query-Validierung
        query = call_args[0][0]
        query_validation = MutationQueryValidator.validate_mutation_query(
            query, "_createInventory"
        )
        assert query_validation["valid"], (
            f"Query-Validierung fehlgeschlagen: {query_validation['errors']}"
        )
        assert query_validation["mutation_type"] == "dynamic_inventory_create"

        # Variables validieren
        variables = call_args[0][1]
        input_validation = MutationInputValidator.validate_create_inventory_input(
            variables
        )
        assert input_validation["valid"], (
            f"Input-Validierung fehlgeschlagen: {input_validation['errors']}"
        )

        # Input-Daten prüfen
        assert variables["input"]["inventoryName"] == "TestInventory"
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert variables["input"]["description"] == "Test Description"
        assert variables["input"]["enableAudit"] is False
        assert len(variables["input"]["properties"]) == 2

        # Properties prüfen
        name_prop = variables["input"]["properties"][0]
        assert name_prop["propertyName"] == "Name"
        assert name_prop["dataType"] == "STRING"
        assert name_prop["isRequired"] is True
        assert name_prop["string"]["maxLength"] == "255"

        age_prop = variables["input"]["properties"][1]
        assert age_prop["propertyName"] == "Age"
        assert age_prop["dataType"] == "INT"
        assert age_prop["isRequired"] is False

    def test_create_inventory_minimal(
        self, mock_graphql_execute, create_inventory_success_response
    ):
        """Test create_inventory with minimalen Parametern."""
        mock_graphql_execute.return_value = create_inventory_success_response

        mutations = MutationOperations(mock_graphql_execute)
        properties = [
            InventoryProperty(
                propertyName="Id",
                dataType=AssignableDataType.INT,
                isRequired=True,
            )
        ]

        result = mutations.create_inventory(
            inventory_name="MinimalInventory",
            properties=properties,
        )

        assert result.name == "TestInventory"  # Aus Mock-Response
        assert result.existed is False

        # Variables validieren
        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]

        assert variables["input"]["inventoryName"] == "MinimalInventory"
        assert variables["input"]["namespaceName"] is None
        assert variables["input"]["description"] is None
        assert variables["input"]["enableAudit"] is False
        assert len(variables["input"]["properties"]) == 1

    def test_create_inventory_with_audit(
        self, mock_graphql_execute, create_inventory_success_response
    ):
        """Test create_inventory with Audit aktiviert."""
        mock_graphql_execute.return_value = create_inventory_success_response

        mutations = MutationOperations(mock_graphql_execute)
        properties = [
            InventoryProperty(
                propertyName="Name",
                dataType=AssignableDataType.STRING,
                isRequired=True,
            )
        ]

        result = mutations.create_inventory(
            inventory_name="AuditInventory",
            properties=properties,
            enable_audit=True,
        )

        assert result.existed is False

        # enableAudit prüfen
        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["enableAudit"] is True

    def test_create_inventory_conflict_ignore(
        self, mock_graphql_execute, create_inventory_conflict_response
    ):
        """Test create_inventory with Konflikt (IGNORE - keine Exception)."""
        mock_graphql_execute.return_value = create_inventory_conflict_response

        mutations = MutationOperations(mock_graphql_execute)
        properties = [
            InventoryProperty(
                propertyName="Name",
                dataType=AssignableDataType.STRING,
                isRequired=True,
            )
        ]

        result = mutations.create_inventory(
            inventory_name="ExistingInventory",
            properties=properties,
            if_exists=ConflictAction.IGNORE,
        )

        # IGNORE: existed=True, keine Exception
        assert result.name == "ExistingInventory"
        assert result.existed is True

        # ifExists Parameter prüfen
        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["ifExists"] == "IGNORE"

    def test_create_inventory_conflict_raise_error(
        self, mock_graphql_execute, create_inventory_error_duplicate_response
    ):
        """Test create_inventory with Konflikt (RAISE_ERROR - Exception erwartet)."""
        # Mock konfigurieren: QuestraGraphQLError directly werfen
        # (simuliert Transport-Layer Error-Handling)
        error_data = create_inventory_error_duplicate_response["errors"][0]
        extensions = error_data["extensions"]

        mock_graphql_execute.side_effect = QuestraGraphQLError(
            message=error_data["message"],
            code=extensions["code"],
            category="Data",  # Aus "DATA_MODEL_*"
            placeholders=extensions["Placeholders"],
            locations=error_data["locations"],
            path=error_data["path"],
            extensions=extensions,
        )

        mutations = MutationOperations(mock_graphql_execute)
        properties = [
            InventoryProperty(
                propertyName="Name",
                dataType=AssignableDataType.STRING,
                isRequired=True,
            )
        ]

        # RAISE_ERROR sollte QuestraGraphQLError werfen
        with pytest.raises(QuestraGraphQLError) as exc_info:
            mutations.create_inventory(
                inventory_name="ExistingInventory",
                properties=properties,
                if_exists=ConflictAction.RAISE_ERROR,
            )

        # Exception-Details prüfen
        error = exc_info.value
        assert error.code == "DATA_MODEL_DUPLICATE_INVENTORY_NAME"
        assert "already exists" in error.message
        assert error.placeholders["InventoryName"] == "ExistingInventory"
        assert error.placeholders["NamespaceName"] == "TestNamespace"
        assert error.is_duplicate_error() is True


@pytest.mark.unit
class TestMutationOperationsDeleteInventory:
    """Tests für delete_inventory() Methode."""

    def test_delete_inventory_success(
        self, mock_graphql_execute, delete_inventory_success_response
    ):
        """Test delete_inventory - erfolgreich gelöscht."""
        mock_graphql_execute.return_value = delete_inventory_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.delete_inventory(
            inventory_name="TestInventory",
            namespace_name="TestNamespace",
        )

        # Response validieren
        assert isinstance(result, NamedItemResult)
        assert result.name == "TestInventory"
        assert result.existed is True

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query enthält _dropInventory
        query = call_args[0][0]
        assert "_dropInventory" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["inventoryName"] == "TestInventory"
        assert variables["input"]["namespaceName"] == "TestNamespace"

    def test_delete_inventory_minimal(
        self, mock_graphql_execute, delete_inventory_success_response
    ):
        """Test delete_inventory without Namespace."""
        mock_graphql_execute.return_value = delete_inventory_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.delete_inventory(inventory_name="TestInventory")

        assert result.existed is True

        # namespaceName sollte None sein
        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] is None


@pytest.mark.unit
class TestMutationOperationsCreateNamespace:
    """Tests für create_namespace() Methode."""

    def test_create_namespace_success(
        self, mock_graphql_execute, create_namespace_success_response
    ):
        """Test create_namespace - erfolgreich erstellt."""
        mock_graphql_execute.return_value = create_namespace_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_namespace(
            namespace_name="TestNamespace",
            description="Test Description",
        )

        # Response validieren
        assert isinstance(result, NamedItemResult)
        assert result.name == "TestNamespace"
        assert result.existed is False

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query-Validierung (statische Mutation)
        query = call_args[0][0]
        query_validation = MutationQueryValidator.validate_mutation_query(
            query, "_createNamespace"
        )
        assert query_validation["valid"], (
            f"Query-Validierung fehlgeschlagen: {query_validation['errors']}"
        )
        assert query_validation["mutation_type"] == "static"

        # Input-Validierung
        variables = call_args[0][1]
        input_validation = MutationInputValidator.validate_create_namespace_input(
            variables
        )
        assert input_validation["valid"], (
            f"Input-Validierung fehlgeschlagen: {input_validation['errors']}"
        )

        # Input-Daten prüfen
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert variables["input"]["description"] == "Test Description"

    def test_create_namespace_minimal(
        self, mock_graphql_execute, create_namespace_success_response
    ):
        """Test create_namespace with minimalen Parametern."""
        mock_graphql_execute.return_value = create_namespace_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_namespace(namespace_name="MinimalNamespace")

        assert result.existed is False

        # description sollte None sein
        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] == "MinimalNamespace"
        assert variables["input"]["description"] is None


@pytest.mark.unit
class TestMutationOperationsAlterNamespace:
    """Tests für alter_namespace() Methode."""

    def test_alter_namespace_rename(self, mock_graphql_execute):
        """Test alter_namespace - umbenennen."""
        mock_graphql_execute.return_value = {
            "_alterNamespace": {"name": "NewNamespaceName", "existed": True}
        }

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.alter_namespace(
            namespace_name="OldNamespace", new_namespace_name="NewNamespaceName"
        )

        assert isinstance(result, NamedItemResult)
        assert result.name == "NewNamespaceName"
        assert result.existed is True

        call_args = mock_graphql_execute.call_args
        query = call_args[0][0]
        assert "_alterNamespace" in query

        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] == "OldNamespace"
        assert variables["input"]["newNamespaceName"] == "NewNamespaceName"
        assert "description" not in variables["input"]

    def test_alter_namespace_change_description(self, mock_graphql_execute):
        """Test alter_namespace - Beschreibung ändern."""
        mock_graphql_execute.return_value = {
            "_alterNamespace": {"name": "TestNamespace", "existed": True}
        }

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.alter_namespace(
            namespace_name="TestNamespace", description="New Description"
        )

        assert result.name == "TestNamespace"
        assert result.existed is True

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert variables["input"]["description"] == {"value": "New Description"}
        assert "newNamespaceName" not in variables["input"]

    def test_alter_namespace_clear_description(self, mock_graphql_execute):
        """Test alter_namespace - Beschreibung löschen."""
        mock_graphql_execute.return_value = {
            "_alterNamespace": {"name": "TestNamespace", "existed": True}
        }

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.alter_namespace(
            namespace_name="TestNamespace", description=None
        )

        assert result.existed is True

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["description"] == {"value": None}

    def test_alter_namespace_rename_and_description(self, mock_graphql_execute):
        """Test alter_namespace - umbenennen UND Beschreibung ändern."""
        mock_graphql_execute.return_value = {
            "_alterNamespace": {"name": "RenamedNamespace", "existed": True}
        }

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.alter_namespace(
            namespace_name="OldNamespace",
            new_namespace_name="RenamedNamespace",
            description="Updated Description",
        )

        assert result.name == "RenamedNamespace"

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] == "OldNamespace"
        assert variables["input"]["newNamespaceName"] == "RenamedNamespace"
        assert variables["input"]["description"] == {"value": "Updated Description"}

    def test_alter_namespace_not_exists_ignore(self, mock_graphql_execute):
        """Test alter_namespace - Namespace existiert nicht, IGNORE."""
        mock_graphql_execute.return_value = {
            "_alterNamespace": {"name": "NonExistent", "existed": False}
        }

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.alter_namespace(
            namespace_name="NonExistent",
            new_namespace_name="NewName",
            if_not_exists=ConflictAction.IGNORE,
        )

        assert result.existed is False

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["ifNotExists"] == "IGNORE"


@pytest.mark.unit
class TestMutationOperationsDropNamespace:
    """Tests für drop_namespace() Methode."""

    def test_drop_namespace_success(self, mock_graphql_execute):
        """Test drop_namespace - erfolgreich gelöscht."""
        mock_graphql_execute.return_value = {
            "_dropNamespace": {"name": "TestNamespace", "existed": True}
        }

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.drop_namespace(namespace_name="TestNamespace")

        assert isinstance(result, NamedItemResult)
        assert result.name == "TestNamespace"
        assert result.existed is True

        call_args = mock_graphql_execute.call_args
        query = call_args[0][0]
        assert "_dropNamespace" in query

        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert variables["input"]["ifNotExists"] == "RAISE_ERROR"

    def test_drop_namespace_not_exists_ignore(self, mock_graphql_execute):
        """Test drop_namespace - Namespace existiert nicht, IGNORE."""
        mock_graphql_execute.return_value = {
            "_dropNamespace": {"name": "NonExistent", "existed": False}
        }

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.drop_namespace(
            namespace_name="NonExistent", if_not_exists=ConflictAction.IGNORE
        )

        assert result.existed is False

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["ifNotExists"] == "IGNORE"

    def test_drop_namespace_minimal(self, mock_graphql_execute):
        """Test drop_namespace with minimalen Parametern."""
        mock_graphql_execute.return_value = {
            "_dropNamespace": {"name": "MinimalNamespace", "existed": True}
        }

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.drop_namespace(namespace_name="MinimalNamespace")

        assert result.existed is True


@pytest.mark.unit
class TestMutationOperationsCreateRole:
    """Tests für create_role() Methode."""

    def test_create_role_success(
        self, mock_graphql_execute, create_role_success_response
    ):
        """Test create_role - erfolgreich erstellt."""
        mock_graphql_execute.return_value = create_role_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_role(
            role_name="TestRole",
            description="Test Role Description",
        )

        # Response validieren
        assert isinstance(result, NamedItemResult)
        assert result.name == "TestRole"
        assert result.existed is False

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query-Validierung (statische Mutation)
        query = call_args[0][0]
        query_validation = MutationQueryValidator.validate_mutation_query(
            query, "_createRole"
        )
        assert query_validation["valid"], (
            f"Query-Validierung fehlgeschlagen: {query_validation['errors']}"
        )
        assert query_validation["mutation_type"] == "static"

        # Input-Validierung
        variables = call_args[0][1]
        input_validation = MutationInputValidator.validate_create_role_input(variables)
        assert input_validation["valid"], (
            f"Input-Validierung fehlgeschlagen: {input_validation['errors']}"
        )

        # Input-Daten prüfen
        assert variables["input"]["roleName"] == "TestRole"
        assert variables["input"]["description"] == "Test Role Description"

    def test_create_role_minimal(
        self, mock_graphql_execute, create_role_success_response
    ):
        """Test create_role with minimalen Parametern."""
        mock_graphql_execute.return_value = create_role_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_role(role_name="MinimalRole")

        assert result.existed is False

        # description sollte None sein
        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["roleName"] == "MinimalRole"
        assert variables["input"]["description"] is None


@pytest.mark.unit
class TestMutationOperationsGrantPermissions:
    """Tests für grant_inventory_permissions() Methode."""

    def test_grant_permissions_success(
        self, mock_graphql_execute, grant_permissions_success_response
    ):
        """Test grant_inventory_permissions - erfolgreich."""
        mock_graphql_execute.return_value = grant_permissions_success_response

        mutations = MutationOperations(mock_graphql_execute)

        # Methode gibt None zurück (Response ist "NONE")
        result = mutations.grant_inventory_permissions(
            role_name="TestRole",
            inventory_name="TestInventory",
            privileges=["SELECT", "INSERT"],
            namespace_name="TestNamespace",
        )

        # Kein Return-Wert erwartet
        assert result is None

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query-Validierung
        query = call_args[0][0]
        query_validation = MutationQueryValidator.validate_mutation_query(
            query, "_grantInventoryPermissions"
        )
        assert query_validation["valid"], (
            f"Query-Validierung fehlgeschlagen: {query_validation['errors']}"
        )
        assert query_validation["mutation_type"] == "static"

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["roleName"] == "TestRole"
        assert variables["input"]["inventoryName"] == "TestInventory"
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert "SELECT" in variables["input"]["privileges"]
        assert "INSERT" in variables["input"]["privileges"]


@pytest.mark.unit
class TestMutationValidatorsStandalone:
    """Standalone-Tests für Validators (without Mock)."""

    def test_query_validator_static_mutation(self):
        """Test MutationQueryValidator für statische Mutation."""
        query = """
            mutation CreateNamespace($input: _CreateNamespace__InputType!) {
                _createNamespace(input: $input) {
                    name
                    existed
                }
            }
        """

        result = MutationQueryValidator.validate_mutation_query(
            query, "_createNamespace"
        )

        assert result["valid"] is True
        assert result["mutation_type"] == "static"
        assert len(result["errors"]) == 0

    def test_query_validator_dynamic_inventory(self):
        """Test MutationQueryValidator für _createInventory."""
        query = """
            mutation CreateInventory($input: _CreateInventory__InputType!) {
                _createInventory(input: $input) {
                    name
                    existed
                }
            }
        """

        result = MutationQueryValidator.validate_mutation_query(
            query, "_createInventory"
        )

        assert result["valid"] is True
        assert result["mutation_type"] == "dynamic_inventory_create"
        assert len(result["errors"]) == 0

    def test_query_validator_invalid_missing_mutation_keyword(self):
        """Test MutationQueryValidator - fehlendes 'mutation' Keyword."""
        query = """
            {
                _createNamespace(input: $input) {
                    name
                }
            }
        """

        result = MutationQueryValidator.validate_mutation_query(
            query, "_createNamespace"
        )

        assert result["valid"] is False
        assert "mutation" in result["errors"][0].lower()

    def test_input_validator_create_inventory_valid(self):
        """Test MutationInputValidator für valide Inventory-Inputs."""
        variables = {
            "input": {
                "inventoryName": "TestInventory",
                "namespaceName": "TestNamespace",
                "properties": [
                    {
                        "propertyName": "Name",
                        "dataType": "STRING",
                        "isRequired": True,
                    }
                ],
                "ifExists": "IGNORE",
            }
        }

        result = MutationInputValidator.validate_create_inventory_input(variables)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_input_validator_create_inventory_missing_required(self):
        """Test MutationInputValidator - fehlendes Pflichtfeld."""
        variables = {
            "input": {
                "namespaceName": "TestNamespace",
                # inventoryName fehlt!
                "properties": [],
            }
        }

        result = MutationInputValidator.validate_create_inventory_input(variables)

        assert result["valid"] is False
        assert any("inventoryName" in err for err in result["errors"])

    def test_input_validator_create_inventory_invalid_datatype(self):
        """Test MutationInputValidator - ungültiger AssignableDataType."""
        variables = {
            "input": {
                "inventoryName": "TestInventory",
                "properties": [
                    {
                        "propertyName": "Name",
                        "dataType": "INVALID_TYPE",  # Ungültig!
                        "isRequired": True,
                    }
                ],
            }
        }

        result = MutationInputValidator.validate_create_inventory_input(variables)

        assert result["valid"] is False
        assert any("dataType" in err for err in result["errors"])


@pytest.mark.unit
class TestMutationOperationsDenyPermissions:
    """Tests für deny_inventory_permissions() Methode."""

    def test_deny_permissions_success(
        self, mock_graphql_execute, deny_permissions_success_response
    ):
        """Test deny_inventory_permissions - erfolgreich."""
        mock_graphql_execute.return_value = deny_permissions_success_response

        mutations = MutationOperations(mock_graphql_execute)

        result = mutations.deny_inventory_permissions(
            role_name="TestRole",
            inventory_name="TestInventory",
            privileges=["SELECT", "INSERT"],
            namespace_name="TestNamespace",
        )

        # Kein Return-Wert erwartet (NONE Response)
        assert result is None

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query validieren
        query = call_args[0][0]
        assert "_denyInventoryPermissions" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["roleName"] == "TestRole"
        assert variables["input"]["inventoryName"] == "TestInventory"
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert "SELECT" in variables["input"]["privileges"]
        assert "INSERT" in variables["input"]["privileges"]

    def test_deny_permissions_minimal(
        self, mock_graphql_execute, deny_permissions_success_response
    ):
        """Test deny_inventory_permissions without Namespace."""
        mock_graphql_execute.return_value = deny_permissions_success_response

        mutations = MutationOperations(mock_graphql_execute)

        result = mutations.deny_inventory_permissions(
            role_name="TestRole",
            inventory_name="TestInventory",
            privileges=["SELECT"],
        )

        assert result is None

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] is None


@pytest.mark.unit
class TestMutationOperationsRevokePermissions:
    """Tests für revoke_inventory_permissions() Methode."""

    def test_revoke_permissions_success(
        self, mock_graphql_execute, revoke_permissions_success_response
    ):
        """Test revoke_inventory_permissions - erfolgreich."""
        mock_graphql_execute.return_value = revoke_permissions_success_response

        mutations = MutationOperations(mock_graphql_execute)

        result = mutations.revoke_inventory_permissions(
            role_name="TestRole",
            inventory_name="TestInventory",
            privileges=["SELECT", "UPDATE", "DELETE"],
            namespace_name="TestNamespace",
        )

        # Kein Return-Wert erwartet (NONE Response)
        assert result is None

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query validieren
        query = call_args[0][0]
        assert "_revokeInventoryPermissions" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["roleName"] == "TestRole"
        assert variables["input"]["inventoryName"] == "TestInventory"
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert "SELECT" in variables["input"]["privileges"]
        assert "UPDATE" in variables["input"]["privileges"]
        assert "DELETE" in variables["input"]["privileges"]


@pytest.mark.unit
class TestMutationOperationsCreateInventoryPolicy:
    """Tests für create_inventory_policy() Methode."""

    def test_create_inventory_policy_success(
        self, mock_graphql_execute, create_inventory_policy_success_response
    ):
        """Test create_inventory_policy - erfolgreich erstellt."""
        mock_graphql_execute.return_value = create_inventory_policy_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_inventory_policy(
            policy_name="TestPolicy",
            role_name="TestRole",
            inventory_name="TestInventory",
            property_name="Region",
            filter_value="EU",
            namespace_name="TestNamespace",
            description="Policy for EU region",
        )

        # Response validieren
        assert isinstance(result, NamedItemResult)
        assert result.name == "TestPolicy"
        assert result.existed is False

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query validieren
        query = call_args[0][0]
        assert "_createInventoryPolicy" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["policyName"] == "TestPolicy"
        assert variables["input"]["roleName"] == "TestRole"
        assert variables["input"]["inventoryName"] == "TestInventory"
        assert variables["input"]["propertyName"] == "Region"
        assert variables["input"]["filterValue"] == "EU"
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert variables["input"]["description"] == "Policy for EU region"
        assert variables["input"]["ifExists"] == "RAISE_ERROR"

    def test_create_inventory_policy_minimal(
        self, mock_graphql_execute, create_inventory_policy_success_response
    ):
        """Test create_inventory_policy with minimalen Parametern."""
        mock_graphql_execute.return_value = create_inventory_policy_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_inventory_policy(
            policy_name="MinimalPolicy",
            role_name="TestRole",
            inventory_name="TestInventory",
            property_name="Status",
            filter_value="Active",
        )

        assert result.existed is False

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] is None
        assert variables["input"]["description"] is None

    def test_create_inventory_policy_conflict_ignore(
        self, mock_graphql_execute, create_inventory_policy_conflict_response
    ):
        """Test create_inventory_policy with Konflikt (IGNORE)."""
        mock_graphql_execute.return_value = create_inventory_policy_conflict_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_inventory_policy(
            policy_name="ExistingPolicy",
            role_name="TestRole",
            inventory_name="TestInventory",
            property_name="Region",
            filter_value="US",
            if_exists=ConflictAction.IGNORE,
        )

        # IGNORE: existed=True, keine Exception
        assert result.name == "ExistingPolicy"
        assert result.existed is True

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["ifExists"] == "IGNORE"


@pytest.mark.unit
class TestMutationOperationsDeleteInventoryPolicy:
    """Tests für delete_inventory_policy() Methode."""

    def test_delete_inventory_policy_success(
        self, mock_graphql_execute, delete_inventory_policy_success_response
    ):
        """Test delete_inventory_policy - erfolgreich gelöscht."""
        mock_graphql_execute.return_value = delete_inventory_policy_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.delete_inventory_policy(
            policy_name="TestPolicy",
            inventory_name="TestInventory",
            namespace_name="TestNamespace",
        )

        # Response validieren
        assert isinstance(result, NamedItemResult)
        assert result.name == "TestPolicy"
        assert result.existed is True

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query validieren
        query = call_args[0][0]
        assert "_dropInventoryPolicy" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["policyName"] == "TestPolicy"
        assert variables["input"]["inventoryName"] == "TestInventory"
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert variables["input"]["ifNotExists"] == "RAISE_ERROR"

    def test_delete_inventory_policy_minimal(
        self, mock_graphql_execute, delete_inventory_policy_success_response
    ):
        """Test delete_inventory_policy without Namespace."""
        mock_graphql_execute.return_value = delete_inventory_policy_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.delete_inventory_policy(
            policy_name="TestPolicy",
            inventory_name="TestInventory",
        )

        assert result.existed is True

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["namespaceName"] is None


@pytest.mark.unit
class TestMutationOperationsCreateUnit:
    """Tests für create_unit() Methode."""

    def test_create_unit_success(
        self, mock_graphql_execute, create_unit_success_response
    ):
        """Test create_unit - erfolgreich erstellt."""
        mock_graphql_execute.return_value = create_unit_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_unit(
            symbol="kWh",
            aggregation="SUM",
        )

        # Response validieren
        assert isinstance(result, NamedItemResult)
        assert result.name == "kWh"
        assert result.existed is False

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query validieren
        query = call_args[0][0]
        assert "_createUnit" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["symbol"] == "kWh"
        assert variables["input"]["aggregation"] == "SUM"
        assert variables["input"]["ifExists"] == "RAISE_ERROR"

    def test_create_unit_with_conflict_ignore(
        self, mock_graphql_execute, create_unit_success_response
    ):
        """Test create_unit with IGNORE at Konflikt."""
        # Modify response to show existed=True
        response = create_unit_success_response.copy()
        response["_createUnit"]["existed"] = True

        mock_graphql_execute.return_value = response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.create_unit(
            symbol="kW",
            aggregation="AVERAGE",
            if_exists=ConflictAction.IGNORE,
        )

        assert result.existed is True

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["ifExists"] == "IGNORE"


@pytest.mark.unit
class TestMutationOperationsDeleteUnit:
    """Tests für delete_unit() Methode."""

    def test_delete_unit_success(
        self, mock_graphql_execute, delete_unit_success_response
    ):
        """Test delete_unit - erfolgreich gelöscht."""
        mock_graphql_execute.return_value = delete_unit_success_response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.delete_unit(symbol="kWh")

        # Response validieren
        assert isinstance(result, NamedItemResult)
        assert result.name == "kWh"
        assert result.existed is True

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query validieren
        query = call_args[0][0]
        assert "_dropUnit" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["symbol"] == "kWh"
        assert variables["input"]["ifNotExists"] == "RAISE_ERROR"

    def test_delete_unit_if_not_exists_ignore(
        self, mock_graphql_execute, delete_unit_success_response
    ):
        """Test delete_unit with IGNORE wenn nicht vorhanden."""
        response = delete_unit_success_response.copy()
        response["_dropUnit"]["existed"] = False

        mock_graphql_execute.return_value = response

        mutations = MutationOperations(mock_graphql_execute)
        result = mutations.delete_unit(
            symbol="NonExistent",
            if_not_exists=ConflictAction.IGNORE,
        )

        assert result.existed is False

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["ifNotExists"] == "IGNORE"


@pytest.mark.unit
class TestMutationOperationsCreateTimeSeries:
    """Tests für create_timeseries() Methode."""

    def test_create_timeseries_success(
        self, mock_graphql_execute, create_timeseries_success_response
    ):
        """Test create_timeseries - erfolgreich erstellt."""
        from seven2one.questra.data.models.inputs import (
            Aggregation,
            CreateTimeSeriesInput,
            IntervalConfig,
            QuotationBehavior,
            TimeSeriesSpecifics,
            TimeUnit,
            ValueAlignment,
            ValueAvailability,
        )

        mock_graphql_execute.return_value = create_timeseries_success_response

        mutations = MutationOperations(mock_graphql_execute)

        ts_input = CreateTimeSeriesInput(
            inventoryName="PowerPlant",
            propertyName="PowerOutput",
            namespaceName="Energy",
            specifics=TimeSeriesSpecifics(
                interval=IntervalConfig(timeUnit=TimeUnit.MINUTE, multiplier=15),
                valueAlignment=ValueAlignment.LEFT,
                valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
                unit="kW",
                timeZone="Europe/Berlin",
                defaultAggregation=Aggregation.AVERAGE,
                startOfTime="2025-01-01T00:00:00Z",
                defaultQuotationBehavior=QuotationBehavior.LATEST,
            ),
        )

        result = mutations.create_timeseries([ts_input])

        # Response validieren
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == "1234567890"

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query validieren
        query = call_args[0][0]
        assert "_createTimeSeries" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert len(variables["input"]) == 1
        ts_vars = variables["input"][0]
        assert ts_vars["inventoryName"] == "PowerPlant"
        assert ts_vars["propertyName"] == "PowerOutput"
        assert ts_vars["namespaceName"] == "Energy"
        assert ts_vars["specifics"]["interval"]["timeUnit"] == "MINUTE"
        assert ts_vars["specifics"]["interval"]["multiplier"] == "15"
        assert ts_vars["specifics"]["unit"] == "kW"
        assert ts_vars["specifics"]["timeZone"] == "Europe/Berlin"

    def test_create_timeseries_multiple(
        self, mock_graphql_execute, create_timeseries_success_response
    ):
        """Test create_timeseries with mehreren TimeSeries."""
        from seven2one.questra.data.models.inputs import (
            Aggregation,
            CreateTimeSeriesInput,
            IntervalConfig,
            QuotationBehavior,
            TimeSeriesSpecifics,
            TimeUnit,
            ValueAlignment,
            ValueAvailability,
        )

        # Modify response to return multiple IDs
        response = {
            "_createTimeSeries": [
                {"_id": "1111111111"},
                {"_id": "2222222222"},
            ]
        }
        mock_graphql_execute.return_value = response

        mutations = MutationOperations(mock_graphql_execute)

        ts_inputs = [
            CreateTimeSeriesInput(
                inventoryName="Plant1",
                propertyName="Power",
                specifics=TimeSeriesSpecifics(
                    interval=IntervalConfig(timeUnit=TimeUnit.HOUR, multiplier=1),
                    valueAlignment=ValueAlignment.LEFT,
                    valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
                    unit="kW",
                    timeZone="UTC",
                    defaultAggregation=Aggregation.SUM,
                    startOfTime="2025-01-01T00:00:00Z",
                    defaultQuotationBehavior=QuotationBehavior.LATEST,
                ),
            ),
            CreateTimeSeriesInput(
                inventoryName="Plant2",
                propertyName="Power",
                specifics=TimeSeriesSpecifics(
                    interval=IntervalConfig(timeUnit=TimeUnit.HOUR, multiplier=1),
                    valueAlignment=ValueAlignment.LEFT,
                    valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
                    unit="MW",
                    timeZone="UTC",
                    defaultAggregation=Aggregation.AVERAGE,
                    startOfTime="2025-01-01T00:00:00Z",
                    defaultQuotationBehavior=QuotationBehavior.LATEST,
                ),
            ),
        ]

        result = mutations.create_timeseries(ts_inputs)

        assert len(result) == 2
        assert result[0].id == "1111111111"
        assert result[1].id == "2222222222"

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert len(variables["input"]) == 2


@pytest.mark.unit
class TestMutationOperationsStartAlterInventory:
    """Tests für start_alter_inventory() Methode."""

    def test_start_alter_inventory_add_properties(
        self, mock_graphql_execute, start_alter_inventory_success_response
    ):
        """Test start_alter_inventory - Properties hinzufügen."""
        mock_graphql_execute.return_value = start_alter_inventory_success_response

        mutations = MutationOperations(mock_graphql_execute)

        add_properties = [
            InventoryProperty(
                propertyName="NewProperty",
                dataType=AssignableDataType.STRING,
                isRequired=False,
                string=StringPropertyConfig(maxLength=100),
            )
        ]

        result = mutations.start_alter_inventory(
            inventory_name="TestInventory",
            namespace_name="TestNamespace",
            add_properties=add_properties,
        )

        # Response validieren
        from seven2one.questra.data.models import BackgroundJobResult

        assert isinstance(result, BackgroundJobResult)
        assert result.background_job_id == "12345678-1234-1234-1234-123456789012"

        # GraphQL Execute was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args

        # Query validieren
        query = call_args[0][0]
        assert "_startAlterInventory" in query

        # Variables prüfen
        variables = call_args[0][1]
        assert variables["input"]["inventoryName"] == "TestInventory"
        assert variables["input"]["namespaceName"] == "TestNamespace"
        assert len(variables["input"]["addProperties"]) == 1
        assert variables["input"]["addProperties"][0]["propertyName"] == "NewProperty"

    def test_start_alter_inventory_drop_properties(
        self, mock_graphql_execute, start_alter_inventory_success_response
    ):
        """Test start_alter_inventory - Properties löschen."""
        mock_graphql_execute.return_value = start_alter_inventory_success_response

        mutations = MutationOperations(mock_graphql_execute)

        result = mutations.start_alter_inventory(
            inventory_name="TestInventory",
            drop_properties=["OldProperty", "ObsoleteField"],
        )

        assert result.background_job_id == "12345678-1234-1234-1234-123456789012"

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert len(variables["input"]["dropProperties"]) == 2
        assert variables["input"]["dropProperties"][0]["propertyName"] == "OldProperty"
        assert (
            variables["input"]["dropProperties"][1]["propertyName"] == "ObsoleteField"
        )

    def test_start_alter_inventory_rename(
        self, mock_graphql_execute, start_alter_inventory_success_response
    ):
        """Test start_alter_inventory - Inventory umbenennen."""
        mock_graphql_execute.return_value = start_alter_inventory_success_response

        mutations = MutationOperations(mock_graphql_execute)

        result = mutations.start_alter_inventory(
            inventory_name="OldInventoryName",
            namespace_name="TestNamespace",
            new_inventory_name="NewInventoryName",
            description="Updated description",
        )

        assert result.background_job_id == "12345678-1234-1234-1234-123456789012"

        call_args = mock_graphql_execute.call_args
        variables = call_args[0][1]
        assert variables["input"]["inventoryName"] == "OldInventoryName"
        assert variables["input"]["newInventoryName"] == "NewInventoryName"
        assert variables["input"]["description"] == "Updated description"
