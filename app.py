"""
Mint Scan v7 — Main Application
Full GUI desktop security auditor for Linux
"""
import tkinter as tk
import customtkinter as ctk
import threading
import time
import sys
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Import C from widgets — supports dark/light theme switching
from widgets import C, apply_theme
MONO    = ('Courier', 10)
MONO_SM = ('Courier', 9)
MONO_LG = ('Courier', 14)
MONO_XL = ('Courier', 28, 'bold')

BOOT_LINES = [
    "INITIALISING MINT SCAN v7.0...",
    "LOADING SYSTEM LIBRARIES...",
    "PROBING NETWORK INTERFACES...",
    "SCANNING WIFI SUBSYSTEM...",
    "LOADING PROCESS MONITOR...",
    "BUILDING THREAT ENGINE...",
    "LOADING CALL LOG READER...",
    "READING SYSTEM NOTIFICATIONS...",
    "ALL SYSTEMS READY.",
]


class MintScanApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Mint Scan v7 — Security Auditor")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(fg_color=C['bg'])

        # App icon
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            for name in ['icon.png', 'icon_128.png', 'icon_256.png']:
                p = os.path.join(base, name)
                if os.path.exists(p):
                    img = tk.PhotoImage(file=p)
                    self.root.iconphoto(True, img)
                    break
        except Exception:
            pass

        self.current_tab = tk.StringVar(value='dash')
        self._frames   = {}
        self._tab_btns = {}
        self._show_boot()

    def _show_boot(self):
        self.boot_frame = ctk.CTkFrame(self.root, fg_color=C['bg'], corner_radius=0)
        self.boot_frame.pack(fill='both', expand=True)
        inner = ctk.CTkFrame(self.boot_frame, fg_color='transparent')
        inner.place(relx=0.5, rely=0.5, anchor='center')
        ctk.CTkLabel(inner, text="[ MINT SCAN ]",
                     font=('Courier', 32, 'bold'), text_color=C['ac']).pack(anchor='w')
        ctk.CTkLabel(inner, text="SECURITY AUDITOR v7.0  |  MINT PROJECTS",
                     font=MONO_SM, text_color=C['mu']).pack(anchor='w', pady=(0,20))
        self.boot_log = ctk.CTkTextbox(inner, width=480, height=220,
                                       font=MONO_SM, fg_color=C['bg'],
                                       text_color=C['ac'], border_width=0)
        self.boot_log.pack()
        self._boot_idx = 0
        self._animate_boot()

    def _animate_boot(self):
        if self._boot_idx < len(BOOT_LINES):
            line = BOOT_LINES[self._boot_idx]
            self.boot_log.configure(state='normal')
            self.boot_log.insert('end', line + '\n')
            self.boot_log.configure(state='disabled')
            self._boot_idx += 1
            self.root.after(220, self._animate_boot)
        else:
            self.root.after(400, self._launch_main)

    def _launch_main(self):
        self.boot_frame.destroy()
        self._build_ui()

    def _build_ui(self):
        # ── Navbar ───────────────────────────────────────────
        self.navbar = ctk.CTkFrame(self.root, height=52,
                                   fg_color=C['sf'], corner_radius=0)
        self.navbar.pack(fill='x', side='top')
        self.navbar.pack_propagate(False)
        ctk.CTkLabel(self.navbar, text="[ MINT SCAN ]",
                     font=('Courier',15,'bold'), text_color=C['ac']
                     ).pack(side='left', padx=16)
        ctk.CTkLabel(self.navbar, text="v7.0",
                     font=MONO_SM, text_color=C['mu']).pack(side='left', padx=2)
        self.clock_lbl = ctk.CTkLabel(self.navbar, text="--:--:--",
                                       font=MONO_SM, text_color=C['mu'])
        self.clock_lbl.pack(side='right', padx=16)
        self.score_lbl = ctk.CTkLabel(self.navbar, text="SCORE: --",
                                       font=('Courier',11,'bold'), text_color=C['ok'])
        self.score_lbl.pack(side='right', padx=12)

        # ── Sidebar ───────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self.root, width=162,
                                    fg_color=C['sf'], corner_radius=0)
        self.sidebar.pack(fill='y', side='left')
        self.sidebar.pack_propagate(False)

        # ── Content ───────────────────────────────────────────
        self.content = ctk.CTkFrame(self.root, fg_color=C['bg'], corner_radius=0)
        self.content.pack(fill='both', expand=True, side='left')

        # ── Load screens ──────────────────────────────────────
        # Add this file's directory to path so all screens resolve
        import importlib as _il
        _base = os.path.dirname(os.path.abspath(__file__))
        if _base not in sys.path:
            sys.path.insert(0, _base)

        def _safe(mod, cls):
            try:
                return getattr(_il.import_module(mod), cls)
            except Exception as e:
                print(f"  [skip] {mod}: {e}")
                return None

        # Core screens
        DashScreen    = _safe('dash',    'DashScreen')
        PermsScreen   = _safe('perms',   'PermsScreen')
        WifiScreen    = _safe('wifi',    'WifiScreen')
        CallsScreen   = _safe('calls',   'CallsScreen')
        NetworkScreen = _safe('network', 'NetworkScreen')
        BatteryScreen = _safe('battery', 'BatteryScreen')
        ThreatsScreen = _safe('threats', 'ThreatsScreen')
        NotifsScreen  = _safe('notifs',  'NotifsScreen')
        PortsScreen   = _safe('ports',   'PortsScreen')
        # Extended screens
        UsbScreen      = _safe('usb',         'UsbScreen')
        ApkScreen      = _safe('apk_install', 'ApkScreen')
        NetScanScreen  = _safe('netscan',     'NetScanScreen')
        MalwareScreen  = _safe('malware',     'MalwareScreen')
        SysFixScreen   = _safe('sysfix',      'SysFixScreen')
        SettingsScreen  = _safe('settings',   'SettingsScreen')
        WirelessScreen  = _safe('wireless',   'WirelessScreen')

        # screen_classes: only include screens that loaded
        _all_screens = [
            ('dash',     DashScreen),
            ('perms',    PermsScreen),
            ('wifi',     WifiScreen),
            ('calls',    CallsScreen),
            ('network',  NetworkScreen),
            ('battery',  BatteryScreen),
            ('threats',  ThreatsScreen),
            ('notifs',   NotifsScreen),
            ('ports',    PortsScreen),
            ('usb',      UsbScreen),
            ('apk',      ApkScreen),
            ('netscan',  NetScanScreen),
            ('malware',  MalwareScreen),
            ('sysfix',   SysFixScreen),
            ('settings',  SettingsScreen),
            ('wireless',  WirelessScreen),
        ]
        screen_classes = {k: v for k, v in _all_screens if v is not None}

        # ── TABS: built AFTER screen_classes ──────────────────
        # This MUST stay below screen_classes — do not move up
        ALL_TABS = [
            ('DASHBOARD',   'dash'),
            ('PERMISSIONS', 'perms'),
            ('WI-FI',       'wifi'),
            ('CALLS',       'calls'),
            ('NETWORK',     'network'),
            ('BATTERY',     'battery'),
            ('THREATS',     'threats'),
            ('NOTIFS',      'notifs'),
            ('PORT SCAN',   'ports'),
            ('USB SYNC',    'usb'),
            ('APK INSTALL', 'apk'),
            ('NET SCAN',    'netscan'),
            ('MALWARE',     'malware'),
            ('SYS FIX',     'sysfix'),
            ('SETTINGS',    'settings'),
            ('FIREWALL',    'firewall'),
            ('WIFI SYNC',   'wireless'),
        ]
        tabs = [(lbl, key) for lbl, key in ALL_TABS if key in screen_classes]

        # ── Sidebar buttons ───────────────────────────────────
        self._tab_btns = {}
        for label, key in tabs:
            btn = ctk.CTkButton(
                self.sidebar, text=label,
                font=('Courier', 9), height=40,
                fg_color='transparent', hover_color=C['br'],
                text_color=C['mu'], anchor='w',
                corner_radius=0,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(fill='x', pady=1, padx=4)
            self._tab_btns[key] = btn

        ctk.CTkLabel(self.sidebar, text="MINT PROJECTS",
                     font=('Courier', 7), text_color=C['mu']
                     ).pack(side='bottom', pady=8)

        # ── Instantiate screens ───────────────────────────────
        for key, cls in screen_classes.items():
            try:
                frame = cls(self.content, self)
                frame.place(relwidth=1, relheight=1)
                self._frames[key] = frame
            except Exception as e:
                print(f"  [error] Could not build {key}: {e}")

        # Start on dashboard
        if 'dash' in self._frames:
            self._switch_tab('dash')
        elif self._frames:
            self._switch_tab(next(iter(self._frames)))

        self._tick_clock()

    def _switch_tab(self, key):
        if key not in self._frames:
            return
        for frame in self._frames.values():
            frame.place_forget()
        self._frames[key].place(relwidth=1, relheight=1)
        self._frames[key].on_focus()
        for k, btn in self._tab_btns.items():
            btn.configure(
                text_color=C['ac'] if k == key else C['mu'],
                fg_color=C['br'] if k == key else 'transparent'
            )
        self.current_tab.set(key)

    def _tick_clock(self):
        self.clock_lbl.configure(text=time.strftime('%H:%M:%S'))
        self.root.after(1000, self._tick_clock)

    def update_score(self, score):
        col = C['ok'] if score >= 75 else C['am'] if score >= 50 else C['wn']
        self.score_lbl.configure(text=f"SCORE: {score}", text_color=col)

    def run(self):
        self.root.mainloop()
