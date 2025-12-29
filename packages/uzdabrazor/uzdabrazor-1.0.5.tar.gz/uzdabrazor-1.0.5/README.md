# 🏴‍☠️ UZDABRAZOR - The Anal-King of AI Browser Automation 🏴‍☠️

**A beautifully fucked-up Skynet-powered browser automation AI Agent that harnesses neural brainfuck and machine learning chaos to give zero shits about anything while somehow still working perfectly. Smells like smegma but runs like a dream.**

<p align="center">
<a href="https://github.com/uzdabrazor/anal-core"><img src="https://img.shields.io/badge/GITHUB-ANAL--CORE-orange?style=for-the-badge"></a>&nbsp;
<a href="https://pump.fun/coin/DCDQBmZM9HYcfqDj8PQXzEQxvEtmWSKmAFWScKcxpump"><img src="https://img.shields.io/badge/PUMPFUN-SHIT TOKEN-brightgreen?style=for-the-badge"></a>&nbsp;
<a href="https://x.com/uzdabrazor"><img src="https://img.shields.io/badge/X-FOLLOW-blue?style=for-the-badge"></a>
</p>

---
[![PyPI version](https://badge.fury.io/py/uzdabrazor.svg)](https://pypi.org/project/uzdabrazor/)
[![Python Versions](https://img.shields.io/pypi/pyversions/uzdabrazor.svg)](https://pypi.org/project/uzdabrazor/)
[![License](https://img.shields.io/pypi/l/uzdabrazor.svg)](https://github.com/uzdabrazor/anal-core/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/uzdabrazor.svg)](https://pypi.org/project/uzdabrazor/)
## 🔥 What This Beautiful Disaster Does

uzdabrazor is the most irreverent, crude, and effective neural brainfuck automation script you'll ever encounter. This digital Skynet harnesses machine learning chaos and turns your browser into an unstoppable cybernetic organism. Built on top of the excellent [browser-use](https://github.com/browser-use/browser-use) library, it provides:

- **2 simple neural overlords** - Ollama (local/free) + OpenRouter (400+ cloud models with ONE API key)
- **Complete Big Brother surveillance** - Monitors every single machine learning brainfart like a paranoid NSA cyborg
- **Terminator stealth mode** - Uses patchright to dodge bot detection like a shapeshifting T-1000
- **Organized digital anarchy** - Crude language wrapped around Skynet-grade engineering
- **Zero corporate Matrix bullshit** - No enterprise nonsense, just pure cyberpunk functional chaos
- **Simplified as fuck** - One local provider, one cloud gateway. No more juggling 9 different API keys.

---

## 💻 System Requirements (Don't Skip This Shit)

- **Python 3.11+** (anything older is prehistoric garbage)
- **Chrome or Chromium** (for the actual browser automation, duh)
- **Ollama server** (if you want free local AI, get it at https://ollama.ai)
- **Patchright** (for stealth mode: `pip install patchright && patchright install`)

---

## 🚀 Quick Start (For the Impatient)

```bash
# 1. Install the package globally
pipx install uzdabrazor

# 2. Create a .env file in your current working directory
# Download .env.example from the repo or create your own with these variables:
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OLLAMA_ENDPOINT=http://localhost:11434
EOF

# 3. Run with local ollama (free neural overlord, fuck paying corporate Skynet)
uzdabrazor --task "Go to example.com and tell me the page title"

# 4. Or use OpenRouter for cloud models
uzdabrazor --provider openrouter --model anthropic/claude-3.5-sonnet

# 5. Better yet, copy run.example.sh from the repo and shove it up your asshole somewhere
# Then customize it for your own automation needs
```

### 📝 Environment File Location

**IMPORTANT:** After installing via pipx, place your `.env` file in the **directory where you run the `uzdabrazor` command**.

The script loads environment variables from `.env` in your current working directory. Example:

```bash
# Create .env in your project folder
cd ~/my-automation-project
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OLLAMA_ENDPOINT=http://localhost:11434
EOF

# Run uzdabrazor from the same directory
uzdabrazor --task "your task here"
```

Grab `.env.example` from the [GitHub repo](https://github.com/uzdabrazor/anal-core) for the full list of variables.

---

## 🤖 Supported Neural Overlords

**Simplified to TWO providers because more options != better code:**

| Provider       | Description                                                               | Example Models                                                                       |
| -------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **ollama**     | Local neural brainfuck (DEFAULT - FREE and PRIVATE)                       | `llama3.1`, `qwen3`, `gemma3`, etc.                                                  |
| **openrouter** | 400+ cloud models via ONE API key (OpenAI, Anthropic, Google, DeepSeek+) | `anthropic/claude-3.5-sonnet`, `openai/gpt-4-turbo`, `google/gemini-2.0-flash-exp` |

**Why only two?** Because managing 9 different API keys and endpoints is a clusterfuck. OpenRouter gives you access to literally every major model with one API key and adds only ~10-20% markup. Ollama gives you free local models. Done. Simple. Efficient.

### OpenRouter Configuration

OpenRouter uses the standard `ChatOpenAI` from LangChain with optimized settings:

- **Temperature**: Set to `0.0` for deterministic, consistent browser actions
- **Max Tokens**: Limited to `4096` for cost control and response quality
- **Tool Choice**: Set to `auto` for proper function calling support
- **Base URL**: `https://openrouter.ai/api/v1`

These settings ensure reliable browser automation while keeping costs predictable.

---

## 🎯 Usage Examples

### Basic Destruction

```bash
# Default: ollama (because fuck paying for AI)
uzdabrazor --task "Go to GitHub and find trending repositories"

# Use OpenRouter for Claude
uzdabrazor --provider openrouter --model anthropic/claude-3.5-sonnet --task "Analyze this website"

# Use OpenRouter for GPT-4
uzdabrazor --provider openrouter --model openai/gpt-4-turbo --task "Analyze this website"
```

### Advanced Fuckery

```bash
# Headless stealth mode
uzdabrazor --headless --provider openrouter --model anthropic/claude-3.5-sonnet

# Custom browser and window size
uzdabrazor --browser-bin-path /usr/bin/google-chrome-beta --window-width 1920 --window-height 1080

# Connect to existing browser
google-chrome --remote-debugging-port=9222 &
uzdabrazor --cdp-url http://localhost:9222

# Different models for main task vs extraction (cost optimization strategy)
# MAIN LLM: Complex reasoning and decision-making (use powerful models)
# EXTRACTION LLM: Data parsing and text extraction (use fast cheap models)
uzdabrazor --provider openrouter --model anthropic/claude-3.5-sonnet --extraction-model openai/gpt-4o-mini

# Docker mode with no security (because we live dangerously)
uzdabrazor --dockerize --headless --no-security --provider ollama

# Custom output directory and logging
uzdabrazor --history-dir ~/automation-logs --log-level debug
```

### Vision Control

```bash
# Disable vision to save tokens (blind destruction is still destruction)
uzdabrazor --no-vision

# Low/high detail vision
uzdabrazor --vision-detail low
uzdabrazor --vision-detail high
```

---

## 🔧 Command Line Arguments

| Flag                            | Description                                      | Default               |
| ------------------------------- | ------------------------------------------------ | --------------------- |
| `--provider`                    | AI provider to use                               | `ollama`              |
| `--model`                       | Specific model name                              | `llama3.1`            |
| `--extraction-provider`         | Separate AI for page extraction (save cash)      | Same as `--provider`  |
| `--extraction-model`            | Model for extraction tasks                       | Same as `--model`     |
| `--task`                        | Task for the AI to perform                       | Stealth test          |
| `--headless`                    | Invisible browser mode                           | `false`               |
| `--no-stealth`                  | Disable stealth (live dangerously)               | `false`               |
| `--no-vision`                   | Disable AI vision                                | Vision enabled        |
| `--vision-detail`               | Vision detail level (`auto`/`low`/`high`)        | `auto`                |
| `--window-width`                | Browser width                                    | `1920`                |
| `--window-height`               | Browser height                                   | `1080`                |
| `--browser-bin-path`            | Custom browser executable                        | None                  |
| `--cdp-url`                     | Connect to existing browser                      | None                  |
| `--browser-profile-dir`         | Custom profile directory                         | None                  |
| `--no-security`                 | Disable security features                        | `false`               |
| `--log-level`                   | Logging verbosity (`debug`/`info`/`warning`...)  | `info`                |
| `--debug-host`                  | Debug server host                                | `localhost`           |
| `--debug-port`                  | Debug server port                                | `9222`                |
| `--dockerize`                   | Docker-optimized flags                           | `false`               |
| `--skip-llm-api-key-verif`      | Skip API key validation (for testing/debugging)  | `false`               |
| `--history-dir`                 | Output directory                                 | `/tmp/agent_history`  |

---

## 🕵️ Surveillance Features (Big Brother Is Watching)

This beautiful bastard monkey-patches all LLM providers to log every single AI call. You'll see exactly when your neural overlords are thinking:

**What Gets Logged:**
- Every `ainvoke()` call to any LLM provider
- Which model is being used
- How many messages are in the prompt
- What output format is requested

**Example Output:**
```text
🦙 OLLAMA AINVOKE DETECTED! Model: llama3.1 is spitting some local llama wisdom
   📝 Processing 5 messages with output_format: None

🔀 OPENROUTER AINVOKE DETECTED! Model: anthropic/claude-3.5-sonnet is routing through 400+ models like a fucking switchboard
   📝 Processing 3 messages with output_format: <class 'ActionResult'>

🦙 OLLAMA AINVOKE DETECTED! Model: qwen3:8b is spitting some local llama wisdom
   📝 Processing 12 messages with output_format: None
```

This shit is useful for:
- Debugging which model is actually being called
- Understanding token usage patterns
- Catching when browser-use makes unexpected AI calls
- Feeling like a paranoid NSA cyborg monitoring everything

---

## 📁 Output Files

Each run generates two files in your `--history-dir`:

- `uzdabrazor_{timestamp}_{unique_id}.gif` - Visual recording of all browser actions
- `uzdabrazor_{timestamp}_{unique_id}.json` - Complete conversation history and task results

Example filenames:
```
uzdabrazor_20250101_235959_a1b2c3d4.gif
uzdabrazor_20250101_235959_a1b2c3d4.json
```

---

## 🏴‍☠️ Stealth Mode (Dodging Bot Detection Like a Boss)

Stealth mode uses **patchright** to patch browser binaries and evade detection:

```bash
pip install patchright
patchright install  # Downloads patched browsers
```

**What Patchright Does:**
- Removes webdriver signals that scream "I'M A BOT!"
- Modifies browser fingerprints
- Spoofs navigator properties
- Bypasses common bot detection techniques

**Default:** Stealth is **ENABLED** (use `--no-stealth` to disable if you're feeling suicidal)

---

## ⚙️ Environment Variables

Copy the example file and fill in your fucking API keys:

```bash
cp .env.example .env
# Then edit .env with your actual keys
```

Check `.env.example` in the repo for the full list of variables. Main ones:
- `OPENROUTER_API_KEY` - OpenRouter API key (for 400+ cloud models: OpenAI, Anthropic, Google, DeepSeek, etc.)
- `OLLAMA_ENDPOINT` - Local Ollama server (default: http://localhost:11434)

---

## 🐛 Troubleshooting (When Shit Breaks)

**Chrome not found:**
- Install Chrome or Chromium, you genius
- Or use `--browser-bin-path` to point to your browser

**Ollama connection refused:**
- Make sure Ollama server is running: `ollama serve`
- Check the endpoint: `--provider ollama` uses `http://localhost:11434` by default

**API key errors:**
- Check your keys actually work (make test API calls)
- OpenRouter keys start with `sk-or-v1-`
- Get your OpenRouter key at https://openrouter.ai/keys

**Patchright issues:**
- Run `patchright install` to download patched browsers
- Check if you have write permissions

**CDP connection fails:**
- Make sure browser is running: `google-chrome --remote-debugging-port=9222`
- Can't use `--browser-bin-path` AND `--cdp-url` together (pick one, genius)

---

## 🔥 Why This Exists

Because browser automation doesn't have to be boring corporate shit.

---

## 💬 Final Words

**Peen goes in vageen. Code works. End of story.**
