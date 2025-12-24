import typer
import sys
import os
import json
import base64
import pyotp
import pyfiglet
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

from .config import ensure_config_dir, SESSION_FILE
from .auth import AuthManager
from .client import FirestoreClient
from .crypto import CryptoEngine

app = typer.Typer(help="locknkeycmd: Zero-Knowledge Secret Management CLI", add_completion=False)
console = Console()
auth_manager = AuthManager()

# Project ID - Hardcoded for demo/MVP
FIREBASE_PROJECT_ID = "lockbox-45257"

def show_banner():
    banner = pyfiglet.figlet_format("locknkeycmd", font="slant")
    console.print(f"[cyan]{banner}[/cyan]")
    console.print("[dim]Secure, Zero-Knowledge Secret Management[/dim]\n")

def show_help(ctx: typer.Context):
    show_banner()
    console.print(ctx.get_help())

def get_client(token_data: dict) -> FirestoreClient:
    return FirestoreClient(FIREBASE_PROJECT_ID, token_data.get('token'))

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context, 
    show: bool = typer.Option(False, "--show", help="Display current logged-in account"),
    org: bool = typer.Option(False, "--org", help="Display organization details"),
    proj: bool = typer.Option(False, "--proj", help="Display project details"),
    help: bool = typer.Option(False, "-h", "--help", help="Display help") # Override help
):
    """
    locknkeycmd CLI.
    Usage: locknkeycmd run [FLAGS] PROJECT_ID_OR_NAME -- COMMAND [ARGS]
    """
    if help:
        show_help(ctx)
        raise typer.Exit()

    # If no options and no command, show banner + help
    if ctx.invoked_subcommand is None and not any([show, org, proj]):
        show_help(ctx)
        raise typer.Exit()

    if show or org or proj:
        token_data = auth_manager.get_stored_token()
        if not token_data:
            console.print(Panel("[red]Not logged in.[/red]", title="Status", border_style="red"))
            raise typer.Exit()

        # Handle Org Listing
        if org:
            list_orgs_logic(token_data)
        
        # Handle Project Listing
        elif proj:
            list_projects_logic(token_data)

        # Handle Show (User Info)
        elif show:
            if 'email' in token_data:
                 console.print(Panel(f"Logged in as: [bold green]{token_data['email']}[/bold green]", title="Current Session", border_style="cyan"))
            elif 'uid' in token_data:
                 console.print(Panel(f"Logged in as UID: [bold green]{token_data['uid']}[/bold green]", title="Current Session", border_style="cyan"))

        # If a subcommand was invoked, let it pass through (but we checked invoked_subcommand is None if no options)
        # But if options are set, we might not want to run subcommand? 
        # Node behavior: flags are actions.
        if ctx.invoked_subcommand: 
             return # Let subcommand run if any? 
        else:
             raise typer.Exit()

    ensure_config_dir()

def list_orgs_logic(token_data):
    uid = token_data.get('uid')
    client = get_client(token_data)
    
    with console.status("Fetching organizations...", spinner="dots"):
        try:
             # Refresh check could go here
             query = {
                "from": [{"collectionId": "organizations"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "memberIds"},
                        "op": "ARRAY_CONTAINS",
                        "value": {"stringValue": uid}
                    }
                }
            }
             orgs = client.run_query("organizations", query)
        except Exception as e:
            if "401" in str(e):
                 # Simple refresh logic
                 try:
                    new_token = client.exchange_refresh_token(token_data.get('token'))
                    client.auth_token = new_token
                    orgs = client.run_query("organizations", query)
                 except:
                     console.print("[red]Auth failed, please login again.[/red]")
                     return
            else:
                 console.print(f"[red]Error fetching orgs: {e}[/red]")
                 return

    console.print(Panel(f"[bold]Found {len(orgs)} Organizations[/bold]", style="cyan"))
    for o in orgs:
         members = o.get('memberIds', [])
         console.print(f"[bold cyan]ID: {o['id']}[/bold cyan]")
         console.print(f"[dim]Owner: {o.get('ownerId', 'Unknown')}[/dim]")
         console.print(f"[dim]Members: {members}[/dim]")
         console.print("")

def list_projects_logic(token_data):
    uid = token_data.get('uid')
    client = get_client(token_data)

    # 1. Get Orgs first
    with console.status("Fetching projects...", spinner="dots"):
        try:
             query = {
                "from": [{"collectionId": "organizations"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "memberIds"},
                        "op": "ARRAY_CONTAINS",
                        "value": {"stringValue": uid}
                    }
                }
            }
             orgs = client.run_query("organizations", query)
        except Exception as e:
             console.print(f"[red]Error fetching projects: {e}[/red]")
             return

    # 2. Iterate Orgs
    for o in orgs:
        console.print(f"[bold]Org: {o['id']}[/bold]")
        proj_path = f"organizations/{o['id']}/projects"
        try:
            projects = client.list_documents(proj_path)
            if not projects:
                 console.print("[dim]  (No projects)[/dim]")
            for p in projects:
                name = p.get('name', p['id'])
                console.print(f"  [bold green]➤ {name}[/bold green] [dim]({p['id']})[/dim]")
        except:
             console.print("[yellow]  (Failed to list projects)[/yellow]")
        console.print("")


@app.command()
def login():
    """
    Authenticate with Firebase via browser.
    """
    try: 
        with console.status("Waiting for browser login...", spinner="dots") as status:
             # We can't really visually simulate the waiting inside logic easily without callbacks, 
             # but AuthManager.login_flow prints messages.
             # Let's just run it.
             auth_manager.login_flow()
        
        console.print(Panel("Login successful!\nYou are now authenticated with Lockbox.", title="Welcome", border_style="green"))
    except Exception as e:
        console.print(Panel(f"{e}", title="Login Error", border_style="red"))

@app.command()
def logout():
    """
    Remove stored credentials.
    """
    auth_manager.logout()
    if SESSION_FILE.exists():
        os.remove(SESSION_FILE)
    console.print(Panel("You have been logged out.", title="Logout", border_style="blue"))

@app.command()
def init():
    """
    Initialize LocknKey for this session (unlock vault).
    """
    token_data = auth_manager.get_stored_token()
    if not token_data:
        console.print(Panel("Please run 'locknkeycmd login' first.", title="Authentication Required", border_style="red"))
        raise typer.Exit(code=1)
    
    uid = token_data.get('uid')
    client = FirestoreClient(FIREBASE_PROJECT_ID, token_data.get('token')) 

    try:
        with console.status("Fetching vault...", spinner="dots"):
            try:
                user_doc = client.get_document("users", uid)
            except Exception as e:
                if "401" in str(e): # Refresh
                     new_token = client.exchange_refresh_token(token_data.get('token'))
                     client.auth_token = new_token
                     # Update stored token?Ideally yes but auth_manager stores structure.
                     # For now just use in memory.
                     user_doc = client.get_document("users", uid)
                else:
                    raise e
                    
        if not user_doc:
            console.print(Panel("User not found. Please sign up on Web Dashboard.", title="Account Error", border_style="red"))
            raise typer.Exit(code=1)

        # 2FA Check
        two_factor = user_doc.get('twoFactor', {})
        if not two_factor.get('enabled') or not two_factor.get('secret'):
             console.print(Panel("2FA is not enabled.\nPlease set up Google Authenticator on the dashboard.", title="Security Alert", border_style="red"))
             raise typer.Exit(code=1)
        
        secret = two_factor['secret']

        # Prompt for TOTP
        totp_code = Prompt.ask("Enter Google Authenticator Code")
        
        totp = pyotp.TOTP(secret)
        if not totp.verify(totp_code):
             console.print(Panel("Invalid Authenticator Code.", title="Access Denied", border_style="red"))
             raise typer.Exit(code=1)

        # Key Derivation
        epk = user_doc['encryptedPrivateKey']
        salt = base64.b64decode(epk['salt'])
        ciphertext = epk['ciphertext']
        nonce = epk['nonce']

        with console.status("Deriving security keys...", spinner="dots"):
             # Use TOTP Secret as password
             master_key = CryptoEngine.derive_master_key(secret, salt)
             private_key = CryptoEngine.decrypt_private_key(ciphertext, nonce, master_key)
        
        if not private_key:
             console.print(Panel("Secret mismatch. Your keys could not be derived.", title="Decryption Failed", border_style="red"))
             raise typer.Exit(code=1)

        # Save session
        with open(SESSION_FILE, 'w') as f:
            json.dump({
                "master_key": base64.b64encode(master_key).decode('utf-8'),
                "uid": uid
            }, f)
            
        console.print(Panel("Session initialized successfully.\nYou can now run commands.", title="Vault Unlocked", border_style="green"))

    except Exception as e:
        console.print(Panel(f"{e}", title="Init Failed", border_style="red"))
        raise typer.Exit(code=1)

def get_session():
    if not SESSION_FILE.exists():
        return None
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def find_project_path(project_identifier: str, uid: str, client: FirestoreClient) -> Optional[str]:
    # Query orgs
    query = {
        "from": [{"collectionId": "organizations"}],
        "where": {
            "fieldFilter": {
                "field": {"fieldPath": "memberIds"},
                "op": "ARRAY_CONTAINS",
                "value": {"stringValue": uid}
            }
        }
    }
    orgs = client.run_query("organizations", query)
    
    for org in orgs:
        org_id = org['id']
        projects_collection = f"organizations/{org_id}/projects"
        
        # 1. Try Direct ID
        try:
             doc = client.get_document(projects_collection, project_identifier)
             if doc: return f"{projects_collection}/{project_identifier}"
        except: pass
        
        # 2. Try Name
        try:
            projects = client.list_documents(projects_collection)
            for p in projects:
                if p.get('name') == project_identifier:
                    return f"{projects_collection}/{p['id']}"
        except: pass
            
    return None

@app.command()
def run(
    project_id: str = typer.Argument(..., help="Project ID or Name"), 
    cmd: list[str] = typer.Argument(None, help="Command to run"),
    dev: bool = typer.Option(True, "-d", "--dev", help="Use development environment"),
    staging: bool = typer.Option(False, "-s", "--staging", help="Use staging environment"),
    prod: bool = typer.Option(False, "-p", "--prod", help="Use production environment")
):
    """
    Run a command with secrets injected into the environment.
    """
    try:
        env_id = "dev"
        if staging: env_id = "staging"
        if prod: env_id = "prod"

        session = get_session()
        if not session:
            console.print(Panel("Run 'locknkeycmd init' first.", title="Session Locked", border_style="red"))
            raise typer.Exit(code=1)
            
        token_data = auth_manager.get_stored_token()
        client = FirestoreClient(FIREBASE_PROJECT_ID, token_data['token'])
        uid = session['uid']
        master_key = base64.b64decode(session['master_key'])
        
        # Refresh check logic (simplified)
        try:
             client.get_document("users", uid)
        except Exception as e:
            if "401" in str(e):
                 new_token = client.exchange_refresh_token(token_data.get('token'))
                 client.auth_token = new_token
        
        # Decrypt Private Key (Assuming session key is good)
        # We need to re-fetch user doc to get salt/nonce if we wanted to be stateless, 
        # but we derived master_key already. 
        # Wait, to decrypt private key we need the User Doc's encryptedPrivateKey blob again.
        # The session only stores the Master Key.
        user_doc = client.get_document("users", uid)
        epk = user_doc['encryptedPrivateKey']
        
        private_key = CryptoEngine.decrypt_private_key(
            epk['ciphertext'], 
            epk['nonce'], 
            master_key
        )
        
        if not private_key:
             console.print(Panel("Decryption failed. Re-run init.", title="Session Invalid", border_style="red"))
             raise typer.Exit(code=1)
             
        # Find Project
        full_project_path = find_project_path(project_id, uid, client)
        if not full_project_path:
             console.print(f"[red]Project '{project_id}' not found.[/red]")
             raise typer.Exit(code=1)
             
        # Fetch Project Key
        key_doc = client.get_document(f"{full_project_path}/keys", uid)
        if not key_doc:
             console.print(f"[red]Access denied (Key not found).[/red]")
             raise typer.Exit(code=1)
             
        project_key_bytes = CryptoEngine.decrypt_project_key(
            key_doc['ciphertext'],
            key_doc['nonce'],
            key_doc['ephemeralPublicKey'],
            private_key
        )
        
        # List Secrets
        secrets_path = f"{full_project_path}/environments/{env_id}/secrets"
        secret_docs = client.list_documents(secrets_path)
        
        secrets_env = {}
        for doc in secret_docs:
            try:
                decrypted_bytes = CryptoEngine.decrypt_secret(
                    doc['ciphertext'],
                    doc['nonce'],
                    project_key_bytes
                )
                payload = json.loads(decrypted_bytes.decode('utf-8'))
                secrets_env[payload['name']] = payload['value']
            except: pass

        if not cmd:
            console.print(Panel(f"Secrets: {project_id} ({env_id})", border_style="green"))
            console.print(secrets_env)
            return

        # Execute
        command_str = " ".join(cmd)
        
        env = os.environ.copy()
        env.update(secrets_env)
        
        if sys.platform == 'win32':
             import subprocess
             subprocess.run(cmd, env=env, shell=True)
        else:
            os.execvpe(cmd[0], cmd, env)

    except Exception as e:
        console.print(Panel(f"{e}", title="Runtime Error", border_style="red"))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
