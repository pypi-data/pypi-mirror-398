<p align="center">
  <img src="https://raw.githubusercontent.com/Samet-MohamedAmin/tofu-tree/main/assets/logo.png" alt="tofu-tree logo" width="200">
</p>

<h1 align="center">tofu-tree</h1>

<p align="center">
  <strong>🌳 Simple tree visualization for Terraform/OpenTofu plan output</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/tofu-tree/"><img src="https://img.shields.io/pypi/v/tofu-tree?style=flat-square&color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/tofu-tree/"><img src="https://img.shields.io/pypi/pyversions/tofu-tree?style=flat-square" alt="Python versions"></a>
  <a href="https://github.com/yourusername/tofu-tree/actions"><img src="https://img.shields.io/github/actions/workflow/status/yourusername/tofu-tree/ci.yml?style=flat-square" alt="CI status"></a>
  <a href="https://codecov.io/gh/yourusername/tofu-tree"><img src="https://img.shields.io/codecov/c/github/yourusername/tofu-tree?style=flat-square" alt="Coverage"></a>
  <a href="https://github.com/yourusername/tofu-tree/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/tofu-tree?style=flat-square" alt="License"></a>
</p>

<p align="center">
  Transform your <code>terraform plan</code> or <code>tofu plan</code> output into an easy-to-read hierarchical tree structure with color-coded change indicators.
</p>

---

## ✨ Features

- 🌳 **Beautiful Tree Output** — Visualize your Terraform plan as a clean, hierarchical tree
- 🎨 **Color-Coded Symbols** — Instantly see what's being created (+), destroyed (-), or modified (~)
- 🔄 **Auto-Detection** — Automatically finds and runs `tofu` or `terraform` in your PATH
- 📊 **Summary Statistics** — Quick overview of total changes at a glance
- 📦 **Zero Dependencies** — Pure Python, works out of the box
- 🖥️ **Cross-Platform** — Works on Linux, macOS, and Windows

## 📦 Installation

```bash
pip install tofu-tree
```

Or with [pipx](https://pipx.pypa.io/) for isolated installation:

```bash
pipx install tofu-tree
```

## 🚀 Quick Start

### Run in a Terraform/OpenTofu directory

```bash
cd your-terraform-project
tofu-tree
```

### Pipe plan output directly

```bash
tofu plan -concise -no-color | tofu-tree --input
```

### Specify a directory

```bash
tofu-tree /path/to/terraform/project
```

## 📖 Usage

```
usage: tofu-tree [-h] [-V] [--no-color] [--input] [path]

Parse Terraform/OpenTofu plan output and display as a beautiful tree

positional arguments:
  path           Path to the Terraform/OpenTofu directory (default: current directory)

options:
  -h, --help     show this help message and exit
  -V, --version  show program's version number and exit
  --no-color     Disable ANSI color output for symbols (color is enabled by default)
  --input, -i    Read plan output from stdin instead of running terraform/tofu plan
```

## 🎬 Example Output

```
+ local_file
│  ├── + config_files
│  │   ├── + config_files: app
│  │   ├── + config_files: cache
│  │   └── + config_files: db
│  │
│  ├── + nested_docs
│  │   ├── + nested_docs: changelog
│  │   ├── + nested_docs: license
│  │   └── + nested_docs: readme
│  │
│  └── + scripts
│      ├── + scripts: backup
│      └── + scripts: deploy
│
+ module.nested_module
│  └── + local_file
│      ├── + health_checks
│      │   ├── + health_checks: api
│      │   ├── + health_checks: web
│      │   └── + health_checks: worker
│      │
│      ├── + service_configs
│      │   ├── + service_configs: api
│      │   ├── + service_configs: web
│      │   └── + service_configs: worker
│      │
│      └── + service_deployments
│          ├── + service_deployments: api
│          ├── + service_deployments: web
│          └── + service_deployments: worker
│

+ 20 resources to be created
-  0 resources to be destroyed
~  0 resources to be replaced/updated
```

### Symbol Legend

| Symbol | Color  | Meaning |
|--------|--------|---------|
| `+`    | 🟢 Green  | Resource will be created |
| `-`    | 🔴 Red    | Resource will be destroyed |
| `~`    | 🟡 Yellow | Resource will be modified/replaced |

## 🔧 How It Works

1. **Parse** — Reads Terraform/OpenTofu plan output (concise format with `-concise` flag)
2. **Build** — Constructs a hierarchical graph from resource addresses
3. **Display** — Renders the graph as a tree with proper connectors (├──, └──)
4. **Summarize** — Shows counts of created, destroyed, and modified resources

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

```bash
# Clone the repository
git clone https://github.com/yourusername/tofu-tree.git
cd tofu-tree

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src tests

# Run type checker
mypy src/tofu_tree
```

## 📄 License

Hippocratic License 3.0 — see [LICENSE](LICENSE) for details.

This license includes ethical restrictions, including a prohibition on using this software to train artificial intelligence systems without explicit permission.

## 🙏 Acknowledgments

Inspired by the Unix `tree` command and the need for better Terraform plan visualization.

---

<p align="center">
  Vibe Coded with ❤️ for the Infrastructure as Code community
</p>
