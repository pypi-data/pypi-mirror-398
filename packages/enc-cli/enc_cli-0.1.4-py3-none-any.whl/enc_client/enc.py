import os
import json
import subprocess
import sys
import shlex
import socket
import shutil
import re
import click
import pexpect
from urllib.parse import urlparse
import threading
import signal
import platform
from rich.console import Console
from enc_client.session import Session

console = Console()

class Enc:
    def __init__(self):
        self.global_dir = os.path.expanduser("~/.enc")
        self.global_config_file = os.path.join(self.global_dir, "config.json")
        
        # Local config relies on current working directory
        self.local_dir = os.path.join(os.getcwd(), ".enc")
        self.local_config_file = os.path.join(self.local_dir, "config.json")
        
        self.config, self.active_config_path = self.load_config()
        self.config_dir = os.path.dirname(self.active_config_path)
        self.session_manager = Session(self.config_dir)

    def load_config(self):
        """
        Load configuration with precedence: Local > Global.
        Returns (merged_config_dict, active_config_path_for_writes)
        """
        cfg = {
            "url": "",
            "username": "",
            "ssh_key": "",
            "session_id": None,
            "context": None
        }
        active_path = self.global_config_file

        # 1. Load Global
        if os.path.exists(self.global_config_file):
            try:
                with open(self.global_config_file, 'r') as f:
                    global_cfg = json.load(f)
                    cfg.update(global_cfg)
            except Exception as e:
                console.print(f"[red]Error loading global config: {e}[/red]")

        # 2. Load Local (Override)
        if os.path.exists(self.local_config_file):
            try:
                with open(self.local_config_file, 'r') as f:
                    local_cfg = json.load(f)
                    # Merge logic: meaningful values override (except maybe None/empty?)
                    # For simplicty, simple update() works well for KV pairs.
                    cfg.update(local_cfg)
                    active_path = self.local_config_file
                    # console.print("[dim]Loaded local project configuration.[/dim]")
            except Exception as e:
                console.print(f"[red]Error loading local config: {e}[/red]")
        
        return cfg, active_path

    def save_config(self, cfg, target_path=None):
        """Save config to specific path or default active path."""
        path = target_path if target_path else self.active_config_path
        
        # Ensure dir exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(cfg, f, indent=4)
        
        # Reload to ensure state consistency
        self.config, self.active_config_path = self.load_config()

    def init_config(self, url, username, ssh_key="", target_path=None):
        """Initialize config at specific location."""
        # Create fresh config dict for init
        new_cfg = {
            "url": url,
            "username": username,
            "ssh_key": ssh_key,
            "session_id": None
        }
        
        # Note: If we are initing a LOCAL config, we might inherit values from global?
        # User request implies "create local use dir for the project".
        # So usually a fresh start or copy. Fresh start is safer for isolation.
        
        save_target = target_path if target_path else self.global_config_file
        self.save_config(new_cfg, save_target)

    def set_config_value(self, key, value):
        """Set value in the ACTIVE configuration scope."""
        # Load the specific file for the active scope to avoid polluting it with merged data
        # actually save_config overwrites. 
        # CAUTION: If we loaded Merged Config, writing it back to Local File might copy Global values into Local file.
        # This is usually acceptable (pinning dependencies), OR we should only write the delta.
        # For this MVP, writing the Full Merged Config to the Active File is easiest and pin-safe.
        
        self.config[key] = value
        self.save_config(self.config, self.active_config_path)

    def setup_ssh_key_flow(self, password=None):
        """Interactive flow to generate and setup SSH key."""
        # 1. Determine local .ssh directory based on ACTIVE config context
        # self.config_dir is set in init (derived from active_config_path)
        ssh_dir = os.path.join(self.config_dir, ".ssh")
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o700)
            
        key_name = "enc_id_rsa"
        private_key_path = os.path.join(ssh_dir, key_name)
        public_key_path = private_key_path + ".pub"
        
        # 2. Generate Key if missing
        if not os.path.exists(private_key_path):
            console.print(f"Generating new SSH key pair in [cyan]{ssh_dir}[/cyan]...")
            try:
                # ssh-keygen -t rsa -b 4096 -f path -N "" -q
                subprocess.run(
                    ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", private_key_path, "-N", "", "-q"],
                    check=True
                )
                os.chmod(private_key_path, 0o600)
                console.print("[green]SSH key pair generated.[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Failed to generate SSH key:[/red] {e}")
                return False
        else:
            console.print(f"Using existing key: [cyan]{private_key_path}[/cyan]")
            
        # 3. Read Public Key
        try:
            with open(public_key_path, 'r') as f:
                pub_key_content = f.read().strip()
        except Exception as e:
            console.print(f"[red]Failed to read public key:[/red] {e}")
            return False
            
        # 4. Send to Server (requires Login)
        session_id = self.config.get("session_id")
        if not session_id:
            console.print("[yellow]Please login first. We need an active session to authorize key addition.[/yellow]")
            return False
            
        console.print("Sending public key to ENC Server...")
        cmd = self.get_remote_cmd(f"server-setup-ssh-key --key {shlex.quote(pub_key_content)}")
        
        # Use existing _run_remote helper which handles SSH execution
        res = self._run_remote(cmd, password=password)
        
        if res and res.get("status") == "success":
            console.print("[bold green]Success![/bold green] Server accepted your key.")
            
            # 5. Update Local Config
            self.set_config_value("ssh_key", private_key_path)
            console.print(f"Local configuration updated to use: [cyan]{private_key_path}[/cyan]")
            return True
        else:
             msg = res.get("message") if res else "Unknown Error"
             console.print(f"[red]Server rejected key setup:[/red] {msg}")
             return False

    def get_config_value(self, key):
        return self.config.get(key)
        
    def get_session_data(self):
        """Load session data from the session file."""
        session_id = self.config.get("session_id")
        return self.session_manager.load_session(session_id)

    def check_permission(self, command):
        """Check if the current user has permission to run the command."""
        data = self.get_session_data()
        if not data:
            return False
            
        allowed = data.get("allowed_commands", [])
        if "*" in allowed:
            return True
            
        return command in allowed
        
    def _parse_url(self):
        """Helper to parse the configured URL."""
        url = self.config.get("url")
        if not url: return None
        
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port
        
        # Handle "host:port" without scheme
        if not host: 
            if "://" not in url:
                if ":" in url:
                    parts = url.split(":")
                    host = parts[0]
                    if len(parts) > 1 and parts[1].isdigit():
                        port = int(parts[1])
                else:
                    host = url
        
        if not host:
            return None
            
        # Fallback port logic
        if not port:
            if parsed.scheme == "https": port = 443
            elif parsed.scheme == "http": port = 80
            else: port = 22 # Default to SSH
            
        return host, port

    def check_connection(self):
        """Checks if the configured URL is available (reachable)."""
        url_parts = self._parse_url()
        if not url_parts:
            console.print("[red]No URL configured or invalid.[/red]")
            return False
            
        host, port = url_parts
        console.print(f"Checking connection to [cyan]{host}:{port}[/cyan]...")
        
        try:
            sock = socket.create_connection((host, int(port)), timeout=5)
            sock.close()
            console.print("[bold green]Connection Successful![/bold green] Host is reachable.")
            return True
        except Exception as e:
            console.print(f"[bold red]Connection Failed:[/bold red] {e}")
            return False

    def get_ssh_base_cmd(self):
        url_parts = self._parse_url()
        username = self.config.get("username")
        ssh_key = self.config.get("ssh_key")
        
        if not url_parts or not username:
             console.print("[red]Not configured global or local config. Run 'enc config init' first.[/red]")
             return None, None
        
        host, port = url_parts
        cmd = ["ssh"]
        if port:
            cmd.extend(["-p", str(port)])
        
        if ssh_key:
            cmd.extend(["-i", os.path.expanduser(ssh_key)])
            # Avoid falling back to password if key is provided
            cmd.extend(["-o", "PreferredAuthentications=publickey"])
        
        target = f"{username}@{host}"
        return cmd, target

    def get_remote_cmd(self, sub_cmd):
        """Construct a remote command including the session ID if available."""
        session_id = self.config.get("session_id")
        if session_id:
            return f"enc --session-id {session_id} {sub_cmd}"
        return f"enc {sub_cmd}"

    def _run_with_password(self, cmd_list, password):
        """Run command with password authentication using pexpect."""
        try:
            cmd_safe = " ".join([shlex.quote(x) for x in cmd_list])
            child = pexpect.spawn(cmd_safe, encoding='utf-8', timeout=30)
            
            while True:
                idx = child.expect(["(?i)password:", "(?i)continue connecting", pexpect.EOF, pexpect.TIMEOUT, "(?i)permission denied"])
                
                if idx == 0:
                    child.sendline(password)
                elif idx == 1:
                    child.sendline("yes")
                elif idx == 2:
                    break
                elif idx == 3:
                     # Timeout
                     child.close()
                     return {"status": "error", "message": "Connection timed out"}
                elif idx == 4:
                     child.close()
                     return {"status": "error", "message": "Permission denied"}

            output = child.before
            child.close()
            
            # Parse JSON
            match = re.search(r'\{.*\}', output, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            return {"status": "error", "message": f"Invalid response: {output.strip()}"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def login(self, password=None):
        """Authenticate with the server and establish a session."""
        base, target = self.get_ssh_base_cmd()
        if not base or not target:
             return

        username = self.config.get("username")
        console.print(f"Authenticating as {username}...")
        
        login_cmd = ["enc", "server-login", username]
        full_ssh_cmd = list(base) + [target] + login_cmd
        
        session_data = None
        
        if password:
            session_data = self._run_with_password(full_ssh_cmd, password)
        else:
             # Interactive logic kept inline or use pexpect with prompt?
             # For simplicity, let's keep old interactive logic here specially if we want custom prompting
             # BUT actually we can use _run_with_password if we prompt first!
             # But SSH prompts effectively.
             # Let's revert to old manual pexpect for interactive to allow Click prompt
             try:
                cmd_safe = " ".join([shlex.quote(x) for x in full_ssh_cmd])
                child = pexpect.spawn(cmd_safe, encoding='utf-8', timeout=30)
                while True:
                    idx = child.expect(["(?i)password:", "(?i)continue connecting", pexpect.EOF, pexpect.TIMEOUT, "(?i)permission denied"])
                    if idx == 0:
                        pwd = click.prompt("Enter Server Password", hide_input=True)
                        child.sendline(pwd)
                    elif idx == 1:
                        child.sendline("yes")
                    elif idx == 2: break
                    elif idx == 3: return
                    elif idx == 4: return

                output = child.before
                child.close()
                match = re.search(r'\{.*\}', output, re.DOTALL)
                if match:
                    session_data = json.loads(match.group(0))
             except Exception as e:
                 console.print(f"[red]Error:[/red] {e}")
                 return

        if session_data:
            if session_data.get("status") == "error":
                 console.print(f"[red]Login Error:[/red] {session_data.get('message')}")
                 return

            self._save_local_session(session_data)
            console.print(f"[bold green]Login Success![/bold green] Session ID: {session_data['session_id']}")
            self.monitor_session()

    def update_project_info(self, project_name, local_dir=None, server_mount=None, exec_point=None):
        """Update session file with project info."""
        session_id = self.config.get("session_id")
        return self.session_manager.update_project_info(session_id, project_name, local_dir, server_mount, exec_point)

    def _save_local_session(self, session_data):
        self.session_manager.save_session(session_data)
            
        # Update current config context
        self.config["session_id"] = session_data.get("session_id")
        self.save_config(self.config)

    def user_list(self):
        """Get list of users. Checks local cache first, then server."""
        # 1. Get Session
        session = self.get_session_data()
        if not session:
             console.print("[yellow]No active session. Please login.[/yellow]")
             return None
             
        # 2. Check Permissions
        allowed = session.get("allowed_commands", [])
        # We assume 'user list' is the permission key. 
        # If allowed_commands is empty or doesn't contain it, strictly we should deny.
        # BUT for this task, the requirement is "check if its have this 'user list' in allowed commad".
        
        if "user list" not in allowed:
            console.print("[red]Permission Denied: 'user list' not in allowed commands.[/red]")
            return None
            
        # # 3. Check Cache
        # if "user_list" in session:
        #     # console.print("[dim]Returning cached user list.[/dim]")
        #     return session["user_list"]
            
        # 4. Call Server
        # console.print("[dim]Fetching user list from server...[/dim]")
        base, target = self.get_ssh_base_cmd()
        
        # Construct command
        remote_cmd = self.get_remote_cmd("user list --json")
        full_ssh = cmd = list(base) + [target, remote_cmd]
        
        try:
            res = subprocess.run(full_ssh, capture_output=True, text=True)
            if res.returncode == 0:
                # Expecting JSON list of users or object with "users" key
                try:
                    import re
                    match = re.search(r'\{.*\}|\[.*\]', res.stdout, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        data = json.loads(json_str)
                        
                        # Handle if wrapped in status object or direct list
                        users = data
                        if isinstance(data, dict):
                            if "users" in data:
                                users = data["users"]
                            elif data.get("status") != "success":
                                console.print(f"[red]Server Error:[/red] {data.get('message')}")
                                return None
                                
                        # 5. Update Cache
                        self.session_manager.update_session_key(self.config.get("session_id"), "user_list", users)
                        return users
                    else:
                        console.print(f"[red]Invalid Server Response:[/red] {res.stdout}")
                except json.JSONDecodeError:
                    console.print(f"[red]Parse Error:[/red] {res.stdout}")
            else:
                 console.print(f"[red]Server Error:[/red] {res.stderr}")
                 
        except Exception as e:
             console.print(f"[red]Error:[/red] {e}")
             
        return None

    def project_init(self, name, password, project_dir):
        """Call server to init project vault."""

        # check if project_dir has any files or folders
        backup_dir = None
        try:
             # Trigger potential OSError before logic
             if os.path.exists(project_dir):
                 os.listdir(project_dir)
        except OSError as e:
            if e.errno == 6: # Device not configured
                 console.print(f"[yellow]Detected zombie mount at {project_dir}. Attempting cleanup...[/yellow]")
                 try:
                     subprocess.run(["umount", "-f", project_dir], check=True)
                     console.print("[green]Cleanup successful.[/green]")
                 except Exception:
                     console.print(f"[red]Failed to clean up zombie mount. Please run 'umount -f {project_dir}' manually.[/red]")
                     return False
            else:
                 raise e

        if os.path.exists(project_dir) and os.listdir(project_dir):
            # create a backup of project_dir contents
            # We move the entire folder to backup_path to be safe/atomic
            backup_dir = os.path.join(self.config_dir, "backups", f"{name}_temp")
            
            # Clean up previous stuck backup if exists
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
                
            console.print(f"[yellow]Backing up existing files to {backup_dir}...[/yellow]")
            # Move project_dir (source) to backup_dir (dest)
            # Use copytree + rmtree to be robust against cross-device links and ghost files
            try:
                shutil.copytree(project_dir, backup_dir)
                
                def on_rm_error(func, path, exc_info):
                    # Ignore FileNotFoundError (race condition/ghost files like ._*)
                    if not os.path.exists(path):
                        return
                    # Re-raise others
                    raise exc_info[1]

                shutil.rmtree(project_dir, onerror=on_rm_error)
            except Exception as e:
                console.print(f"[red]Backup failed:[/red] {e}")
                return False
            
            # Recreate empty project_dir for mounting
            os.makedirs(project_dir)
            
        base, target = self.get_ssh_base_cmd()
        
        cmd = list(base)
        # Construct command with password and project_dir as flags
        remote_cmd = self.get_remote_cmd(f"server-project-init {shlex.quote(name)} --password {shlex.quote(password)} --project-dir {shlex.quote(project_dir)}")
        full_ssh = cmd + [target, remote_cmd]
        
        try:
            # We can now use run/capture_output since password is a flag
            res = subprocess.run(full_ssh, capture_output=True, text=True)
            stdout = res.stdout
            if res.returncode != 0:
                console.print(f"[red]Init Failed:[/red] {res.stderr}")
                return False

            try:
                 # Parse JSON output from server
                match = re.search(r'\{.*\}', stdout, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if data.get("status") == "success":
                         server_mount_point = data.get("mount_point")
                         if server_mount_point:
                             from enc_client.sshfs_handler import SshfsHandler
                             ssh_bridge = SshfsHandler(self.config)
                             success = ssh_bridge.mount_project(name, project_dir, server_mount_point)
                             if success:
                                # Restore backup contents to the new mount
                                if backup_dir and os.path.exists(backup_dir):
                                    console.print("[yellow]Restoring files to encrypted vault...[/yellow]")
                                    for item in os.listdir(backup_dir):
                                        s = os.path.join(backup_dir, item)
                                        d = os.path.join(project_dir, item)
                                        if os.path.isdir(s):
                                            shutil.copytree(s, d, dirs_exist_ok=True)
                                            shutil.rmtree(s)
                                        else:
                                            shutil.copy2(s, d)
                                            os.remove(s)
                                    os.rmdir(backup_dir)
                                    
                                console.print(f"[green]Project {name} initialized successfully.[/green]")

                                # update session file with project info
                                self.update_project_info(name, local_dir=project_dir, server_mount=server_mount_point)
                            
                                return True
                    else:
                         console.print(f"[red]Server Error:[/red] {data.get('message')}")
                else:
                    console.print(f"[red]Invalid Response:[/red] {stdout}")
            except Exception as e:
                console.print(f"[red]Parse Error:[/red] {e}")
                
            return False
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return False

    def monitor_project(self, session_id, name):
        """Call server to monitor project."""
        # Start monitoring thread as daemon so CLI can exit
        thread = threading.Thread(
            target=self.session_manager.monitor_project, 
            args=(session_id, name, self.project_unmount),
            daemon=True
        )
        thread.start()      

    def monitor_session(self):
        """Monitor terminal signals to logout session on close in background."""
        import subprocess
        import sys
        import os
        try:
            # Capture the parent PID (the shell) to monitor
            ppid = os.getppid()
            
            # Use sys.argv[0] to get the path to the current 'enc' executable
            cmd = [sys.argv[0], 'internal-watchdog', '--ppid', str(ppid)]
            subprocess.Popen(cmd,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             stdin=subprocess.DEVNULL,
                             close_fds=True)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not start session watchdog: {e}[/yellow]")

    def project_mount(self, name, password, local_dir="."):
        """Call server to mount project and establish local SSHFS bridge."""
        # Check if project active locally
        session_id = self.config.get("session_id")
        if self.session_manager.is_project_active(session_id, name):
             console.print(f"[yellow]Project '{name}' is already mounted locally.[/yellow]")
             return False

        base, target = self.get_ssh_base_cmd()
        
        cmd = list(base)
        remote_cmd = self.get_remote_cmd(f"server-project-mount {shlex.quote(name)} --password {shlex.quote(password)}")
        full_ssh = cmd + [target, remote_cmd]
        
        try:
            # Using run instead of Popen/pipe for better reliability with flags
            res = subprocess.run(full_ssh, capture_output=True, text=True)
            stdout = res.stdout
            
            if res.returncode != 0:
                console.print(f"[red]Mount Failed:[/red] {res.stderr}")
                return False

            try:
                import json
                import re
                match = re.search(r'\{.*\}', stdout, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if data.get("status") == "success":
                        server_mount_point = data.get("mount_point")
                        if server_mount_point:
                            from enc_client.sshfs_handler import SshfsHandler
                            ssh_bridge = SshfsHandler(self.config)
                            success = ssh_bridge.mount_project(name, local_dir, server_mount_point)
                            
                            
                            if success:
                                self.update_project_info(name, local_dir=os.path.abspath(local_dir), server_mount=server_mount_point)
                                
                                # call session.monitor_project() after updating session info
                                self.monitor_project(session_id, name)
                                
                                return True
            except:
                pass
            return False
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return False

    def _run_remote(self, remote_cmd_str, password=None):
        """Helper to run a remote command via SSH and parse JSON output."""
        base, target = self.get_ssh_base_cmd()
        full_ssh = base + [target, remote_cmd_str]
        
        if password:
             return self._run_with_password(full_ssh, password)

        # UX Improvement: If SSH key is configured, try BatchMode first to detect auth failure
        # and warn the user before falling back to password prompt.
        use_key = self.config.get("ssh_key")
        
        try:
            if use_key:
                # Try with BatchMode=yes to fail fast if key doesn't work
                batch_cmd = base + ["-o", "BatchMode=yes", target, remote_cmd_str]
                res = subprocess.run(batch_cmd, capture_output=True, text=True)
                
                if res.returncode == 255: # SSH Error (likely auth)
                     console.print("[yellow]SSH Key authentication failed. Falling back to password...[/yellow]")
                     # Proceed to run normally (which allows interactive password if not capturing output, 
                     # but here we capture output. SSH usually prompts on TTY even if stdout is captured, 
                     # but stdin might matter. subprocess.run captures stdin by default?)
                     # subprocess.run w/ capture_output closes stdin? No.
                     # But ssh needs a TTY for password. 
                     
                     # Since we use capture_output=True, SSH password prompt might fail or be hidden.
                     # However, typical Enc usage for remote commands assumes non-interactive/json response.
                     # If we need password, we might be stuck.
                     
                     # Actually, if we capture output, we can't easily interact with password prompt 
                     # unless we don't capture. But we need to capture to parse JSON.
                     # Sshpass or expect would be needed, or we just let it fail and tell user "Check key or set up agent".
                     
                     # Wait, user said "ask for password". 
                     # If we can't support interactive password with capture_output, we should just warn.
                     pass 
                else:
                    # Key auth worked (or other error but not connectivity/auth)
                    if res.returncode != 0:
                         return {"status": "error", "message": f"SSH Error: {res.stderr.strip()}"}
                    
                    # Parse output
                    match = re.search(r'\{.*\}', res.stdout, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
                    return {"status": "error", "message": f"Invalid server response: {res.stdout.strip()}"}

            # Fallback or standard run
            res = subprocess.run(full_ssh, capture_output=True, text=True)
            if res.returncode != 0:
                return {"status": "error", "message": f"SSH Error: {res.stderr.strip()}"}
            
            # Parse output
            match = re.search(r'\{.*\}', res.stdout, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"status": "error", "message": f"Invalid server response: {res.stdout.strip()}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def project_remove(self, name, password):
         """Remove a project from server and delete local files."""
         # 1. Permission Check
         if not self.check_permission("server-project-remove"):
             console.print("[red]Access Denied: You do not have permission to remove projects.[/red]")
             return False

         console.print(f"To remove project '{name}', we must verify ownership by mounting it first.")
         
         session_id = self.config.get("session_id")
         if self.session_manager.is_project_active(session_id, name):
             console.print(f"[yellow]Project '{name}' is already active. Proceeding with removal.[/yellow]")
             # Logic for ALREADY MOUNTED project
             if not click.confirm(f"WARNING: This will PERMANENTLY DELETE project '{name}' and all its files from the server. Are you sure?", abort=True):
                 return False

             # Call Server Remove
             cmd = self.get_remote_cmd(f"server-project-remove {name}")
             res = self._run_remote(cmd)
             
             # Unmount (locally)
             self.project_unmount(name, forced=True) 
             
             if res and res.get("status") == "success":
                 console.print(f"[green]Project '{name}' successfully removed.[/green]")
                 return True
             else:
                 console.print(f"[red]Failed to remove project on server:[/red] {res.get('message') if res else 'Unknown error'}")
                 return False
         else:
             # Mount to temp dir for verification
             import tempfile
             # We use a try...finally block around the temp dir usage if we were manually managing it,
             # but TemporaryDirectory handles cleanup on exit.
             # THE ISSUE was that project_unmount wasn't called before cleanup.
             # We must ensure unmount happens.
             
             temp_mount = tempfile.mkdtemp()
             try:
                 console.print(f"Mounting '{name}' for verification...")
                 success = self.project_mount(name, password, local_dir=temp_mount)
                 if not success:
                     console.print("[red]Authentication failed. Cannot remove project.[/red]")
                     return False
                 
                 try:
                     # 3. Confirmation
                     if not click.confirm(f"WARNING: This will PERMANENTLY DELETE project '{name}' and all its files. Are you sure?", abort=True):
                         return False

                     # 5. Call Server Remove
                     cmd = self.get_remote_cmd(f"server-project-remove {name}")
                     res = self._run_remote(cmd)
                     
                     if res and res.get("status") == "success":
                         console.print(f"[green]Project '{name}' successfully removed.[/green]")
                         return True
                     else:
                         console.print(f"[red]Failed to remove project on server:[/red] {res.get('message') if res else 'Unknown error'}")
                         return False
                 finally:
                     # 6. Unmount - MUST happen before we try to remove temp dir
                     # We force unmount to ensure bridge is killed
                     self.project_unmount(name, local_dir=temp_mount, forced=True)
             finally:
                 # Cleanup temp dir
                 if os.path.exists(temp_mount):
                     shutil.rmtree(temp_mount, ignore_errors=True)

         # 5. Call Server Remove
         cmd = self.get_remote_cmd(f"server-project-remove {name}")
         res = self._run_remote(cmd)
         
         # 6. Unmount
         self.project_unmount(name) # Auto-detects path
         
         if res and res.get("status") == "success":
             console.print(f"[green]Project '{name}' successfully removed.[/green]")
             return True
         else:
             console.print(f"[red]Failed to remove project on server:[/red] {res.get('message') if res else 'Unknown error'}")
             return False
        
    def project_unmount(self, name=None, local_dir=".", forced=False):
        """Call server to unmount project and close local SSHFS bridge."""
        # Detect project from CWD if name not provided
        if not name:
             session_id = self.config.get("session_id")
             cwd = os.path.abspath(os.getcwd())
             name = self.session_manager.get_project_by_path(session_id, cwd)
             if not name:
                 # Try finding via local_dir arg if different from .
                 name = self.session_manager.get_project_by_path(session_id, os.path.abspath(local_dir))
             
             if not name:
                 console.print("[red]No active project found in current directory. Please specify project name.[/red]")
                 return False

        # Validate if project is actually active (locally mounted) before unmount
        # This prevents unmounting a project that isn't running locally (as requested)
        session_id = self.config.get("session_id")
        if not self.session_manager.is_project_active(session_id, name) and not forced:
             console.print(f"[yellow]Project '{name}' is not currently active.[/yellow]")
             return False

        # 1. Close local bridge first
        from enc_client.sshfs_handler import SshfsHandler
        ssh_bridge = SshfsHandler(self.config)
        # We need the local dir for unmount. If we inferred name, we need exact path?
        # SSHFS unmount usually takes path.
        # If we have name, look up path in session?
        session_id = self.config.get("session_id")
        session_data = self.session_manager.load_session(session_id)
        
        project_local_path = local_dir 
        if session_data and "projects" in session_data and name in session_data["projects"]:
             saved_path = session_data["projects"][name].get("local_mount_point")
             if saved_path:
                 project_local_path = saved_path
        
        # Fallback Heuristic: If default local_dir (.) is not the mount, but a folder with 'name' exists
        # and IS a mount, use that. This handles cases where session is lost but user is in parent dir.
        if not os.path.ismount(project_local_path):
            potential_path = os.path.join(os.getcwd(), name)
            if os.path.isdir(potential_path) and os.path.ismount(potential_path):
                project_local_path = potential_path
        
        ssh_bridge.unmount_project(project_local_path)

        # 2. Call server to unmount vault
        base, target = self.get_ssh_base_cmd()
        remote_cmd = self.get_remote_cmd(f"server-project-unmount {name}")
        cmd = list(base) + [target, remote_cmd]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            # Remove from session tracking
            self.session_manager.remove_project_mount(session_id, name)
            
            if res.returncode == 0:
                console.print(f"[green]Remote project '{name}' unmounted.[/green]")
                return True
            else:
                console.print(f"[red]Remote unmount failed:[/red] {res.stderr}")
                return False
        except Exception:
            return False

    def start_project_removal(self, name):
        """Call server to permanently remove project."""
        base, target = self.get_ssh_base_cmd()
        remote_cmd = self.get_remote_cmd(f"server-project-remove {name}")
        cmd = list(base) + [target, remote_cmd]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                match = re.search(r'\{.*\}', res.stdout, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if data.get("status") == "success":
                        console.print(f"[green]Project '{name}' deleted successfully.[/green]")
                        # Remove from session entirely
                        session_id = self.config.get("session_id")
                        self.session_manager.remove_project(session_id, name)
                        return True
                    else:
                        console.print(f"[red]Server Error:[/red] {data.get('message', 'Unknown Error')}")
                else:
                    console.print(f"[red]Invalid Response:[/red] {res.stdout}")
            else:
                console.print(f"[red]Remote Error:[/red] {res.stderr}")
            return False
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return False

    def is_project_active(self, name):
        """Check if project is active in current session."""
        session_id = self.config.get("session_id")
        return self.session_manager.is_project_active(session_id, name)

    def project_list(self):
        """Get the merged list of projects (Server + Local Session)."""
        # 1. Fetch Server List
        base, target = self.get_ssh_base_cmd()
        remote_cmd = self.get_remote_cmd("server-project-list")
        cmd = list(base) + [target, remote_cmd]
        
        server_projects = {}
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                match = re.search(r'\{.*\}', res.stdout, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    if data.get("status") == "success":
                        server_projects = data.get("projects", {})
        except Exception:
            pass # Use empty server list if failed

        # 2. Load Local Session
        session_id = self.config.get("session_id")
        session_data = self.session_manager.load_session(session_id)
        local_projects = {}
        if session_data and "projects" in session_data:
            local_projects = session_data["projects"]

        # 3. Merge
        merged_list = []
        
        for name, meta in server_projects.items():
            entry = {
                "name": name,
                "server_mount_point": meta.get("mount_path", ""),
                "exec_entry_point": meta.get("exec", ""),
                "local_mount_point": "",
                "is_active": False
            }
            
            # Merge local info
            if name in local_projects:
                local_info = local_projects[name]
                if local_info.get("local_mount_point"):
                    entry["local_mount_point"] = local_info.get("local_mount_point")
                    entry["is_active"] = True 
            
            merged_list.append(entry)
            
        return merged_list

    def project_sync(self, name, local_path):
        """Sync files using rsync over SSH."""
        base, target = self.get_ssh_base_cmd()
        username = self.config.get("username")
        url_parts = self._parse_url()
        if not url_parts: 
            return False
            
        host, port = url_parts
        
        # Remote path: ~/.enc/run/master/<project>/
        remote_path = f"~/.enc/run/master/{name}/"
        
        # Construct rsync command
        # rsync -avz -e "ssh -p port" local_path user@host:remote_path
        
        # We need absolute local path
        local_path = os.path.abspath(local_path)
        if not local_path.endswith("/"):
             local_path += "/" # Ensure rsync copies CONTENTS, not folder itself if desired. 
                               # Usually 'src/' -> 'dest/'
        
        # Build SSH options string for -e
        ssh_opts = f"ssh -p {port}"
        # Incorporate ssh_key if present
        ssh_key = self.config.get("ssh_key")
        if ssh_key:
            key_path = os.path.expanduser(ssh_key)
            ssh_opts += f" -i {key_path}"
            ssh_opts += f" -o PreferredAuthentications=publickey"
        
        # Add strict host key checking off for convenience/test?
        # Maybe: -o StrictHostKeyChecking=no
        if not ssh_key:
             # If using password/default keys, standard ssh behavior.
             pass
        else:
             # Ensure key usage
             ssh_opts += f" -o StrictHostKeyChecking=no"
        
        cmd = [
            "rsync",
            "-avz",
            "-e", ssh_opts,
            local_path,
            f"{username}@{host}:{remote_path}"
        ]
        
        try:
            # We use subprocess.call to allow streaming output to console
            ret = subprocess.call(cmd)
            if ret == 0:
                # Log success to server
                sync_remote = self.get_remote_cmd(f"server-project-sync {name} 'rsync sync completed successfully'")
                subprocess.run(list(base) + [target, sync_remote], capture_output=True)
            return ret == 0
        except Exception as e:
            console.print(f"[red]Sync Error:[/red] {e}")
            return False

    def project_run(self, name, command_str):
        """Execute a command in the remote project directory via server-project-run for logging."""
        base, target = self.get_ssh_base_cmd()
        
        # We use shlex.quote to handle complex commands
        import shlex
        quoted_cmd = shlex.quote(command_str)
        
        remote_cmd = self.get_remote_cmd(f"server-project-run {name} {quoted_cmd}")
        
        cmd = list(base)
        # Use -t for potential interactivity, though server-project-run currently uses subprocess.run
        full_ssh = cmd + ["-t", target, remote_cmd]
        
        try:
            ret = subprocess.call(full_ssh)
            return ret == 0
        except Exception as e:
            console.print(f"[red]Execution Error:[/red] {e}")
            return False

    def unmount_all(self):
        """Unmount all mounted projects."""
        
        #check all the active project names
        session_id = self.config.get("session_id")
        active_projects = self.session_manager.get_active_projects(session_id)
        for name in active_projects:
            self.project_unmount(name)

    def cleanup_stray_mounts(self):
        """
        Scan system mounts for any remaining ENC SSHFS connections and unmount them.
        This provides an extra layer of security during logout.
        """
        username = self.config.get("username")
        url_parts = self._parse_url()
        if not url_parts or not username:
             return
             
        host, _ = url_parts
        
        # Pattern to look for in 'mount' output:
        # username@host:.*.enc/run/master/
        pattern = f"{username}@{host}:"
        
        try:
            output = subprocess.check_output(["mount"], text=True)
            for line in output.splitlines():
                if pattern in line and ".enc/run/master/" in line:
                    # Parse local mount point from line:
                    # format: source on /path (type, options)
                    match = re.search(r' on (.*?) \(', line)
                    if match:
                        mount_path = match.group(1).strip()
                        if os.path.exists(mount_path):
                            console.print(f"[yellow]Detected stray mount at {mount_path}. Cleaning up...[/yellow]")
                            # Force unmount logic based on OS
                            import platform
                            if platform.system() == "Darwin":
                                subprocess.run(["diskutil", "unmount", "force", mount_path], capture_output=True)
                            else:
                                subprocess.run(["fusermount", "-uz", mount_path], capture_output=True)
        except Exception:
            pass

    def logout(self):
        """Clear local session state."""

        # if project is mounted then unmount it
        self.unmount_all()
        
        # Check for any remaining stray mounts not tracked in session
        self.cleanup_stray_mounts()

        # Optional: Call server-logout to invalidate on server side too?
        # Yes, good practice.
        base, target = self.get_ssh_base_cmd()
        username = self.config.get("username")
        
        if base and target and username:
            try:
                session_id = self.config.get("session_id")
                if session_id:
                    remote_cmd = self.get_remote_cmd(f"server-logout {session_id}")
                    logout_cmd = list(base) + [target, remote_cmd]
                    subprocess.run(logout_cmd, capture_output=True)
            except: 
                pass # Ignore network errors during logout
        
        # Clear local
        # save loging out command in session file logs
        session_id = self.config.get("session_id")
        self.session_manager.save_log(session_id, f"logout session!")

        if self.session_manager.clear_all_sessions():
            self.config["session_id"] = None
            self.save_config(self.config)
            return True
        return False

    def user_create(self, username, password, role, ssh_key=None):
        """Call enc user create."""
        base, target = self.get_ssh_base_cmd()
        
        # New standardized command
        remote_cmd_str = f"user create {username} --password {password} --role {role} --json"
        
        if ssh_key:
             remote_cmd_str += f' --ssh-key "{ssh_key}"'
             
        cmd = list(base) + [
            target, 
            self.get_remote_cmd(remote_cmd_str)
        ]
        
        try:
            # We assume current session user is admin
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and "success" in res.stdout:
                return True
            else:
                console.print(f"[red]Server Error:[/red] {res.stdout} {res.stderr}")
                return False
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return False

    def user_delete(self, username):
        """Call enc user remove."""
        base, target = self.get_ssh_base_cmd()
        # New standardized command
        cmd = list(base) + [
            target, 
            self.get_remote_cmd(f"user remove {username} --json")
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and "success" in res.stdout:
                return True
            else:
                 console.print(f"[red]Server Error:[/red] {res.stdout} {res.stderr}")
                 return False
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return False
