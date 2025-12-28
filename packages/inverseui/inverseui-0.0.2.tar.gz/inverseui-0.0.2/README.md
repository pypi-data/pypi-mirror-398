# InverseUI CLI

Local runtime for browser automation agents with automatic error recovery.

## Installation

```bash
pip install inverseui
```

Requires Python 3.10+ and Google Chrome.

## Quick Start

```bash
# 1. Login
inverseui login

# 2. Run a track
inverseui run <track_id>

# 3. Or run with auto-fix
inverseui fix <track_id>
```

## Commands

| Command | Description |
|---------|-------------|
| `inverseui login` | Authenticate with InverseUI |
| `inverseui logout` | Clear stored credentials |
| `inverseui run <track_id>` | Run a track once |
| `inverseui fix <track_id>` | Run with auto-fix loop |

## Options

```bash
-r, --max-retries    # default: 5
--production         # longer timeouts
```

## Key Features

- Preserves Chrome login sessions
- AI-powered auto-fix on failures

## Browser Profile

On first run, you'll be prompted to select which Chrome profile to use. InverseUI copies the selected profile to `~/.inverseui/chrome-data`, preserving your login sessions, cookies, and local storage.

### Profile Location

| OS | Source Profile | InverseUI Copy |
|----|----------------|----------------|
| macOS | `~/Library/Application Support/Google/Chrome` | `~/.inverseui/chrome-data` |
| Linux | `~/.config/google-chrome` | `~/.inverseui/chrome-data` |
| Windows | `%LOCALAPPDATA%\Google\Chrome\User Data` | `~/.inverseui/chrome-data` |

To reset the profile, delete `~/.inverseui/chrome-data` and run again.
