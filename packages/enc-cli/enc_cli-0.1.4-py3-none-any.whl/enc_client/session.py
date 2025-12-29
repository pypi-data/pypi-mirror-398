import os
import json
import time
import threading
import signal
import sys
import datetime
import shutil
import glob
from rich.console import Console

console = Console()

class Session:
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.sessions_dir = os.path.join(self.config_dir, "sessions")
        self.backup_dir = os.path.join(self.config_dir, "backups")

        os.makedirs(self.sessions_dir, exist_ok=True)

    def get_session_path(self, session_id):
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def load_session(self, session_id):
        """Load session data from the session file."""
        if not session_id:
            return None
            
        session_file = self.get_session_path(session_id)
        if not os.path.exists(session_file):
            return None
            
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
                
                # Normalize projects to dictionary if it's a list (legacy support)
                if "projects" in data and isinstance(data["projects"], list):
                    new_projects = {}
                    for p in data["projects"]:
                        if isinstance(p, str):
                            new_projects[p] = {}
                        elif isinstance(p, dict) and "name" in p:
                            new_projects[p["name"]] = p
                    data["projects"] = new_projects
                
                return data
        except Exception:
            return None

    def save_session(self, session_data):
        """Save session data to file."""
        session_id = session_data.get("session_id")
        if not session_id:
            return False

        session_file = self.get_session_path(session_id)
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=4)
            return True
        except Exception as e:
            console.print(f"[red]Error saving session:[/red] {e}")
            return False

    def monitor_project(self, session_id, project_name, unmount_callback):
        """Monitor a project in the session."""
        data = self.load_session(session_id)
        if not data:
            return False

        if "projects" not in data:
            data["projects"] = {}

        if project_name not in data["projects"]:
            return False

        # Add monitoring logic here


        def moniter(mounted_path):

            if not mounted_path:
                console.print(f"[red]Project {project_name} is not mounted.[/red]")
                return False

            if not os.path.ismount(mounted_path):
                # Only log error if unmounted unexpectedly
                return False

            return True

        mounted_path = data["projects"][project_name]["local_mount_point"]
            
        while True:

            if not moniter(mounted_path):
                
                # Callback expects name=project_name. We force it because monitor detected unmount (or failure).
                unmount_callback(name=project_name, forced=True)
                break
            time.sleep(3)

        console.print(f"Monitoring loop closed for project: {project_name}")


    def update_session_key(self, session_id, key, value):
        """Update a specific key in the session file."""
        data = self.load_session(session_id)
        if not data:
            return False
        
        data[key] = value
        return self.save_session(data)

    def update_project_info(self, session_id, project_name, local_dir=None, server_mount=None, exec_point=None):
        """Add or update project information in the session."""
        data = self.load_session(session_id)
        if not data:
            return False

        if "projects" not in data:
            data["projects"] = {}
            
        if project_name not in data["projects"]:
            data["projects"][project_name] = {}
            
        proj = data["projects"][project_name]
        if local_dir is not None: 
            proj["local_mount_point"] = local_dir
        if server_mount is not None: 
            proj["server_mount_point"] = server_mount
        if exec_point is not None:
            proj["exec_entry_point"] = exec_point
            
        # Ensure we don't hold onto stale "mounted" state if local_dir is explicitly set to None/Empty?
        # If unmounting, caller should probably set local_dir="" or remove entry.
        # Let's add specific remove method or handle it here?
        # User implies unmount removes it from "active".
        
        return self.save_session(data)

    def get_project_by_path(self, session_id, path):
        """Find project name by local mount path."""
        data = self.load_session(session_id)
        if not data or "projects" not in data:
            return None

        # Check for list format
        if isinstance(data["projects"], list):
            # Cannot do lookup by path if it's just a list of names
            # But we can try to find if path matches? No, list has no path info.
            return None
        
        abs_path = os.path.abspath(path)
        for name, info in data["projects"].items():
             if info.get("local_mount_point") == abs_path:
                 return name
        return None

    def remove_project_mount(self, session_id, project_name):
        """Mark project as unmounted locally."""
        data = self.load_session(session_id)
        if not data or "projects" not in data:
            return False
            
        if project_name in data["projects"]:
            # We don't delete the project info (server metadata), just clear local mount
            data["projects"][project_name]["local_mount_point"] = None
            return self.save_session(data)
        return False

    def remove_project(self, session_id, project_name):
        """Permanently remove project from session."""
        data = self.load_session(session_id)
        if not data or "projects" not in data:
            return False
            
        if project_name in data["projects"]:
            del data["projects"][project_name]
            return self.save_session(data)
        return False

    def clear_all_sessions(self):
        """Remove all session files."""
        try:
            files = glob.glob(os.path.join(self.sessions_dir, "*.json"))
            for f in files:
                os.remove(f)

            # remove all the files from the backup directory if exist.
            if os.path.exists(self.backup_dir):
                for item in os.listdir(self.backup_dir):
                    item_path = os.path.join(self.backup_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not remove backup item {item}: {e}[/yellow]")


            return True
        except Exception as e:
            console.print(f"[red]Error clearing sessions:[/red] {e}")
            return False

    def is_project_active(self, session_id, project_name):
        """Check if a project is locally active (mounted)."""
        data = self.load_session(session_id)
        if not data or "projects" not in data:
            return False
            
        projects = data["projects"]
        if project_name in projects:
            # Consistent with project_list logic: if local_mount_point is set, it's active
            return bool(projects[project_name].get("local_mount_point"))
            
        return False

    def get_active_projects(self, session_id):
        """Return a list of active project names."""
        data = self.load_session(session_id)
        if not data or "projects" not in data:
            return []
            
        projects = data["projects"]
        active_list = []
        for name, info in projects.items():
            if info.get("local_mount_point"):
                active_list.append(name)
        return active_list

    def monitor_session(self, logout_callback, ppid=None):
        """Monitor terminal signals and parent PID to logout all sessions on close."""
        log_file = os.path.join(self.config_dir, "watchdog.log")
        
        def log_message(msg):
            try:
                with open(log_file, "a") as f:
                    f.write(f"[{datetime.datetime.now()}] {msg}\n")
            except:
                pass

        log_message(f"Watchdog process started (Monitoring PPID: {ppid}).")

        def handle_signal(signum, frame):
            log_message(f"Received signal {signum}. Starting logout...")
            perform_logout()

        def perform_logout():
            try:
                logout_callback()
                log_message("Logout successful.")
            except Exception as e:
                log_message(f"Logout failed: {e}")
            sys.exit(0)

        # Register signal handlers
        signal.signal(signal.SIGHUP, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
        
        # Keep process alive and monitor parent
        while True:
            # Check if parent PID (the shell) is still alive
            if ppid:
                try:
                    os.kill(ppid, 0)
                except OSError:
                    log_message(f"Parent PID {ppid} (Shell) is dead. Starting logout...")
                    perform_logout()
            
            time.sleep(1)

    def save_log(self, session_id, message):
        """Save a log message to the session file."""
        data = self.load_session(session_id)

        #     "logs": {
        #     "[2025-12-24 00:09:41] login": "Session started"
        # }
        if not data:
            data = {"logs": {}}
        else:
            data.setdefault("logs", {})
        key = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        data["logs"][key] = message
        self.save_session(data)