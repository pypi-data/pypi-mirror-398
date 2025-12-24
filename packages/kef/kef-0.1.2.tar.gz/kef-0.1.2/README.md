# kef

Hierarchical configuration management for Kaggle projects using OmegaConf.

## Overview

`kef` provides a unified interface for merging repository-wide base configurations with project-specific overrides. It is designed for monorepos or projects where multiple experiments share global infrastructure settings but require local hyperparameter variations.

## Installation

```bash
uv add kef
```

## Configuration Hierarchy

`kef` automatically discovers and merges configurations in the following priority (lowest to highest):

1. **Base Configuration**: `kef.yaml` or `kef.toml` located at the git repository root.
2. **Project Configuration**: `kef.yaml` or `kef.toml` found in the current directory or its parent hierarchy.

Project-level configurations override base configurations.

## API Usage

Access the merged configuration singleton:

```python
from kef import cfg

# Access via dot notation
print(cfg.ml.model.max_iter)

# Access via dictionary keys
print(cfg["mlflow"]["tracking_uri"])

# Convert to native dictionary
config_dict = cfg.to_dict()
```

If you need to reload the configuration (e.g., after changing directories programmatically):

```python
from kef import reload_config
cfg = reload_config()
```

## Command Line Interface

`kef` includes a CLI for inspecting the configuration applied in the current workspace.

### View Configuration

```bash
# Render the entire merged configuration with syntax highlighting
kef view

# View a specific section or key
kef view ml.feature_engineering

# View without resolving OmegaConf interpolations
kef view --no-resolve
```

### Discovery Info

Check which files are being used:

```bash
kef info
```

## Shell Completion

To enable tab completion for `kef` commands and options, add the following to your shell profile:

### Zsh
```zsh
eval "$(_KEF_COMPLETE=zsh_source kef)"
```

*Note: Once enabled, `kef view` supports dynamic tab-completion for your configuration keys (including dot notation).*

### Bash
```bash
eval "$(_KEF_COMPLETE=bash_source kef)"
```

### Fish
```fish
_KEF_COMPLETE=fish_source kef | source
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, development workflow, and semantic commit message conventions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
