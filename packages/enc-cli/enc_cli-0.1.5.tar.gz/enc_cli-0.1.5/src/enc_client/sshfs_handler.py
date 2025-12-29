import os
import subprocess
import platform
from pathlib import Path
from rich.console import Console
from urllib.parse import urlparse

console = Console()

class SshfsHandler:
    def __init__(self, config):
        self.config = config

    def mount_project(self, project_name, local_dir, server_path):
        """
        Mount the server's vault directory to the local client directory.
        """
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        if os.path.ismount(local_path):
             console.print(f"[yellow]Local directory {local_dir} is already mounted.[/yellow]")
             return True

        username = self.config.get("username")
        url = self.config.get("url")
        
        # Parse host and port from URL
        parsed = urlparse(url)
        host = parsed.hostname or url
        port = parsed.port or 22
        
        # Optimized SSHFS command
        # Use relative path from home directory to avoid issues with absolute paths in restricted/chroot envs
        if server_path.startswith("/home/"):
             # naive strip, assuming standard linux paths
             import re
             relative_path = re.sub(r'^/home/[^/]+/', '', server_path)
             remote_path = f"{username}@{host}:{relative_path}"
        else:
             # Fallback or use as is if it looks relative (starts with . or ~)
             remote_path = f"{username}@{host}:{server_path}"
        
        cmd = [
            "sshfs",
            remote_path,
            str(local_path),
            "-p", str(port),
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null"
        ]

        ssh_key = self.config.get("ssh_key")
        if ssh_key:
            key_path = os.path.expanduser(ssh_key)
            cmd.extend(["-o", f"IdentityFile={key_path}"])
            cmd.extend(["-o", "PreferredAuthentications=publickey"])

        try:
            # Check if sshfs is installed
            import shutil
            sshfs_path = shutil.which("sshfs")
            # Fallback for common paths if not in PATH
            if not sshfs_path:
                 common_paths = ["/usr/local/bin/sshfs", "/opt/homebrew/bin/sshfs", "/usr/bin/sshfs"]
                 for p in common_paths:
                     if os.path.exists(p):
                         sshfs_path = p
                         break
            
            if not sshfs_path:
                console.print("[bold red]Error: 'sshfs' is not installed or found.[/bold red] Please run [cyan]enc install[/cyan] to set up dependencies.")
                # Debug info
                # console.print(f"PATH: {os.environ.get('PATH')}")
                return False


            subprocess.run(cmd, check=True, capture_output=True, text=True)
            console.print(f"[green]Successfully mounted project {project_name}.[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]SSHFS Mount Failed:[/red] {e.stderr}")
            return False
        except Exception as e:
            console.print(f"[red]Unexpected error during mount:[/red] {e}")
            return False

    def unmount_project(self, local_dir):
        """Unmount the local bridged directory."""
        local_path = Path(local_dir)
        if not os.path.ismount(local_path):
            return True

        try:
            if platform.system() == "Darwin":
                subprocess.run(["umount", str(local_path)], check=True)
            else:
                subprocess.run(["fusermount", "-u", str(local_path)], check=True)
            console.print(f"[green]Unmounted {local_dir}.[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Unmount failed:[/red] {e}")
            return False
