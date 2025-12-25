# Dyngle

An experimental, lightweight, easily configurable workflow engine for automating development, operations, data processing, and content management tasks.

## Documentation

Complete documentation is available at **https://dyngle.steamwiz.io**

- **[Overview](https://dyngle.steamwiz.io/overview.html)** - Introduction and key features
- **[Installation](https://dyngle.steamwiz.io/installation.html)** - Setup instructions
- **[Getting Started](https://dyngle.steamwiz.io/getting-started.html)** - Your first operation
- **[Configuration](https://dyngle.steamwiz.io/configuration.html)** - Configuration files and imports
- **[Commands](https://dyngle.steamwiz.io/cli-commands.html)** - CLI command reference

### Core Concepts

- **[Operations](https://dyngle.steamwiz.io/operations.html)** - Defining and running operations
- **[Data and Templates](https://dyngle.steamwiz.io/data-and-templates.html)** - Working with data
- **[Expressions](https://dyngle.steamwiz.io/expressions.html)** - Python expressions in operations
- **[Data Flow](https://dyngle.steamwiz.io/data-flow.html)** - Data flow operators

### Advanced Features

- **[Sub-operations](https://dyngle.steamwiz.io/sub-operations.html)** - Composing operations
- **[Return Values](https://dyngle.steamwiz.io/return-values.html)** - Returning data from operations
- **[Display Options](https://dyngle.steamwiz.io/display-options.html)** - Controlling output
- **[Access Control](https://dyngle.steamwiz.io/access-control.html)** - Public vs private operations
- **[MCP Server](https://dyngle.steamwiz.io/mcp-server.html)** - AI assistant integration

### Reference

- **[Operation Lifecycle](https://dyngle.steamwiz.io/lifecycle.html)** - How operations execute
- **[Security](https://dyngle.steamwiz.io/security.html)** - Security considerations

## Quick Start

Install (macOS):

```bash
brew install python@3.11
python3.11 -m pip install pipx
pipx install dyngle
```

Create `.dyngle.yml`:

```yaml
dyngle:
  operations:
    hello:
      - echo "Hello world"
```

Run:

```bash
dyngle run hello
```

See [Getting Started](https://dyngle.steamwiz.io/getting-started.html) for more.

## Developer Documentation

For contributors and maintainers, see:

- **[README.md](README.md)** - Development setup and contribution guidelines
- **[VISION.md](VISION.md)** - Project vision and roadmap
