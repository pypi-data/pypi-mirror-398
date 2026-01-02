# AttackIQ Platform API

> ⚠️ **Beta** - Under active development. APIs subject to change. Feedback: rajesh.sharma@attackiq.com | Access: Request invite to AttackIQ GitHub.

Tools for interacting with the AttackIQ Platform API:
- **Python SDK** (`aiq-platform-api`) - Async library for Python applications
- **CLI** (`aiq`) - Command-line interface

---

## Python SDK

Install from PyPI:

```sh
pip install aiq-platform-api
```

### Usage

```python
import asyncio
from aiq_platform_api import AttackIQClient, Scenarios, Assets

async def main():
    async with AttackIQClient(
        "https://your-platform.attackiq.com",
        "your-api-token"
    ) as client:
        # Search scenarios
        result = await Scenarios.search_scenarios(client, query="powershell", limit=10)
        print(f"Found {result['count']} scenarios")

        # List assets
        async for asset in Assets.get_assets(client, limit=5):
            print(asset["hostname"])

asyncio.run(main())
```

---

## Configuration

Both the SDK and CLI require these environment variables:

```sh
export ATTACKIQ_PLATFORM_URL="https://your-platform.attackiq.com"
export ATTACKIQ_PLATFORM_API_TOKEN="your-api-token"
```

Or create a `.env` file in your working directory (auto-loaded).

---

## CLI

### Quick Install (Recommended)

#### Linux / macOS

```sh
GITHUB_TOKEN="your_token" sh -c 'curl -fsSL -H "Authorization: token $GITHUB_TOKEN" \
  https://raw.githubusercontent.com/AttackIQ/aiq-platform-api/main/install.sh | sh'
```

**Add to PATH** (first time only):
```sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc  # or ~/.bashrc
```

Auto-detects OS/arch, installs to `~/.local/bin` (no sudo).

#### Windows (Native)

**PowerShell installer:**
```powershell
$env:GITHUB_TOKEN = "your_token"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/AttackIQ/aiq-platform-api/main/install.ps1" -Headers @{Authorization="token $env:GITHUB_TOKEN"} -OutFile "$env:TEMP\install.ps1"
powershell -ExecutionPolicy Bypass -File "$env:TEMP\install.ps1"
```

Installs to `%LOCALAPPDATA%\Programs\aiq` and adds to PATH automatically.

### Usage

```sh
# List available commands
aiq --help

# List assessments
aiq assessments list

# Search assets
aiq assets search --query "hostname"

# Get scenario details
aiq scenarios get --scenario-id "abc123"
```

### Shell Completion

The CLI supports shell completion for bash, zsh, fish, and PowerShell.

#### Bash

**Current session:**
```sh
source <(aiq completion bash)
```

**Permanent installation:**
```sh
# Linux
aiq completion bash | sudo tee /etc/bash_completion.d/aiq

# macOS
aiq completion bash > $(brew --prefix)/etc/bash_completion.d/aiq
```

#### Zsh

**Current session:**
```sh
source <(aiq completion zsh)
```

**Permanent installation:**
```sh
# Add to ~/.zshrc
echo "source <(aiq completion zsh)" >> ~/.zshrc

# Or install to completions directory
aiq completion zsh > "${fpath[1]}/_aiq"
```

#### Fish

**Permanent installation:**
```sh
aiq completion fish | source

# Or save to completions directory
aiq completion fish > ~/.config/fish/completions/aiq.fish
```

#### PowerShell

**Current session:**
```powershell
aiq completion powershell | Out-String | Invoke-Expression
```

**Permanent installation:**
Add the following to your PowerShell profile:
```powershell
aiq completion powershell | Out-String | Invoke-Expression
```

## Contributing

We welcome feedback and contributions! For detailed contribution guidelines, please see [CONTRIBUTING.md](CONTRIBUTING.md).

Quick ways to contribute:
- Open issues for bugs or feature requests
- Submit pull requests
- Provide feedback on the API design

## License

MIT License - See LICENSE file for details