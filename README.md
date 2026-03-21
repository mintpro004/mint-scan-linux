# Mint Scan v6 — Linux Desktop Security Auditor
**by Mint Projects, Pretoria**

A full GUI security dashboard for Linux — Chromebook, Ubuntu, Debian, Kali.

---

## Features

| Screen | What it does | Data Source |
|---|---|---|
| **Dashboard** | System info, public IP, ISP, RAM, disk, CPU, battery | `/proc`, `/sys`, `ipapi.co` |
| **Wi-Fi** | Live scan of all nearby networks — SSID, security, signal | `nmcli` / `iwlist` |
| **Calls** | GNOME Calls history + KDE Connect Android integration | `~/.local/share/gnome-calls/` |
| **Network** | Interfaces, live ping graph, real speed test, connections | `netifaces`, `speedtest-cli` |
| **Battery** | Level, status, health, voltage, current, cycles | `/sys/class/power_supply/` |
| **Permissions** | Root status, sudo rules, device file access, firewall | `ufw`, `sudoers`, `/dev/` |
| **Threats** | Root check, open ports, SSH config, firewall, processes | `ss`, `ufw`, `/etc/ssh/` |
| **Notifications** | Real-time D-Bus notification monitor | `dbus-monitor` |
| **Port Scanner** | Local open ports + remote host scanner | `ss`, `nmap`, Python sockets |

---

## Install on Chromebook (Linux environment)

### Step 1 — Enable Linux on Chromebook
Settings → Advanced → Developers → Linux development environment → Turn on

### Step 2 — Clone from GitHub
```bash
git clone https://github.com/mintpro004/mint-scan-linux.git
cd mint-scan-linux
```

### Step 3 — Run installer
```bash
chmod +x install.sh
./install.sh
```

### Step 4 — Launch
```bash
./run.sh
```
Or find **Mint Scan** in your Linux apps menu.

---

## Install on Ubuntu / Debian / Kali

```bash
git clone https://github.com/mintpro004/mint-scan-linux.git
cd mint-scan-linux
chmod +x install.sh
./install.sh
./run.sh
```

---

## Manual install (without install.sh)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

## Android Phone Integration (KDE Connect)

To get your phone's calls, SMS and WhatsApp notifications on your Linux desktop:

```bash
sudo apt install kdeconnect
```

Then:
1. Install **KDE Connect** on your Android phone (Play Store)
2. Open KDE Connect on both devices — they must be on the same Wi-Fi
3. Pair them — your phone's calls, notifications and files will mirror to Linux

---

## Permissions & sudo

Some features need elevated access:
- **Wi-Fi scan**: Works without sudo via `nmcli` (NetworkManager must be running)
- **Port scan**: `nmap` works faster with sudo but also works without
- **SSH config check**: Needs sudo to read `/etc/ssh/sshd_config`
- **Battery**: Reads directly from `/sys/class/power_supply/` — no sudo needed

---

## Dependencies

Installed automatically by `install.sh`:
- `python3`, `python3-tk`, `python3-pip`
- `nmcli` (NetworkManager)
- `iw`, `wireless-tools`
- `nmap`
- `dbus` (notifications)
- Python packages: `customtkinter`, `psutil`, `netifaces`, `requests`, `speedtest-cli`

---

Mint Projects © 2025 — Pretoria, South Africa

---

## Push to GitHub (first time)

After creating the repo at github.com/mintpro004/mint-scan-linux:

```bash
cd mint-scan-linux
git init
git add .
git commit -m "Mint Scan v6 — Initial release"
git branch -M main
git remote add origin https://github.com/mintpro004/mint-scan-linux.git
git push -u origin main
```
