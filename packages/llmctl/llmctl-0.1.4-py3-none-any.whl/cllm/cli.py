#!/usr/bin/env python3
"""
LLMCTL - Command Line LLM Interface
A simple CLI tool to interact with various LLM providers with interactive sessions
"""

import os
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Try to import colorama for cross-platform colored output
try:
    from colorama import init, Fore, Style, Back

    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback if colorama not available
    COLORS_AVAILABLE = False


    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""


    class Style:
        BRIGHT = DIM = RESET_ALL = ""


    class Back:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""

# Configuration file path
CONFIG_DIR = Path.home() / ".cllm"
CONFIG_FILE = CONFIG_DIR / "config.json"
SESSIONS_DIR = CONFIG_DIR / "sessions"

# Pricing per 1M tokens (updated as of Dec 2024)
MODEL_PRICING = {
    # OpenAI models
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "gpt-3.5-turbo-16k": {"input": 3.00, "output": 4.00},

    # Anthropic models
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-haiku-4-20250514": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


def print_colored(text, color=Fore.WHITE, style=Style.NORMAL, end="\n"):
    """Print colored text"""
    if COLORS_AVAILABLE:
        print(f"{style}{color}{text}{Style.RESET_ALL}", end=end)
    else:
        print(text, end=end)


def print_error(text):
    """Print error message"""
    print_colored(f"❌ Error: {text}", Fore.RED, Style.BRIGHT)


def print_success(text):
    """Print success message"""
    print_colored(f"✅ {text}", Fore.GREEN)


def print_info(text):
    """Print info message"""
    print_colored(f"ℹ️  {text}", Fore.CYAN)


def print_warning(text):
    """Print warning message"""
    print_colored(f"⚠️  {text}", Fore.YELLOW)


def calculate_cost(model, input_tokens, output_tokens):
    """Calculate cost in USD for the given tokens"""
    pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens
    }


def print_cost_info(model, cost_info):
    """Print formatted cost information"""
    print_colored("\n" + "─" * 60, Fore.CYAN)
    print_colored("💰 Cost Breakdown:", Fore.CYAN, Style.BRIGHT)
    print_colored(f"   Model: {model}", Fore.WHITE)
    print_colored(f"   Input tokens: {cost_info['input_tokens']:,} (${cost_info['input_cost']:.6f})", Fore.WHITE)
    print_colored(f"   Output tokens: {cost_info['output_tokens']:,} (${cost_info['output_cost']:.6f})", Fore.WHITE)
    print_colored(f"   Total tokens: {cost_info['total_tokens']:,}", Fore.YELLOW)
    print_colored(f"   Total cost: ${cost_info['total_cost']:.6f}", Fore.GREEN, Style.BRIGHT)
    print_colored("─" * 60, Fore.CYAN)


class CLLMConfig:
    """Manages CLLM configuration"""

    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self.sessions_dir = SESSIONS_DIR
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            "current_provider": None,
            "current_session": None,
            "providers": {}
        }

    def save_config(self):
        """Save configuration to file"""
        self.config_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def set_provider(self, provider_name):
        """Set the current LLM provider"""
        self.config["current_provider"] = provider_name
        self.save_config()

    def get_provider(self):
        """Get current provider"""
        return self.config.get("current_provider")

    def set_current_session(self, session_name):
        """Set the current session"""
        self.config["current_session"] = session_name
        self.save_config()

    def get_current_session(self):
        """Get current session name"""
        return self.config.get("current_session")


class Session:
    """Manages conversation sessions"""

    def __init__(self, name, sessions_dir):
        self.name = name
        self.sessions_dir = sessions_dir
        self.session_file = sessions_dir / f"{name}.json"
        self.data = self.load()

    def load(self):
        """Load session from file"""
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                return json.load(f)
        return {
            "name": self.name,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "attached_files": {},
            "metadata": {},
            "total_cost": 0.0,
            "total_tokens": 0
        }

    def save(self):
        """Save session to file"""
        self.sessions_dir.mkdir(exist_ok=True)
        with open(self.session_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add_message(self, role, content):
        """Add a message to the session"""
        self.data["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save()

    def add_cost(self, cost_info):
        """Add cost information to session"""
        if "total_cost" not in self.data:
            self.data["total_cost"] = 0.0
        if "total_tokens" not in self.data:
            self.data["total_tokens"] = 0

        self.data["total_cost"] += cost_info["total_cost"]
        self.data["total_tokens"] += cost_info["total_tokens"]
        self.save()

    def get_session_stats(self):
        """Get session statistics"""
        return {
            "total_cost": self.data.get("total_cost", 0.0),
            "total_tokens": self.data.get("total_tokens", 0),
            "message_count": len(self.data["messages"]) // 2  # Divide by 2 for user-assistant pairs
        }

    def get_messages(self):
        """Get all messages in OpenAI format"""
        return [{"role": msg["role"], "content": msg["content"]}
                for msg in self.data["messages"]]

    def attach_file(self, filename, content):
        """Attach a file to the session"""
        self.data["attached_files"][filename] = {
            "content": content,
            "attached_at": datetime.now().isoformat()
        }
        self.save()

    def detach_file(self, filename):
        """Remove a file from the session"""
        if filename in self.data["attached_files"]:
            del self.data["attached_files"][filename]
            self.save()
            return True
        return False

    def list_files(self):
        """List all attached files"""
        return list(self.data["attached_files"].keys())

    def get_file_content(self, filename):
        """Get content of an attached file"""
        return self.data["attached_files"].get(filename, {}).get("content")

    def get_context(self):
        """Get context from all attached files"""
        if not self.data["attached_files"]:
            return None

        context_parts = []
        for filename, file_data in self.data["attached_files"].items():
            context_parts.append(f"=== File: {filename} ===\n{file_data['content']}\n")

        return "\n".join(context_parts)

    def clear(self):
        """Clear all messages"""
        self.data["messages"] = []
        self.save()

    def clear_files(self):
        """Clear all attached files"""
        self.data["attached_files"] = {}
        self.save()


class LLMProvider:
    """Base class for LLM providers"""

    def __init__(self, api_key):
        self.api_key = api_key

    def ask(self, messages, context=None):
        """Send messages to the LLM"""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation"""

    def __init__(self, api_key, model="gpt-4"):
        super().__init__(api_key)
        # Map friendly names to actual model IDs (if needed)
        model_map = {
            "gpt4": "gpt-4",
            "gpt4-turbo": "gpt-4-turbo",
            "gpt35": "gpt-3.5-turbo",
        }
        self.model = model_map.get(model, model)
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            print_error("openai package not installed. Run: pip install openai")
            sys.exit(1)

    def ask(self, messages, context=None):
        """Send messages to OpenAI"""
        api_messages = messages.copy()

        # Add context as system message if provided
        if context:
            api_messages.insert(0, {"role": "system", "content": f"Context from attached files:\n{context}"})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages
            )

            # Extract usage information
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            return response.choices[0].message.content, usage
        except Exception as e:
            return f"Error: {str(e)}", None


class AnthropicProvider(LLMProvider):
    """Anthropic/Claude provider implementation"""

    def __init__(self, api_key, model="claude-sonnet-4-20250514"):
        super().__init__(api_key)
        # Map friendly names to actual model IDs
        model_map = {
            "sonnet-4": "claude-sonnet-4-20250514",
            "sonnet-4.5": "claude-sonnet-4-5-20250929",
            "opus-4": "claude-opus-4-20250514",
            "haiku-4": "claude-haiku-4-20250514",
            "sonnet": "claude-sonnet-4-20250514",
            "opus": "claude-opus-4-20250514",
            "haiku": "claude-haiku-4-20250514",
        }
        self.model = model_map.get(model, model)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            print_error("anthropic package not installed. Run: pip install anthropic")
            sys.exit(1)

    def ask(self, messages, context=None):
        """Send messages to Claude"""
        # Convert messages to Anthropic format
        system_message = None
        api_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                api_messages.append(msg)

        # Add context to system message
        if context:
            if system_message:
                system_message = f"{system_message}\n\nContext from attached files:\n{context}"
            else:
                system_message = f"Context from attached files:\n{context}"

        try:
            kwargs = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": api_messages
            }

            if system_message:
                kwargs["system"] = system_message

            response = self.client.messages.create(**kwargs)

            # Extract usage information
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }

            return response.content[0].text, usage
        except Exception as e:
            return f"Error: {str(e)}", None


class CLLM:
    """Main CLLM application"""

    def __init__(self):
        self.config = CLLMConfig()
        self.current_session = None

    def init(self):
        """Initialize CLLM configuration"""
        print_info("Initializing LLMCTL...")
        CONFIG_DIR.mkdir(exist_ok=True)
        SESSIONS_DIR.mkdir(exist_ok=True)

        if CONFIG_FILE.exists():
            print_success(f"Configuration already exists at: {CONFIG_FILE}")
        else:
            self.config.save_config()
            print_success(f"Configuration created at: {CONFIG_FILE}")

        print_info("\nTo use LLMCTL, you need to:")
        print("1. Set your API keys using environment variables:")
        print("   - OPENAI_API_KEY for OpenAI/GPT models")
        print("   - ANTHROPIC_API_KEY for Claude models")
        print("2. Select a provider: llmctl use <provider>:<model>")
        print("   Example: llmctl use gpt-4 or llmctl use claude:sonnet-4")
        print("3. Start interactive session: llmctl interactive")

    def use(self, provider_spec):
        """Set the current LLM provider"""
        # Parse provider specification
        if ":" in provider_spec:
            provider, model = provider_spec.split(":", 1)
        else:
            # Default models
            if provider_spec.startswith("gpt"):
                provider = "openai"
                model = provider_spec
            elif provider_spec.startswith("claude"):
                provider = "anthropic"
                model = provider_spec
            else:
                provider = provider_spec
                model = None

        # Normalize provider names
        if provider in ["gpt", "openai"]:
            provider = "openai"
            if not model or model == "openai":
                model = "gpt-4"
        elif provider in ["claude", "anthropic"]:
            provider = "anthropic"
            if not model or model == "anthropic":
                model = "claude-sonnet-4-20250514"

        self.config.set_provider(f"{provider}:{model}")
        print_success(f"Activated provider: {provider} (model: {model})")

    def load_session(self, session_name):
        """Load or create a session"""
        self.current_session = Session(session_name, SESSIONS_DIR)
        self.config.set_current_session(session_name)
        return self.current_session

    def attach(self, filename):
        """Attach a file to current session"""
        if not self.current_session:
            print_error("No active session. Use 'llmctl interactive' first")
            return False

        filepath = Path(filename.lstrip('@'))

        if not filepath.exists():
            print_error(f"File '{filepath}' not found")
            return False

        try:
            with open(filepath, 'r') as f:
                content = f.read()
            self.current_session.attach_file(str(filepath), content)
            print_success(f"Attached file: {filepath}")
            return True
        except Exception as e:
            print_error(f"Error reading file: {e}")
            return False

    def detach(self, filename):
        """Detach a file from current session"""
        if not self.current_session:
            print_error("No active session")
            return False

        if self.current_session.detach_file(filename):
            print_success(f"Detached file: {filename}")
            return True
        else:
            print_error(f"File '{filename}' not found in session")
            return False

    def list_files(self):
        """List all attached files"""
        if not self.current_session:
            print_error("No active session")
            return

        files = self.current_session.list_files()
        if not files:
            print_info("No files attached")
        else:
            print_colored("\n📎 Attached files:", Fore.CYAN, Style.BRIGHT)
            for f in files:
                print_colored(f"  • {f}", Fore.CYAN)

    def ask(self, prompt):
        """Ask a question to the current LLM provider"""
        provider_spec = self.config.get_provider()

        if not provider_spec:
            print_error("No provider selected. Use 'llmctl use <provider>' first")
            return None

        # Parse provider specification
        provider, model = provider_spec.split(":", 1)

        # Get API key from environment
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print_error("OPENAI_API_KEY environment variable not set")
                return None
            llm = OpenAIProvider(api_key, model)
            actual_model = model  # OpenAI uses model name directly
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print_error("ANTHROPIC_API_KEY environment variable not set")
                return None
            llm = AnthropicProvider(api_key, model)
            actual_model = llm.model  # Get the resolved model ID from the provider
        else:
            print_error(f"Unknown provider '{provider}'")
            return None

        # Build messages
        if self.current_session:
            messages = self.current_session.get_messages()
            messages.append({"role": "user", "content": prompt})
            context = self.current_session.get_context()
        else:
            messages = [{"role": "user", "content": prompt}]
            context = None

        # Send request
        print_colored(f"\n🤖 {provider} ({model}):", Fore.MAGENTA, Style.BRIGHT)
        response, usage = llm.ask(messages, context)

        # Display response in default terminal color (black/dark)
        print(response)

        # Calculate and display cost using actual model ID
        if usage:
            cost_info = calculate_cost(actual_model, usage["input_tokens"], usage["output_tokens"])
            print_cost_info(actual_model, cost_info)

            # Save to session if active
            if self.current_session:
                self.current_session.add_cost(cost_info)

        # Save messages to session if active
        if self.current_session:
            self.current_session.add_message("user", prompt)
            self.current_session.add_message("assistant", response)

        return response

    def interactive(self, session_name="default"):
        """Start interactive session"""
        self.load_session(session_name)

        print_colored("\n" + "═" * 70, Fore.CYAN, Style.BRIGHT)
        print_colored("  🚀 LLMCTL - Interactive LLM Session", Fore.CYAN, Style.BRIGHT)
        print_colored("═" * 70, Fore.CYAN, Style.BRIGHT)

        provider_spec = self.config.get_provider()
        if provider_spec:
            provider, model = provider_spec.split(":", 1)
            print_colored(f"\n  📡 Provider: ", Fore.CYAN, end="")
            print_colored(f"{provider}", Fore.GREEN, Style.BRIGHT, end="")
            print_colored(f" ({model})", Fore.WHITE)
        else:
            print_colored("\n  ⚠️  No provider selected", Fore.YELLOW)
            print_colored("     Use '/use <provider>' to set one", Fore.YELLOW)

        print_colored(f"  💾 Session:  ", Fore.CYAN, end="")
        print_colored(f"{session_name}", Fore.GREEN, Style.BRIGHT)

        print_colored("\n" + "─" * 70, Fore.CYAN)
        print_colored("  📚 Quick Commands:", Fore.MAGENTA, Style.BRIGHT)
        print_colored("     /help", Fore.YELLOW, end="")
        print("        - Show all commands")
        print_colored("     /use", Fore.YELLOW, end="")
        print(" <model>  - Switch LLM provider")
        print_colored("     /attach", Fore.YELLOW, end="")
        print(" <file> - Add file context")
        print_colored("     /stats", Fore.YELLOW, end="")
        print("       - Show costs & usage")
        print_colored("     /exit", Fore.YELLOW, end="")
        print("        - Exit session")
        print_colored("─" * 70, Fore.CYAN)
        print_colored("  💡 Tip: Type naturally - no quotes needed!", Fore.CYAN)
        print_colored("═" * 70 + "\n", Fore.CYAN, Style.BRIGHT)

        while True:
            try:
                # Get user input
                print_colored("\n❯ ", Fore.BLUE, Style.BRIGHT, end="")
                user_input = input().strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                else:
                    # Regular question
                    self.ask(user_input)

            except KeyboardInterrupt:
                print_colored("\n\n👋 Use /exit to quit properly", Fore.YELLOW)
                continue
            except EOFError:
                print_colored("\n\n👋 Goodbye!", Fore.CYAN)
                break

    def handle_command(self, command):
        """Handle interactive session commands"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "/help":
            print_colored("\n" + "─" * 70, Fore.CYAN)
            print_colored("  📖 Available Commands", Fore.CYAN, Style.BRIGHT)
            print_colored("─" * 70, Fore.CYAN)
            print_colored("\n  🔧 Provider & Session:", Fore.MAGENTA, Style.BRIGHT)
            print_colored("     /use", Fore.YELLOW, Style.BRIGHT, end="")
            print(" <provider>    - Switch provider (e.g., /use gpt-4, /use claude:sonnet-4)")

            print_colored("\n  📎 File Management:", Fore.MAGENTA, Style.BRIGHT)
            print_colored("     /attach", Fore.YELLOW, Style.BRIGHT, end="")
            print(" <file>      - Attach a file as context")
            print_colored("     /detach", Fore.YELLOW, Style.BRIGHT, end="")
            print(" <file>      - Remove attached file")
            print_colored("     /files", Fore.YELLOW, Style.BRIGHT, end="")
            print("             - List all attached files")
            print_colored("     /clearfiles", Fore.YELLOW, Style.BRIGHT, end="")
            print("       - Clear all attached files")

            print_colored("\n  💬 Conversation:", Fore.MAGENTA, Style.BRIGHT)
            print_colored("     /history", Fore.YELLOW, Style.BRIGHT, end="")
            print("           - Show conversation history")
            print_colored("     /clear", Fore.YELLOW, Style.BRIGHT, end="")
            print("             - Clear conversation history")

            print_colored("\n  📊 Analytics:", Fore.MAGENTA, Style.BRIGHT)
            print_colored("     /stats", Fore.YELLOW, Style.BRIGHT, end="")
            print("             - Show session statistics and costs")

            print_colored("\n  ℹ️  Other:", Fore.MAGENTA, Style.BRIGHT)
            print_colored("     /help", Fore.YELLOW, Style.BRIGHT, end="")
            print("              - Show this help")
            print_colored("     /exit", Fore.YELLOW, Style.BRIGHT, end="")
            print(", ", end="")
            print_colored("/quit", Fore.YELLOW, Style.BRIGHT, end="")
            print("        - Exit interactive session")
            print_colored("─" * 70 + "\n", Fore.CYAN)

        elif cmd == "/use":
            if not arg:
                print_error("Usage: /use <provider>")
            else:
                self.use(arg)

        elif cmd == "/attach":
            if not arg:
                print_error("Usage: /attach <filename>")
            else:
                self.attach(arg)

        elif cmd == "/detach":
            if not arg:
                print_error("Usage: /detach <filename>")
            else:
                self.detach(arg)

        elif cmd == "/files":
            self.list_files()

        elif cmd == "/clear":
            if self.current_session:
                self.current_session.clear()
                print_success("Conversation cleared")
            else:
                print_error("No active session")

        elif cmd == "/clearfiles":
            if self.current_session:
                self.current_session.clear_files()
                print_success("All files detached")
            else:
                print_error("No active session")

        elif cmd == "/history":
            if not self.current_session:
                print_error("No active session")
                return

            messages = self.current_session.data["messages"]
            if not messages:
                print_info("No conversation history")
                return

            print_colored("\n" + "═" * 70, Fore.CYAN, Style.BRIGHT)
            print_colored("  📜 Conversation History", Fore.CYAN, Style.BRIGHT)
            print_colored("═" * 70 + "\n", Fore.CYAN, Style.BRIGHT)

            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                timestamp = msg.get("timestamp", "")

                if role == "user":
                    print_colored(f"\n❯ You", Fore.BLUE, Style.BRIGHT, end="")
                    print_colored(f" ({timestamp})", Fore.CYAN)
                    print(content)
                else:
                    print_colored(f"\n🤖 Assistant", Fore.MAGENTA, Style.BRIGHT, end="")
                    print_colored(f" ({timestamp})", Fore.CYAN)
                    print(content)

            print_colored("\n" + "═" * 70 + "\n", Fore.CYAN, Style.BRIGHT)

        elif cmd == "/stats":
            if not self.current_session:
                print_error("No active session")
                return

            stats = self.current_session.get_session_stats()
            print_colored("\n" + "═" * 70, Fore.CYAN, Style.BRIGHT)
            print_colored("  📊 Session Statistics", Fore.CYAN, Style.BRIGHT)
            print_colored("═" * 70, Fore.CYAN, Style.BRIGHT)

            print_colored(f"\n  Session Name:    ", Fore.CYAN, end="")
            print_colored(f"{self.current_session.name}", Fore.WHITE, Style.BRIGHT)

            print_colored(f"  Exchanges:       ", Fore.CYAN, end="")
            print_colored(f"{stats['message_count']}", Fore.WHITE, Style.BRIGHT, end="")
            print(" conversations")

            print_colored(f"  Total Tokens:    ", Fore.CYAN, end="")
            print_colored(f"{stats['total_tokens']:,}", Fore.YELLOW, Style.BRIGHT)

            print_colored(f"  Total Cost:      ", Fore.CYAN, end="")
            print_colored(f"${stats['total_cost']:.6f}", Fore.GREEN, Style.BRIGHT)

            # Show attached files
            files = self.current_session.list_files()
            if files:
                print_colored(f"  Attached Files:  ", Fore.CYAN, end="")
                print_colored(f"{len(files)}", Fore.WHITE, Style.BRIGHT, end="")
                print(f" file{'s' if len(files) != 1 else ''}")

            print_colored("═" * 70 + "\n", Fore.CYAN, Style.BRIGHT)

        elif cmd in ["/exit", "/quit"]:
            print_colored("\n👋 Goodbye!", Fore.CYAN)
            sys.exit(0)

        else:
            print_error(f"Unknown command: {cmd}. Type /help for available commands")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="LLMCTL - Command Line LLM Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    subparsers.add_parser("init", help="Initialize LLMCTL configuration")

    # Use command
    use_parser = subparsers.add_parser("use", help="Set LLM provider")
    use_parser.add_argument("provider", help="Provider specification (e.g., gpt-4, claude:sonnet-4)")

    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Start interactive session")
    interactive_parser.add_argument("--session", "-s", default="default", help="Session name")

    # Ask command (one-off)
    ask_parser = subparsers.add_parser("ask", help="Ask a one-off question")
    ask_parser.add_argument("prompt", nargs="*", help="Your question or prompt")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cllm = CLLM()

    if args.command == "init":
        cllm.init()
    elif args.command == "use":
        cllm.use(args.provider)
    elif args.command == "interactive":
        cllm.interactive(args.session)
    elif args.command == "ask":
        if not args.prompt:
            print_error("Please provide a prompt")
            return
        prompt = " ".join(args.prompt)
        cllm.ask(prompt)


if __name__ == "__main__":
    main()