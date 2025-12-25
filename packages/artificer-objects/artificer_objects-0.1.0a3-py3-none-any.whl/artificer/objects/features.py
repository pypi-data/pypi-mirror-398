"""ObjectsFeature for Artificer CLI integration."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click
import questionary
from questionary import Style

from artificer.cli.feature import ArtificerFeature

from .base import Object, _deserialize_value, _serialize_value

if TYPE_CHECKING:
    from artificer.cli.config import ArtificerConfig

# Custom style for questionary prompts
_style = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:cyan"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
    ]
)


def _select_object_type(message: str = "Select object type:") -> str | None:
    """Show an interactive object type selector."""
    types = Object.get_registered_types()

    if not types:
        click.echo("No object types registered.")
        return None

    if len(types) == 1:
        return types[0]

    choices = [questionary.Choice(title=t, value=t) for t in types]

    result: str | None = questionary.select(
        message,
        choices=choices,
        style=_style,
        use_shortcuts=False,
        use_indicator=True,
    ).ask()
    return result


def _select_object(
    type_name: str,
    message: str = "Select object:",
) -> str | None:
    """Show an interactive object selector for the given type."""
    instance = Object.get_instance(type_name)
    objects = instance.list_objects()

    if not objects:
        click.echo(f"No objects found in {type_name}.")
        return None

    choices = [questionary.Choice(title=name, value=name) for name in objects]

    result: str | None = questionary.select(
        message,
        choices=choices,
        style=_style,
        use_shortcuts=False,
        use_indicator=True,
    ).ask()
    return result


class ObjectsFeature(ArtificerFeature):
    """Feature providing CLI commands for object store management."""

    @classmethod
    def register(cls, cli: click.Group, config: "ArtificerConfig") -> None:
        """Register object commands with the CLI."""
        cls._import_object_entrypoint(config)

        @cli.group()
        def objects():
            """Manage object stores."""
            pass

        @objects.command(name="list")
        @click.argument("type_name", required=False)
        def list_cmd(type_name: str | None = None):
            """List objects. Shows type selector if multiple types registered."""
            if type_name is None:
                type_name = _select_object_type(message="Select type to list:")
                if type_name is None:
                    return

            try:
                instance = Object.get_instance(type_name)
                object_names = instance.list_objects()

                if not object_names:
                    click.echo(f"No objects in {type_name}.")
                    return

                click.echo(f"Objects in {type_name}:")
                for name in object_names:
                    click.echo(f"  - {name}")

            except KeyError as e:
                click.echo(f"Error: {e}", err=True)
                raise SystemExit(1)

        @objects.command(name="read")
        @click.argument("name", required=False)
        @click.option("--type", "type_name", help="Object type")
        def read_cmd(name: str | None = None, type_name: str | None = None):
            """Read an object. Opens selector if no name given."""
            if type_name is None:
                type_name = _select_object_type(message="Select object type:")
                if type_name is None:
                    return

            if name is None:
                name = _select_object(type_name, message="Select object to read:")
                if name is None:
                    return

            try:
                instance = Object.get_instance(type_name)
                result = instance.read(name)
                serialized = _serialize_value(result, instance.model)
                click.echo(json.dumps(serialized, indent=2))

            except KeyError as e:
                click.echo(f"Error: {e}", err=True)
                raise SystemExit(1)
            except Exception as e:
                click.echo(f"Error reading object: {e}", err=True)
                raise SystemExit(1)

        @objects.command(name="write")
        @click.argument("name")
        @click.argument("data", required=False)
        @click.option("--type", "type_name", help="Object type")
        @click.option(
            "--file",
            "file_path",
            type=click.Path(exists=True),
            help="Read data from JSON file",
        )
        def write_cmd(
            name: str,
            data: str | None = None,
            type_name: str | None = None,
            file_path: str | None = None,
        ):
            """Write an object. Accepts JSON data or --file path."""
            if type_name is None:
                type_name = _select_object_type(message="Select object type:")
                if type_name is None:
                    return

            if file_path:
                with open(file_path) as f:
                    data = f.read()
            elif data is None:
                click.echo("Error: Provide data as argument or use --file", err=True)
                raise SystemExit(1)

            try:
                instance = Object.get_instance(type_name)
                parsed = json.loads(data)
                model_instance = _deserialize_value(parsed, instance.model)
                instance.write(name, model_instance)
                click.echo(f"Successfully wrote '{name}' to {type_name}")

            except KeyError as e:
                click.echo(f"Error: {e}", err=True)
                raise SystemExit(1)
            except json.JSONDecodeError as e:
                click.echo(f"Invalid JSON: {e}", err=True)
                raise SystemExit(1)
            except Exception as e:
                click.echo(f"Error writing object: {e}", err=True)
                raise SystemExit(1)

        @objects.command(name="delete")
        @click.argument("name", required=False)
        @click.option("--type", "type_name", help="Object type")
        def delete_cmd(name: str | None = None, type_name: str | None = None):
            """Delete an object. Opens selector if no name given."""
            if type_name is None:
                type_name = _select_object_type(message="Select object type:")
                if type_name is None:
                    return

            if name is None:
                name = _select_object(type_name, message="Select object to delete:")
                if name is None:
                    return

            try:
                instance = Object.get_instance(type_name)
                instance.delete(name)
                click.echo(f"Successfully deleted '{name}' from {type_name}")

            except KeyError as e:
                click.echo(f"Error: {e}", err=True)
                raise SystemExit(1)
            except Exception as e:
                click.echo(f"Error deleting object: {e}", err=True)
                raise SystemExit(1)

        @objects.command(name="exists")
        @click.argument("name")
        @click.option("--type", "type_name", help="Object type")
        def exists_cmd(name: str, type_name: str | None = None):
            """Check if an object exists."""
            if type_name is None:
                type_name = _select_object_type(message="Select object type:")
                if type_name is None:
                    return

            try:
                instance = Object.get_instance(type_name)
                exists = instance.exists(name)
                if exists:
                    click.echo(f"'{name}' exists in {type_name}")
                else:
                    click.echo(f"'{name}' does not exist in {type_name}")
                    raise SystemExit(1)

            except KeyError as e:
                click.echo(f"Error: {e}", err=True)
                raise SystemExit(1)

        @objects.command(name="types")
        def types_cmd():
            """List registered object types."""
            types = Object.get_registered_types()

            if not types:
                click.echo("No object types registered.")
                return

            click.echo("Registered object types:")
            for t in types:
                instance = Object.get_instance(t)
                click.echo(f"  - {t}: {instance.model.__name__}")

    @classmethod
    def _import_object_entrypoint(cls, config: "ArtificerConfig") -> None:
        """Import object modules to register object types."""
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        pyproject_path = Path.cwd() / "pyproject.toml"
        if not pyproject_path.exists():
            return

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        objects_config = (
            pyproject.get("tool", {}).get("artificer", {}).get("objects", {})
        )

        # Add cwd to path so local object modules can be imported
        cwd = str(Path.cwd())
        if cwd not in sys.path:
            sys.path.insert(0, cwd)

        object_modules: list[str] = objects_config.get("modules", [])
        for module_path in object_modules:
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                click.echo(
                    f"Warning: Could not import object module '{module_path}': {e}",
                    err=True,
                )
