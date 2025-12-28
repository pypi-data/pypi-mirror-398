# Change Log

All notable changes to Aii CLI will be documented in this file.

## [0.9.4] - 2025-11-19

### 🐛 Fixed

- **Proxy Interference** - Server health checks now bypass system proxy settings to prevent connection failures on localhost (fixes "Server started but not responding" error when HTTP proxy is configured)

## [0.9.3] - 2025-11-19

### ✨ New

- **Gemini 3 Pro Preview** - Google's newest flagship model for deep reasoning, coding, and multimodal tasks (released Nov 18, 2025)

### 🐛 Fixed

- **Config Commands** - Fixed `aii config provider` and `aii config model` commands that were broken after model registry refactor
- **Model Errors** - Removed invalid model from registry that caused 404 errors
- **Deprecated Models** - Outdated models automatically replaced with recommended alternatives (with warning)

## [0.9.2] - 2025-11-18

### ✨ New

- **Client Usage Tracking** - Track costs across CLI, VSCode, Chrome, and API interfaces (`aii stats cost --breakdown-by client`)

### 🐛 Fixed

- **Cost Accuracy** - Unified cost calculation to eliminate inconsistencies across clients

## [0.9.1] - 2025-11-14

### ✨ New

- **GPT-5.1 Support** - OpenAI's new flagship model for coding and agentic tasks with configurable reasoning

### 🐛 Fixed

- **Cost Analytics** - OpenAI model costs now display accurately in `aii stats models` and `aii stats cost`

## [0.9.0] - 2025-11-14

### 🎉 Model Intelligence & Analytics

Track LLM performance, optimize costs, and gain insights into your AI usage patterns.

**New Commands:**

```bash
# Model performance across all LLM providers
aii stats models                          # Success rates, latency, token usage
aii stats models --period 7d              # Last 7 days
aii stats models --category translation   # Filter by function type

# Cost analytics and optimization
aii stats cost                            # Total cost, projections, breakdowns
aii stats cost --show-trends              # Usage and cost growth rates
aii stats cost --show-top-spenders        # Identify expensive functions
```

**What You Get:**

- 📊 Success rates and latency metrics (TTFT, execution time) per model
- 💰 Cost breakdowns by model, category, and provider
- 📈 Usage trends with growth rate analysis
- 🎯 Top spender identification for cost optimization
- 🔌 REST API endpoints for programmatic access (`/api/stats/models`, `/api/stats/cost`)

## [0.8.1] - 2025-11-13

### 🔧 Internal Improvements

- **Code Quality** - Reduced code duplication through model inheritance (50% fewer field definitions)
- **Better Errors** - WebSocket requests now show clear, helpful error messages with suggestions
- **Security** - Server now binds to localhost (127.0.0.1) by default instead of all interfaces (0.0.0.0)
- **Header Support** - API accepts both `Aii-API-Key` (recommended) and `AII-API-Key` (legacy) for backward compatibility

## [0.8.0] - 2025-11-13

### ✨ New

- **Choose Your Model Per Request** - Use `--model` to try different AI models without changing config (`aii --model gpt-4.1-mini "your request"`)
- **Natural Language REST API** - REST API now supports natural language requests via `user_prompt` field, matching WebSocket pattern (`curl -d '{"user_prompt": "translate hello to spanish"}'`)

### 🐛 Fixed

- **Large Git Commits** - No more timeouts when committing changes with big diffs
- **Server Stability** - Better error handling prevents crashes
- **Content Filter Errors** - Clear user-friendly error messages when content is filtered by AI providers (OpenAI, Moonshot), with suggestions to try alternative models

## [0.7.2] - 2025-11-11

### 🐛 Fixed

- **Model Names** - Moonshot and DeepSeek models now display correctly in execution summary
- **Server Crash** - Fixed crash when API key is missing, now shows helpful setup instructions
- **Server Logs** - Cleaner logging during long-running requests
- **Output Format** - Execution summary shows provider and model names more clearly

## [0.7.1] - 2025-11-09

### ✨ New Providers

- **Moonshot AI (Kimi)** - Long-context models up to 256K tokens, starting at $0.20/1M tokens
- **DeepSeek AI** - Ultra-low-cost models at $0.14/1M tokens (10x cheaper than GPT-4)

### 🐛 Fixed

- Model names now display correctly without technical prefixes
- Cost tracking works for all new providers

## [0.7.0] - 2025-11-07

### 🎉 Major Release - Enhanced API Reliability

- **Structured Error Responses** - Machine-readable error codes for better client error handling (24 error codes across 7 categories)
- **Request ID Tracing** - Automatic request IDs in all API calls for debugging (`Aii-Request-ID` header)
- **CJK Token Fix** - Accurate token estimation for Chinese/Japanese/Korean text (99% improvement)
- **WebSocket Stability** - Improved connection handling with proper state checks

## [0.6.3] - 2025-10-26

### 🐛 Fixed

- **WebSocket Streaming** - Fixed token-by-token streaming for all clients (CLI, VSCode, Chrome Extension). Responses now stream character-by-character instead of appearing all at once.

## [0.6.2] - 2025-10-25

### ✨ New

- **Enhanced Prompt Wizard** - `aii prompt create` now generates clean YAML with proper formatting and supports unlimited custom categories

### 🐛 Fixed

- **Shell Commands** - Generated commands now preview before execution with full explanation
- **Custom Prompts** - Fixed prompt adherence and cost tracking in Execution Summary
- **Output Display** - Improved formatting and metadata display across all commands

## [0.6.1] - 2025-10-23

### ✨ New

- **Prompt Library** - 25 ready-to-use prompts across 6 categories: business, content, development, marketing, productivity, and social (`aii prompt list`, `aii prompt use <name>`). Generate professional content with natural language input.

## [0.6.0] - 2025-10-22

### ✨ Major Update

- **Unified Server Architecture** - Aii now runs as a background server, enabling multiple terminal windows and VSCode to share one AI instance. Includes server management commands (`aii serve start/stop/status`), auto-start for seamless experience, and `--host` parameter to connect to any server instance.

## [0.5.2] - 2025-10-16

### ✨ New

- **Claude Haiku 4.5 Support** - High-performance coding model with near-frontier quality at 75% lower cost than Sonnet

## [0.5.1] - 2025-10-14

### 🐛 Fixed

- **VSCode Token Display** - Fixed token usage and cost showing correctly in chat panel and status bar

## [0.5.0] - 2025-10-12

### ✨ New

- **HTTP API Server** - Run `aii serve` to enable VSCode and other IDE integrations
- **WebSocket Streaming** - Real-time responses for connected clients

## [0.4.13] - 2025-10-10

### 🐛 Fixed

- **Reliable Confirmations** - Fixed shell command confirmation flow (no more double prompts)
- **Accurate Token Tracking** - Session summaries now show correct token counts
- **Better Function Recognition** - Improved LLM understanding of your requests

## [0.4.12] - 2025-10-09

### ✨ New

- **API Server** - HTTP endpoints for integration with VSCode and other tools

## [0.4.11] - 2025-10-08

### ✨ Improved

- **Lazy MCP Connections** - Servers connect only when needed (faster startup)
- **Better Error Handling** - Clearer messages when MCP servers fail

## [0.4.10] - 2025-10-07

### ✨ New

- **Content Signatures** - Configurable signatures for AI-generated content (git commits, PRs, etc.)

## [0.4.9] - 2025-10-06

### ✨ New

- **Easy MCP Setup** - Browse and install MCP servers with one command (`aii mcp catalog`, `aii mcp install <server>`)
- **10+ Pre-configured Servers** - GitHub, Chrome DevTools, Postgres, and more

### 🐛 Fixed

- **MCP Token Tracking** - Operations now show correct token counts
- **Output Formatting** - Cleaner display without duplicate status lines

## [0.4.8] - 2025-10-05

### ✨ New

- **Multi-Step Tool Chaining** - Automatically execute complex workflows requiring multiple tools
- **Direct MCP Control** - `aii mcp invoke <tool>` for power users

### 🐛 Fixed

- **GitHub Integration** - Full access to 26 GitHub tools (search repos, create issues, etc.)

## [0.4.7] - 2025-10-03

### ✨ New

- **Template Library** - 8 pre-built templates for marketing, development, and business content (`aii template list`)
- **Usage Analytics** - Track your AI usage with `aii stats` (local storage, privacy-first)

## [0.4.6] - 2025-10-02

### ✨ Improved

- **Performance** - Faster processing for large files
- **Error Messages** - More actionable suggestions when things go wrong

## [0.4.5] - 2025-10-01

### ✨ New

- **Git PR Generator** - Create pull requests with AI-generated titles and descriptions (`aii pr`)
- **Smart Branch Naming** - Generate conventional branch names (`aii branch "add user auth"` → `feature/add-user-auth`)

## [0.4.4] - 2025-09-30

### ✨ New

- **Real-Time Streaming** - See responses as they generate for faster experience
- **Smart Output Modes** - CLEAN (just results), STANDARD (with metrics), THINKING (full reasoning)

## [0.4.3] - 2025-09-28

### ✨ New

- **Shell Autocomplete** - Tab completion for bash/zsh/fish (`aii install-completion`)
- **Command History** - Arrow keys to recall previous commands in interactive mode

## [0.4.2] - 2025-09-26

### ✨ New

- **Interactive Setup Wizard** - 2-minute guided setup with arrow key navigation (`aii config init`)
- **Cost Tracking** - See transparent pricing for all LLM operations
- **Quick Config** - Fast provider/model switching (`aii config provider`, `aii config model`)

## [0.4.1] - 2025-09-24

### ✨ New

- **Web Search Integration** - DuckDuckGo (free), Brave Search, and Google Search support
- **Health Diagnostics** - `aii doctor` troubleshoots configuration issues

## [0.4.0] - 2025-09-22

### ✨ New

- **Multi-LLM Support** - Choose between Claude, GPT, and Gemini models
- **Session Memory** - Conversations persist across commands
- **Smart Confirmations** - Only asks when operations are risky

## [0.3.0] - 2025-09-15

### ✨ New

- **Git Integration** - Smart commit messages, PR generation, branch naming
- **Code Tools** - Generate and review code in any language
- **Translation** - Support for 100+ languages

## [0.2.0] - 2025-09-08

### ✨ New

- **Content Generation** - Create emails, blogs, social media posts
- **Shell Automation** - Safe command generation with explanations
- **Analysis Tools** - Explain code, summarize documents, research topics

## [0.1.0] - 2025-09-01

### 🎉 Initial Release

- Natural language command interface
- Claude integration
- Git commit generation
