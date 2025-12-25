"""GraphQL mutation operations for Questra Data."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any  # Only still needed for GraphQL variable values

logger = logging.getLogger(__name__)

from ..models import (
    BackgroundJobResult,
    ConflictAction,
    NamedItemResult,
    TimeSeriesIdResult,
)
from ..models.inputs import CreateTimeSeriesInput, InventoryProperty, InventoryRelation
from ..models.permissions import InventoryPrivilege


class MutationOperations:
    """
    Mutation operations for Dyno GraphQL API.

    Responsible for:
    - Creating and deleting inventories
    - Creating namespaces
    - Creating roles
    - Managing permissions
    - Managing policies
    - Creating and deleting units
    - Creating timeseries
    """

    def __init__(self, execute_func: Callable):
        """
        Initialize the mutation operations.

        Args:
            execute_func: Function to execute GraphQL mutations
        """
        self._execute = execute_func

    def create_inventory(
        self,
        inventory_name: str,
        properties: list[InventoryProperty],
        namespace_name: str | None = None,
        description: str | None = None,
        enable_audit: bool = False,
        relations: list[InventoryRelation] | None = None,
        if_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Create a new inventory.

        Args:
            inventory_name: Name of the inventory
            properties: List of properties (InventoryProperty dataclasses)
            namespace_name: Optional namespace
            description: Optional description
            enable_audit: Enable audit
            relations: Optional relations (InventoryRelation dataclasses)
            if_exists: Behavior on conflict

        Returns:
            NamedItemResult: Dictionary with name and existed flag

        Examples:
            ```python
            # With Dataclasses (recommended)
            from seven2one.questra.data import (
                InventoryProperty,
                StringPropertyConfig,
                DataType,
            )

            properties = [
                InventoryProperty(
                    propertyName="Name",
                    dataType=DataType.STRING,
                    isRequired=True,
                    string=StringPropertyConfig(maxLength=200),
                )
            ]

            result = mutations.create_inventory(
                inventory_name="TestInventory", properties=properties
            )
            ```
        """
        logger.debug(
            f"Creating inventory. inventory_name={inventory_name}, namespace_name={namespace_name}, num_properties={len(properties)}, enable_audit={enable_audit}"
        )

        # Convert Dataclasses to Dictionaries
        properties_dicts = [prop.to_dict() for prop in properties]

        relations_dicts = []
        if relations:
            relations_dicts = [rel.to_dict() for rel in relations]

        mutation = """
            mutation CreateInventory($input: _CreateInventory__InputType!) {
                _createInventory(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "inventoryName": inventory_name,
                "properties": properties_dicts,
                "namespaceName": namespace_name,
                "description": description,
                "enableAudit": enable_audit,
                "relations": relations_dicts,
                "ifExists": if_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        created_result = NamedItemResult.from_dict(result["_createInventory"])
        logger.info(
            f"Inventory {'already existed' if created_result.existed else 'created'}. inventory_name={created_result.name}, existed={created_result.existed}"
        )
        return created_result

    def delete_inventory(
        self,
        inventory_name: str,
        namespace_name: str | None = None,
        if_not_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Delete to inventory.

        Args:
            inventory_name: Name of the inventory
            namespace_name: Optional namespace
            if_not_exists: Behavior when not exists

        Returns:
            NamedItemResult: Dictionary with name and existed flag
        """
        logger.debug(
            f"Deleting inventory. inventory_name={inventory_name}, namespace_name={namespace_name}"
        )

        mutation = """
            mutation DropInventory($input: _DropInventory__InputType!) {
                _dropInventory(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "inventoryName": inventory_name,
                "namespaceName": namespace_name,
                "ifNotExists": if_not_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        delete_result = NamedItemResult.from_dict(result["_dropInventory"])
        logger.info(
            f"Inventory {'deleted' if delete_result.existed else 'did not exist'}. inventory_name={delete_result.name}, existed={delete_result.existed}"
        )
        return delete_result

    def create_namespace(
        self,
        namespace_name: str,
        description: str | None = None,
        if_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Create a new namespace.

        Args:
            namespace_name: Name of the namespace
            description: Optional description
            if_exists: Behavior on conflict

        Returns:
            NamedItemResult: Dictionary with name and existed flag
        """
        logger.debug(f"Creating namespace. namespace_name={namespace_name}")

        mutation = """
            mutation CreateNamespace($input: _CreateNamespace__InputType!) {
                _createNamespace(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "namespaceName": namespace_name,
                "description": description,
                "ifExists": if_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        ns_result = NamedItemResult.from_dict(result["_createNamespace"])
        logger.info(
            f"Namespace {'already existed' if ns_result.existed else 'created'}. namespace_name={ns_result.name}, existed={ns_result.existed}"
        )
        return ns_result

    def alter_namespace(
        self,
        namespace_name: str,
        new_namespace_name: str | None = None,
        description: str | None = ...,  # type: ignore
        if_not_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Alter a namespace.

        Args:
            namespace_name: Name of the namespace to alter
            new_namespace_name: New name (optional)
            description: New description. Use None to delete description,
                        ... (default) to leave description unchanged
            if_not_exists: Behavior when not exists

        Returns:
            NamedItemResult: Dictionary with name and existed flag
        """
        logger.debug(
            f"Altering namespace. namespace_name={namespace_name}, new_namespace_name={new_namespace_name}"
        )

        mutation = """
            mutation AlterNamespace($input: _AlterNamespace__InputType!) {
                _alterNamespace(input: $input) {
                    name
                    existed
                }
            }
        """

        variables: dict = {
            "input": {
                "namespaceName": namespace_name,
                "ifNotExists": if_not_exists.value,
            }
        }

        if new_namespace_name is not None:
            variables["input"]["newNamespaceName"] = new_namespace_name

        if description is not ...:
            variables["input"]["description"] = {"value": description}

        result = self._execute(mutation, variables)
        ns_result = NamedItemResult.from_dict(result["_alterNamespace"])
        logger.info(
            f"Namespace {'altered' if ns_result.existed else 'did not exist'}. namespace_name={ns_result.name}, existed={ns_result.existed}"
        )
        return ns_result

    def drop_namespace(
        self,
        namespace_name: str,
        if_not_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Drop a namespace.

        Args:
            namespace_name: Name of the namespace
            if_not_exists: Behavior when not exists

        Returns:
            NamedItemResult: Dictionary with name and existed flag
        """
        logger.debug(f"Dropping namespace. namespace_name={namespace_name}")

        mutation = """
            mutation DropNamespace($input: _DropNamespace__InputType!) {
                _dropNamespace(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "namespaceName": namespace_name,
                "ifNotExists": if_not_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        ns_result = NamedItemResult.from_dict(result["_dropNamespace"])
        logger.info(
            f"Namespace {'dropped' if ns_result.existed else 'did not exist'}. namespace_name={ns_result.name}, existed={ns_result.existed}"
        )
        return ns_result

    def create_role(
        self,
        role_name: str,
        description: str | None = None,
        if_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Create a new role.

        Args:
            role_name: Name of the role
            description: Optional description
            if_exists: Behavior on conflict

        Returns:
            NamedItemResult: Dictionary with name and existed flag
        """
        logger.debug(f"Creating role. role_name={role_name}")

        mutation = """
            mutation CreateRole($input: _CreateRole__InputType!) {
                _createRole(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "roleName": role_name,
                "description": description,
                "ifExists": if_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        role_result = NamedItemResult.from_dict(result["_createRole"])
        logger.info(
            f"Role {'already existed' if role_result.existed else 'created'}. role_name={role_result.name}, existed={role_result.existed}"
        )
        return role_result

    def grant_inventory_permissions(
        self,
        inventory_name: str,
        role_name: str,
        privileges: list[InventoryPrivilege | str],
        namespace_name: str | None = None,
    ) -> None:
        """
        Grant inventory permissions for a role.

        Args:
            inventory_name: Name of the inventory
            role_name: Name of the role
            privileges: List of privileges (InventoryPrivilege enums or strings)
            namespace_name: Optional namespace

        Examples:
            ```python
            # With Enums (recommended)
            from seven2one.questra.data import InventoryPrivilege

            mutations.grant_inventory_permissions(
                inventory_name="TestUser",
                role_name="TestRole",
                privileges=[
                    InventoryPrivilege.SELECT,
                    InventoryPrivilege.INSERT,
                    InventoryPrivilege.UPDATE,
                ],
            )

            # With Strings (legacy)
            mutations.grant_inventory_permissions(
                inventory_name="TestUser",
                role_name="TestRole",
                privileges=["SELECT", "INSERT", "UPDATE"],
            )
            ```
        """
        logger.debug(
            f"Granting inventory permissions. inventory_name={inventory_name}, role_name={role_name}, privileges={privileges}"
        )

        # Convert Enums to Strings if needed
        privileges_values = [
            priv.value if isinstance(priv, InventoryPrivilege) else priv
            for priv in privileges
        ]

        mutation = """
            mutation GrantInventoryPermissions(
                $input: _GrantInventoryPermissions__InputType!
            ) {
                _grantInventoryPermissions(input: $input)
            }
        """

        variables = {
            "input": {
                "inventoryName": inventory_name,
                "roleName": role_name,
                "privileges": privileges_values,
                "namespaceName": namespace_name,
            }
        }

        self._execute(mutation, variables)
        logger.info(
            f"Permissions granted. inventory_name={inventory_name}, role_name={role_name}, privileges={privileges_values}"
        )

    def deny_inventory_permissions(
        self,
        inventory_name: str,
        role_name: str,
        privileges: list[InventoryPrivilege | str],
        namespace_name: str | None = None,
    ) -> None:
        """
        Deny inventory permissions for a role.

        Args:
            inventory_name: Name of the inventory
            role_name: Name of the role
            privileges: List of privileges (InventoryPrivilege enums or strings)
            namespace_name: Optional namespace
        """
        logger.debug(
            f"Denying inventory permissions. inventory_name={inventory_name}, role_name={role_name}, privileges={privileges}"
        )

        # Convert Enums to Strings if needed
        privileges_values = [
            priv.value if isinstance(priv, InventoryPrivilege) else priv
            for priv in privileges
        ]

        mutation = """
            mutation DenyInventoryPermissions(
                $input: _DenyInventoryPermissions__InputType!
            ) {
                _denyInventoryPermissions(input: $input)
            }
        """

        variables = {
            "input": {
                "inventoryName": inventory_name,
                "roleName": role_name,
                "privileges": privileges_values,
                "namespaceName": namespace_name,
            }
        }

        self._execute(mutation, variables)
        logger.info(
            f"Permissions denied. inventory_name={inventory_name}, role_name={role_name}, privileges={privileges_values}"
        )

    def revoke_inventory_permissions(
        self,
        inventory_name: str,
        role_name: str,
        privileges: list[InventoryPrivilege | str],
        namespace_name: str | None = None,
    ) -> None:
        """
        Revoke inventory permissions for a role.

        Args:
            inventory_name: Name of the inventory
            role_name: Name of the role
            privileges: List of privileges (InventoryPrivilege enums or strings)
            namespace_name: Optional namespace
        """
        logger.debug(
            f"Revoking inventory permissions. inventory_name={inventory_name}, role_name={role_name}, privileges={privileges}"
        )

        # Convert Enums to Strings if needed
        privileges_values = [
            priv.value if isinstance(priv, InventoryPrivilege) else priv
            for priv in privileges
        ]

        mutation = """
            mutation RevokeInventoryPermissions(
                $input: _RevokeInventoryPermissions__InputType!
            ) {
                _revokeInventoryPermissions(input: $input)
            }
        """

        variables = {
            "input": {
                "inventoryName": inventory_name,
                "roleName": role_name,
                "privileges": privileges_values,
                "namespaceName": namespace_name,
            }
        }

        self._execute(mutation, variables)
        logger.info(
            f"Permissions revoked. inventory_name={inventory_name}, role_name={role_name}, privileges={privileges_values}"
        )

    def create_inventory_policy(
        self,
        policy_name: str,
        role_name: str,
        inventory_name: str,
        property_name: str,
        filter_value: Any,
        namespace_name: str | None = None,
        description: str | None = None,
        if_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Create to inventory policy.

        Args:
            policy_name: Name of the policy
            role_name: Name of the role
            inventory_name: Name of the inventory
            property_name: Name of the property
            filter_value: Filter value
            namespace_name: Optional namespace
            description: Optional description
            if_exists: Behavior on conflict

        Returns:
            NamedItemResult: Dictionary with name and existed flag
        """
        logger.debug(
            f"Creating inventory policy. policy_name={policy_name}, role_name={role_name}, inventory_name={inventory_name}"
        )

        mutation = """
            mutation CreateInventoryPolicy(
                $input: _CreateInventoryPolicy__InputType!
            ) {
                _createInventoryPolicy(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "policyName": policy_name,
                "roleName": role_name,
                "inventoryName": inventory_name,
                "propertyName": property_name,
                "filterValue": filter_value,
                "namespaceName": namespace_name,
                "description": description,
                "ifExists": if_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        policy_result = NamedItemResult.from_dict(result["_createInventoryPolicy"])
        logger.info(
            f"Policy {'already existed' if policy_result.existed else 'created'}. policy_name={policy_result.name}, existed={policy_result.existed}"
        )
        return policy_result

    def delete_inventory_policy(
        self,
        policy_name: str,
        inventory_name: str,
        namespace_name: str | None = None,
        if_not_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Delete to inventory policy.

        Args:
            policy_name: Name of the policy
            inventory_name: Name of the inventory
            namespace_name: Optional namespace
            if_not_exists: Behavior when not exists

        Returns:
            NamedItemResult: Dictionary with name and existed flag
        """
        logger.debug(
            f"Deleting inventory policy. policy_name={policy_name}, inventory_name={inventory_name}"
        )

        mutation = """
            mutation DropInventoryPolicy(
                $input: _DropInventoryPolicy__InputType!
            ) {
                _dropInventoryPolicy(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "policyName": policy_name,
                "inventoryName": inventory_name,
                "namespaceName": namespace_name,
                "ifNotExists": if_not_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        delete_result = NamedItemResult.from_dict(result["_dropInventoryPolicy"])
        logger.info(
            f"Policy {'deleted' if delete_result.existed else 'did not exist'}. policy_name={delete_result.name}, existed={delete_result.existed}"
        )
        return delete_result

    def start_alter_inventory(
        self,
        inventory_name: str,
        namespace_name: str | None = None,
        add_properties: list[InventoryProperty] | None = None,
        alter_properties: list[InventoryProperty] | None = None,
        drop_properties: list[str] | None = None,
        add_relations: list[InventoryRelation] | None = None,
        drop_relations: list[str] | None = None,
        alter_relations: list[InventoryRelation] | None = None,
        new_inventory_name: str | None = None,
        description: str | None = None,
        if_not_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> BackgroundJobResult:
        """
        Start to inventory alteration as a background job.

        Args:
            inventory_name: Name of the inventory
            namespace_name: Optional namespace
            add_properties: Properties to add (InventoryProperty dataclasses)
            alter_properties: Properties to alter (InventoryProperty dataclasses)
            drop_properties: Properties to drop (names)
            add_relations: Relations to add (InventoryRelation dataclasses)
            drop_relations: Relations to drop (names)
            alter_relations: Relations to alter (InventoryRelation dataclasses)
            new_inventory_name: New name for the inventory
            description: New description
            if_not_exists: Behavior when not exists

        Returns:
            BackgroundJobResult: Dictionary with background job information
        """
        logger.debug(
            f"Starting alter inventory job. inventory_name={inventory_name}, namespace_name={namespace_name}, new_inventory_name={new_inventory_name}"
        )

        # Convert Dataclasses to Dictionaries if needed
        add_properties_dicts = []
        if add_properties:
            add_properties_dicts = [
                prop.to_dict() if isinstance(prop, InventoryProperty) else prop
                for prop in add_properties
            ]

        alter_properties_dicts = []
        if alter_properties:
            alter_properties_dicts = [
                prop.to_dict() if isinstance(prop, InventoryProperty) else prop
                for prop in alter_properties
            ]

        add_relations_dicts = []
        if add_relations:
            add_relations_dicts = [
                rel.to_dict() if isinstance(rel, InventoryRelation) else rel
                for rel in add_relations
            ]

        alter_relations_dicts = []
        if alter_relations:
            alter_relations_dicts = [
                rel.to_dict() if isinstance(rel, InventoryRelation) else rel
                for rel in alter_relations
            ]

        mutation = """
            mutation StartAlterInventory(
                $input: _StartAlterInventory__InputType!
            ) {
                _startAlterInventory(input: $input) {
                    backgroundJobId
                }
            }
        """

        drop_properties_list = (
            [{"propertyName": prop} for prop in drop_properties]
            if drop_properties
            else []
        )
        drop_relations_list = (
            [{"propertyName": rel} for rel in drop_relations] if drop_relations else []
        )

        variables = {
            "input": {
                "inventoryName": inventory_name,
                "namespaceName": namespace_name,
                "addProperties": add_properties_dicts,
                "alterProperties": alter_properties_dicts,
                "dropProperties": drop_properties_list,
                "addRelations": add_relations_dicts,
                "dropRelations": drop_relations_list,
                "alterRelations": alter_relations_dicts,
                "newInventoryName": new_inventory_name,
                "description": description,
                "ifNotExists": if_not_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        alter_result = BackgroundJobResult.from_dict(result["_startAlterInventory"])
        logger.info(
            f"Alter inventory job started. inventory_name={inventory_name}, background_job_id={alter_result.background_job_id}"
        )
        return alter_result

    def create_unit(
        self,
        symbol: str,
        aggregation: str,
        if_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Create a new unit.

        Args:
            symbol: Unit symbol (e.g. "kW", "kWh", "MW")
            aggregation: Aggregation type (SUM, AVERAGE, MIN, MAX, etc.)
            if_exists: Behavior on conflict

        Returns:
            NamedItemResult: Dictionary with name and existed flag

        Examples:
            ```python
            result = client.mutations.create_unit(
                symbol="kW", aggregation="AVERAGE", if_exists=ConflictAction.IGNORE
            )
            ```
        """
        logger.debug(f"Creating unit. symbol={symbol}, aggregation={aggregation}")

        mutation = """
            mutation CreateUnit($input: _CreateUnit__InputType!) {
                _createUnit(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "symbol": symbol,
                "aggregation": aggregation,
                "ifExists": if_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        unit_result = NamedItemResult.from_dict(result["_createUnit"])
        logger.info(
            f"Unit {'already existed' if unit_result.existed else 'created'}. symbol={unit_result.name}, existed={unit_result.existed}"
        )
        return unit_result

    def delete_unit(
        self,
        symbol: str,
        if_not_exists: ConflictAction = ConflictAction.RAISE_ERROR,
    ) -> NamedItemResult:
        """
        Delete a unit.

        Args:
            symbol: Unit symbol
            if_not_exists: Behavior when not exists

        Returns:
            NamedItemResult: Dictionary with name and existed flag

        Examples:
            ```python
            result = client.mutations.delete_unit(
                symbol="kW", if_not_exists=ConflictAction.IGNORE
            )
            ```
        """
        logger.debug(f"Deleting unit. symbol={symbol}")

        mutation = """
            mutation DropUnit($input: _DropUnit__InputType!) {
                _dropUnit(input: $input) {
                    name
                    existed
                }
            }
        """

        variables = {
            "input": {
                "symbol": symbol,
                "ifNotExists": if_not_exists.value,
            }
        }

        result = self._execute(mutation, variables)
        delete_result = NamedItemResult.from_dict(result["_dropUnit"])
        logger.info(
            f"Unit {'deleted' if delete_result.existed else 'did not exist'}. symbol={delete_result.name}, existed={delete_result.existed}"
        )
        return delete_result

    def create_timeseries(
        self,
        time_series_inputs: list[CreateTimeSeriesInput],
    ) -> list[TimeSeriesIdResult]:
        """
        Create one or more timeseries.

        Args:
            time_series_inputs: List of timeseries definitions (CreateTimeSeriesInput)

        Returns:
            list[TimeSeriesIdResult]: List with _id for each created timeseries

        Examples:
            ```python
            from seven2one.questra.data import (
                CreateTimeSeriesInput,
                TimeSeriesSpecifics,
                IntervalConfig,
                TimeUnit,
                ValueAlignment,
                ValueAvailability,
                Aggregation,
                QuotationBehavior,
            )

            result = client.mutations.create_timeseries(
                [
                    CreateTimeSeriesInput(
                        inventoryName="PowerPlant",
                        propertyName="PowerOutput",
                        namespaceName="Energy",
                        specifics=TimeSeriesSpecifics(
                            interval=IntervalConfig(
                                timeUnit=TimeUnit.MINUTE, multiplier=15
                            ),
                            valueAlignment=ValueAlignment.LEFT,
                            valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
                            unit="kW",
                            timeZone="Europe/Berlin",
                            defaultAggregation=Aggregation.AVERAGE,
                            startOfTime="2024-01-01T00:00:00Z",
                            defaultQuotationBehavior=QuotationBehavior.LATEST,
                        ),
                    )
                ]
            )
            ```
        """
        logger.debug(f"Creating {len(time_series_inputs)} timeseries")

        mutation = """
            mutation CreateTimeSeries($input: [_CreateTimeSeries__InputType!]!) {
                _createTimeSeries(input: $input) {
                    _id
                }
            }
        """

        # Convert CreateTimeSeriesInput Dataclasses to Dicts
        normalized_inputs = [ts_input.to_dict() for ts_input in time_series_inputs]

        variables = {"input": normalized_inputs}

        result = self._execute(mutation, variables)
        ts_results_raw = result["_createTimeSeries"]

        # Convert to TimeSeriesIdResult Dataclasses
        ts_results = [TimeSeriesIdResult.from_dict(ts) for ts in ts_results_raw]

        logger.info(
            f"Created {len(ts_results)} timeseries. ids={[ts.id for ts in ts_results]}"
        )
        return ts_results
