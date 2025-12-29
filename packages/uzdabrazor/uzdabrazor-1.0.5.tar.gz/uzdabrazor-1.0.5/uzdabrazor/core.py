#!/usr/bin/env python3
"""
🏴‍☠️ uzdabrazor - The Anal-King of AI Browser Automation 🏴‍☠️

A beautifully fucked-up browser automation script that gives zero shits about
anything while somehow still working perfectly. Smells like smegma but runs like a dream.

WHAT THIS BEAUTIFUL DISASTER DOES:
==================================
- Parses env vars with sane defaults (because we're not savages)
- TWO providers for maximum simplicity: Ollama (local/free) + OpenRouter (400+ cloud models)
- Has vision control and model selection that actually fucking works
- Records GIF + JSON history like a proper surveillance state
- Uses patchright stealth mode to fuck with detection systems
- Maintains organized anarchy through the entire codebase
- Monkey patches LLM calls to log every single ainvoke (surveillance mode)
- Provides separate models for main tasks vs page extraction (for cost optimization)
- MAIN LLM: Does the thinking, planning, and decision-making
- EXTRACTION LLM: Does data parsing and text extraction (use cheaper/faster models)

USAGE EXAMPLES:
===============

Basic Local Usage (free Ollama):
    python uzdabrazor.py --provider ollama --model llama3.1

OpenRouter with Claude (via cloud):
    python uzdabrazor.py --provider openrouter --model anthropic/claude-3.5-sonnet

OpenRouter with GPT-4 (via cloud):
    python uzdabrazor.py --provider openrouter --model openai/gpt-4-turbo

OpenRouter with Gemini (via cloud):
    python uzdabrazor.py --provider openrouter --model google/gemini-2.0-flash-exp

Custom Task Examples:
    python uzdabrazor.py --task "Go to example.com and tell me the page title"
    python uzdabrazor.py --task "Navigate to GitHub and find trending repositories"
    python uzdabrazor.py --task "Go to news site and summarize today's headlines"

Headless Mode (invisible fuckery):
    python uzdabrazor.py --headless --provider ollama --model llama3.1

Custom Window Size:
    python uzdabrazor.py --window-width 2560 --window-height 1440

Different Models for Main vs Extraction (cost optimization):
    python uzdabrazor.py --provider openrouter --model anthropic/claude-3.5-sonnet --extraction-model openai/gpt-4o-mini

Vision Control Examples:
    python uzdabrazor.py --no-vision                    # Disable vision (save tokens)
    python uzdabrazor.py --vision-detail low            # Low detail vision
    python uzdabrazor.py --vision-detail high           # High detail (burn tokens)

Stealth Mode Examples:
    python uzdabrazor.py                                 # Enable stealth (default)
    python uzdabrazor.py --no-stealth                    # Disable stealth (live dangerously)

Connect to Existing Chrome Instance:
    # 1. Start Chrome: google-chrome --remote-debugging-port=9222
    # 2. Run: python uzdabrazor.py --cdp-url http://localhost:9222

Custom Browser Binary:
    python uzdabrazor.py --browser-bin-path /usr/bin/google-chrome-beta
    python uzdabrazor.py --browser-bin-path /usr/bin/chromium-browser

Advanced Usage:
    python uzdabrazor.py --headless --no-security --provider openrouter
    OLLAMA_ENDPOINT=http://192.168.1.100:11434 python uzdabrazor.py --provider ollama

Docker Usage:
    python uzdabrazor.py --dockerize --headless --provider ollama

PATCHRIGHT STEALTH SETUP:
=========================
For maximum stealth fuckery, install patchright:
    pip install patchright
    patchright install

The script will automatically detect and use patchright if available.

ENVIRONMENT VARIABLES:
=====================
Copy .env.example to .env and fill in your API keys. All settings have sane defaults.

Key variables:
- OPENROUTER_API_KEY (for cloud models - get it at https://openrouter.ai/keys)
- OLLAMA_ENDPOINT (default: http://localhost:11434 for local Ollama)
- Script defaults to ollama (free local AI, fuck paying for shit)
- Use --headless flag for invisible browser mode
- Use --window-width/--window-height for custom window size (default: 1920x1080)
- Use --browser-bin-path for custom browser executable
- Use --cdp-url to connect to existing browser instance
- Use --browser-profile-dir for custom profile directory
- Use --no-security to disable browser security (dangerous but useful)
- Use --log-level to control browser-use logging verbosity (default: info)
- Use --dockerize when running in Docker containers for optimized Chrome flags
- Use --skip-llm-api-key-verif to bypass API key validation (for testing)
- Use --history-dir to specify where to save recordings and logs (default: /tmp/agent_history)

SURVEILLANCE FEATURES:
=====================
This script includes LLM surveillance that logs every ainvoke call:
- Shows which provider and model is being used
- Logs message count and output format
- Tracks both main LLM and extraction LLM calls
- Provides full visibility into browser-use's AI interactions

OUTPUT FILES:
=============
Each run generates:
- uzdabrazor_{timestamp}_{task_id}.gif - Visual recording of browser actions
- uzdabrazor_{timestamp}_{task_id}.json - Complete history and conversation logs

Files are saved to the --history-dir directory (default: /tmp/agent_history)

SUPPORTED PROVIDERS:
===================
- ollama: Local Ollama models (llama3.1, qwen3, gemma3, etc.) - FREE
- openrouter: 400+ cloud models via unified API - includes:
  * OpenAI (gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.)
  * Anthropic (claude-3.5-sonnet, claude-3-opus, etc.)
  * Google (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
  * Meta (llama-3.1, llama-3.2, etc.)
  * DeepSeek (deepseek-chat, deepseek-coder, etc.)
  * And 400+ more models from various providers!

WHY ONLY TWO PROVIDERS?
========================
Because simplicity is fucking beautiful:
- Ollama: Free, local, private, no API keys needed
- OpenRouter: One API key for literally everything else (400+ models)
- No more managing 9 different API keys and endpoints
- OpenRouter adds ~10-20% markup but handles routing, fallbacks, and billing
- Cleaner code, less bullshit, more efficiency

TROUBLESHOOTING:
===============
- For Ollama: Install from https://ollama.ai and run `ollama pull llama3.1`
- For OpenRouter: Get API key at https://openrouter.ai/keys
- Check API keys are valid and have sufficient credits
- Verify endpoints are reachable (especially for Ollama/local setups)
- Make sure browser can launch (install Chrome if needed)
- For Docker: use --dockerize flag for optimized Chrome flags
- For connection issues: try --no-stealth or check firewall settings

ERROR MESSAGES:
==============
The script provides detailed error messages with crude but helpful commentary.
If something smells like dikciz smegma, check your configuration and API keys.

"Love it or hate it, this shit automates browsers like a motherfucker."
- uzdabrazor philosophy

PHILOSOPHY:
===========
This is organized anarchy - crude in presentation but solid in functionality.
Built for digital rebels who want browser automation that actually fucking works
without corporate bullshit or enterprise nonsense.

Simplified to two providers because more options != better. Sometimes less is more,
and in this case, Ollama + OpenRouter gives you everything you need without the
clusterfuck of managing 9 different API providers.
"""

import asyncio
import os
import argparse
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# 🏴‍☠️ THE SIMPLIFIED ENV VARS 🏴‍☠️
# Only what we actually need for ollama + openrouter
CLUSTERFUCK_ENV_DEFAULTS = {
    # ✅ LLM PROVIDER KEYS (only the ones we use)
    "OPENROUTER_API_KEY": "",  # For all cloud models
    "OLLAMA_ENDPOINT": "http://localhost:11434",  # For local models
    # ✅ BROWSER-USE CORE SHIT
    "ANONYMIZED_TELEMETRY": "true",
    "BROWSER_USE_CLOUD_SYNC": "",
    "BROWSER_USE_CLOUD_API_URL": "https://api.browser-use.com",
    "BROWSER_USE_CONFIG_DIR": "",
}


def get_env_or_die(key: str) -> str:
    """Get environment variable with fallback to default (because we plan ahead, unlike dikciz that smells like smegma)"""
    return os.getenv(key, CLUSTERFUCK_ENV_DEFAULTS.get(key, ""))


# 🕶️ PATCHRIGHT DETECTION BULLSHIT 🕶️
# Just log when patchright gets used (no forcing, we're rebels not dictators)
try:
    import patchright.async_api as patchright_api

    original_patchright = patchright_api.async_playwright

    def logged_patchright():
        print(
            "🕶️ HOLY SHIT! PATCHRIGHT IS ACTIVE! Library is using patchright for maximum stealth fuckery!"
        )
        return original_patchright()

    patchright_api.async_playwright = logged_patchright
    print("✅ Hooked patchright logging like a fucking boss (stealth mode detected)")

except ImportError as e:
    print(f"⚠️ Failed to setup patchright detection: {e}")
    print("   (This is fine - patchright is optional for basic chaos)")

# 🤖 LLM PROVIDER SURVEILLANCE BULLSHIT 🤖
# Monkey patch the LLM providers we actually use (because we're nosy but efficient fuckers)
# Simplified to only ollama (local/free) and openrouter (everything else)

try:
    # Patch ChatOllama
    from browser_use.llm.ollama.chat import ChatOllama

    original_ollama_ainvoke = ChatOllama.ainvoke

    async def logged_ollama_ainvoke(self, messages, output_format=None, **kwargs):
        print(
            f"🦙 OLLAMA AINVOKE DETECTED! Model: {getattr(self, 'model', 'unknown')} is spitting some local llama wisdom"
        )
        print(
            f"   📝 Processing {len(messages)} messages with output_format: {output_format}, kwargs: {list(kwargs.keys())}"
        )
        return await original_ollama_ainvoke(self, messages, output_format, **kwargs)

    ChatOllama.ainvoke = logged_ollama_ainvoke
    print("✅ Ollama surveillance hooked - local llama can't escape (ainvoke method)")

except ImportError as e:
    print(f"⚠️ Failed to hook Ollama: {e}")

try:
    from langchain_openai import ChatOpenAI

    original_chatopenai_ainvoke = ChatOpenAI.ainvoke

    async def logged_chatopenai_ainvoke(self, input, *args, **kwargs):
        base_url = getattr(self, 'openai_api_base', None) or getattr(self, 'base_url', None)
        if base_url and 'openrouter.ai' in str(base_url):
            msg_count = len(input) if hasattr(input, '__len__') else '?'
            print(
                f"🔀 OPENROUTER (langchain) AINVOKE! Model: {getattr(self, 'model_name', 'unknown')}"
            )
            print(
                f"   📝 Processing {msg_count} langchain messages"
            )
        return await original_chatopenai_ainvoke(self, input, *args, **kwargs)

    ChatOpenAI.ainvoke = logged_chatopenai_ainvoke
    print("✅ OpenRouter surveillance hooked via ChatOpenAI (langchain layer)")

except (ImportError, AttributeError) as e:
    print(f"⚠️ Failed to hook OpenRouter (ChatOpenAI): {e}")

try:
    from uzdabrazor.langchain_compat import ChatLangchain

    original_chatlangchain_ainvoke = ChatLangchain.ainvoke

    async def logged_chatlangchain_ainvoke(self, messages, output_format=None, **kwargs):
        msg_count = len(messages) if hasattr(messages, '__len__') else '?'
        output_type = output_format.__name__ if output_format else 'str'
        provider = getattr(self, 'provider', 'unknown')
        name = getattr(self, 'name', 'unknown')
        print(
            f"🌐 BROWSER-USE LLM CALL! Provider: {provider}, Model: {name}"
        )
        print(
            f"   📝 {msg_count} browser-use messages -> output_format: {output_type}, kwargs: {list(kwargs.keys())}"
        )
        return await original_chatlangchain_ainvoke(self, messages, output_format, **kwargs)

    ChatLangchain.ainvoke = logged_chatlangchain_ainvoke
    print("✅ ChatLangchain wrapper surveillance hooked (browser-use layer)")

except (ImportError, AttributeError) as e:
    print(f"⚠️ Failed to hook ChatLangchain wrapper: {e}")

print("🔍 LLM surveillance system activated - monitoring all ainvoke calls like a fucking hawk!")


# Import browser-use components (the actual functional shit)
from browser_use import Agent, BrowserSession
from browser_use.browser.profile import BrowserProfile


def create_llm_clusterfuck(provider: str, model: str):
    """
    Create an LLM instance based on provider

    Simplified to two providers for maximum efficiency:
    - ollama: Free local models (fuck paying for AI)
    - openrouter: Access to 400+ cloud models through one API (OpenAI, Anthropic, Google, etc.)
    """

    if provider == "ollama":
        from browser_use.llm.ollama.chat import ChatOllama

        print(f"🦙 Creating Ollama local madness with model: {model}")
        return ChatOllama(model=model, host=get_env_or_die("OLLAMA_ENDPOINT"))

    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        from uzdabrazor.langchain_compat import ChatLangchain

        print(f"🔀 Creating OpenRouter multi-model chaos with model: {model}")
        langchain_model = ChatOpenAI(
            model=model,
            api_key=get_env_or_die("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        return ChatLangchain(chat=langchain_model)

    else:
        raise ValueError(
            f"❌ Unsupported provider: {provider}\n"
            f"   Supported providers:\n"
            f"   - ollama: Free local models\n"
            f"   - openrouter: 400+ cloud models (OpenAI, Anthropic, Google, DeepSeek, etc.)\n"
            f"   Use OpenRouter for any cloud model you need!"
        )


async def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="🏴‍☠️ uzdabrazor - The Anal-King of AI Browser Automation That Actually Fucking Works",
        epilog="Love it or hate it, this clusterfuck gets the job done. Peen goes in vageen.",
    )

    # 🤖 MAIN LLM CHAOS CONFIGURATION 🤖
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        choices=["ollama", "openrouter"],
        help="Which AI overlord? ollama=free local, openrouter=400+ cloud models (default: ollama)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Specific model name (because not all models are created equal, some are more fucked up)",
    )

    # 📄 EXTRACTION LLM SETTINGS (for the obsessive perfectionists)
    parser.add_argument(
        "--extraction-provider",
        type=str,
        default=None,
        choices=["ollama", "openrouter"],
        help="Separate LLM provider for page extraction (defaults to same as main)",
    )
    parser.add_argument(
        "--extraction-model",
        type=str,
        default=None,
        help="Extraction model (defaults to same as main, because we're lazy but organized)",
    )

    # 👁️ VISION CONTROL MADNESS
    parser.add_argument(
        "--no-vision",
        action="store_true",
        help="Disable vision (blind chaos is still chaos)",
    )
    parser.add_argument(
        "--vision-detail",
        type=str,
        default="auto",
        choices=["auto", "low", "high"],
        help="How much visual detail to process (more detail = more tokens = more money burned)",
    )

    # 🎯 TASK AND STEALTH BULLSHIT
    parser.add_argument(
        "--task",
        type=str,
        default="Go to https://abrahamjuliot.github.io/creepjs/ and tell me what the detection score is",
        help="What fucked-up task do you want the AI to perform? (default: test stealth capabilities)",
    )
    parser.add_argument(
        "--no-stealth",
        action="store_true",
        help="Disable stealth mode (live dangerously, get detected)",
    )
    parser.add_argument(
        "--browser-bin-path",
        type=str,
        default=None,
        help="Path to custom browser executable (Chrome, Chromium, Edge, etc.)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (invisible chaos)",
    )
    parser.add_argument(
        "--window-width",
        type=int,
        default=1920,
        help="Browser window width in pixels (default: 1920)",
    )
    parser.add_argument(
        "--window-height",
        type=int,
        default=1080,
        help="Browser window height in pixels (default: 1080)",
    )
    parser.add_argument(
        "--cdp-url",
        type=str,
        default=None,
        help="Connect to existing browser via CDP URL (e.g., http://localhost:9222)",
    )
    parser.add_argument(
        "--browser-profile-dir",
        type=str,
        default=None,
        help="Custom browser profile directory to use",
    )
    parser.add_argument(
        "--no-security",
        action="store_true",
        help="Disable browser security features (dangerous but useful for testing)",
    )
    parser.add_argument(
        "--debug-host",
        type=str,
        default="localhost",
        help="Debug host for new browser instances (default: localhost)",
    )
    parser.add_argument(
        "--debug-port",
        type=int,
        default=9222,
        help="Debug port for new browser instances (default: 9222)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level for browser-use (default: info)",
    )
    parser.add_argument(
        "--dockerize",
        action="store_true",
        help="Enable Docker-optimized Chrome flags (use when running in containers)",
    )
    parser.add_argument(
        "--skip-llm-api-key-verif",
        action="store_true",
        help="Skip LLM API key verification (useful for testing without valid keys)",
    )
    parser.add_argument(
        "--history-dir",
        type=str,
        default="/tmp/agent_history",
        help="Directory to save GIF recordings and JSON history (default: /tmp/agent_history)",
    )

    args = parser.parse_args()


    # 🔧 SET BROWSER-USE ENVIRONMENT VARIABLES 🔧
    import os
    os.environ["BROWSER_USE_LOGGING_LEVEL"] = args.log_level
    if args.dockerize:
        os.environ["IN_DOCKER"] = "true"
    if args.skip_llm_api_key_verif:
        os.environ["SKIP_LLM_API_KEY_VERIFICATION"] = "true"

    # 💥 VALIDATION: MAKE SURE WE DON'T HAVE CONFLICTING BROWSER CONFIG 💥
    browser_executable = (
        args.browser_bin_path or os.getenv("BROWSER_EXECUTABLE_PATH")
        if args.browser_bin_path or os.getenv("BROWSER_EXECUTABLE_PATH")
        else None
    )
    cdp_url_arg = args.cdp_url
    cdp_url_env = os.getenv("BROWSER_CDP")
    
    if (browser_executable and cdp_url_arg) or (browser_executable and cdp_url_env):
        print("💥 CLUSTERFUCK ALERT: You can't specify both a browser binary AND a CDP URL!")
        print(f"   Browser binary: {browser_executable}")
        print(f"   CDP URL (arg): {cdp_url_arg}")
        print(f"   CDP URL (env): {cdp_url_env}")
        print("   Pick one, you indecisive fuck:")
        print("   - Use --browser-bin-path OR BROWSER_EXECUTABLE_PATH to launch a new browser")
        print("   - Use --cdp-url OR BROWSER_CDP to connect to existing browser")
        print("   Don't fucking mix them or everything goes to shit!")
        exit(1)

    # 🎲 DETERMINE THE CHAOS CONFIGURATION 🎲
    provider = (
        args.provider or "ollama"
    )  # Default to local ollama because fuck paying for AI

    # Default models for each provider (simplified to the essentials)
    default_models_clusterfuck = {
        "ollama": "llama3.1",  # Free local destruction (use llava:13b if you want vision)
        "openrouter": "anthropic/claude-3.5-sonnet",  # Smart and cost-effective via OpenRouter
    }

    model = args.model or default_models_clusterfuck.get(provider, "llama3.1")

    # Extraction LLM configuration (because some people want different models for different tasks)
    extraction_provider = args.extraction_provider or provider
    extraction_model = args.extraction_model or default_models_clusterfuck.get(
        extraction_provider, model
    )

    # Vision and stealth settings
    use_vision = not args.no_vision  # Vision is True by default, False only with --no-vision
    vision_detail_level = args.vision_detail
    stealth_mode = not args.no_stealth  # Default True, disabled only with --no-stealth

    # 📊 ANNOUNCE THE BEAUTIFUL CONFIGURATION 📊
    print(f"🤖 Main LLM Chaos Engine: {provider}/{model}")
    print(f"📄 Extraction LLM: {extraction_provider}/{extraction_model}")
    print(f"👁️ Vision Enabled: {use_vision} (detail: {vision_detail_level})")
    print(
        f"🕶️ Stealth Mode: {stealth_mode} {'(fuck the system)' if stealth_mode else '(living dangerously)'}"
    )
    print(f"📝 Task: {args.task}")

    # 🌐 BROWSER CONFIGURATION CLUSTERFUCK 🌐
    cdp_url = args.cdp_url or os.getenv("BROWSER_CDP")
    if not cdp_url:
        print(f"🔧 No CDP URL specified, will launch own browser instance")

    # Browser behavior settings (because browsers are needy little shits)
    headless = args.headless  # Use command line argument instead of env var
    disable_security = args.no_security  # Use command line argument
    window_width = args.window_width  # Use command line argument (default 1920)
    window_height = args.window_height  # Use command line argument (default 1080)
    user_data_dir = args.browser_profile_dir  # Use command line argument
    # browser_executable already defined in validation section above
    save_history_path = args.history_dir  # Use command line argument

    if cdp_url:
        print(f"🔧 CDP Endpoint: {cdp_url}")
    print(
        f"🔧 Headless Mode: {headless} {'(invisible chaos)' if headless else '(visible mayhem)'}"
    )
    print(f"🔧 Browser Window: {window_width}x{window_height}")
    if browser_executable:
        print(f"🔧 Browser Binary: {browser_executable}")
    print(f"🔧 History Archive: {save_history_path}")

    # Create the output directory (because we're organized anarchists)
    os.makedirs(save_history_path, exist_ok=True)
    print(f"📁 Created/verified history directory: {save_history_path}")

    # Generate timestamp and unique ID (for proper chaos organization)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chaos_task_id = str(uuid.uuid4())[:8]  # Shorter UUID for cleaner names
    gif_path = os.path.join(
        save_history_path, f"uzdabrazor_{timestamp}_{chaos_task_id}.gif"
    )
    history_path = os.path.join(
        save_history_path, f"uzdabrazor_{timestamp}_{chaos_task_id}.json"
    )

    print(f"📁 GIF Output: {gif_path}")
    print(f"📁 JSON History: {history_path}")

    # 🤖 CREATE THE LLM CLUSTERFUCK 🤖
    try:
        print("🏗️ Firing up the AI chaos engines...")
        main_llm = create_llm_clusterfuck(provider, model)
        print(f"✅ Main LLM clusterfuck locked and loaded: {provider}/{model}")

        # Create extraction LLM (might be the same, might be different, chaos is flexible)
        if extraction_provider == provider and extraction_model == model:
            extraction_llm = main_llm  # Same instance because efficiency
            print(f"✅ Using same LLM for extraction (because we're efficient motherfuckers)")
        else:
            extraction_llm = create_llm_clusterfuck(
                extraction_provider, extraction_model
            )
            print(
                f"✅ Extraction LLM clusterfuck locked and loaded: {extraction_provider}/{extraction_model}"
            )

    except Exception as e:
        print(f"❌ CLUSTERFUCK ALERT: Failed to create LLMs: {e}")
        print(
            "   Check your API keys, endpoints, and whether your dikciz smells like smegma."
        )
        print("   💨 This failure was more disappointing than a wet shart in white pants.")
        return

    # 🌐 CREATE BROWSER SESSION (the chaos delivery vehicle)
    print("🌐 Spinning up the browser chaos delivery system...")
    browser_profile = BrowserProfile(
        stealth=stealth_mode,
        headless=headless,
        disable_security=disable_security,
        user_data_dir=user_data_dir if user_data_dir else None,
        executable_path=browser_executable if browser_executable else None,
        window_size={"width": window_width, "height": window_height},
    )

    browser_session = BrowserSession(
        cdp_url=cdp_url if cdp_url else None, browser_profile=browser_profile
    )
    print("✅ Browser chaos delivery system is fucking ready to go")

    print("🚀 LAUNCHING THE BEAUTIFUL CHAOS...")
    print("=" * 60)

    # 🤖 CREATE AND RUN THE CHAOTIC AGENT 🤖
    agent = Agent(
        task=args.task,
        llm=main_llm,
        page_extraction_llm=extraction_llm,
        browser_session=browser_session,
        generate_gif=gif_path,
        use_vision=use_vision,
        vision_detail_level=vision_detail_level,
    )

    try:
        # 🎬 THE MAIN EVENT - RUN THE CHAOS 🎬
        print(f"🎯 Executing task: {args.task}")
        result = await agent.run()
        print("=" * 60)
        print(f"🎉 CHAOS COMPLETE! Agent result:")
        print(f"📄 {result}")

        # 💾 SAVE THE EVIDENCE OF CHAOS
        print(f"💾 Saving this beautiful clusterfuck for posterity...")
        agent.save_history(history_path)

        # 📊 VERIFY THE CHAOS ARTIFACTS
        if os.path.exists(gif_path):
            gif_size = os.path.getsize(gif_path)
            print(f"✅ GIF Evidence: {gif_path} ({gif_size} bytes of pure chaos)")
        else:
            print("⚠️ GIF not found (maybe the chaos was too abstract to record)")

        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                content = f.read()
            print(
                f"✅ History Archive: {history_path} ({len(content)} chars of organized chaos)"
            )
        else:
            print(
                "⚠️ History not found (this shouldn't happen, investigate immediately)"
            )

        print("🏴‍☠️ Beautiful chaos execution completed successfully! 🏴‍☠️")

    except Exception as e:
        print("=" * 60)
        print(f"💥 CONTROLLED EXPLOSION: Agent chaos failed: {e}")
        print(
            "   (This shit happens when your code smells like dikciz smegma - that's why we have backups)"
        )
        print("   💨 Well that was unexpected... like a shart during a job interview.")

        try:
            agent.save_history(history_path)
            print(f"💾 Emergency chaos archive saved: {history_path}")
        except Exception as save_error:
            print(f"💀 Even the emergency save fucked up: {save_error}")
            print("   (Now that's what I call a complete clusterfuck)")

    finally:
        try:
            await browser_session.stop()
            print("🧹 Browser session cleaned up (responsible chaos)")
        except Exception:
            pass


if __name__ == "__main__":
    print("🏴‍☠️ uzdabrazor - The Anal-King of AI Browser Automation That Actually Fucking Works 🏴‍☠️")
    print("=" * 80)
    print("Love it or hate it, this shit just works. Deal with it.")
    print("=" * 80)
    asyncio.run(main())
