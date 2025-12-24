# Project Structure for mcp-builder

```bash
mcp-builder/
├── src/
│   └── mcp_builder/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py                 # Main CLI interface
│       ├── generator.py           # Project generation logic
│       ├── validators.py          # Input validation
│       ├── config.py              # Configuration models
│       ├── templates/             # Jinja2 templates
│       │   ├── base/
│       │   │   ├── pyproject.toml.j2
│       │   │   ├── README.md.j2
│       │   │   ├── .gitignore.j2
│       │   │   ├── .pre-commit-config.yaml.j2
│       │   │   └── Dockerfile.j2
│       │   ├── src/
│       │   │   ├── __init__.py.j2
│       │   │   ├── server.py.j2
│       │   │   ├── config.py.j2
│       │   │   └── main.py.j2
│       │   ├── tools/
│       │   │   ├── genai_tools.py.j2
│       │   │   ├── rag_tools.py.j2
│       │   │   ├── web_tools.py.j2
│       │   │   └── data_tools.py.j2
│       │   ├── github/
│       │   │   └── workflows/
│       │   │       ├── ci.yml.j2
│       │   │       └── release.yml.j2
│       │   └── tests/
│       │       ├── conftest.py.j2
│       │       └── test_server.py.j2
│       └── utils/
│           ├── __init__.py
│           ├── logger.py
│           └── file_ops.py
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_generator.py
│   └── test_validators.py
├── docs/
│   ├── index.md
│   ├── usage.md
│   └── contributing.md
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
└── .gitignore
```

# CLI MODULE EXPENDED

```bash
src/mcp_builder/
├── cli/
│   ├── __init__.py         # CLI package exports
│   ├── main.py             # Main CLI app
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── create.py       # Create command
│   │   ├── init.py         # Init command
│   │   ├── validate.py     # Validate command
│   │   ├── list.py         # List templates command
│   │   └── example.py      # Example projects command
│   ├── prompts.py          # Interactive prompts
│   └── utils.py            # CLI utilities
├── config.py
├── generator.py
├── validators.py
└── exceptions.py
```