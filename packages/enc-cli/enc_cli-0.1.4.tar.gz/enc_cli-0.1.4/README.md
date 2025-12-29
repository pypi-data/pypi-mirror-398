# ENC Client Documentation

> **Part of the [ENC Ecosystem](https://github.com/Pranjalab/enc)**
>
> 📚 **[Read the Full Documentation](https://pranjalab.github.io/enc)**

The **ENC Client** (`enc-cli`) is your secure gateway to the ENC ecosystem. It allows you to create, manage, and edit encrypted projects from your local machine, seamlessly integrating them with your favorite tools.

## 🚀 Installation

### Prerequisites
*   Python 3.8+
*   `pip`
*   `sshfs` (Optional, required for mounting projects)

### Installer Script
We provide an easy installer script that handles dependencies and proper path setup:

```bash
cd enc-cli
./install.sh
```

This will:
1.  Create a virtual environment.
2.  Install dependencies (`rich`, `click`, etc.).
3.  Symlink the `enc` binary to your local bin path (e.g., `~/.local/bin/enc`).

To verify installation:
```bash
enc --version
```

---

## ⚙️ Configuration

Before you can login, you need to tell the CLI where your server is located.

### 1. Initialize Config
Run the interactive configuration wizard:

```bash
enc config init
```

You will be asked for:
*   **Server URL**: The address of your ENC Server (e.g., `http://myserver.com:2222`).
*   **Username**: Your assigned username.
*   **SSH Key Path**: Path to your private SSH key (e.g., `~/.ssh/id_ed25519`).

To view your current configuration:
```bash
enc show
```

### 2. SSH Key Setup
For a seamless experience, we recommend using an SSH agent or specifying your key in the config.

**Using SSH Agent:**
```bash
ssh-add -K ~/.ssh/my_enc_key
```

**Using Config File:**
If you set the key path during `enc config init`, the CLI will automatically use it for all connections.

---

## 🔐 Workflow Guide

### 1. Login
Start your secure session. This establishes the encrypted tunnel.
```bash
enc login
```

### 2. Managing Projects

**Create a New Project:**
```bash
enc project init <project-name>
# You will be prompted to set a unique password for this project vault.
```

**List Projects:**
```bash
enc project list
# Shows all your projects and their mount status.
```

**Remove a Project:**
```bash
enc project remove <project-name>
# WARNING: This permanently deletes the encrypted vault from the server.
```

### 3. Editing Code (Mounting)
This is the magic of ENC. You can mount a remote encrypted project to a local folder.

```bash
mkdir ./my-work-folder
enc project mount <project-name> ./my-work-folder
# Enter project password when prompted
```

Once mounted:
*   Open `./my-work-folder` in VS Code, Vim, or any editor.
*   Files you see are plaintext.
*   Files written to disk are instantly encrypted and saved on the server.

### 4. Logout
When you are done, logout to secure your session.

```bash
enc logout
```
**Safety Feature**: This command automatically detects and force-unmounts any active project connections to ensure no plaintext access remains.

---

## 🛡️ Client-Side Monitoring Protocols

The ENC Client employs active monitoring to ensure session security and clean resource management.

### 1. Project Integrity Monitor
*   **Function**: Continuously verifies that your local mount points are active and valid.
*   **Behavior**:
    *   Checks status every **3 seconds**.
    *   If a mount point becomes invalid (e.g., directory deleted, connection dropped), it automatically triggers a **forced unmount** cleanup to remove stale handles.

### 2. Session Watchdog
*   **Function**: Ties your ENC session to your active terminal window.
*   **Behavior**:
    *   Runs as a background process monitoring the **Parent PID** (your shell).
    *   **Auto-Logout**: If you close your terminal window or the shell process terminates, the watchdog immediately triggers a full `enc logout`.
    *   **Signal Handling**: Captures termination signals (`SIGINT`, `SIGTERM`, `SIGHUP`) to ensure sessions close gracefully even during unexpected shutdowns.

---

## 🛠 Command Reference

| Command | Description |
| :--- | :--- |
| `enc config init` | Setup or update local configuration. |
| `enc login` | Authenticate with the server. |
| `enc logout` | Close session and unmount all projects. |
| `enc user create` | (Admin) Create a new user account. |
| `enc project init` | Create a new encrypted project vault. |
| `enc project list` | View available projects. |
| `enc project mount` | Mount a remote project locally via SSHFS. |
| `enc project unmount` | Unmount a specific project. |
| `enc status` | Check current session validity. |

---

## 🗑 Uninstallation

To remove the CLI and its virtual environment:

```bash
./uninstall.sh
```
