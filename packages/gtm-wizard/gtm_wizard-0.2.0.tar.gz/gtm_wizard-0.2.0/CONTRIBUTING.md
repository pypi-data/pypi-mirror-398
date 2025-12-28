# Contributing to GTM Wizard

Thank you for your interest in contributing to GTM Wizard! This MCP server aims to package Go-To-Market Engineering expertise for AI agents.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/MathewJoseph1993/gtm-wizard.git
   cd gtm-wizard
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Verify setup:
   ```bash
   make all  # Runs format, lint, type-check, and tests
   ```

## Development Workflow

### Running Tests

```bash
make test        # Run all tests
make test-cov    # Run tests with coverage report
```

### Code Quality

```bash
make format      # Format code with ruff
make lint        # Run linter
make type-check  # Run mypy type checking
make all         # Run all checks
```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python -m gtm_wizard.server
```

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Use the provided issue templates
- Include clear steps to reproduce any bugs
- Describe expected vs actual behavior

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run `make all` to ensure all checks pass
5. Commit with clear, descriptive messages
6. Push to your fork
7. Open a Pull Request using the PR template

### What We're Looking For

**High-value contributions:**
- New GTM engineering tools (lead qualification, scoring, routing)
- Documentation improvements
- Bug fixes
- Real-world use case examples
- Test coverage improvements

**Areas of expertise we need:**
- Lead qualification and scoring
- Sales automation infrastructure
- CRM integration patterns
- Email deliverability
- Multi-channel orchestration

## Code Style

- We use `ruff` for linting and formatting
- We use `mypy` with strict mode for type checking
- Follow existing code patterns in the codebase
- Add type hints to all functions
- Keep functions focused and small

## Adding a New Tool

1. Add the tool definition in `src/gtm_wizard/server.py`
2. Add the handler in the `call_tool` function
3. Write tests in `tests/test_tools.py`
4. Update CHANGELOG.md
5. Update README.md if user-facing

## Questions?

Open an issue with your question and we'll help you get started.

---

*GTM Wizard is maintained by [Mathew Joseph](https://github.com/MathewJoseph1993)*
