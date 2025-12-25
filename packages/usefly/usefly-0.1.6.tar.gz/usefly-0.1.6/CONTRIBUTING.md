# Contributing to Usefly

Contributions are welcome! Please feel free to submit a Pull Request.

## Prerequisites

- Python 3.12+
- Node.js 20+ with pnpm (only if modifying the UI)

## Development Setup

```bash
# Clone the repository
git clone https://github.com/dudany/usefly.git
cd usefly

# Create and activate virtual environment (requires Python 3.12+)
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install browser
playwright install chromium

# Start the server with auto-reload
usefly --reload
```

## Architecture

```
usefly/
├── src/                  # Python backend (FastAPI)
│   ├── cli.py           # CLI entry point
│   ├── server.py        # FastAPI application
│   ├── database.py      # SQLite + SQLAlchemy
│   ├── models/          # Data models & schemas
│   ├── handlers/        # Business logic
│   ├── routers/         # API endpoints
│   ├── prompts/         # AI prompt templates
│   └── static/          # Built UI files (gitignored, built at release/deploy)
├── ui/                   # Next.js frontend source
│   ├── app/             # Pages & routes
│   ├── components/      # React components
│   └── lib/             # Utilities
├── tests/               # Test suite
├── Dockerfile           # Container build
└── pyproject.toml       # Package configuration
```

## Tech Stack

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [SQLite](https://sqlite.org/) - In process db
- [browser-use](https://github.com/browser-use/browser-use) - AI browser automation
- [LangChain](https://www.langchain.com/) - LLM orchestration

**Frontend:**
- [Next.js](https://nextjs.org/) 16 - React framework
- [Tailwind CSS](https://tailwindcss.com/) - Styling
- [shadcn/ui](https://ui.shadcn.com/) - UI components
- [Recharts](https://recharts.org/) - Data visualization

## Running Tests

```bash
source .venv/bin/activate
pytest
```

## Rebuilding the UI

If you make changes to the frontend (`ui/` directory), you need to rebuild:

```bash
cd ui && pnpm install && pnpm build
```

This outputs static files to `src/static/` which are served by FastAPI. **Note:** The built files are NOT committed to the repo, so you must build them locally to run the server.

## Development Workflow

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. **If you modified `ui/`**: Rebuild with `cd ui && pnpm build`
5. Run tests: `pytest`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Releasing

Releases are automated via GitHub Actions. To create a new release:

1. Merge your changes to `main`
2. Create and push a version tag:
   ```bash
   git checkout main
   git pull
   git tag v0.1.0
   git push origin v0.1.0
   ```

This triggers two workflows:
- **Release** - Builds and publishes the package to PyPI
- **Docker** - Builds and pushes the Docker image to `ghcr.io/dudany/usefly`

Tags must follow semver format: `v0.1.0`, `v1.0.0`, etc.
