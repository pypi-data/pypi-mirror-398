"""Demo of general-purpose Python builders (ready for funcy-bear extraction).

This demonstrates the enhanced builders that are now fully decoupled from PyDB
and can generate any Python code: dataclasses, Pydantic models, enums, etc.
"""  # noqa: INP001

from __future__ import annotations

from codec_cub.pythons import (
    Attribute,
    ClassBuilder,
    Dataclass,
    Decorator,
    EnumBuilder,
    FileBuilder,
    FunctionBuilder,
    ImportBuilder,
    MethodBuilder,
    PydanticModel,
    generate_all_export,
)
from codec_cub.pythons.builders.function_builder import generate_main_block


def demo_dataclass() -> None:
    """Demonstrate building a dataclass with the ClassBuilder."""
    print("=" * 60)
    print("DATACLASS BUILDER DEMO")
    print("=" * 60)

    user_class = Dataclass(
        name="User",
        docstring="Represents a user in the system.",
        attributes=[
            Attribute("id", "int"),
            Attribute("username", annotations="str"),
            Attribute("email", "str | None", default="None"),
            Attribute("is_active", "bool", default="True"),
            Attribute("created_at", "datetime", default="field(default_factory=datetime.now)"),
        ],
        methods=[
            MethodBuilder(
                name="to_dict",
                returns="dict[str, Any]",
                docstring="Convert user to dictionary.",
                body="return asdict(self)",
            )
        ],
    )

    print(user_class.render())


def demo_pydantic() -> None:
    """Demonstrate building a Pydantic model."""
    print("=" * 60)
    print("PYDANTIC MODEL BUILDER DEMO")
    print("=" * 60)

    config_model: PydanticModel = PydanticModel(
        name="ServerConfig",
        docstring="Server configuration settings.",
        attributes=[
            Attribute("host", "str", default='"localhost"'),
            Attribute("port", "int", default="8000"),
            Attribute("debug", "bool", default="False"),
            Attribute("workers", "int | None", default="None"),
        ],
    ).method(
        name="display",
        returns="str",
        docstring="Return a string representation of the config.",
        body='return f"Server running on {self.host}:{self.port} (debug={self.debug})"',
    )

    print(config_model.render())


def demo_enum() -> None:
    """Demonstrate building enums."""
    print("=" * 60)
    print("ENUM BUILDER DEMO")
    print("=" * 60)

    # Simple Enum with auto() values
    status_enum = EnumBuilder(
        name="Status",
        members=["PENDING", "APPROVED", "REJECTED"],
        base_class="Enum",
        docstring="Request status values.",
    )

    print(status_enum.render())

    # IntEnum with explicit values
    priority_enum = EnumBuilder(
        name="Priority",
        members={"LOW": 1, "MEDIUM": 5, "HIGH": 10, "CRITICAL": 99},
        base_class="IntEnum",
        docstring="Task priority levels.",
    )

    print(priority_enum.render())

    env_enum = EnumBuilder(
        name="Environment",
        members={"DEVELOPMENT": "dev", "STAGING": "staging", "PRODUCTION": "prod"},
        base_class="StrEnum",
        docstring="Deployment environments.",
    )

    print(env_enum.render())


def demo_import_manager() -> None:
    """Demonstrate the ImportBuilder."""
    print("=" * 60)
    print("IMPORT BUILDER DEMO")
    print("=" * 60)

    imports = ImportBuilder()

    # Add future imports
    imports.add_import("__future__")

    # Add standard library imports
    imports.add_from_import("typing", ["Any", "Optional", "Dict"])
    imports.add_from_import("dataclasses", "dataclass")
    imports.add_from_import("datetime", "datetime")
    imports.add_import("json")

    # Add third-party imports
    imports.add_from_import("pydantic", ["BaseModel", "Field"], is_third_party=True)
    imports.add_import("pandas", is_third_party=True)

    # Add local imports
    imports.add_from_import(".models", ["User", "Post"], is_local=True)
    imports.add_from_import("..utils", "logger", is_local=True)

    print(imports.render())


def demo_full_file() -> None:
    """Demonstrate building a complete Python file."""
    print("=" * 60)
    print("COMPLETE FILE BUILDER DEMO")
    print("=" * 60)

    builder = FileBuilder()
    builder.header.add('"""User management module."""')
    builder.imports.add("from __future__ import annotations")
    builder.imports.add("from dataclasses import dataclass")
    builder.imports.add("from datetime import datetime")
    builder.imports.add("from typing import Any")

    status_enum = EnumBuilder(name="UserStatus", members=["ACTIVE", "INACTIVE", "BANNED"], base_class="Enum")
    builder.add(status_enum.render())

    user_class = ClassBuilder(
        name="User",
        decorators=[Decorator("dataclass")],
        attributes=[
            Attribute("id", "int"),
            Attribute("name", "str"),
            Attribute("status", "UserStatus", default="UserStatus.ACTIVE"),
        ],
    )
    builder.add(user_class.render())

    print(builder.render(add_section_separators=True))


def demo_footer_helpers() -> None:
    """Demonstrate footer generation helpers."""
    print("=" * 60)
    print("FOOTER HELPERS DEMO")
    print("=" * 60)

    # Demo 1: __all__ export generation
    print("# Example 1: Simple __all__ export")
    exports: str = generate_all_export(["User", "Post", "Comment"])
    print(exports)

    # Demo 2: if __name__ == "__main__": with strings
    print("# Example 2: Main block with simple strings")
    main_block: str = generate_main_block(
        ["config = load_config()", "app = create_app(config)", "app.run()"],
        include_docstring=True,
    )
    print(main_block)

    # Demo 3: if __name__ == "__main__": with CodeBuilder objects
    print("# Example 3: Main block with CodeBuilder objects")
    setup_func = FunctionBuilder(
        name="setup",
        args="",
        returns="None",
        body='print("Setting up...")',
    )

    main_block_with_builders = generate_main_block(
        [
            setup_func,  # CodeBuilder object!
            "",
            "setup()",
            'print("Running main logic...")',
        ],
        include_docstring=True,
    )
    print(main_block_with_builders)


def main() -> None:
    """Run all demos."""
    demo_dataclass()
    demo_pydantic()
    demo_enum()
    demo_import_manager()
    demo_full_file()
    demo_footer_helpers()

    print("=" * 60)
    print("✨ These builders are ready to move to funcy-bear!")
    print("   They're completely decoupled from PyDB.")
    print("=" * 60)


if __name__ == "__main__":
    main()
