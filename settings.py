"""Settings Screen — UI font size, scaling, theme, preferences"""
import tkinter as tk
import customtkinter as ctk
import json, os, threading
from widgets import ScrollableFrame, Card, SectionHeader, ResultBox, Btn, C, MONO, MONO_SM

SETTINGS_FILE = os.path.expanduser('~/.mint_scan_settings.json')

DEFAULTS = {
    'font_size':    10,
    'ui_scale':     1.0,
    'theme':        'dark',
    'accent_color': '#00ffe0',
    'show_clock':   True,
    'ping_interval': 3,
    'scan_on_start': True,
}

def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            d = json.load(f)
            return {**DEFAULTS, **d}
    except Exception:
        return dict(DEFAULTS)

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built = False
        self.settings = load_settings()

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True
        self._load_values()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="⚙  SETTINGS", font=('Courier',13,'bold'),
                     text_color=C['ac']).pack(side='left', padx=16)
        Btn(hdr, "💾 SAVE & APPLY", command=self._save,
            variant='success', width=150).pack(side='right', padx=12, pady=6)
        Btn(hdr, "↺ RESET", command=self._reset,
            variant='ghost', width=80).pack(side='right', padx=4, pady=6)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # ── APPEARANCE ──────────────────────────────────────
        SectionHeader(body, '01', 'APPEARANCE').pack(fill='x', padx=14, pady=(14,4))
        appear = Card(body)
        appear.pack(fill='x', padx=14, pady=(0,8))

        # Font size
        row = ctk.CTkFrame(appear, fg_color='transparent')
        row.pack(fill='x', padx=12, pady=(10,4))
        ctk.CTkLabel(row, text="FONT SIZE", font=('Courier',9,'bold'),
                     text_color=C['ac'], width=140).pack(side='left')
        self.font_lbl = ctk.CTkLabel(row, text="10px", font=MONO_SM, text_color=C['tx'], width=40)
        self.font_lbl.pack(side='right')
        self.font_slider = ctk.CTkSlider(row, from_=8, to=16, number_of_steps=8,
                                          command=self._on_font_change,
                                          button_color=C['ac'], progress_color=C['ac'],
                                          fg_color=C['br'])
        self.font_slider.pack(side='left', fill='x', expand=True, padx=8)
        ctk.CTkLabel(appear, text="Adjusts text size throughout the app",
                     font=('Courier',8), text_color=C['mu']).pack(anchor='w', padx=12, pady=(0,4))

        # UI Scale
        row2 = ctk.CTkFrame(appear, fg_color='transparent')
        row2.pack(fill='x', padx=12, pady=(8,4))
        ctk.CTkLabel(row2, text="UI SCALE", font=('Courier',9,'bold'),
                     text_color=C['ac'], width=140).pack(side='left')
        self.scale_lbl = ctk.CTkLabel(row2, text="100%", font=MONO_SM, text_color=C['tx'], width=40)
        self.scale_lbl.pack(side='right')
        self.scale_slider = ctk.CTkSlider(row2, from_=0.7, to=1.5, number_of_steps=16,
                                           command=self._on_scale_change,
                                           button_color=C['ac'], progress_color=C['ac'],
                                           fg_color=C['br'])
        self.scale_slider.pack(side='left', fill='x', expand=True, padx=8)
        ctk.CTkLabel(appear, text="Makes all elements larger or smaller (restart to apply fully)",
                     font=('Courier',8), text_color=C['mu']).pack(anchor='w', padx=12, pady=(0,10))

        # Accent colour
        row3 = ctk.CTkFrame(appear, fg_color='transparent')
        row3.pack(fill='x', padx=12, pady=(4,10))
        ctk.CTkLabel(row3, text="ACCENT COLOUR", font=('Courier',9,'bold'),
                     text_color=C['ac'], width=140).pack(side='left')
        colours = ['#00ffe0','#39ff88','#4d9fff','#ffb830','#ff4c4c','#c084fc']
        self._accent_var = tk.StringVar(value=self.settings.get('accent_color','#00ffe0'))
        for colour in colours:
            btn = ctk.CTkButton(row3, text='', width=28, height=28,
                                fg_color=colour, hover_color=colour,
                                corner_radius=14, border_width=0,
                                command=lambda c=colour: self._set_accent(c))
            btn.pack(side='left', padx=3)

        # ── PERFORMANCE ─────────────────────────────────────
        SectionHeader(body, '02', 'PERFORMANCE').pack(fill='x', padx=14, pady=(10,4))
        perf = Card(body)
        perf.pack(fill='x', padx=14, pady=(0,8))

        row4 = ctk.CTkFrame(perf, fg_color='transparent')
        row4.pack(fill='x', padx=12, pady=(10,4))
        ctk.CTkLabel(row4, text="PING INTERVAL", font=('Courier',9,'bold'),
                     text_color=C['ac'], width=140).pack(side='left')
        self.ping_lbl = ctk.CTkLabel(row4, text="3s", font=MONO_SM, text_color=C['tx'], width=40)
        self.ping_lbl.pack(side='right')
        self.ping_slider = ctk.CTkSlider(row4, from_=1, to=10, number_of_steps=9,
                                          command=self._on_ping_change,
                                          button_color=C['ac'], progress_color=C['ac'],
                                          fg_color=C['br'])
        self.ping_slider.pack(side='left', fill='x', expand=True, padx=8)
        ctk.CTkLabel(perf, text="How often the network graph updates (lower = more CPU use)",
                     font=('Courier',8), text_color=C['mu']).pack(anchor='w', padx=12, pady=(0,6))

        # Scan on start
        row5 = ctk.CTkFrame(perf, fg_color='transparent')
        row5.pack(fill='x', padx=12, pady=(4,10))
        ctk.CTkLabel(row5, text="AUTO-SCAN ON START", font=('Courier',9,'bold'),
                     text_color=C['ac'], width=200).pack(side='left')
        self.scan_start_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(row5, text='', variable=self.scan_start_var,
                      onvalue=True, offvalue=False,
                      button_color=C['ac'], progress_color=C['br2']
                      ).pack(side='left', padx=8)
        ctk.CTkLabel(row5, text="Load dashboard data automatically on launch",
                     font=('Courier',8), text_color=C['mu']).pack(side='left', padx=4)

        # ── DISPLAY ─────────────────────────────────────────
        SectionHeader(body, '03', 'DISPLAY').pack(fill='x', padx=14, pady=(10,4))
        disp = Card(body)
        disp.pack(fill='x', padx=14, pady=(0,8))

        row6 = ctk.CTkFrame(disp, fg_color='transparent')
        row6.pack(fill='x', padx=12, pady=(10,10))
        ctk.CTkLabel(row6, text="SHOW CLOCK", font=('Courier',9,'bold'),
                     text_color=C['ac'], width=200).pack(side='left')
        self.clock_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(row6, text='', variable=self.clock_var,
                      onvalue=True, offvalue=False,
                      button_color=C['ac'], progress_color=C['br2']
                      ).pack(side='left', padx=8)

        # Preview box
        SectionHeader(body, '04', 'LIVE PREVIEW').pack(fill='x', padx=14, pady=(10,4))
        self.preview = Card(body)
        self.preview.pack(fill='x', padx=14, pady=(0,8))
        self.prev_title = ctk.CTkLabel(self.preview, text="[ MINT SCAN ]",
                                        font=('Courier',14,'bold'), text_color=C['ac'])
        self.prev_title.pack(anchor='w', padx=12, pady=(10,4))
        self.prev_body = ctk.CTkLabel(self.preview,
                                       text="Sample text — this is how your UI will look at the selected font size.",
                                       font=('Courier',10), text_color=C['tx'])
        self.prev_body.pack(anchor='w', padx=12, pady=(0,10))

        self.status_lbl = ctk.CTkLabel(body, text="", font=MONO_SM, text_color=C['ok'])
        self.status_lbl.pack(pady=8)
        ctk.CTkLabel(body, text="", height=20).pack()

    def _load_values(self):
        s = self.settings
        self.font_slider.set(s.get('font_size', 10))
        self.font_lbl.configure(text=f"{int(s.get('font_size',10))}px")
        self.scale_slider.set(s.get('ui_scale', 1.0))
        self.scale_lbl.configure(text=f"{int(s.get('ui_scale',1.0)*100)}%")
        self.ping_slider.set(s.get('ping_interval', 3))
        self.ping_lbl.configure(text=f"{int(s.get('ping_interval',3))}s")
        self.scan_start_var.set(s.get('scan_on_start', True))
        self.clock_var.set(s.get('show_clock', True))

    def _on_font_change(self, val):
        size = int(val)
        self.font_lbl.configure(text=f"{size}px")
        self.prev_title.configure(font=('Courier', size+4, 'bold'))
        self.prev_body.configure(font=('Courier', size))

    def _on_scale_change(self, val):
        pct = int(float(val)*100)
        self.scale_lbl.configure(text=f"{pct}%")

    def _on_ping_change(self, val):
        self.ping_lbl.configure(text=f"{int(val)}s")

    def _set_accent(self, colour):
        self._accent_var.set(colour)
        self.prev_title.configure(text_color=colour)
        self.status_lbl.configure(text=f"Accent: {colour} — tap SAVE to apply")

    def _save(self):
        self.settings = {
            'font_size':     int(self.font_slider.get()),
            'ui_scale':      round(float(self.scale_slider.get()), 1),
            'theme':         'dark',
            'accent_color':  self._accent_var.get() if hasattr(self,'_accent_var') else '#00ffe0',
            'ping_interval': int(self.ping_slider.get()),
            'scan_on_start': bool(self.scan_start_var.get()),
            'show_clock':    bool(self.clock_var.get()),
        }
        if save_settings(self.settings):
            self.status_lbl.configure(
                text="✓ Settings saved. Restart Mint Scan to apply all changes.",
                text_color=C['ok'])
            # Apply font size immediately via CTk scaling
            try:
                ctk.set_widget_scaling(self.settings['ui_scale'])
            except Exception:
                pass
        else:
            self.status_lbl.configure(text="✗ Failed to save settings", text_color=C['wn'])

    def _reset(self):
        self.settings = dict(DEFAULTS)
        self._load_values()
        self.status_lbl.configure(text="Reset to defaults — tap SAVE to apply", text_color=C['am'])
