# Aii — AI-Powered Terminal Assistant

**Aii** (pronounced *"eye"*) is your intelligent command-line companion that brings AI directly into your terminal through natural language.

**One CLI. Comprehensive AI capabilities. 5 LLM Providers.**

Stop context-switching between your terminal and ChatGPT. Get instant AI assistance for git commits, code generation, translation, content writing, shell automation, and analysis—all without leaving your terminal.

[![PyPI version](https://badge.fury.io/py/aiiware-cli.svg)](https://pypi.org/project/aiiware-cli/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **What's New in v0.8.1:** Enhanced security with localhost-only server binding by default. Internal code improvements for better maintainability. [See CHANGELOG](CHANGELOG.md)

---

## ✨ What Can Aii Do?

```bash
# 🎯 Choose Your Model (v0.8.0)
aii --model gpt-4.1-mini translate "hello" to french
aii --model claude-sonnet-4.5 "explain quantum computing"
aii --model kimi-k2-thinking "solve this complex problem"
# → Try different models without changing config

# 🔀 Smart Git Workflows
aii run git commit                    # → Analyzes changes, generates conventional commit
aii run git pr                        # → Creates PR with smart description

# 💻 Code Generation
aii create a python function to validate emails
# → Complete function with typing, docstrings, tests

# 🌍 Translation (100+ languages)
aii translate "hello world" to spanish
# → hola mundo

# 📝 Content Writing
aii prompt use tweet-launch "launching Aii CLI v0.6.2"
# → Engaging product launch tweet ready to post

aii prompt use daily-standup "yesterday: fixed bugs, today: features, blockers: none"
# → Professional standup update formatted

# 🐚 Shell Automation (Safe by Default)
aii find files larger than 100MB
# → Shows command + explanation → Asks confirmation

# 🧠 Analysis & Research
aii explain "how do transformers work"
# → Clear explanation with web research

aii "summarize the README.md file"
# → Key points extracted from file
```

---

## 🚀 Quick Start

### Installation

```bash
# With uv (recommended)
uv tool install aiiware-cli

# Or with pip
pip install aiiware-cli

# Verify
aii --version
```

### Setup (2 minutes)

```bash
# Interactive setup wizard
aii config init

# Choose your LLM provider:
#  1. Anthropic Claude (Sonnet, Opus, Haiku)
#  2. OpenAI GPT (GPT-4o, GPT-4 Turbo, GPT-4o-mini)
#  3. Google Gemini (2.5 Flash, 2.0 Flash, Pro)
#  4. Moonshot AI (Kimi K2, up to 256K context)
#  5. DeepSeek AI (Ultra-low-cost, 10x cheaper than GPT-4)

# Verify
aii doctor
```

**Get API Keys:**
- **Claude**: [console.anthropic.com](https://console.anthropic.com/)
- **OpenAI**: [platform.openai.com](https://platform.openai.com/)
- **Gemini**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Moonshot**: [platform.moonshot.ai](https://platform.moonshot.ai/)
- **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com/)

### First Command

```bash
aii translate "hello" to french
# → bonjour

aii run git commit  # (after git add .)
# → Smart commit message generated

aii                 # Interactive mode
```

---

## 📋 Key Features

### 🎯 Natural Language Interface
- **39 AI Functions** across 8 categories (git, code, shell, content, translation, analysis)
- **25 Ready-to-Use Prompts** (business, social, development, marketing, productivity)
- **Multiple LLM Providers**: Claude, GPT-4, Gemini (switch anytime)
- **Smart Confirmations**: Asks only when needed (dangerous operations)

### 📚 Prompt Library (v0.6.1+)

Generate professional content in seconds:

```bash
# Discover prompts
aii prompt list                    # Browse all 25 prompts
aii prompt list --category social  # Filter by category
aii prompt show tweet-launch       # View details

# Use prompts
aii prompt use pr-description "add user authentication with JWT"
aii prompt use email-professional "decline meeting, suggest async update"
aii prompt use blog-intro "Getting Started with AI CLI tools"

# Create custom prompts (v0.6.2)
aii prompt create
# → Interactive wizard with beautiful YAML formatting
# → Unlimited custom categories
# → Inline examples at every step
```

**25 Prompts by Category:**
- **Business** (4): Daily standups, incident reports, meeting notes, professional emails
- **Content** (4): Blog outlines/intros, newsletters, landing pages
- **Development** (7): PR descriptions, release notes, commits, code reviews, bug reports, API/architecture docs
- **Social** (5): Tweet launches, LinkedIn posts, Instagram captions, thread builders
- **Marketing** (2): Product announcements, feature highlights
- **Productivity** (3): Task lists, brainstorming, definitions

### 🛠️ Developer Productivity
- **Git Integration**: Smart commits, PR creation, branch naming
- **Code Generation**: Language-agnostic with best practices
- **Shell Safety**: Previews commands before execution (v0.6.2 improved)
- **MCP Support**: Extend with Model Context Protocol servers (GitHub, filesystem, etc.)

### ⚙️ Platform Features
- **Unified Server**: One AI instance shared across terminal windows and VSCode
- **Real-Time Streaming**: 60-80% faster perceived speed (token-by-token)
- **Cost Tracking**: Transparent pricing per request (`aii stats`)
- **Smart Output Modes**: CLEAN (just answer) / STANDARD (+ metrics) / THINKING (+ reasoning)
- **Interactive Mode**: Type `aii` for multi-turn conversations

---

## 💰 Pricing

Aii uses **your own API keys**—pay only for LLM usage. No subscriptions.

**Top 5 Cost-Efficient Models** (per 10k input + 5k output tokens):

| Provider | Model | Cost/10k Tokens | Notes |
|----------|-------|-----------------|-------|
| **Google** | `gemini-2.0-flash-lite-001` | **$0.0023** | Cheapest 🥇 |
| **Google** | `gemini-2.5-flash-lite` | **$0.0030** | Very efficient 🥈 |
| **Google** | `gemini-2.0-flash-001` | **$0.0030** | Fast 🥉 |
| **OpenAI** | `gpt-4o-mini` | $0.0045 | Recommended for most tasks ⭐ |
| **Anthropic** | `claude-haiku-4-5` | $0.0350 | Near-frontier quality ⭐ |

**Premium Models:**
- **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`): $0.1050 per 10k tokens - Best quality ⭐
- **GPT-4o** (`gpt-4o`): $0.1250 per 10k tokens
- **Claude Opus 4.1** (`claude-opus-4-1-20250805`): $0.5250 per 10k tokens - Most capable

**Track your usage:**
```bash
aii stats  # View function usage, token counts, and costs
```

See [full pricing table](https://github.com/aiiware/aii-cli/wiki/Pricing) for all 20+ models.

---

## 🔌 Using with VSCode

Install the [Aii VSCode Extension](https://marketplace.visualstudio.com/items?itemName=aiiware.aii) to use AI in your editor:

- **Code Generation** (`Cmd+Shift+G`)
- **Smart Git Commits** (`Cmd+Shift+C`)
- **Interactive Chat** (`Cmd+Shift+A`)
- **Code Explanation** & **Translation**

CLI and VSCode share the same AI server—seamlessly switch between terminal and editor.

**Server Management:**
```bash
aii serve start --daemon  # Start background server (binds to localhost by default)
aii serve status          # Check health
aii serve stop            # Stop server

# Optional: Bind to all interfaces for remote access
aii serve start --host 0.0.0.0
```

---

## 📚 Documentation

- **[CHANGELOG](CHANGELOG.md)** - Version history and release notes
- **[GitHub Wiki](https://github.com/aiiware/aii-cli/wiki)** - Full documentation (coming soon)
- **Command Help**: `aii --help` or `aii <command> --help`

**Common Commands:**
```bash
aii doctor               # Diagnose configuration issues
aii config init          # Re-run setup wizard
aii config provider      # Switch LLM provider
aii mcp catalog          # Browse available MCP servers
aii stats                # View usage analytics
```

---

## 🤝 Support

**Need Help?**
- 🩺 Run `aii doctor` to diagnose issues
- 📖 Check [CHANGELOG](CHANGELOG.md) for updates
- 💡 Report bugs or suggest features via GitHub issues

**Common Issues:**
- **"No LLM provider configured"** → Run `aii config init`
- **"API key invalid"** → Check key at provider console, re-run `aii config provider`
- **"Command not found: aii"** → Add `~/.local/bin` to PATH (uv tool install location)
- **"Server started but not responding"** → System HTTP proxy is interfering with localhost connections (fixed in v0.9.4). If using older version, disable proxy: `export NO_PROXY="localhost,127.0.0.1"`

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **PyPI**: <https://pypi.org/project/aiiware-cli/>
- **VSCode Extension**: <https://marketplace.visualstudio.com/items?itemName=aiiware.aii>
- **Twitter**: [@aii_dev](https://x.com/aii_dev)

---

**Made with ❤️ by the AiiWare team**

*Stay in your terminal. Get AI assistance. Maintain flow state.*
