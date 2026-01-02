"""Interactive setup wizard for LLM configuration."""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess

import typer

logger = logging.getLogger(__name__)


# Model configurations with user-friendly descriptions
AVAILABLE_MODELS = [
    {
        "id": "codellama:7b",
        "name": "CodeLlama 7B",
        "description": "Fast, code-focused (Recommended)",
        "ram": "4GB",
        "recommended": True,
    },
    {
        "id": "codellama:13b",
        "name": "CodeLlama 13B",
        "description": "Better quality, slower",
        "ram": "8GB",
        "recommended": False,
    },
    {
        "id": "deepseek-coder:6.7b",
        "name": "DeepSeek Coder 6.7B",
        "description": "Fast, code-focused alternative",
        "ram": "4GB",
        "recommended": False,
    },
    {
        "id": "mistral:7b",
        "name": "Mistral 7B",
        "description": "General purpose, good quality",
        "ram": "4GB",
        "recommended": False,
    },
]


def check_ollama_installed() -> bool:
    """Check if Ollama is installed and available on PATH.

    Returns:
        True if ollama command is available
    """
    return shutil.which("ollama") is not None


def check_ollama_running() -> bool:
    """Check if Ollama server is running.

    Returns:
        True if Ollama server is responding
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_ollama_models() -> list[str]:
    """Get list of models already downloaded in Ollama.

    Returns:
        List of model names
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []

        # Parse output (skip header line)
        lines = result.stdout.strip().split("\n")[1:]
        models = []
        for line in lines:
            parts = line.split()
            if parts:
                models.append(parts[0])  # First column is model name
        return models
    except Exception as e:
        logger.debug(f"Failed to get Ollama models: {e}")
        return []


def print_ollama_install_instructions() -> None:  # pragma: no cover
    """Print instructions for installing Ollama based on platform."""
    system = platform.system().lower()

    typer.echo("\n📥 Ollama is not installed. Here's how to install it:\n")

    if system == "darwin":  # macOS
        typer.echo("macOS:")
        typer.secho(
            "  1. Visit: https://ollama.com/download", fg=typer.colors.CYAN, bold=True
        )
        typer.echo("  2. Download and run the macOS installer")
        typer.echo("  3. Or use Homebrew: brew install ollama")
    elif system == "linux":
        typer.echo("Linux:")
        typer.secho(
            "  Run: curl -fsSL https://ollama.com/install.sh | sh",
            fg=typer.colors.CYAN,
            bold=True,
        )
    elif system == "windows":
        typer.echo("Windows:")
        typer.secho(
            "  1. Visit: https://ollama.com/download", fg=typer.colors.CYAN, bold=True
        )
        typer.echo("  2. Download and run the Windows installer")
    else:
        typer.echo("Visit: https://ollama.com/download")

    typer.echo("\nAfter installing, run this command again to continue setup.")


def pull_model(model_id: str) -> bool:  # pragma: no cover
    """Pull/download an Ollama model.

    Args:
        model_id: Model identifier (e.g., "codellama:7b")

    Returns:
        True if successful
    """
    typer.echo(f"\n📦 Downloading {model_id}...")
    typer.echo("This may take a few minutes depending on your internet connection.\n")

    try:
        # Run ollama pull with live output
        process = subprocess.Popen(
            ["ollama", "pull", model_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Stream output
        if process.stdout:
            for line in process.stdout:
                typer.echo(line.rstrip())

        process.wait()

        if process.returncode == 0:
            typer.secho(
                f"\n✅ {model_id} downloaded successfully!", fg=typer.colors.GREEN
            )
            return True
        else:
            typer.secho(f"\n❌ Failed to download {model_id}", fg=typer.colors.RED)
            return False

    except Exception as e:
        typer.secho(f"\n❌ Error downloading model: {e}", fg=typer.colors.RED)
        return False


def run_llm_setup_wizard() -> dict[str, str | bool] | None:  # pragma: no cover
    """Run the interactive LLM setup wizard.

    Returns:
        Dictionary with LLM configuration, or None if user skips
    """
    typer.echo("\n" + "=" * 70)
    typer.secho("🤖 AI Assistant Setup (Optional)", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 70)

    typer.echo("\nVibeGate can use a local AI model to:")
    typer.echo("  • Explain issues in plain English")
    typer.echo("  • Generate fix prompts for your AI coding assistant")
    typer.echo("  • Make code quality fun and approachable")
    typer.echo("\n✨ This runs 100% locally - no data leaves your machine.\n")

    # Ask if user wants to set up LLM
    setup = typer.confirm("Would you like to set this up?", default=True)
    if not setup:
        typer.echo("\nNo problem! You can set this up later by running:")
        typer.secho("  vibegate init --force", fg=typer.colors.YELLOW)
        return None

    # Check if Ollama is installed
    typer.echo("\n🔍 Checking for Ollama...")
    if not check_ollama_installed():
        typer.secho("❌ Ollama not found", fg=typer.colors.RED)
        print_ollama_install_instructions()
        return None

    typer.secho("✅ Ollama is installed", fg=typer.colors.GREEN)

    # Check if Ollama is running
    if not check_ollama_running():
        typer.secho("\n⚠️  Ollama server is not running", fg=typer.colors.YELLOW)
        typer.echo("Start it with: ollama serve")
        typer.echo(
            "Or on macOS/Windows, Ollama should start automatically after installation.\n"
        )

        start_now = typer.confirm("Continue anyway?", default=True)
        if not start_now:
            return None

    # Get already installed models
    installed_models = get_ollama_models()
    if installed_models:
        typer.echo(f"\n📚 Models already installed: {', '.join(installed_models)}")

    # Show model options
    typer.echo("\n📋 Choose your model:\n")

    for idx, model in enumerate(AVAILABLE_MODELS, 1):
        prefix = "✨" if model["recommended"] else "  "
        already = " (already installed)" if model["id"] in installed_models else ""
        typer.echo(
            f"{prefix} {idx}. {model['name']} - {model['description']} ({model['ram']} RAM){already}"
        )

    typer.echo(f"   {len(AVAILABLE_MODELS) + 1}. Skip for now")

    # Get user choice
    choice = typer.prompt(
        "\nYour choice",
        type=int,
        default=1,
        show_default=True,
    )

    if choice < 1 or choice > len(AVAILABLE_MODELS) + 1:
        typer.secho("Invalid choice", fg=typer.colors.RED)
        return None

    if choice == len(AVAILABLE_MODELS) + 1:
        typer.echo("\nSkipping LLM setup. You can configure it later in vibegate.yaml")
        return None

    selected_model = AVAILABLE_MODELS[choice - 1]
    model_id = selected_model["id"]

    # Pull model if not already installed
    if model_id not in installed_models:
        if not pull_model(model_id):
            typer.secho(
                "\n❌ Model download failed. Skipping LLM setup.",
                fg=typer.colors.RED,
            )
            return None
    else:
        typer.secho(f"\n✅ {model_id} is already installed", fg=typer.colors.GREEN)

    # Test the model
    typer.echo("\n🧪 Testing model...")
    try:
        import ollama

        client = ollama.Client(host="http://localhost:11434")
        response = client.generate(
            model=model_id,
            prompt="Reply with just 'OK' if you can read this.",
            options={"num_predict": 5},
        )
        if response and "response" in response:
            typer.secho("✅ Model is working!", fg=typer.colors.GREEN)
        else:
            typer.secho(
                "⚠️  Model test inconclusive, but continuing...",
                fg=typer.colors.YELLOW,
            )
    except Exception as e:
        logger.debug(f"Model test failed: {e}")
        typer.secho(
            "⚠️  Couldn't test model, but configuration will be saved",
            fg=typer.colors.YELLOW,
        )

    # Return configuration
    typer.secho("\n✅ LLM setup complete!", fg=typer.colors.GREEN, bold=True)

    return {
        "enabled": True,
        "provider": "ollama",
        "model": model_id,
    }


def get_llm_config_yaml(config: dict[str, str | bool]) -> str:
    """Generate YAML configuration block for LLM settings.

    Args:
        config: LLM configuration from wizard

    Returns:
        YAML string to append to vibegate.yaml
    """
    model = config.get("model", "codellama:7b")

    return f"""
llm:
  enabled: true
  provider: ollama
  cache_dir: .vibegate/llm_cache
  ollama:
    base_url: http://localhost:11434
    model: {model}
    temperature: 0.3
  features:
    explain_findings: true
    generate_prompts: true
"""
