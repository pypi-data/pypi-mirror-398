# Usefly

> Find UX friction before your users do.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/dudany/usefly/actions/workflows/ci.yml/badge.svg)](https://github.com/dudany/usefly/actions/workflows/ci.yml)

**AI-powered UX testing platform.** Deploy browser agents to simulate real user journeys on your web app and identify friction points, broken flows, and usability issues.

<p align="center">
  <img src="https://raw.githubusercontent.com/dudany/usefly/main/ui/public/usefly-logo.png" alt="Usefly Logo" width="120">
</p>

## What It Does

Usefly uses AI browser agents to test your application like a real user would. Instead of writing manual test scripts, you describe what your app does and Usefly generates realistic user tasks, executes them with AI-controlled browsers, and reports back with detailed analytics on where users struggle.

### Key Features

- **Automated Website Analysis** - AI crawls your site to understand its structure, navigation, and available features
- **Smart Task Generation** - Automatically generates realistic user journey tasks based on your site's capabilities
- **AI Browser Agents** - Executes tasks using vision-enabled AI agents that interact with your app like real users
- **Friction Detection** - Identifies UX issues, confusing flows, and broken functionality
- **Detailed Reports** - View step-by-step agent interactions, screenshots, and success/failure analysis

## Installation

Choose the method that works best for you:

### Option 1: Docker (Simplest)

No Python or Node.js required. Just Docker.

```bash
docker run -p 8080:8080 -v usefly-data:/app/src/data ghcr.io/dudany/usefly
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

> **Note:** The `-v usefly-data:/app/src/data` flag persists your data between container restarts.

### Option 2: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. Requires Python 3.12+.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install (requires Python 3.12+)
uv venv --python 3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install usefly

# Install browser for AI agents
playwright install chromium

# Start the server
usefly
```

### Option 3: Using pip

Requires Python 3.12+.

```bash
# Create virtual environment (requires Python 3.12+)
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install from PyPI
pip install usefly

# Install browser for AI agents
playwright install chromium

# Start the server
usefly
```

Open [http://localhost:8080](http://localhost:8080) in your browser.
 
> **Note for Contributors:** If you are installing from source (e.g. cloning the repo), you must build the UI manually. See [CONTRIBUTING.md](CONTRIBUTING.md).

### First Run Setup

1. Navigate to **Settings** in the sidebar
2. Configure your AI provider:
   - Select a provider (OpenAI, Claude, Groq, or Google)
   - Enter your API key
   - Choose a model (e.g., `claude-sonnet-4-20250514`, `claude-opus-4-20250514`, `claude-haiku-4-20250514`)
3. Optionally adjust:
   - **Max Steps** - Maximum actions per task (default: 30)
   - **Max Browser Workers** - Parallel browser count (default: 3)

## Usage

### 1. Create a Scenario

- Go to **Scenarios** → **New Scenario**
- Enter your target URL and a description of your application
- Click **Analyze Website** to let AI understand your site structure
- Generate tasks automatically or add custom ones

### 2. Run Tests

- Select a scenario and click **Run**
- Watch AI agents interact with your app in real-time
- Each agent executes assigned tasks and records every interaction

### 3. View Reports

- Go to **Reports** to see aggregated results
- Analyze friction points and failure patterns
- Review step-by-step screenshots and agent decisions
- Use **Replay** to watch recorded sessions

## CLI Reference

```bash
usefly                    # Start server on default port 8080
usefly --port 3000        # Use custom port
usefly --reload           # Enable auto-reload for development
usefly --help             # Show all options
```

## Supported AI Providers

| Provider |
|----------|
| OpenAI |
| Anthropic |
| Google |
| Groq |

## Troubleshooting

### Common Issues

**Browser agents fail to start**
- Check that your API key is correctly configured in Settings
- Ensure you have sufficient API credits

**UI shows blank page**
- Clear browser cache and refresh


## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [browser-use](https://github.com/browser-use/browser-use) - The excellent browser automation library powering our agents
- [LangChain](https://www.langchain.com/) - For seamless LLM integration
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
