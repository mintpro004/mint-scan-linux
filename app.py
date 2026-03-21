"""
Mint Scan v7 — Main Application
Polished UI: smooth tab switching, proper sizing, responsive layout.
"""
import tkinter as tk
import customtkinter as ctk
import threading, time, sys, os, json

# Import colour palette from widgets (single source of truth)
from widgets import C, apply_theme

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BOOT_LINES = [
    "INITIALISING MINT SCAN v7...",
    "LOADING SECURITY MODULES...",
    "PROBING NETWORK INTERFACES...",
    "LOADING THREAT ENGINE...",
    "READING SYSTEM STATE...",
    "✓ ALL SYSTEMS READY.",
]

# Tab definitions: (key, label, icon)
ALL_TABS = [
    ('dash',        'Dashboard',    '⬡'),
    ('perms',       'Permissions',  '🔑'),
    ('wifi',        'Wi-Fi',        '📶'),
    ('calls',       'Calls',        '📞'),
    ('network',     'Network',      '📡'),
    ('battery',     'Battery',      '🔋'),
    ('threats',     'Threats',      '⚠'),
    ('notifs',      'Notifs',       '🔔'),
    ('ports',       'Port Scan',    '🔍'),
    ('usb',         'USB Sync',     '📱'),
    ('apk',         'APK Install',  '📦'),
    ('netscan',     'Net Scan',     '🔬'),
    ('malware',     'Malware',      '🦠'),
    ('sysfix',      'Sys Fix',      '🔧'),
    ('firewall',    'Firewall',     '🔥'),
    ('toolbox',     'Toolbox',      '🛠'),
    ('investigate', 'Investigate',  '🕵'),
    ('settings',    'Settings',     '⚙'),
]


class MintScanApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Mint Scan v7")
        self.root.geometry("1140x740")
        self.root.minsize(920, 620)
        self.root.configure(fg_color=C['bg'])

        # App icon
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            for name in ['icon.png','icon_128.png','icon_256.png']:
                p = os.path.join(base, name)
                if os.path.exists(p):
                    self.root.iconphoto(True, tk.PhotoImage(file=p))
                    break
        except Exception:
            pass

        self.current_tab = 'dash'
        self._frames    = {}
        self._tab_btns  = {}
        self._show_boot()

    # ── BOOT SCREEN ───────────────────────────────────────────

    def _show_boot(self):
        self.boot = ctk.CTkFrame(self.root, fg_color=C['bg'], corner_radius=0)
        self.boot.pack(fill='both', expand=True)

        inner = ctk.CTkFrame(self.boot, fg_color='transparent')
        inner.place(relx=0.5, rely=0.5, anchor='center')

        # Logo
        ctk.CTkLabel(inner, text="[ MINT SCAN ]",
                     font=('Courier',34,'bold'),
                     text_color=C['ac']).pack(anchor='w')
        ctk.CTkLabel(inner, text="ADVANCED SECURITY AUDITOR  v7.0  |  MINT PROJECTS",
                     font=('Courier',9), text_color=C['mu']
                     ).pack(anchor='w', pady=(2,18))

        # Boot log
        self.boot_log = ctk.CTkTextbox(inner, width=500, height=200,
                                        font=('Courier',9),
                                        fg_color=C['s2'],
                                        text_color=C['ac'],
                                        border_color=C['br'],
                                        border_width=1,
                                        corner_radius=6)
        self.boot_log.pack()

        # Progress bar
        self.boot_prog = ctk.CTkProgressBar(inner, width=500,
                                             progress_color=C['ac'],
                                             fg_color=C['br'], height=4)
        self.boot_prog.pack(pady=(8,0))
        self.boot_prog.set(0)

        self._boot_idx = 0
        self._animate_boot()

    def _animate_boot(self):
        if self._boot_idx < len(BOOT_LINES):
            line = BOOT_LINES[self._boot_idx]
            self.boot_log.configure(state='normal')
            self.boot_log.insert('end', line + '\n')
            self.boot_log.configure(state='disabled')
            self.boot_prog.set((self._boot_idx+1) / len(BOOT_LINES))
            self._boot_idx += 1
            self.root.after(180, self._animate_boot)
        else:
            self.root.after(300, self._launch_main)

    def _launch_main(self):
        self.boot.destroy()
        self._build_ui()

    # ── MAIN UI ───────────────────────────────────────────────

    def _build_ui(self):

        # ── Top navbar ────────────────────────────────────────
        self.navbar = ctk.CTkFrame(self.root, height=52,
                                   fg_color=C['sf'], corner_radius=0)
        self.navbar.pack(fill='x', side='top')
        self.navbar.pack_propagate(False)

        # Left: logo
        logo_frame = ctk.CTkFrame(self.navbar, fg_color='transparent')
        logo_frame.pack(side='left', padx=16)
        ctk.CTkLabel(logo_frame, text="[ MINT SCAN ]",
                     font=('Courier',14,'bold'),
                     text_color=C['ac']).pack(side='left')
        ctk.CTkLabel(logo_frame, text=" v7",
                     font=('Courier',9),
                     text_color=C['mu']).pack(side='left', pady=(4,0))

        # Right: clock + score
        self.clock_lbl = ctk.CTkLabel(self.navbar, text="--:--:--",
                                       font=('Courier',10), text_color=C['mu'])
        self.clock_lbl.pack(side='right', padx=16)

        self.score_lbl = ctk.CTkLabel(self.navbar, text="SCORE --",
                                       font=('Courier',10,'bold'),
                                       text_color=C['ok'])
        self.score_lbl.pack(side='right', padx=(0,8))

        # Thin accent line under navbar
        ctk.CTkFrame(self.root, height=2,
                     fg_color=C['br'], corner_radius=0).pack(fill='x', side='top')

        # ── Main container ────────────────────────────────────
        container = ctk.CTkFrame(self.root, fg_color=C['bg'], corner_radius=0)
        container.pack(fill='both', expand=True)

        # ── Sidebar ───────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(container, width=172,
                                    fg_color=C['sf'], corner_radius=0)
        self.sidebar.pack(fill='y', side='left')
        self.sidebar.pack_propagate(False)

        # Sidebar header label
        ctk.CTkLabel(self.sidebar, text="NAVIGATION",
                     font=('Courier',7,'bold'), text_color=C['mu']
                     ).pack(anchor='w', padx=12, pady=(10,4))

        # ── Content area ──────────────────────────────────────
        self.content = ctk.CTkFrame(container,
                                    fg_color=C['bg'], corner_radius=0)
        self.content.pack(fill='both', expand=True, side='left')

        # ── Load all screens ──────────────────────────────────
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

        screen_map = {
            'dash':        _safe('dash',        'DashScreen'),
            'perms':       _safe('perms',       'PermsScreen'),
            'wifi':        _safe('wifi',        'WifiScreen'),
            'calls':       _safe('calls',       'CallsScreen'),
            'network':     _safe('network',     'NetworkScreen'),
            'battery':     _safe('battery',     'BatteryScreen'),
            'threats':     _safe('threats',     'ThreatsScreen'),
            'notifs':      _safe('notifs',      'NotifsScreen'),
            'ports':       _safe('ports',       'PortsScreen'),
            'usb':         _safe('usb',         'UsbScreen'),
            'apk':         _safe('apk_install', 'ApkScreen'),
            'netscan':     _safe('netscan',     'NetScanScreen'),
            'malware':     _safe('malware',     'MalwareScreen'),
            'sysfix':      _safe('sysfix',      'SysFixScreen'),
            'firewall':    _safe('firewall',    'FirewallScreen'),
            'toolbox':     _safe('toolbox',     'ToolboxScreen'),
            'investigate': _safe('investigate', 'InvestigateScreen'),
            'settings':    _safe('settings',    'SettingsScreen'),
        }
        # Only keep successfully loaded screens
        screen_map = {k: v for k, v in screen_map.items() if v is not None}

        # ── Build sidebar buttons ─────────────────────────────
        # Only tabs whose screen loaded
        visible_tabs = [(k, lbl, icon) for k, lbl, icon in ALL_TABS
                        if k in screen_map]

        self._tab_btns = {}
        for key, label, icon in visible_tabs:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f" {icon}  {label}",
                font=('Courier', 10),
                height=38,
                anchor='w',
                fg_color='transparent',
                hover_color=C['br'],
                text_color=C['mu'],
                corner_radius=6,
                border_width=0,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(fill='x', padx=6, pady=1)
            self._tab_btns[key] = btn

        # Sidebar footer
        ctk.CTkFrame(self.sidebar, height=1,
                     fg_color=C['br']).pack(fill='x', side='bottom', pady=(0,8))
        ctk.CTkLabel(self.sidebar, text="MINT PROJECTS  •  PTY",
                     font=('Courier',7), text_color=C['br2']
                     ).pack(side='bottom', pady=(0,4))

        # ── Instantiate screen frames ─────────────────────────
        for key, cls in screen_map.items():
            try:
                frame = cls(self.content, self)
                frame.place(relwidth=1, relheight=1)
                self._frames[key] = frame
            except Exception as e:
                print(f"  [error] {key}: {e}")

        # Start on dash
        first = 'dash' if 'dash' in self._frames else (
            next(iter(self._frames)) if self._frames else None)
        if first:
            self._switch_tab(first)

        self._tick_clock()

    # ── TAB SWITCHING ─────────────────────────────────────────

    def _switch_tab(self, key):
        if key not in self._frames:
            return
        # Hide all frames
        for frame in self._frames.values():
            frame.place_forget()
        # Show selected
        self._frames[key].place(relwidth=1, relheight=1)
        self._frames[key].on_focus()
        # Update sidebar button styles
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(
                    fg_color=C['br'],
                    text_color=C['ac'],
                    font=('Courier', 10, 'bold')
                )
            else:
                btn.configure(
                    fg_color='transparent',
                    text_color=C['mu'],
                    font=('Courier', 10)
                )
        self.current_tab = key

    # ── CLOCK ─────────────────────────────────────────────────

    def _tick_clock(self):
        self.clock_lbl.configure(text=time.strftime('%H:%M:%S'))
        self.root.after(1000, self._tick_clock)

    # ── PUBLIC API ────────────────────────────────────────────

    def update_score(self, score):
        col = C['ok'] if score >= 75 else C['am'] if score >= 50 else C['wn']
        self.score_lbl.configure(text=f"SCORE {score}", text_color=col)

    def run(self):
        self.root.mainloop()
