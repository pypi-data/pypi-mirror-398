# porthog

A CLI and TUI tool to find and kill dev servers hogging your ports.

Ever run `npm start` only to find port 3000 is already in use? porthog helps you quickly identify what's running on your dev ports and kill it with a single command.

## Features

- **Interactive TUI** - Browse all dev server ports in a beautiful terminal UI
- **CLI commands** - Quick one-liners for scripting and fast actions
- **Smart detection** - Automatically identifies Node, Python, Java, Ruby, Go, Rust, PHP, and .NET processes
- **Framework recognition** - Detects Next.js, Vite, Django, FastAPI, Rails, and 20+ other frameworks
- **Dev port focused** - Filters to common dev ports (3000-9999) by default
- **Cross-platform** - Works on macOS and Linux

## Installation

```bash
pip install porthog
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install porthog
```

## Usage

### Interactive TUI

Simply run `porthog` to launch the interactive terminal UI:

```bash
porthog
```

**Keyboard shortcuts:**
- `k` - Kill selected process (graceful)
- `K` - Force kill selected process
- `r` - Refresh the list
- `a` - Toggle between dev ports and all ports
- `q` / `Ctrl+C` - Quit

### CLI Commands

**List dev server ports:**

```bash
porthog ls
```

**List all listening ports:**

```bash
porthog ls --all
```

**Get info about a specific port:**

```bash
porthog info 3000
```

**Kill a process on a port:**

```bash
porthog kill 3000
```

**Kill multiple ports:**

```bash
porthog kill 3000 8080 5173
```

**Force kill (SIGKILL):**

```bash
porthog kill 3000 --force
```

**Kill all dev servers (use with caution!):**

```bash
porthog kill-all
```

**Skip confirmation prompts:**

```bash
porthog kill 3000 --yes
```

## Dev Port Ranges

By default, porthog focuses on common development server ports:

- **3000-3999** - React, Next.js, Rails, Express
- **4000-4999** - Phoenix, Gatsby, Remix
- **5000-5999** - Flask, Vite, SvelteKit
- **6000-6999** - Various dev tools
- **8000-8999** - Django, FastAPI, Spring Boot
- **9000-9999** - PHP, SonarQube, various tools

Use `--all` or press `a` in the TUI to see all listening ports.

## Detected Frameworks

porthog recognizes these frameworks and displays friendly names:

| Framework | Process Type |
|-----------|-------------|
| Next.js, Vite, Webpack, Vue CLI, Angular, Nuxt, Gatsby, Remix, Astro, SvelteKit | Node |
| Django, Flask, FastAPI, Uvicorn, Gunicorn | Python |
| Spring Boot | Java |
| Rails | Ruby |
| Phoenix | Elixir |
| Hugo, Jekyll | Static |

## Requirements

- Python 3.10+
- macOS or Linux

## License

MIT License - see [LICENSE](LICENSE) for details.
