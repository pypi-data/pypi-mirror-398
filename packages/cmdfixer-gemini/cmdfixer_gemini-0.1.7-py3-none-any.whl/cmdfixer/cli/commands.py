import click
from pydantic.v1.datetime_parse import MAX_NUMBER

from cmdfixer.executor.executor import CommandExecutor
from cmdfixer.llm.gemini_preview_llm import GeminiPreviewLLM
from pathlib import Path
import os
import toml

CONFIG_DIR = Path.home() / ".cmdfixer"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@click.group()
def cmdfix():
    """CmdFixer CLI: Fix corrupted shell commands using AI."""
    pass


def get_api_key():
    if CONFIG_FILE.exists():
        config = toml.load(CONFIG_FILE)
        return config.get("GEMINI_API_KEY")
    return None


@cmdfix.command()
@click.argument('user_input', nargs=-1)
@click.option('--run', is_flag=True, default=False, help='Execute the suggested command')
def fix(user_input, run):
    """Fix corrupted shell commands using AI."""
    api_key = get_api_key()
    if api_key is None:
        click.echo("No API key found. Try 'cmdfix setup'")
        return

    llm = GeminiPreviewLLM(api_key)
    executor = CommandExecutor(enabled=False)
    # Get suggestions from LLM
    suggestions = llm.send_request(user_input)

    # Ensure suggestions is a list
    if not isinstance(suggestions, list):
        suggestions = [suggestions]

    # Show numbered list to the user
    click.echo("Suggested commands:")
    for i, cmd in enumerate(suggestions, start=1):
        click.echo(f"{i}: {cmd}")

    # Let the user pick one
    choice = 1
    if len(suggestions) > 1:
        choice = click.prompt(f"Choose a command to use [1-{len(suggestions)}]", type=int, default=1)

    selected_command = suggestions[choice - 1]

    if run:
        click.echo(f"Executing: {selected_command}")
        executor.enabled = True
        executor.execute(selected_command)
    else:
        click.echo(f"Selected command (copy & paste to run):\n{selected_command}")


@cmdfix.command()
def setup():
    """
       First-time setup: ask for API key and store it locally.
    """
    click.echo(r"Get your Gemini API key from: https://aistudio.google.com/api-keys")
    api_key = click.prompt("Enter your API key", hide_input=True)

    max_number_of_suggestions = click.prompt("Enter max number of resulte per fix")

    try:
        max_number_of_suggestions = int(max_number_of_suggestions)
    except ValueError:
        max_number_of_suggestions = 3
    # Make config directory if it doesn't exist
    CONFIG_DIR.mkdir(exist_ok=True)

    # Save API key to config file
    config_data = {"GEMINI_API_KEY": api_key, "MAX_NUMBER_OF_SUGGESTIONS": max_number_of_suggestions}
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config_data, f)

    click.echo(f"API key saved to {CONFIG_FILE}. It will be used automatically in future runs.")
