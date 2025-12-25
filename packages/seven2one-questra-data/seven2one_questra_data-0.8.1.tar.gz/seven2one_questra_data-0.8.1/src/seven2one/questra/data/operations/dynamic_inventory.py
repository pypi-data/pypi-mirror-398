"""Dynamic inventory operations for Questra Data."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime, time
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """
    Normalize names for GraphQL field names.

    Converts names like 'TestNamespace' to 'testNamespace'.

    Args:
        name: Name to normalize

    Returns:
        str: Normalized name
    """
    if not name:
        return name
    return name[0].lower() + name[1:]


def _convert_numbers_to_strings(value: Any) -> Any:
    """
    Recursively convert numbers and datetime types to strings for GraphQL API.

    JavaScript has limitations with large numbers (2^53-1), so GraphQL API expects numbers as strings.

    Args:
        value: Any value (int, float, datetime, dict, list, etc.)

    Returns:
        Value with converted numbers and datetime objects
    """
    # IMPORTANT: bool is a subclass of int in Python, so bool
    # MUST be checked first, otherwise True/False would be converted to "1"/"0"!
    if isinstance(value, bool):
        # Keep booleans unchanged
        return value
    elif isinstance(value, datetime):
        # datetime to ISO-8601 string with timezone
        return value.isoformat()
    elif isinstance(value, date):
        # date to ISO-8601 string (YYYY-MM-DD)
        return value.isoformat()
    elif isinstance(value, time):
        # time to ISO-8601 string (HH:MM:SS or HH:MM:SS.ffffff)
        return value.isoformat()
    elif isinstance(value, UUID):
        # UUID to string
        return str(value)
    elif isinstance(value, (int, float)):
        # Convert numbers to strings
        return str(value)
    elif isinstance(value, dict):
        # Recursive for dictionaries
        return {key: _convert_numbers_to_strings(val) for key, val in value.items()}
    elif isinstance(value, list):
        # Recursive for lists
        return [_convert_numbers_to_strings(item) for item in value]
    else:
        # All other types (str, None) unchanged
        return value


def _normalize_items_names(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Normalize keys in a list of items and convert numbers to strings.

    Args:
        items: List of items with arbitrary keys

    Returns:
        List of items with normalized keys and numbers as strings
    """
    return [
        {
            _normalize_name(key): _convert_numbers_to_strings(value)
            for key, value in item.items()
        }
        for item in items
    ]


def _build_nested_field_selection(property_name: str) -> str:
    """
    Convert dot notation property to nested GraphQL field syntax.

    Args:
        property_name: Property name with optional dot notation

    Returns:
        GraphQL field selection string
    """
    parts = property_name.split(".")
    if len(parts) == 1:
        # Einfache Property without Verschachtelung
        return _normalize_name(parts[0])

    # Verschachtelte Property - baue rekursiv GraphQL fields auf
    normalized_parts = [_normalize_name(p) for p in parts]
    result = normalized_parts[0]
    for part in normalized_parts[1:]:
        result = f"{result} {{ {part}"
    result += " }" * (len(parts) - 1)
    return result


class DynamicInventoryOperations:
    """
    Dynamic operations for inventory data.

    After creating to inventory, GraphQL operations are auto-generated:

    Queries:
    - namespace__InventoryName: Query items with pagination

    Mutations:
    - namespace__insertInventoryName: Create items
    - namespace__updateInventoryName: Update items
    - namespace__deleteInventoryName: Delete items

    Methods follow Python CRUD naming conventions:
    - create(): Create new items
    - list(): List/query items
    - update(): Update existing items
    - delete(): Delete items
    """

    def __init__(self, execute_func: Callable):
        """
        Initialize the dynamic Inventory operations.

        Args:
            execute_func: Function to execute GraphQL operations
        """
        self._execute = execute_func
        self._schema_cache: dict[str, dict[str, Any]] = {}
        logger.debug("DynamicInventoryOperations initialized")

    def _check_inventory_exists(
        self, inventory_name: str, namespace_name: str | None = None
    ) -> bool:
        """
        Checks if an inventory exists.

        Args:
            inventory_name: Name of the inventory
            namespace_name: Optional Namespace

        Returns:
            bool: True if inventory exists, otherwise False
        """
        try:
            # Query to check inventory (without retries)
            query = """
                query CheckInventory(
                    $where: _InventoryFilter__InputType
                ) {
                    _inventories(where: $where) {
                        name
                        namespace {
                            name
                        }
                    }
                }
            """

            variables = {
                "where": {
                    "inventoryNames": [inventory_name],
                    "namespaceNames": ([namespace_name] if namespace_name else None),
                }
            }

            # No retries for validation (retries=0)
            result = self._execute(query, variables, retries=0)
            inventories = result.get("_inventories", [])

            return len(inventories) > 0

        except Exception as e:
            logger.warning(f"Failed to check inventory existence: {e}")
            return True  # Optimistically continue

    def _load_inventory_schema(
        self, inventory_name: str, namespace_name: str | None = None
    ) -> dict[str, Any]:
        """
        Loads the schema for a specific inventory from the server.

        Args:
            inventory_name: Name of the inventory
            namespace_name: Optional Namespace

        Returns:
            dict: Schema information (fields, required_fields, etc.)

        Raises:
            ValueError: If inventory does not exist
        """
        cache_key = f"{namespace_name or ''}::{inventory_name}"

        if cache_key in self._schema_cache:
            logger.debug(f"Using cached schema for {cache_key}")
            return self._schema_cache[cache_key]

        logger.debug(f"Loading schema for {cache_key} from server")

        # Check if inventory exists
        if not self._check_inventory_exists(inventory_name, namespace_name):
            ns_part = f" in namespace '{namespace_name}'" if namespace_name else ""
            raise ValueError(f"Inventory '{inventory_name}'{ns_part} does not exist")

        type_name = self._build_type_name(inventory_name, namespace_name)

        # Introspection query for a specific type
        introspection_query = f"""
            query IntrospectType {{
                __type(name: "{type_name}__InsertInputType") {{
                    name
                    inputFields {{
                        name
                        type {{
                            kind
                            name
                            ofType {{
                                kind
                                name
                                ofType {{
                                    kind
                                    name
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        """

        try:
            # No retries for schema introspection (retries=0)
            result = self._execute(introspection_query, retries=0)
            type_info = result.get("__type")

            if not type_info:
                raise ValueError(
                    f"Schema for '{type_name}__InsertInputType' not found. "
                    f"Inventory may not be properly created."
                )

            # Extract field information
            fields = {}
            required_fields = set()

            for field in type_info.get("inputFields", []):
                field_name = field["name"]
                field_type = field["type"]

                # Check if field is required (NON_NULL)
                is_required = field_type.get("kind") == "NON_NULL"
                is_array = False
                base_type = None

                # Navigate through the type structure
                current_type = field_type
                while current_type:
                    if current_type.get("kind") == "LIST":
                        is_array = True
                    elif current_type.get("kind") in ["SCALAR", "ENUM", "INPUT_OBJECT"]:
                        base_type = current_type.get("name")
                        break
                    current_type = current_type.get("ofType")

                fields[field_name] = {
                    "required": is_required,
                    "array": is_array,
                    "type": base_type,
                }

                if is_required:
                    required_fields.add(field_name)

            schema_info = {"fields": fields, "required_fields": required_fields}

            self._schema_cache[cache_key] = schema_info
            logger.info(
                f"Loaded schema for {cache_key}: "
                f"{len(fields)} fields, {len(required_fields)} required"
            )

            return schema_info

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to load schema for {type_name}: {e}")

    def _validate_items(
        self,
        items: list[dict[str, Any]],
        inventory_name: str,
        namespace_name: str | None = None,
        operation: str = "insert",
    ) -> None:
        """
        Validates items against the schema.

        Field names are case-insensitive for the first letter
        (Name == name, Email == email).

        Args:
            items: List of items to validate
            inventory_name: Name of the inventory
            namespace_name: Optional Namespace
            operation: Operation (insert, update, delete)

        Raises:
            ValueError: If validation fails
        """
        if operation == "insert":
            schema_info = self._load_inventory_schema(inventory_name, namespace_name)

            required_fields = schema_info.get("required_fields", set())
            available_fields = schema_info.get("fields", {})

            # Erstelle Mappings with normalisiertem ersten Buchstaben
            required_fields_normalized = {_normalize_name(f) for f in required_fields}
            available_fields_normalized = {
                _normalize_name(f) for f in available_fields.keys()
            }

            for idx, item in enumerate(items):
                # Normalisiere Item-Keys (erster Buchstabe lowercase)
                item_keys_normalized = {_normalize_name(k) for k in item.keys()}

                # Check required fields
                missing_fields = required_fields_normalized - item_keys_normalized
                if missing_fields:
                    raise ValueError(
                        f"Item {idx}: Missing required fields: "
                        f"{', '.join(sorted(missing_fields))}"
                    )

                # Check unknown fields
                if available_fields:
                    unknown_fields = item_keys_normalized - available_fields_normalized
                    if unknown_fields:
                        logger.warning(
                            f"Item {idx}: Unknown fields will be ignored: "
                            f"{', '.join(sorted(unknown_fields))}"
                        )

        elif operation in ["update", "delete"]:
            # For Update and Delete: _id and _rowVersion are required
            for idx, item in enumerate(items):
                if "_id" not in item:
                    raise ValueError(
                        f"Item {idx}: Missing required field '_id' "
                        f"for {operation} operation"
                    )
                if "_rowVersion" not in item:
                    raise ValueError(
                        f"Item {idx}: Missing required field '_rowVersion' "
                        f"for {operation} operation"
                    )

    def _build_field_name(
        self,
        inventory_name: str,
        namespace_name: str | None = None,
        operation: str | None = None,
    ) -> str:
        """
        Creates the GraphQL Field Name from Namespace and Inventory.

        Args:
            inventory_name: Name of the inventory (z.B. 'TestUser')
            namespace_name: Optional Namespace (z.B. 'TestNamespace')
            operation: Optional Operation (z.B. 'insert', 'update', 'delete')

        Returns:
            str: Field Name (z.B. 'testNamespace__TestUser' or 'testNamespace__insertTestUser')
        """
        if namespace_name:
            normalized_ns = _normalize_name(namespace_name)
            base_name = f"{normalized_ns}__{inventory_name}"
        else:
            base_name = _normalize_name(inventory_name)

        if operation:
            # For operations: testNamespace__insertTestUser
            if namespace_name:
                normalized_ns = _normalize_name(namespace_name)
                return f"{normalized_ns}__{operation}{inventory_name}"
            else:
                return f"{operation}{inventory_name}"

        return base_name

    def _build_type_name(
        self,
        inventory_name: str,
        namespace_name: str | None = None,
    ) -> str:
        """
        Creates the GraphQL Type Name from Namespace and Inventory.

        Args:
            inventory_name: Name of the inventory (z.B. 'TestUser')
            namespace_name: Optional Namespace (z.B. 'TestNamespace')

        Returns:
            str: Type Name (z.B. 'testNamespace__TestUser')
        """
        if namespace_name:
            normalized_ns = _normalize_name(namespace_name)
            return f"{normalized_ns}__{inventory_name}"
        else:
            return inventory_name

    def list(
        self,
        inventory_name: str,
        namespace_name: str | None = None,
        properties: list[str] | None = None,
        where: dict[str, Any] | None = None,
        order: list[dict[str, Any]] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
    ) -> dict[str, Any]:
        """
        Lists items from a dynamic inventory.

        Args:
            inventory_name: Name of the inventory (z.B. 'TestUser')
            namespace_name: Optional Namespace (z.B. 'TestNamespace')
            properties: Properties to query (default: ['_id', '_rowVersion'])
                       Supports dot notation for nested properties:
                       - Einfach: 'Name', 'Email'
                       - Verschachtelt: 'BodyBattery.id', 'BodyBattery.interval.timeUnit'
            where: Filter-Bedingungen
            order: Sortierung
            first: Number of elements from the beginning
            after: Cursor for pagination
            last: Number of elements from the end
            before: Cursor for pagination

        Returns:
            dict: Dictionary with pageInfo and nodes/edges

        Beispiele:
            # Einfache Properties
            result = client.inventory.list(
                inventory_name='TestUser',
                namespace_name='TestNamespace',
                properties=['_id', 'Name', 'Email', 'Age'],
                first=10
            )

            # Verschachtelte Properties (z.B. TimeSeries)
            result = client.inventory.list(
                inventory_name='TestUser',
                namespace_name='TestNamespace',
                properties=['_id', 'Name', 'BodyBattery.id', 'BodyBattery.unit', 'BodyBattery.interval.timeUnit'],
                first=10
            )
        """
        field_name = self._build_field_name(inventory_name, namespace_name)
        type_name = self._build_type_name(inventory_name, namespace_name)

        # Standard-Properties wenn nichts angegeben
        if not properties:
            properties = ["_id", "_rowVersion"]

        # Build nested field selection for each property (internal GraphQL fields)
        normalized_fields = [_build_nested_field_selection(prop) for prop in properties]
        fields_str = "\n                    ".join(normalized_fields)

        logger.debug(
            f"Listing items from dynamic inventory. field_name={field_name}, type_name={type_name}, properties={properties}, where={where}, order={order}"
        )

        # Baue GraphQL Query
        query = f"""
            query ListInventory(
                $where: {type_name}__FilterInputType
                $order: [{type_name}__SortInputType!]
                $first: Int
                $after: String
                $last: Int
                $before: String
            ) {{
                {field_name}(
                    where: $where
                    order: $order
                    first: $first
                    after: $after
                    last: $last
                    before: $before
                ) {{
                    pageInfo {{
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }}
                    nodes {{
                        {fields_str}
                    }}
                }}
            }}
        """

        variables = {
            "where": where,
            "order": order,
            "first": first,
            "after": after,
            "last": last,
            "before": before,
        }

        result = self._execute(query, variables)
        data = result[field_name]

        logger.info(
            f"Listed {len(data.get('nodes', []))} items from {field_name}. has_next_page={data.get('pageInfo', {}).get('hasNextPage')}"
        )

        return data

    def create(
        self,
        inventory_name: str,
        items: list[dict[str, Any]],
        namespace_name: str | None = None,
        validate: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Creates new items in a dynamic inventory.

        Args:
            inventory_name: Name of the inventory (z.B. 'TestUser')
            items: List of items to create
            namespace_name: Optional Namespace (z.B. 'TestNamespace')
            validate: Perform schema validation (default: True)

        Returns:
            list[dict]: List of the created Items with _id, _rowVersion, _existed
                (Only these 3 standard fields are returned)

        Raises:
            ValueError: If validation fails

        Examples:
            ```python
            items = client.inventory.create(
                inventory_name="TestUser",
                namespace_name="TestNamespace",
                items=[
                    {
                        "Name": "John Doe",
                        "Email": "john@example.com",
                        "Age": 30,
                        "IsActive": True,
                    },
                    {
                        "Name": "Jane Doe",
                        "Email": "jane@example.com",
                        "Age": 28,
                        "IsActive": True,
                    },
                ],
            )
            ```
        """
        # Validation
        if validate:
            self._validate_items(items, inventory_name, namespace_name, "insert")

        field_name = self._build_field_name(inventory_name, namespace_name, "insert")

        type_name = self._build_type_name(inventory_name, namespace_name)

        logger.debug(
            f"Creating items in dynamic inventory. field_name={field_name}, type_name={type_name}, num_items={len(items)}, validated={validate}"
        )

        # The return type is _Items__PayloadType with items array
        mutation = f"""
            mutation CreateInventory(
                $input: [{type_name}__InsertInputType!]!
            ) {{
                {field_name}(input: $input) {{
                    items {{
                        _id
                        _rowVersion
                        _existed
                    }}
                }}
            }}
        """

        normalized_items = _normalize_items_names(items)

        variables = {"input": normalized_items}

        result = self._execute(mutation, variables)
        created_items = result[field_name]["items"]

        logger.info(
            f"Created {len(created_items)} items in {field_name}. num_new={sum(1 for item in created_items if not item.get('_existed', False))}"
        )

        return created_items

    def update(
        self,
        inventory_name: str,
        items: list[dict[str, Any]],
        namespace_name: str | None = None,
        validate: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Updates items in a dynamic inventory.

        Args:
            inventory_name: Name of the inventory (z.B. 'TestUser')
            items: List of items to update (with _id, _rowVersion)
            namespace_name: Optional Namespace (z.B. 'TestNamespace')
            validate: Perform schema validation (default: True)

        Returns:
            list[dict]: List of the updated items with _id, _rowVersion, _existed
                (Only these 3 standard fields are returned)

        Raises:
            ValueError: If validation fails

        Examples:
            ```python
            items = client.inventory.update(
                inventory_name="TestUser",
                namespace_name="TestNamespace",
                items=[{"_id": "123", "_rowVersion": "1", "Age": 31}],
            )
            ```
        """
        # Validation
        if validate:
            self._validate_items(items, inventory_name, namespace_name, "update")

        field_name = self._build_field_name(inventory_name, namespace_name, "update")
        type_name = self._build_type_name(inventory_name, namespace_name)

        logger.debug(
            f"Updating items in dynamic inventory. field_name={field_name}, type_name={type_name}, num_items={len(items)}, validated={validate}"
        )

        # The return type is _Items__PayloadType with items array
        mutation = f"""
            mutation UpdateInventory(
                $input: [{type_name}__UpdateInputType!]!
            ) {{
                {field_name}(input: $input) {{
                    items {{
                        _id
                        _rowVersion
                        _existed
                    }}
                }}
            }}
        """

        normalized_items = _normalize_items_names(items)

        variables = {"input": normalized_items}

        result = self._execute(mutation, variables)
        updated_items = result[field_name]["items"]

        logger.info(
            f"Updated {len(updated_items)} items in {field_name}. num_found={sum(1 for item in updated_items if item.get('_existed', False))}"
        )

        return updated_items

    def delete(
        self,
        inventory_name: str,
        items: list[dict[str, Any]],
        namespace_name: str | None = None,
        validate: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Deletes items from a dynamic inventory.

        Args:
            inventory_name: Name of the inventory (z.B. 'TestUser')
            items: List of items to delete (with _id and _rowVersion)
            namespace_name: Optional Namespace (z.B. 'TestNamespace')
            validate: Perform schema validation (default: True)

        Returns:
            list[dict]: List with _id, _rowVersion, _existed for each deleted item
                (Only these 3 standard fields are returned)

        Raises:
            ValueError: If validation fails

        Examples:
            ```python
            items = client.inventory.delete(
                inventory_name="TestUser",
                namespace_name="TestNamespace",
                items=[{"_id": "123", "_rowVersion": "1"}],
            )
            ```
        """
        # Validation
        if validate:
            self._validate_items(items, inventory_name, namespace_name, "delete")

        field_name = self._build_field_name(inventory_name, namespace_name, "delete")
        type_name = self._build_type_name(inventory_name, namespace_name)

        logger.debug(
            f"Deleting items from dynamic inventory. field_name={field_name}, type_name={type_name}, num_items={len(items)}, validated={validate}"
        )

        # The return type is _Items__PayloadType with items array
        mutation = f"""
            mutation DeleteInventory(
                $input: [{type_name}__DeleteInputType!]!
            ) {{
                {field_name}(input: $input) {{
                    items {{
                        _id
                        _rowVersion
                        _existed
                    }}
                }}
            }}
        """

        variables = {"input": items}

        result = self._execute(mutation, variables)
        deleted_items = result[field_name]["items"]

        logger.info(
            f"Deleted {len(deleted_items)} items from {field_name}. num_found={sum(1 for item in deleted_items if item.get('_existed', False))}"
        )

        return deleted_items
