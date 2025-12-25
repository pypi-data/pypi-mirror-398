"""Generate Pydantic models from data.sdl and swagger.json."""

from __future__ import annotations

from pathlib import Path

from questra_codegen import CodeGenerator
from questra_codegen.processors import OpenAPIProcessor, SDLProcessor


def generate_sdl_models() -> None:
    """Generate Pydantic models from GraphQL SDL schema."""
    package_dir = Path(__file__).parent.parent
    schema_file = package_dir / "schemas" / "data.sdl"
    output_file = (
        package_dir
        / "src"
        / "seven2one"
        / "questra"
        / "data"
        / "generated"
        / "models.py"
    )

    # Configure SDL processor with data-specific scalar mappings
    processor = SDLProcessor(
        scalar_mappings={
            "LongNumberString": "LongNumberString = int  # GraphQL serialisiert as string, Python behandelt as int (64-bit)",
            "IntNumberString": "IntNumberString = int  # GraphQL serialisiert as string, Python behandelt as int (32-bit)",
            "UIntNumberString": "UIntNumberString = int  # GraphQL serialisiert as string, Python behandelt as int (unsigned 32-bit)",
            "DecimalWithPrecisionString": "DecimalWithPrecisionString = float  # GraphQL serialisiert as string, Python behandelt as float",
            "DateTimeWithMicroseconds": "DateTimeWithMicroseconds = datetime",
            "Date2": "Date2 = date",
            "TimeWithMicroseconds": "TimeWithMicroseconds = time",
            # Remove UUID TypeAlias (imported from uuid)
            "UUID": "",
            "Any": "",
            # Replace JSON with Any
            "JSON": "JSON = Any",
        },
        extra_imports=[
            "from datetime import date, datetime, time",
            "from decimal import Decimal",
            "from typing import Any, Literal",
            "from uuid import UUID",
        ],
        inject_config=True,
        fix_forward_references=True,
        fix_enum_collisions=True,
        # optional_output_fields=True is now the default
    )

    # Create generator
    generator = CodeGenerator(
        output_file=output_file,
        post_processor=processor,
        run_formatter=True,
        run_linter=True,
    )

    # Generate from GraphQL SDL
    generator.generate_from_graphql(schema_file)


def generate_swagger_models() -> None:
    """Generate Pydantic models from Swagger/OpenAPI schema."""
    package_dir = Path(__file__).parent.parent
    schema_file = package_dir / "schemas" / "swagger.json"
    output_file = (
        package_dir
        / "src"
        / "seven2one"
        / "questra"
        / "data"
        / "generated"
        / "rest_models.py"
    )

    # Configure OpenAPI processor with custom type mappings
    # In REST API: Number-Strings and DateTime-Strings werden as native Python Typen behandelt
    processor = OpenAPIProcessor(
        convert_number_strings=True,
        custom_mappings={
            # Import datetime für die neuen Typen
            "from pydantic import BaseModel, ConfigDict, Field": "from datetime import datetime\nfrom pydantic import BaseModel, ConfigDict, Field",
        },
    )

    # Create generator
    generator = CodeGenerator(
        output_file=output_file,
        post_processor=processor,
        run_formatter=True,
        run_linter=True,
    )

    # Generate from OpenAPI/Swagger
    generator.generate_from_openapi(schema_file)


def generate_models() -> None:
    """Generate all models (SDL and Swagger)."""
    print("=" * 80)
    print("Generating GraphQL SDL models...")
    print("=" * 80)
    generate_sdl_models()

    print("\n" + "=" * 80)
    print("Generating REST API models from Swagger...")
    print("=" * 80)
    generate_swagger_models()


if __name__ == "__main__":
    generate_models()
