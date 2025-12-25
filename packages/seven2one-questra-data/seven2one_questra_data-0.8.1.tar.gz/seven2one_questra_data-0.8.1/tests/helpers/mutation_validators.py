"""
Validation Helfer für Mutation-Tests.

Statische Mutations: Schema-Validierung gegen data.sdl
Dynamische Mutations (create_inventory): Regel-basierte Validierung
"""

from __future__ import annotations

import re
from typing import Any


class MutationQueryValidator:
    """
    Validiert generierte GraphQL Mutation-Queries.

    Für statische Mutations: Schema-konform
    Für dynamische Mutations: Naming-Konventionen
    """

    # Statische Mutations (im Schema definiert)
    STATIC_MUTATIONS = {
        "_createNamespace",
        "_createRole",
        "_dropInventory",
        "_grantInventoryPermissions",
        "_denyInventoryPermissions",
        "_revokeInventoryPermissions",
        "_createInventoryPolicy",
        "_deleteInventoryPolicy",
        "_startAlterInventory",
        "_createUnit",
        "_deleteUnit",
        "_createTimeSeries",
    }

    # Dynamische Mutations (werden zur Laufzeit generiert)
    DYNAMIC_MUTATION_PATTERNS = {
        "create": r"^insert[A-Z][a-zA-Z0-9]*$",  # insertTestUser
        "update": r"^update[A-Z][a-zA-Z0-9]*$",  # updateTestUser
        "delete": r"^delete[A-Z][a-zA-Z0-9]*$",  # deleteTestUser
    }

    @classmethod
    def validate_mutation_query(cls, query: str, mutation_name: str) -> dict[str, Any]:
        """
        Validiert eine Mutation Query.

        Args:
            query: GraphQL Mutation Query String
            mutation_name: Name der Mutation (z.B. "_createNamespace", "insertTestUser")

        Returns:
            dict with Validierungsergebnis:
                - valid: bool
                - errors: list[str]
                - warnings: list[str]
                - mutation_type: "static" | "dynamic_create" | "dynamic_update" | "dynamic_delete"

        Examples:
            >>> result = MutationQueryValidator.validate_mutation_query(
            ...     "mutation { _createNamespace(input: {...}) { name existed } }",
            ...     "_createNamespace",
            ... )
            >>> result["valid"]
            True
        """
        errors: list[str] = []
        warnings: list[str] = []
        mutation_type = "unknown"

        # Query enthält Mutation-Name?
        if mutation_name not in query:
            errors.append(f"Mutation '{mutation_name}' nicht in Query gefunden")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
                "mutation_type": mutation_type,
            }

        # Statische Mutation?
        if mutation_name in cls.STATIC_MUTATIONS:
            mutation_type = "static"
            return cls._validate_static_mutation(
                query, mutation_name, errors, warnings, mutation_type
            )

        # Dynamische Mutation?
        if mutation_name == "_createInventory":
            mutation_type = "dynamic_inventory_create"
            return cls._validate_inventory_create(
                query, mutation_name, errors, warnings, mutation_type
            )

        # Dynamische Item-Mutations (insert/update/delete)
        for operation, pattern in cls.DYNAMIC_MUTATION_PATTERNS.items():
            if re.match(pattern, mutation_name):
                mutation_type = f"dynamic_{operation}"
                return cls._validate_dynamic_item_mutation(
                    query, mutation_name, errors, warnings, mutation_type
                )

        # Unbekannte Mutation
        errors.append(f"Unbekannte Mutation: {mutation_name}")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "mutation_type": mutation_type,
        }

    @classmethod
    def _validate_static_mutation(
        cls,
        query: str,
        mutation_name: str,
        errors: list[str],
        warnings: list[str],
        mutation_type: str,
    ) -> dict[str, Any]:
        """Validiert statische Mutations (im Schema definiert)."""
        # Query muss "mutation" Keyword enthalten
        if "mutation" not in query.lower():
            errors.append("Query muss 'mutation' Keyword enthalten")

        # Query muss "input:" Parameter haben
        if "input:" not in query:
            warnings.append(f"Mutation {mutation_name} sollte 'input:' Parameter haben")

        # Naming Convention: _<verb><Noun> (z.B. _createRole)
        if not mutation_name.startswith("_"):
            errors.append(f"Statische Mutation muss with '_' beginnen: {mutation_name}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "mutation_type": mutation_type,
        }

    @classmethod
    def _validate_inventory_create(
        cls,
        query: str,
        mutation_name: str,
        errors: list[str],
        warnings: list[str],
        mutation_type: str,
    ) -> dict[str, Any]:
        """Validiert _createInventory Mutation (dynamisches Schema)."""
        # Query muss "mutation" Keyword enthalten
        if "mutation" not in query.lower():
            errors.append("Query muss 'mutation' Keyword enthalten")

        # Query muss "input:" Parameter haben
        if "input:" not in query:
            errors.append("_createInventory benötigt 'input:' Parameter")

        # Response-Felder: name, existed
        if "name" not in query or "existed" not in query:
            warnings.append("_createInventory sollte 'name' and 'existed' zurückgeben")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "mutation_type": mutation_type,
        }

    @classmethod
    def _validate_dynamic_item_mutation(
        cls,
        query: str,
        mutation_name: str,
        errors: list[str],
        warnings: list[str],
        mutation_type: str,
    ) -> dict[str, Any]:
        """Validiert dynamische Item-Mutations (insert/update/delete)."""
        # Query muss "mutation" Keyword enthalten
        if "mutation" not in query.lower():
            errors.append("Query muss 'mutation' Keyword enthalten")

        # Naming Convention: <verb><PascalCase>
        operation = mutation_type.replace("dynamic_", "")
        verb_map = {"create": "insert", "update": "update", "delete": "delete"}
        expected_verb = verb_map.get(operation)

        if expected_verb and not mutation_name.startswith(expected_verb):
            errors.append(
                f"Dynamische {operation}-Mutation muss with '{expected_verb}' beginnen"
            )

        # PascalCase nach Verb
        if expected_verb:
            entity_name = mutation_name.replace(expected_verb, "", 1)
            if entity_name and not entity_name[0].isupper():
                errors.append(
                    f"Entity-Name muss PascalCase sein (nach '{expected_verb}'): {entity_name}"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "mutation_type": mutation_type,
        }


class MutationInputValidator:
    """
    Validiert Input-Parameter für Mutations.

    Prüft Typen, Required-Fields, Naming-Konventionen.
    """

    @staticmethod
    def validate_create_inventory_input(variables: dict[str, Any]) -> dict[str, Any]:
        """
        Validiert Input für _createInventory Mutation.

        Args:
            variables: GraphQL Variables Dictionary

        Returns:
            dict with Validierungsergebnis:
                - valid: bool
                - errors: list[str]
                - warnings: list[str]

        Examples:
            >>> result = MutationInputValidator.validate_create_inventory_input(
            ...     {
            ...         "input": {
            ...             "inventoryName": "TestInventory",
            ...             "properties": [
            ...                 {"propertyName": "Name", "dataType": "STRING"}
            ...             ],
            ...         }
            ...     }
            ... )
            >>> result["valid"]
            True
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Input vorhanden?
        if "input" not in variables:
            errors.append("Variables müssen 'input' enthalten")
            return {"valid": False, "errors": errors, "warnings": warnings}

        input_data = variables["input"]

        # Required Fields
        if "inventoryName" not in input_data:
            errors.append("'inventoryName' ist Pflichtfeld")

        if "properties" not in input_data:
            errors.append("'properties' ist Pflichtfeld")
        elif not isinstance(input_data["properties"], list):
            errors.append("'properties' muss eine Liste sein")
        elif len(input_data["properties"]) == 0:
            warnings.append("'properties' ist leer - Inventory without Properties?")

        # Naming Convention: inventoryName muss PascalCase sein
        if "inventoryName" in input_data:
            inv_name = input_data["inventoryName"]
            if not isinstance(inv_name, str):
                errors.append(
                    f"'inventoryName' muss String sein, ist: {type(inv_name)}"
                )
            elif not inv_name[0].isupper():
                warnings.append(f"'inventoryName' sollte PascalCase sein: {inv_name}")

        # namespaceName optional, aber wenn vorhanden: PascalCase or None
        if "namespaceName" in input_data:
            ns_name = input_data["namespaceName"]
            if ns_name is not None:
                if not isinstance(ns_name, str):
                    errors.append(
                        f"'namespaceName' muss String or None sein, ist: {type(ns_name)}"
                    )
                elif ns_name and not ns_name[0].isupper():
                    warnings.append(
                        f"'namespaceName' sollte PascalCase sein: {ns_name}"
                    )

        # Properties validieren
        if "properties" in input_data and isinstance(input_data["properties"], list):
            for idx, prop in enumerate(input_data["properties"]):
                prop_errors = MutationInputValidator._validate_property(prop, idx)
                errors.extend(prop_errors)

        # ConflictAction validieren (ifExists)
        if "ifExists" in input_data:
            if_exists = input_data["ifExists"]
            valid_actions = {"RAISE_ERROR", "IGNORE"}
            if if_exists not in valid_actions:
                errors.append(
                    f"'ifExists' muss einer of {valid_actions} sein, ist: {if_exists}"
                )

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    def _validate_property(prop: dict[str, Any], idx: int) -> list[str]:
        """Validiert eine einzelne Property."""
        errors: list[str] = []

        # Required Fields
        if "propertyName" not in prop:
            errors.append(f"Property[{idx}]: 'propertyName' fehlt")
        elif not isinstance(prop["propertyName"], str):
            errors.append(f"Property[{idx}]: 'propertyName' muss String sein")
        elif not prop["propertyName"][0].isupper():
            # Warning statt Error - Best Practice
            pass  # Wird of Caller as Warning behandelt

        if "dataType" not in prop:
            errors.append(f"Property[{idx}]: 'dataType' fehlt")
        else:
            valid_types = {
                "STRING",
                "INT",
                "LONG",
                "DECIMAL",
                "BOOL",
                "DATE",
                "DATETIME",
                "TIME",
                "TIME_SERIES",
                "GUID",
            }
            if prop["dataType"] not in valid_types:
                errors.append(
                    f"Property[{idx}]: ungültiger 'dataType': {prop['dataType']}"
                )

        return errors

    @staticmethod
    def validate_create_namespace_input(variables: dict[str, Any]) -> dict[str, Any]:
        """
        Validiert Input für _createNamespace Mutation.

        Args:
            variables: GraphQL Variables Dictionary

        Returns:
            dict with Validierungsergebnis
        """
        errors: list[str] = []
        warnings: list[str] = []

        if "input" not in variables:
            errors.append("Variables müssen 'input' enthalten")
            return {"valid": False, "errors": errors, "warnings": warnings}

        input_data = variables["input"]

        # Required Fields
        if "namespaceName" not in input_data:
            errors.append("'namespaceName' ist Pflichtfeld")
        elif not isinstance(input_data["namespaceName"], str):
            errors.append(
                f"'namespaceName' muss String sein, ist: {type(input_data['namespaceName'])}"
            )
        elif not input_data["namespaceName"][0].isupper():
            warnings.append(
                f"'namespaceName' sollte PascalCase sein: {input_data['namespaceName']}"
            )

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    def validate_create_role_input(variables: dict[str, Any]) -> dict[str, Any]:
        """
        Validiert Input für _createRole Mutation.

        Args:
            variables: GraphQL Variables Dictionary

        Returns:
            dict with Validierungsergebnis
        """
        errors: list[str] = []
        warnings: list[str] = []

        if "input" not in variables:
            errors.append("Variables müssen 'input' enthalten")
            return {"valid": False, "errors": errors, "warnings": warnings}

        input_data = variables["input"]

        # Required Fields
        if "roleName" not in input_data:
            errors.append("'roleName' ist Pflichtfeld")
        elif not isinstance(input_data["roleName"], str):
            errors.append(
                f"'roleName' muss String sein, ist: {type(input_data['roleName'])}"
            )

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
