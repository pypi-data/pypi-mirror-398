import click
import pyperclip
from pathlib import Path
from rich import print
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Keep these relative imports
from .core import VaultManager, VaultError
from .storage import VAULT_FILE
from .utils import generate_secure_password

console = Console()

def get_vault():
    return VaultManager(VAULT_FILE)

def prompt_master_password(confirm: bool = False) -> str:
    if confirm:
        while True:
            pwd = Prompt.ask("Enter master password", password=True)
            if len(pwd) < 8:
                print("[red]Password is too short (min 8 chars).[/red]")
                continue
            pwd2 = Prompt.ask("Confirm master password", password=True)
            if pwd == pwd2:
                return pwd
            print("[red]Passwords do not match. Try again.[/red]")
    else:
        return Prompt.ask("Enter master password", password=True)

@click.group()
@click.version_option(version="0.1.0", prog_name="termvault")
def app():
    """TermVault: A secure, terminal-only password manager."""
    pass

@app.command()
def init():
    """Initialize a new password vault."""
    vault = get_vault()
    if vault.is_initialized():
        print(f"[yellow]Vault already exists at {VAULT_FILE}[/yellow]")
        return

    print("[bold green]Welcome to TermVault![/bold green]")
    print("We will create a new encrypted vault.")
    
    password = prompt_master_password(confirm=True)
    
    try:
        vault.initialize(password)
        print(f"[green]Vault initialized successfully at {VAULT_FILE}[/green]")
    except Exception as e:
        print(f"[red]Error initializing vault: {e}[/red]")

@app.command()
@click.argument('service')
@click.argument('username')
@click.option('--generate', '-g', is_flag=True, help="Generate a random password")
def add(service, username, generate):
    """Add a new password to the vault.
    
    SERVICE: The service name (e.g., github, gmail)
    USERNAME: The username for this service
    """
    vault = get_vault()
    if not vault.is_initialized():
        print("[red]Vault not found. Run 'termvault init' first.[/red]")
        raise click.Exit(1)

    # 1. Authenticate first
    master_password = prompt_master_password()
    try:
        vault.unlock(master_password)
    except VaultError:
        print("[red]Invalid master password.[/red]")
        raise click.Exit(1)

    # 2. Check existence
    existing_secrets = vault.get_secrets(service)
    # Check if this specific username exists
    user_exists = any(s["username"] == username for s in existing_secrets)
    
    if user_exists:
        overwrite = Confirm.ask(f"Service '{service}' with username '{username}' already exists. Overwrite?")
        if not overwrite:
            return

    # 3. Get password
    if generate:
        secret_password = generate_secure_password()
        print(f"[green]Generated password for {service} ({username}).[/green]")
    else:
        secret_password = Prompt.ask(f"Enter password for {service} ({username})", password=True)

    # 4. Save
    vault.add_secret(service, username, secret_password)
    print(f"[green]Secret for '{service}' ({username}) added successfully.[/green]")

@app.command()
@click.argument('service')
@click.option('--show', '-s', is_flag=True, help="Print password to console instead of copying to clipboard")
def get(service, show):
    """Retrieve a password from the vault.
    
    SERVICE: The service name to retrieve
    """
    vault = get_vault()
    if not vault.is_initialized():
        print("[red]Vault not found. Run 'termvault init' first.[/red]")
        raise click.Exit(1)

    master_password = prompt_master_password()
    try:
        vault.unlock(master_password)
    except VaultError:
        print("[red]Invalid master password.[/red]")
        raise click.Exit(1)

    secrets = vault.get_secrets(service)
    if not secrets:
        print(f"[red]Service '{service}' not found.[/red]")
        raise click.Exit(1)

    selected_secret = None
    if len(secrets) == 1:
        selected_secret = secrets[0]
    else:
        print(f"[cyan]Multiple accounts found for '{service}':[/cyan]")
        for idx, s in enumerate(secrets):
            print(f"  {idx + 1}. {s['username']}")
        
        choice = Prompt.ask("Select account", choices=[str(i+1) for i in range(len(secrets))])
        selected_secret = secrets[int(choice) - 1]

    username = selected_secret["username"]
    password = selected_secret["password"]

    print(f"[bold]Service:[/bold] {service}")
    print(f"[bold]Username:[/bold] {username}")
    
    if show:
        print(f"[bold]Password:[/bold] {password}")
    else:
        try:
            pyperclip.copy(password)
            print("[green]Password copied to clipboard![/green]")
        except pyperclip.PyperclipException:
            print("[yellow]Clipboard unavailable. Printing password:[/yellow]")
            print(f"Password: {password}")

@app.command()
def list():
    """List all stored services."""
    vault = get_vault()
    if not vault.is_initialized():
        print("[red]Vault not found. Run 'termvault init' first.[/red]")
        raise click.Exit(1)

    master_password = prompt_master_password()
    try:
        vault.unlock(master_password)
    except VaultError:
        print("[red]Invalid master password.[/red]")
        raise click.Exit(1)

    services = vault.list_services()
    if not services:
        print("Vault is empty.")
        return

    table = Table(title="Vault Services")
    table.add_column("Service", style="cyan")
    table.add_column("Username", style="magenta")

    for service in services:
        secrets = vault.get_secrets(service)
        for s in secrets:
            table.add_row(service, s["username"])

    console.print(table)

@app.command()
@click.argument('service')
def delete(service):
    """Delete a service from the vault.
    
    SERVICE: The service name to delete
    """
    vault = get_vault()
    if not vault.is_initialized():
        print("[red]Vault not found. Run 'termvault init' first.[/red]")
        raise click.Exit(1)

    master_password = prompt_master_password()
    try:
        vault.unlock(master_password)
    except VaultError:
        print("[red]Invalid master password.[/red]")
        raise click.Exit(1)

    secrets = vault.get_secrets(service)
    if not secrets:
        print(f"[red]Service '{service}' not found.[/red]")
        raise click.Exit(1)

    target_username = None
    if len(secrets) > 1:
        print(f"[cyan]Multiple accounts found for '{service}':[/cyan]")
        for idx, s in enumerate(secrets):
            print(f"  {idx + 1}. {s['username']}")
        print(f"  A. All accounts (Delete Service)")
        
        choices = [str(i+1) for i in range(len(secrets))] + ["A", "a"]
        choice = Prompt.ask("Select account to delete", choices=choices)
        
        if choice.lower() == "a":
             target_username = None # Delete all
        else:
             target_username = secrets[int(choice) - 1]["username"]
    
    msg = f"Are you sure you want to delete '{service}'"
    if target_username:
        msg += f" (user: {target_username})"
    else:
        msg += " (ALL accounts)"
    
    confirm = Confirm.ask(f"{msg}?")
    if confirm:
        vault.delete_secret(service, target_username)
        print(f"[green]Deleted successfully.[/green]")

@app.command()
@click.option('--length', '-l', default=20, help="Length of the password")
@click.option('--symbols/--no-symbols', default=True, help="Include symbols in the password")
def gen(length, symbols):
    """Generate a random strong password."""
    pwd = generate_secure_password(length, symbols)
    print(f"[bold]Generated Password:[/bold] {pwd}")
    try:
        pyperclip.copy(pwd)
        print("[green](Copied to clipboard)[/green]")
    except:
        pass

if __name__ == "__main__":
    app()