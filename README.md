# Mint Scan v7 — Advanced Linux Security Auditor
**By Mint Projects, Pretoria**

## Quick Start
```bash
bash install.sh
bash run.sh
```

## What's Included (20 Screens)
| Tab | Description |
|-----|-------------|
| Dashboard | System overview, security score, IP info |
| Permissions | File/sudo/SUID permission checker |
| Wi-Fi | Network scanner, signal strength, encryption |
| Calls | Call log analysis, number risk scoring |
| Network | Interfaces, active connections, public IP |
| Battery | Live battery stats from /sys/class/power_supply |
| Threats | Port scan, process audit, auto-remediation |
| Guardian | Auto-defense, panic button, USB lockdown |
| Notifs | Desktop notification monitor |
| Port Scan | TCP/UDP open ports with risk flags |
| USB Sync | **Phone companion via USB (ADB)** |
| Wireless | **Wi-Fi companion server (no cable needed)** |
| Net Scan | Device discovery, traffic capture, vuln scan |
| Malware | ClamAV integration, rootkit check (rkhunter) |
| Sys Fix | System health, permissions, firewall repair |
| Firewall | UFW rules manager, add/remove rules |
| Toolbox | Install/manage all security tools |
| Investigate | IP geolocation, WHOIS, attack timeline |
| Auditor | Kernel audit (auditd), binary integrity |
| Settings | Theme, accent color, font size |

## Phone Companion — Two Methods

### Method 1: USB (ADB)
1. Phone → Settings → About → tap Build Number 7× → Developer Options → USB Debugging ON
2. Plug USB cable into Linux machine
3. Mint Scan → USB Sync → tap ↺ RESCAN
4. Tap ALLOW on phone popup
5. Use the sync buttons to pull calls, SMS, contacts, screenshots

### Method 2: Wi-Fi (No cable)
1. Mint Scan → Wireless tab → tap START SERVER
2. Note the IP:Port shown (e.g. 192.168.1.100:7777)
3. On phone browser: open http://192.168.1.100:7777
4. Companion app loads — use Sync tab to send data to desktop

## Requirements
- Ubuntu 20.04+, Kali Linux, Linux Mint, ChromeOS (Linux), WSL2
- Python 3.9+
- python3-tk (auto-installed by install.sh)

## v7 Fixes (this release)
- Fixed: 7 screen modules importing C/MONO/MONO_SM from wrong module (utils → widgets)
- Fixed: Wireless tab missing from ALL_TABS and screen_map in app.py
- Fixed: companion_app.html completely rebuilt — was a static placeholder, now fully functional
- Fixed: /sync/network and /sync/location endpoints missing from wireless server
- Fixed: ADB udev rules not written during install (phone not detected)
- Fixed: run.sh now smarter self-healer
- Added: Wireless tab registered as full screen in navigation
