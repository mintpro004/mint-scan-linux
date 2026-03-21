"""
Mint Scan v7 — Main Application
Full GUI desktop security auditor for Linux
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import threading
import time
import sys
import os

# Dark theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Colour palette
C = {
    'bg':   '#020c14',
    'sf':   '#061523',
    's2':   '#0a1e2e',
    'br':   '#0d2a3d',
    'br2':  '#1a3a52',
    'ac':   '#00ffe0',
    'wn':   '#ff4c4c',
    'am':   '#ffb830',
    'ok':   '#39ff88',
    'bl':   '#4d9fff',
    'pu':   '#c084fc',
    'tx':   '#c8e8f4',
    'mu':   '#3a6278',
    'mu2':  '#5a8298',
}

MONO = ('Courier', 10)
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
    "✓ ALL SYSTEMS READY.",
]


class MintScanApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Mint Scan v7 — Security Auditor")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(fg_color=C['bg'])

        # Set window icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.png')
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
        except Exception:
            pass

        self.current_tab = tk.StringVar(value='dash')
        self._frames = {}

        # Show boot screen first
        self._show_boot()

    def _show_boot(self):
        self.boot_frame = ctk.CTkFrame(self.root, fg_color=C['bg'], corner_radius=0)
        self.boot_frame.pack(fill='both', expand=True)

        inner = ctk.CTkFrame(self.boot_frame, fg_color='transparent')
        inner.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(inner, text="[ MINT SCAN ]",
                     font=('Courier', 32, 'bold'), text_color=C['ac']).pack(anchor='w')
        ctk.CTkLabel(inner, text="SECURITY AUDITOR v7.0 — MINT PROJECTS",
                     font=MONO_SM, text_color=C['mu']).pack(anchor='w', pady=(0, 20))

        self.boot_log = ctk.CTkTextbox(inner, width=480, height=220,
                                       font=MONO_SM, fg_color=C['bg'],
                                       text_color=C['ac'], border_width=0)
        self.boot_log.pack()

        self._boot_idx = 0
        self._animate_boot()

    def _animate_boot(self):
        if self._boot_idx < len(BOOT_LINES):
            line = BOOT_LINES[self._boot_idx]
            color = C['ok'] if line.startswith('✓') else C['ac']
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
        # ── Top nav bar ──
        self.navbar = ctk.CTkFrame(self.root, height=52, fg_color=C['sf'],
                                   corner_radius=0)
        self.navbar.pack(fill='x', side='top')
        self.navbar.pack_propagate(False)

        ctk.CTkLabel(self.navbar, text="[ MINT SCAN ]",
                     font=('Courier', 15, 'bold'), text_color=C['ac']
                     ).pack(side='left', padx=16)
        ctk.CTkLabel(self.navbar, text="v7.0",
                     font=MONO_SM, text_color=C['mu']
                     ).pack(side='left', padx=2)

        self.clock_lbl = ctk.CTkLabel(self.navbar, text="--:--:--",
                                       font=MONO_SM, text_color=C['mu'])
        self.clock_lbl.pack(side='right', padx=16)

        self.score_lbl = ctk.CTkLabel(self.navbar, text="SCORE: —",
                                       font=('Courier', 11, 'bold'), text_color=C['ok'])
        self.score_lbl.pack(side='right', padx=12)

        # ── Sidebar tabs ──
        self.sidebar = ctk.CTkFrame(self.root, width=160, fg_color=C['sf'],
                                    corner_radius=0)
        self.sidebar.pack(fill='y', side='left')
        self.sidebar.pack_propagate(False)

        TABS = [
            ('⬡ DASHBOARD',  'dash'),
            ('🔑 PERMISSIONS','perms'),
            ('📶 WI-FI',      'wifi'),
            ('📞 CALLS',      'calls'),
            ('📡 NETWORK',    'network'),
            ('🔋 BATTERY',    'battery'),
            ('⚠  THREATS',    'threats'),
            ('🔔 NOTIFS',     'notifs'),
            ('🔍 PORT SCAN',  'ports'),
            ('📱 USB SYNC',   'usb'),
            ('🔬 NET SCAN',   'netscan'),
            ('🦠 MALWARE',    'malware'),
            ('🔧 SYS FIX',    'sysfix'),
        ]

        self._tab_btns = {}
        for label, key in TABS:
            btn = ctk.CTkButton(
                self.sidebar, text=label,
                font=('Courier', 10), height=42,
                fg_color='transparent', hover_color=C['br'],
                text_color=C['mu'], anchor='w',
                corner_radius=0,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(fill='x', pady=1, padx=4)
            self._tab_btns[key] = btn

        ctk.CTkLabel(self.sidebar, text="MINT PROJECTS",
                     font=('Courier', 8), text_color=C['mu']
                     ).pack(side='bottom', pady=8)

        # ── Main content area ──
        self.content = ctk.CTkFrame(self.root, fg_color=C['bg'], corner_radius=0)
        self.content.pack(fill='both', expand=True, side='left')

        # Import screens here to avoid circular imports
        from dash     import DashScreen
        from perms    import PermsScreen
        from wifi     import WifiScreen
        from calls    import CallsScreen
        from network  import NetworkScreen
        from battery  import BatteryScreen
        from threats  import ThreatsScreen
        from notifs   import NotifsScreen
        from ports    import PortsScreen

        screen_classes = {
            'dash':    DashScreen,
            'perms':   PermsScreen,
            'wifi':    WifiScreen,
            'calls':   CallsScreen,
            'network': NetworkScreen,
            'battery': BatteryScreen,
            'threats': ThreatsScreen,
            'notifs':  NotifsScreen,
            'ports':   PortsScreen,
            'usb':     UsbScreen,
            'netscan': NetScanScreen,
            'malware': MalwareScreen,
            'sysfix':  SysFixScreen,
        }

        for key, cls in screen_classes.items():
            frame = cls(self.content, self)
            frame.place(relwidth=1, relheight=1)
            self._frames[key] = frame

        # Start on dash
        self._switch_tab('dash')

        # Clock
        self._tick_clock()

    def _switch_tab(self, key):
        # Hide all
        for frame in self._frames.values():
            frame.place_forget()
        # Show selected
        self._frames[key].place(relwidth=1, relheight=1)
        self._frames[key].on_focus()
        # Update sidebar
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(text_color=C['ac'], fg_color=C['br'])
            else:
                btn.configure(text_color=C['mu'], fg_color='transparent')
        self.current_tab.set(key)

    def _tick_clock(self):
        self.clock_lbl.configure(text=time.strftime('%H:%M:%S'))
        self.root.after(1000, self._tick_clock)

    def update_score(self, score):
        col = C['ok'] if score >= 75 else C['am'] if score >= 50 else C['wn']
        self.score_lbl.configure(text=f"SCORE: {score}", text_color=col)

    def run(self):
        self.root.mainloop()
