# Cisco Router Automation Tool
A lightweight Python utility for auditing, backing up, and modifying Cisco IOS‑XE device configurations.

## 📘 Overview
This tool provides a simple, script‑driven workflow for interacting with Cisco routers using Netmiko.
It automates three core tasks:

- Running a quick interface audit

- Creating a running‑config backup

- Applying configuration changes from a file

The script is designed to be safe, predictable, and easy to extend — ideal for lab environments, home labs, or small‑scale network automation tasks.

## ✨ Features
### 1. Automatic Device Connection
The script loads connection details from environment variables using `.env`:

- `DEVICE_HOST`

- `DEVICE_USER`

- `DEVICE_PASS`

- `DEVICE_PORT` (optional, defaults to 22)

This keeps credentials out of the codebase and makes the tool portable.

### 2. Interface Audit
Runs:

```
show ip interface brief
```
and prints the output to the console.
Useful for quick health checks or verifying interface states before making changes.

### 3. Configuration Backup
Automatically saves the device’s running configuration to:

```
backups/<DEVICE_HOST>_config.txt
```
This ensures you always have a snapshot before applying changes.

### 4. Configuration Deployment
Reads commands from:

```
configs/config.txt
```
and applies them using Netmiko’s `send_config_set()`.

If the file doesn’t exist, the script safely skips this step.

## 📁 Project Structure
```
.
├── backups/              # Auto‑generated config backups
├── configs/
│   └── config.txt        # Optional configuration commands to apply
├── .env                  # Device connection details
└── main.py               # Primary automation script
```
## ⚙️ Requirements
- Python 3.8+

- Netmiko

- python‑dotenv

Install dependencies:

```
pip install netmiko python-dotenv
```
## 🔧 Environment Setup
Create a `.env` file:

```
DEVICE_HOST=192.168.1.1
DEVICE_USER=admin
DEVICE_PASS=yourpassword
DEVICE_PORT=22
```
## 🚀 Usage
Run the script:

```
python main.py
```
The workflow:

1. Connects to the router

2. Runs an interface audit

3. Backs up the running config

4. Applies any configuration commands found in `configs/config.txt`

## 🧠 Notes & Safety
- This tool is intended for lab or controlled environments.

- Always review `configs/config.txt` before running the script.

- Backups are created automatically, but restoring them is manual.

- The script uses `cisco_xe` as the Netmiko device type — adjust if needed.

## 📜 Status
This project is intentionally small and focused.
It serves as a foundation for more advanced automation workflows, and as a clean example of:

- Secure credential handling

- Netmiko‑based device interaction

- Automated backups

- Script‑driven configuration management
