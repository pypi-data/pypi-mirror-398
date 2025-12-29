
import click
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
import json
from enc_client.enc import Enc

console = Console()

# Initialize logic class
enc_manager = Enc()

def is_strong_password(p):
    """Check if a password meets the strength requirements."""
    if len(p) < 8: return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in p): return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in p): return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() or not c.isalnum() for c in p): return False, "Password must contain at least one number or special character."
    return True, ""

def interactive_unmount_timer(enc_manager, name, project_dir, timeout=5):
    """Wait for user input to stay mounted, otherwise auto-unmount."""
    import sys
    import select
    import time
    
    # Try to use raw mode for single-key 'y' response
    try:
        import termios
        import tty
        use_raw = sys.stdin.isatty()
    except ImportError:
        use_raw = False

    console.print(f"\n[bold yellow]Auto-Unmount Notice:[/bold yellow]")
    console.print(f"Project '[cyan]{name}[/cyan]' is securely mounted.")
    console.print(f"It will automatically unmount in [bold]{timeout}[/bold] seconds.")
    if use_raw:
        console.print(f"Press [bold cyan]'y'[/bold cyan] to stay mounted, or any other key to unmount now.")
    else:
        console.print(f"Type [bold cyan]'y'[/bold cyan] and press [bold cyan]ENTER[/bold cyan] to stay mounted.")

    if use_raw:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            start_time = time.time()
            while time.time() - start_time < timeout:
                remaining = int(timeout - (time.time() - start_time))
                # Write to stdout directly since console.print might add newlines
                sys.stdout.write(f"\r[Time Remaining: {remaining}s] Press 'y' to stay... ")
                sys.stdout.flush()
                
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    char = sys.stdin.read(1).lower()
                    if char == 'y':
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        console.print("\n\n[bold green]Confirmed![/bold green] Staying mounted. Enjoy your secure workspace!")
                        return True
                    else:
                        break # User pressed something else
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    else:
        # Fallback for systems without termios/tty
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            line = sys.stdin.readline().strip().lower()
            if line == 'y':
                console.print("[bold green]Staying mounted.[/bold green]")
                return True

    console.print("\n\n[bold yellow]Unmounting...[/bold yellow] Closing secure bridge.")
    enc_manager.project_unmount(name, project_dir)
    return False

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', is_flag=True, help="Show version.")
def cli(ctx, version):
    """ENC Client - Secure Remote Access"""
    if version:
        console.print("ENC Client v0.1.5")
        ctx.exit()
    
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())

@cli.group("show", invoke_without_command=True)
@click.option("-v", "--verbose", is_flag=True, help="Show full configuration details.")
@click.option("-a", "--access", is_flag=True, help="Show access rights.")
@click.pass_context
def show_group(ctx, verbose, access):
    """Show configuration or access rights."""
    if ctx.invoked_subcommand is None:
        if access:
            ctx.invoke(show_access)
        else:
            ctx.invoke(show_config, verbose=verbose)

@show_group.command("config")
@click.option("-v", "--verbose", is_flag=True, help="Show full configuration details.")
def show_config(verbose):
    """Display current configuration."""
    cfg = enc_manager.config
    session_id = cfg.get("session_id")
    
    table = Table(title="ENC Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    # Calculate active projects
    active_projects = "None"
    if session_id:
        projects = enc_manager.session_manager.get_active_projects(session_id)
        if projects:
            active_projects = ", ".join(projects)

    for k, v in cfg.items():
        if k in ["url", "ssh_key"] and not verbose:
            continue
        if k == "context": # Replace context with active projects
            k = "active_projects"
            v = active_projects
        table.add_row(k, str(v))
        
    console.print(table)

@show_group.command("access")
def show_access():
    """Show access rights from session file."""
    session_id = enc_manager.config.get("session_id")
    if not session_id:
        console.print("[yellow]No active session found. Login to see access rights.[/yellow]")
        return

    session_data = enc_manager.get_session_data()
    if not session_data:
        console.print("[red]Invalid session data.[/red]")
        return
        
    allowed = session_data.get("allowed_commands", [])
    username = session_data.get("username", "Unknown")
    
    table = Table(title=f"Access Rights for {username}")
    table.add_column("Permission Type", style="cyan")
    table.add_column("Details", style="green")
    
    if "*" in allowed:
         table.add_row("Root Access", "All Commands Allowed (*)")
    else:
         for cmd in allowed:
             table.add_row("Command", cmd)
             
    console.print(table)

@cli.command("set-url")
@click.argument("url")
def set_url(url):
    """Set the ENC Server URL."""
    enc_manager.set_config_value("url", url)
    console.print(f"Set URL to: [green]{url}[/green]")

@cli.command("set-username")
@click.argument("username")
def set_username(username):
    """Set the username."""
    enc_manager.set_config_value("username", username)
    console.print(f"Set Username to: [green]{username}[/green]")

@cli.command("set-ssh-key")
@click.argument("ssh_key")
def set_ssh_key(ssh_key):
    """Set the SSH Private Key path."""
    enc_manager.set_config_value("ssh_key", ssh_key)
    console.print(f"Set SSH Key to: [green]{ssh_key}[/green]")

@cli.command("init")
@click.argument("path", required=False, default=".")
def init(path):
    """Initialize ENC configuration."""
    console.print(Panel("Welcome to ENC Configuration Wizard", title="ENC Init", style="bold cyan"))
    
    # 1. Choose Location
    config_type = Prompt.ask("Initialize Global (~/.enc) or Local (./.enc) config?", choices=["global", "local"], default="global")
    
    target_path = None
    if config_type == "local":
        path = os.path.abspath(path)
        console.print(f"Initializing LOCAL configuration in [cyan]{path}/.enc[/cyan]")
        target_path = os.path.join(path, ".enc", "config.json")
    else:
        console.print("Initializing GLOBAL configuration in [cyan]~/.enc[/cyan]")
        target_path = os.path.expanduser("~/.enc/config.json")
        
    # Check if exists
    if os.path.exists(target_path):
        console.print(f"[yellow]Warning: Configuration already exists at {target_path}[/yellow]")
        if not click.confirm("Do you want to overwrite it?"):
            console.print("[red]Aborted.[/red]")
            return

    # 2. Capture Details
    url = Prompt.ask("Enter ENC Server URL", default="http://localhost:2222")
    username = Prompt.ask("Enter Username")
    ssh_key = Prompt.ask("Enter SSH Key Path", default="")
    
    # 3. Save
    enc_manager.init_config(url, username, ssh_key, target_path=target_path)
    console.print(f"[bold green]Configuration initialized at {target_path}[/bold green]")
    console.print("Run 'enc check-connection' to verify.")

@cli.command("internal-watchdog", hidden=True)
@click.option("--ppid", type=int, help="Parent PID to monitor")
def internal_watchdog(ppid):
    """Hidden command to monitor session in background."""
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return
    enc_manager.session_manager.monitor_session(enc_manager.logout, ppid=ppid)

@cli.group()
def setup():
    """Setup and configuration utilities."""
    pass

@cli.command("install")
def install():
    """Install system dependencies and configure environment."""
    import platform
    import subprocess
    import shutil

    console.print(Panel("ENC Installation & Setup", title="enc install", style="bold cyan"))
    
    os_type = platform.system()
    console.print(f"Detected OS: [cyan]{os_type}[/cyan]")
    
    # 1. Check/Install sshfs
    if shutil.which("sshfs"):
        console.print("[green]✓ sshfs is already installed.[/green]")
    else:
        console.print("[yellow]! sshfs is missing.[/yellow]")
        if click.confirm("Do you want to attempt automatic installation of sshfs?"):
             if os_type == "Darwin":
                 if shutil.which("brew"):
                     console.print("Installing macFUSE and sshfs via Homebrew...")
                     try:
                        # macfuse check might be tricky as it's a cask, just try install
                        subprocess.run(["brew", "install", "--cask", "macfuse"], check=False)
                        subprocess.run(["brew", "install", "gromgit/homebrew-fuse/sshfs"], check=True) 
                        console.print("[green]sshfs installed successfully.[/green]")
                     except subprocess.CalledProcessError:
                        console.print("[red]Homebrew installation failed. Please install sshfs manually.[/red]")
                 else:
                     console.print("[red]Homebrew not found. Please install sshfs manually.[/red]")
             elif os_type == "Linux":
                 # Heuristic for Linux package managers
                 pkg_managers = {
                     "apt-get": ["sudo", "apt-get", "install", "-y", "sshfs"],
                     "dnf": ["sudo", "dnf", "install", "-y", "sshfs"],
                     "yum": ["sudo", "yum", "install", "-y", "sshfs"],
                     "pacman": ["sudo", "pacman", "-S", "--noconfirm", "sshfs"]
                 }
                 
                 installed = False
                 for pm, cmd in pkg_managers.items():
                     if shutil.which(pm):
                         console.print(f"Installing sshfs via {pm}...")
                         try:
                             if pm == "apt-get":
                                 subprocess.run(["sudo", "apt-get", "update"], check=False)
                             subprocess.run(cmd, check=True)
                             console.print(f"[green]sshfs installed successfully via {pm}.[/green]")
                             installed = True
                             break
                         except subprocess.CalledProcessError:
                             console.print(f"[red]Failed to install via {pm}.[/red]")
                 
                 if not installed:
                      console.print("[red]No supported package manager found or installation failed. Please install sshfs manually.[/red]")
             else:
                 console.print("[red]Automatic installation not supported for this OS. Please install sshfs manually.[/red]")

    # 2. Configure PATH
    shell = os.environ.get("SHELL", "")
    rc_file = None
    if "zsh" in shell:
        rc_file = os.path.expanduser("~/.zshrc")
    elif "bash" in shell:
        rc_file = os.path.expanduser("~/.bashrc")
        if os_type == "Darwin" and not os.path.exists(rc_file):
            rc_file = os.path.expanduser("~/.bash_profile")
    
    bin_dir = os.path.expanduser("~/.local/bin") # Standard user bin dir where pip often installs
    
    if rc_file and os.path.exists(rc_file):
        # Check if bin_dir is in PATH (roughly)
        # Or better, check if we've already added our marker
        try:
            with open(rc_file, "r") as f:
                content = f.read()
            
            if "# Added by enc-cli installer" not in content and bin_dir not in os.environ.get("PATH", ""):
                 console.print(f"It is recommended to ensure [cyan]{bin_dir}[/cyan] is in your PATH.")
                 if click.confirm(f"Add {bin_dir} to PATH in {rc_file}?"):
                     with open(rc_file, "a") as f:
                         f.write("\n")
                         f.write("# Added by enc-cli installer\n")
                         f.write(f'export PATH="{bin_dir}:$PATH"\n')
                     console.print(f"[green]Updated {rc_file}. Please restart your terminal or source the file.[/green]")
            else:
                console.print(f"[green]✓ PATH configuration checks pass (found marker or bin_dir implied).[/green]")
        except Exception as e:
            console.print(f"[red]Error checking/updating RC file: {e}[/red]")
    else:
        console.print(f"[yellow]Could not detect shell RC file. Please ensure '{bin_dir}' is in your PATH.[/yellow]")
    
    console.print("\n[bold green]Setup Complete![/bold green] You can now run 'enc init' to configure your client.")

@cli.command("uninstall")
def uninstall():
    """Uninstall configuration and cleanup environment."""
    import shutil
    import subprocess
    import platform
    
    console.print(Panel("[bold red]ENC Uninstallation[/bold red]", style="red"))
    
    if not click.confirm("This will remove your ENC configuration (~/.enc). Continue?"):
        return

    # 0. Unmount all first to prevent hangs
    try:
        console.print("Unmounting all projects...")
        enc_manager.unmount_all()
    except Exception as e:
        console.print(f"[yellow]Warning during unmount: {e}[/yellow]")

    # 1. Remove ~/.enc
    enc_dir = os.path.expanduser("~/.enc")
    if os.path.exists(enc_dir):
        console.print(f"Removing configuration at {enc_dir}...")
        try:
            shutil.rmtree(enc_dir)
            console.print("[green]Removed configuration directory.[/green]")
        except Exception as e:
            console.print(f"[red]Error removing {enc_dir}: {e}[/red]")
    else:
        console.print(f"Configuration directory {enc_dir} not found.")
        
    # 2. Cleanup PATH
    shell = os.environ.get("SHELL", "")
    rc_file = None
    if "zsh" in shell:
        rc_file = os.path.expanduser("~/.zshrc")
    elif "bash" in shell:
        rc_file = os.path.expanduser("~/.bashrc")
        if platform.system() == "Darwin" and not os.path.exists(rc_file):
            rc_file = os.path.expanduser("~/.bash_profile")

    if rc_file and os.path.exists(rc_file):
        try:
            with open(rc_file, "r") as f:
                lines = f.readlines()
            
            new_lines = []
            removed = False
            skip_next = False
            
            # Simple parser to remove the lines we added
            # We look for "# Added by enc-cli installer" and the following line
            for i, line in enumerate(lines):
                 if skip_next:
                     skip_next = False
                     continue
                 if "# Added by enc-cli installer" in line:
                     removed = True
                     # The next line should be the export, skip it
                     skip_next = True 
                     continue
                 new_lines.append(line)
            
            if removed:
                if click.confirm(f"Remove enc-cli PATH addition from {rc_file}?"):
                    with open(rc_file, "w") as f:
                        f.writelines(new_lines)
                    console.print(f"[green]Cleaned up {rc_file}.[/green]")
        except Exception as e:
             console.print(f"[red]Error cleaning RC file: {e}[/red]")

    # 3. Optional sshfs removal
    if shutil.which("sshfs"):
        if click.confirm("Do you want to uninstall sshfs? (Warning: This might affect other apps)"):
            os_type = platform.system()
            if os_type == "Darwin":
                 if shutil.which("brew"):
                     console.print("Uninstalling sshfs via Homebrew...")
                     subprocess.run(["brew", "uninstall", "gromgit/homebrew-fuse/sshfs"], check=False)
                     subprocess.run(["brew", "uninstall", "--cask", "macfuse"], check=False)
            elif os_type == "Linux":
                 console.print("[yellow]Please uninstall sshfs manually using your package manager (apt/dnf/etc).[/yellow]")

    console.print("\n[bold green]Cleanup complete.[/bold green]")
    console.print("To fully remove the enc-cli package, run:\n  [bold]pip uninstall enc-cli[/bold]")


@setup.command("ssh-key")
@click.option("--password", default=None, help="Password for auth if SSH key missing")
def setup_ssh_key(password):
    """Auto-generate and register SSH key with server."""
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return
    enc_manager.setup_ssh_key_flow(password=password)

# --- Connection Commands ---

@cli.command("check-connection")
def check_connection():
    """Check connectivity to the configured URL."""
    enc_manager.check_connection()

@cli.command()
@click.option("--password", default=None, help="Password for non-interactive login")
def login(password):
    """Authenticate with the ENC Server."""
    if not enc_manager.login(password=password):
        raise click.ClickException("Authentication failed. Please check your credentials.")

@cli.group("project")
def project_group():
    """Manage projects."""
    pass

@project_group.command("init")
@click.argument("name", required=False)
@click.option("--directory", "-d", default=None, help="Project directory path")
@click.option("--password", "-p", default=None, help="Project password (skip prompt)")
def project_init(name, directory, password):
    """Initialize a new encrypted project on server."""
    # Check login first
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return

    if not name:
        name = click.prompt("Enter Project Name", type=str)

    # Check in session file if the project_name already exist or not
    session_data = enc_manager.get_session_data()
    if session_data and name in session_data.get("projects", []):
        console.print(f"[yellow]Project '{name}' already exists in your account.[/yellow]")
        if not click.confirm("Do you want to re-initialize it?"):
            return

    # Check permissions from session
    if not enc_manager.check_permission("server-project-init"):
        console.print("[red]Permission Denied: You are not allowed to initialize projects.[/red]")
        return
        
    # Ask for project directory
    if directory:
        project_dir = directory
    else:
        project_dir = click.prompt("Enter Project Directory", default=".", type=click.Path(file_okay=False))
    
    project_dir = os.path.abspath(project_dir)

    # Check for .enc directory within the project directory to avoid configuration conflicts
    local_enc_path = os.path.join(project_dir, ".enc")
    if os.path.exists(local_enc_path):
        console.print(Panel(
            f"[bold red]Configuration Conflict Error[/bold red]\n\n"
            f"A [cyan].enc[/cyan] folder already exists within the directory: [yellow]{project_dir}[/yellow]\n\n"
            "Initializing a new project here might overwrite or conflict with your existing ENC environment "
            "configurations, leading to unexpected behavior.\n\n"
            "[bold white]Please move the existing .enc folder or provide a different project directory.[/bold white]",
            border_style="red"
        ))
        return
    # Handle password
    if password:
        is_strong, msg = is_strong_password(password)
        if not is_strong:
             console.print(f"[red]Provided password is weak: {msg}[/red]")
             return
    else:
        # Ask for password with confirmation and validation
        while True:
            password = click.prompt("Enter Project Password", hide_input=True, confirmation_prompt=True)
            is_strong, msg = is_strong_password(password)
            if is_strong:
                break
            console.print(f"[red]{msg}[/red]")

    console.print(f"Initializing project '[cyan]{name}[/cyan]' in '[cyan]{project_dir}[/cyan]'...")
    # Note: Currently server logic might not use project_dir for vault creation, 
    # but we can pass it if we want to initialize local context there.
    # For now, we call the manager.
    if enc_manager.project_init(name, password, project_dir):
        console.print(f"[bold green]Project '{name}' initialized successfully at '[cyan]{project_dir}[/cyan]'.[/bold green]")
        
        # Interactive unmount timer
        interactive_unmount_timer(enc_manager, name, project_dir)

@project_group.command("list")
def project_list():
    """List all projects you have access to."""
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return
        
    projects = enc_manager.project_list()
    if projects is None:
        console.print("[red]Failed to retrieve project list.[/red]")
        return
        
    if not projects:
        console.print("[yellow]You don't have access to any projects yet.[/yellow]")
        return
        
    table = Table(title="Your Projects")
    table.add_column("Project Name", style="cyan")
    table.add_column("Local Mount", style="green")
    table.add_column("Server Mount", style="dim")
    table.add_column("Exec Point", style="magenta")
    
    for proj in projects:
        name = proj.get("name")
        local_mnt = proj.get("local_mount_point") or ""
        server_mnt = proj.get("server_mount_point") or ""
        exec_pt = proj.get("exec_entry_point") or ""
        is_active = proj.get("is_active")
        
        style = "blue" if is_active else None
        
        table.add_row(
            name,
            local_mnt,
            server_mnt,
            exec_pt,
            style=style
        )
        
    console.print(table)

@project_group.command("remove")
@click.argument("name")
@click.option("--password", "-p", default=None, help="Project password")
def project_remove(name, password):
    """Permanently delete a project."""
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return
    
    if not password:
         password = click.prompt("Enter Project Password (required for verification)", hide_input=True)
         
    enc_manager.project_remove(name, password)

@project_group.command("mount")
@click.argument("name")
@click.argument("directory", required=False, default="./enc_project", type=click.Path(file_okay=False))
@click.option("--password", "-p", default=None, help="Project password (skip prompt)")
def project_mount(name, directory, password):
    """Mount project for development in a specific directory."""
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return
        
    if not enc_manager.check_permission("server-project-mount"):
        console.print("[red]Permission Denied: You are not allowed to mount projects.[/red]")
        return
    
    # Check if project is already mounted to avoid asking for password unnecessarily
    if enc_manager.is_project_active(name):
        console.print(f"[yellow]Project '{name}' is already mounted locally.[/yellow]")
        return

    if not password:
        password = click.prompt("Enter Project Password", hide_input=True)

    directory = os.path.abspath(directory)
        
    console.print(f"Mounting project '[cyan]{name}[/cyan]' to '[cyan]{directory}[/cyan]'...")
    if enc_manager.project_mount(name, password, directory):
        console.print(f"[bold green]Project mounted and bridged.[/bold green]")
    else:
        console.print(f"[bold red]Mount failed.[/bold red]")

@project_group.command("unmount")
@click.argument("name", required=False)
@click.option("--forced", "-f", default=False, help="Force unmount")
def project_unmount(name, forced):
    """Unmount and close bridge for a project."""
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return
        
    if not enc_manager.check_permission("server-project-unmount"):
        console.print("[red]Permission Denied: You are not allowed to unmount projects.[/red]")
        return
        
    console.print(f"Unmounting project '[cyan]{name}[/cyan]'...")
    if enc_manager.project_unmount(name, forced=forced):
        console.print(f"[bold green]Project unmounted and bridge closed.[/bold green]")

@project_group.command("sync")
@click.argument("name")
@click.argument("local_path", type=click.Path(exists=True))
def project_sync(name, local_path):
    """Sync local files to the remote project."""
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return
        
    if not enc_manager.check_permission("server-project-sync"):
        console.print("[red]Permission Denied: You are not allowed to sync projects.[/red]")
        return
        
    console.print(f"Syncing '[cyan]{local_path}[/cyan]' -> '[cyan]{name}[/cyan]'...")
    if enc_manager.project_sync(name, local_path):
        console.print(f"[bold green]Sync Complete.[/bold green]")
    else:
        console.print(f"[bold red]Sync Failed.[/bold red]")

@project_group.command("run")
@click.argument("name")
@click.argument("command", nargs=-1)
def project_run(name, command):
    """Run a command on the remote project."""
    if not enc_manager.check_permission("server-project-run"):
        console.print("[red]Permission Denied: You are not allowed to run commands in projects.[/red]")
        return
    if not command:
        console.print("[yellow]No command provided. Starting interactive shell...[/yellow]")
        # TODO: Interactive shell support
        cmd_str = "bash" # Default to shell
    else:
        cmd_str = " ".join(command) # Naive join, assume user handles quotes or use shlex if needed upstream
    
    console.print(f"Running '[cyan]{cmd_str}[/cyan]' in project '[cyan]{name}[/cyan]'...")
    
    if enc_manager.project_run(name, cmd_str):
        # Return code handles success/fail printing usually
        pass
    else:
        # Failure message handled in manager
        pass

@cli.command()
def logout():
    if not enc_manager.config.get("session_id"):
        console.print("[yellow]Please login first.[/yellow]")
        return
    """Logout and clear local sessions."""
    if enc_manager.logout():
        console.print("[bold green]Logged out successfully.[/bold green] Local sessions cleared.")
    else:
        console.print("[yellow]No active session or error clearing session.[/yellow]")


@cli.group()
def user():
    """Manage users (admin only)."""
    pass

@user.command("list")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def user_list(json_output):
    """List users (cached in session)."""
    if not enc_manager.check_permission("user list"):
        console.print("[red]Permission Denied: You are not allowed to list users.[/red]")
        ctx.exit(1)
    users = enc_manager.user_list()
    if users:
        table = Table(title="ENC Users")
        table.add_column("Username", style="cyan")
        # If server returns more details (like role/id), we could add them.
        # Assuming simple list of strings OR list of dicts.
        # Implementation in enc.py handles dict/list return, but let's assume dicts if possible, or handle strings.
        
        # Heuristic: inspect first element
        if isinstance(users, list) and len(users) > 0:
            if isinstance(users[0], dict):
                 table.add_column("Role", style="magenta")
                 for u in users:
                     table.add_row(u.get("username", "N/A"), u.get("role", "user"))
            else:
                 for u in users:
                     table.add_row(str(u))
        elif isinstance(users, list) and len(users) == 0:
            if json_output:
                click.echo(json.dumps([]))
            else:
                console.print("[yellow]No users found.[/yellow]")
            return
            
        if json_output:
            click.echo(json.dumps(users))
        else:
            console.print(table)

@user.command("create")
@click.argument("username")
@click.option("--password",  default=None, help="User password")
@click.option("--role", type=click.Choice(["admin", "user"], case_sensitive=False), default=None, help="User role")
@click.option("--ssh-key", default=None, help="Path to public SSH key")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def user_create(username, password, role, ssh_key, json_output):
    """Create a new user on the server."""
    if not enc_manager.check_permission("user create"):
        console.print("[red]Permission Denied: You are not allowed to create users.[/red]")
        return
    
    # 1. Prompt for Role if missing
    if not role:
        role = click.prompt("Select Role", type=click.Choice(["admin", "user"], case_sensitive=False), default="user")
    
    # 2. Prompt for Password if missing
    if not password:
        while True:
            password = click.prompt("Enter Password", hide_input=True, confirmation_prompt=True)
            is_strong, msg = is_strong_password(password)
            if is_strong:
                break
            console.print(f"[red]{msg}[/red]")
    
    # 3. Handle SSH Key
    ssh_key_content = None

    if ssh_key:
         path = os.path.expanduser(ssh_key)
         if os.path.exists(path):
             try:
                with open(path, 'r') as f:
                    ssh_key_content = f.read().strip()
             except Exception as e:
                 console.print(f"[red]Error reading key file: {e}[/red]")
                 return
         else:
             console.print(f"[yellow]Warning: SSH key file not found: {path}[/yellow]")
             return
    else:
         # Interactive prompt
         ssh_key_path = click.prompt("Path to public SSH key (optional, press Enter to skip)", default="", show_default=False)
         if ssh_key_path:
             path = os.path.expanduser(ssh_key_path)
             if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        ssh_key_content = f.read().strip()
                except Exception as e:
                     console.print(f"[red]Error reading key file: {e}[/red]")
                     return
             else:
                 console.print(f"[red]File not found: {path}[/red]")
                 return

    console.print(f"Creating user [cyan]{username}[/cyan] with role [magenta]{role}[/magenta]...")
    if enc_manager.user_create(username, password, role, ssh_key_content):
        if json_output:
             click.echo(json.dumps({"status": "success", "username": username}))
        else:
             console.print(f"[green]User {username} created successfully.[/green]")
    else:
        if json_output:
             click.echo(json.dumps({"status": "error", "message": "Failed"}))
        else:
             console.print(f"[red]Failed to create user.[/red]")

@user.command("remove")
@click.argument("username")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def user_delete(username, json_output):
    """Delete a user from the server."""
    if not enc_manager.check_permission("user remove"):
        console.print("[red]Permission Denied: You are not allowed to remove users.[/red]")
        return
    if not json_output:
        if not click.confirm(f"Are you sure you want to delete user '{username}'?"):
            return

    console.print(f"Deleting user [cyan]{username}[/cyan]...")
    if enc_manager.user_delete(username):
        if json_output:
             click.echo(json.dumps({"status": "success", "username": username}))
        else:
             console.print(f"[green]User {username} deleted.[/green]")
    else:
        if json_output:
             click.echo(json.dumps({"status": "error", "message": "Failed"}))
        else:
             console.print(f"[red]Failed to delete user.[/red]")


def main():
    cli()

if __name__ == "__main__":
    main()
