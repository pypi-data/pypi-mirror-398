"""CLI for kef configuration manager."""

from pathlib import Path

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.tree import Tree

from .config import ConfigManager

console = Console()


def _get_config_keys(ctx, param, incomplete):
    """Callback for shell completion of config keys."""
    try:
        from omegaconf import DictConfig, ListConfig

        manager = ConfigManager()
        config = manager.load()

        # If incomplete contains dots, we navigate to that level
        parts = incomplete.split(".")
        current = config
        prefix = ""

        # Navigate to the last full part
        for i in range(len(parts) - 1):
            if isinstance(current, DictConfig) and parts[i] in current:
                current = current[parts[i]]
                prefix += parts[i] + "."
            else:
                # Can't navigate further
                return []

        last_part = parts[-1]
        matches = []

        if isinstance(current, DictConfig):
            for k in current.keys():
                key_str = str(k)
                if key_str.startswith(last_part):
                    # Check if this node has children to decide if we add a dot
                    val = current[k]
                    from omegaconf import DictConfig

                    if isinstance(val, DictConfig) and len(val) > 0:
                        matches.append(prefix + key_str + ".")
                    else:
                        matches.append(prefix + key_str)
        elif isinstance(current, ListConfig):
            # For lists, we could suggest indices, but maybe just skip
            pass
        return matches
    except Exception:
        return []


@click.group()
@click.version_option()
def cli():
    """kef - Kaggle Efficient Framework configuration manager."""
    pass


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell: str):
    """Generate completion script for the specified shell.

    To enable completion, add the following to your shell profile:

    (zsh)  eval "$(_KEF_COMPLETE=zsh_source kef)"

    (bash) eval "$(_KEF_COMPLETE=bash_source kef)"

    (fish) _KEF_COMPLETE=fish_source kef | source
    """
    if shell == "fish":
        click.echo("_KEF_COMPLETE=fish_source kef | source")
    else:
        click.echo(f'eval "$(_{"KEF"}_COMPLETE={shell}_source kef)"')


@cli.command()
@click.argument("key", required=False, shell_complete=_get_config_keys)
@click.option("--resolve/--no-resolve", default=True, help="Resolve OmegaConf interpolations.")
def view(key: str | None, resolve: bool):
    """View the merged configuration.

    If KEY is provided, only that part of the configuration is shown.
    Supports dot notation (e.g., unity_catalog.server).
    """
    try:
        if key:
            # Clean up the key (remove trailing spaces from Zsh, and accidental trailing dots)
            key = key.strip().rstrip(".")

        manager = ConfigManager()
        manager.load()

        if key:
            value = manager.get(key)
            if value is None:
                console.print(f"[red]Key '{key}' not found in configuration.[/red]")
                return

            # If it's a sub-config, convert to YAML
            from omegaconf import DictConfig, OmegaConf

            if isinstance(value, DictConfig):
                content = OmegaConf.to_yaml(value, resolve=resolve)
                syntax = Syntax(content, "yaml", theme="monokai", background_color="default")
                console.print(syntax)
            else:
                console.print(value)
        else:
            content = manager.to_yaml()
            syntax = Syntax(content, "yaml", theme="monokai", background_color="default")
            console.print(syntax)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
    except Exception as e:
        console.print(f"[red]An unexpected error occurred:[/red] {e}")


@cli.command()
@click.option("--prefix", default="", help="Prefix for exported variables.")
@click.option("--key", help="Only dump a specific branch of the configuration.")
def dump(prefix: str, key: str | None):
    """Dump the entire configuration as flattened KEY=VALUE pairs.

    Useful for sourcing in shell scripts or Makefiles.
    """
    try:
        manager = ConfigManager()
        manager.load()

        if key:
            config_node = manager.get(key)
            if config_node is None:
                return
            from omegaconf import DictConfig

            if not isinstance(config_node, (DictConfig, dict)):
                # If it's a leaf, just print it in a safe way
                key_name = key.split(".")[-1].upper()
                click.echo(f"{prefix}{key_name}={config_node}")
                return
            config_dict = manager.to_dict_node(config_node)
        else:
            config_dict = manager.to_dict()

        def flatten(d, parent_key=""):
            items = []
            for k, v in d.items():
                # Convert key to uppercase and replace dots with underscores
                new_key = f"{parent_key}_{k}".upper() if parent_key else k.upper()
                if isinstance(v, dict):
                    items.extend(flatten(v, new_key))
                elif isinstance(v, list):
                    # Join lists with spaces for Makefile/shell compatibility
                    val = " ".join(str(i) for i in v)
                    items.append(f"{prefix}{new_key}={val}")
                else:
                    # Sanitize value for shell/Makefile
                    # Ensure None is empty or represented cleanly
                    val = "" if v is None else v
                    items.append(f"{prefix}{new_key}={val}")
            return items

        for line in flatten(config_dict):
            click.echo(line)

    except Exception as e:
        click.echo(f"# Error dumping config: {e}", err=True)


@cli.command()
def info():
    """Show information about the configuration sources."""
    try:
        manager = ConfigManager()
        manager.discover()

        tree = Tree("[bold blue]kef Configuration Info[/bold blue]")

        tree.add(f"Working Directory: [cyan]{Path.cwd()}[/cyan]")

        if manager.base_config_path:
            tree.add(f"Base Config (Repo Root): [green]{manager.base_config_path}[/green]")
        else:
            tree.add("Base Config (Repo Root): [red]Not found[/red]")

        if manager.project_config_path:
            tree.add(f"Project Config: [green]{manager.project_config_path}[/green]")
        else:
            tree.add("Project Config: [red]Not found[/red]")

        console.print(tree)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    cli()
