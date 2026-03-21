"""
Mint Scan v7 — Shared Widgets
Fixed scrolling + light/dark theme support
All widget classes: ScrollableFrame, Card, SectionHeader, InfoGrid,
                   ResultBox, Btn, Badge, LiveBadge, PortBar
"""
import tkinter as tk
import customtkinter as ctk

# ── Theme palettes ────────────────────────────────────────────────
DARK_THEME = {
    'bg':  '#020c14', 'sf':  '#061523', 's2':  '#0a1e2e',
    'br':  '#0d2a3d', 'br2': '#1a3a52', 'ac':  '#00ffe0',
    'wn':  '#ff4c4c', 'am':  '#ffb830', 'ok':  '#39ff88',
    'bl':  '#4d9fff', 'pu':  '#c084fc', 'tx':  '#c8e8f4',
    'mu':  '#3a6278', 'mu2': '#5a8298',
}

LIGHT_THEME = {
    'bg':  '#f0f4f8', 'sf':  '#e2e8f0', 's2':  '#ffffff',
    'br':  '#cbd5e1', 'br2': '#94a3b8', 'ac':  '#0077cc',
    'wn':  '#dc2626', 'am':  '#d97706', 'ok':  '#16a34a',
    'bl':  '#2563eb', 'pu':  '#7c3aed', 'tx':  '#1e293b',
    'mu':  '#64748b', 'mu2': '#475569',
}

# Active colour palette — starts dark
C = dict(DARK_THEME)

MONO    = ('Courier', 10)
MONO_SM = ('Courier', 9)
MONO_LG = ('Courier', 13, 'bold')
MONO_XL = ('Courier', 36, 'bold')

_current_theme = 'dark'


def get_theme():
    return _current_theme


def apply_theme(theme_name):
    """Switch active colours to dark or light theme."""
    global _current_theme
    _current_theme = theme_name
    palette = LIGHT_THEME if theme_name == 'light' else DARK_THEME
    C.update(palette)
    try:
        ctk.set_appearance_mode('light' if theme_name == 'light' else 'dark')
    except Exception:
        pass


# ── ScrollableFrame ───────────────────────────────────────────────

class ScrollableFrame(tk.Frame):
    """
    Reliable scrollable container.
    Works on Chromebook Linux — mouse wheel, Button-4/5, touchpad all work.
    Usage:
        body = ScrollableFrame(parent)
        body.pack(fill='both', expand=True)
        ctk.CTkLabel(body, text="Hello").pack()   # goes into scrollable area
    """
    def __init__(self, parent, fg_color=None, **kwargs):
        bg = fg_color or C['bg']
        super().__init__(parent, bg=bg)

        # Canvas fills the frame
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)

        # Scrollbar on the right
        self._scrollbar = tk.Scrollbar(
            self, orient='vertical', command=self._canvas.yview)
        self._scrollbar.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # Inner frame — all content goes here
        self._body = tk.Frame(self._canvas, bg=bg)
        self._win  = self._canvas.create_window(
            (0, 0), window=self._body, anchor='nw')

        # Update scroll region whenever content changes
        self._body.bind('<Configure>', self._update_region)
        self._canvas.bind('<Configure>', self._fit_width)

        # Activate scroll when mouse enters
        for w in (self._canvas, self._body):
            w.bind('<Enter>', lambda e: self._bind_scroll())
            w.bind('<Leave>', lambda e: self._unbind_scroll())

    def _update_region(self, e=None):
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _fit_width(self, e):
        """Make inner frame always fill canvas width."""
        self._canvas.itemconfig(self._win, width=e.width)

    def _bind_scroll(self):
        self._canvas.bind_all('<MouseWheel>', self._on_wheel)
        self._canvas.bind_all('<Button-4>',
                              lambda e: self._canvas.yview_scroll(-2, 'units'))
        self._canvas.bind_all('<Button-5>',
                              lambda e: self._canvas.yview_scroll(2, 'units'))

    def _unbind_scroll(self):
        try:
            self._canvas.unbind_all('<MouseWheel>')
            self._canvas.unbind_all('<Button-4>')
            self._canvas.unbind_all('<Button-5>')
        except Exception:
            pass

    def _on_wheel(self, event):
        direction = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(direction * 3, 'units')

    # ── Proxy: make ScrollableFrame transparent to child widgets ──
    # All screens do: body = self.scroll; ctk.CTkLabel(body,...).pack()
    # __str__ makes tkinter create children inside self._body instead

    def __str__(self):
        return str(self._body)

    @property
    def tk(self):
        return self._body.tk

    @property
    def children(self):
        return self._body.children

    def winfo_children(self):
        return self._body.winfo_children()

    def nametowidget(self, name):
        return self._body.nametowidget(name)


# ── Card ──────────────────────────────────────────────────────────

class Card(ctk.CTkFrame):
    def __init__(self, parent, accent=None, **kwargs):
        super().__init__(parent,
                         fg_color=C['sf'],
                         border_color=accent or C['br'],
                         border_width=1,
                         corner_radius=8,
                         **kwargs)


# ── SectionHeader ─────────────────────────────────────────────────

class SectionHeader(ctk.CTkFrame):
    def __init__(self, parent, num, title, **kwargs):
        super().__init__(parent, fg_color='transparent', **kwargs)
        ctk.CTkLabel(self, text=f"[{num}]",
                     font=MONO_SM, text_color=C['ac']
                     ).pack(side='left', padx=(0, 6))
        ctk.CTkLabel(self, text=title,
                     font=MONO_SM, text_color=C['mu2']
                     ).pack(side='left')
        ctk.CTkFrame(self, height=1, fg_color=C['br']
                     ).pack(side='left', fill='x', expand=True, padx=(8, 0))


# ── InfoGrid ──────────────────────────────────────────────────────

class InfoGrid(ctk.CTkFrame):
    def __init__(self, parent, items, columns=2, **kwargs):
        super().__init__(parent, fg_color='transparent', **kwargs)
        for i, item in enumerate(items):
            label = item[0]
            value = str(item[1]) if item[1] is not None else '—'
            color = item[2] if len(item) > 2 and item[2] else C['tx']
            col   = i % columns
            row   = i // columns
            cell  = ctk.CTkFrame(self,
                                  fg_color=C['sf'],
                                  border_color=C['br'],
                                  border_width=1,
                                  corner_radius=6)
            cell.grid(row=row, column=col, padx=3, pady=3, sticky='nsew')
            ctk.CTkLabel(cell, text=label,
                         font=('Courier', 7), text_color=C['mu']
                         ).pack(anchor='w', padx=8, pady=(6, 0))
            ctk.CTkLabel(cell, text=value,
                         font=MONO_SM, text_color=color, wraplength=200
                         ).pack(anchor='w', padx=8, pady=(0, 6))
        for c in range(columns):
            self.grid_columnconfigure(c, weight=1)


# ── ResultBox ─────────────────────────────────────────────────────

class ResultBox(ctk.CTkFrame):
    def __init__(self, parent, rtype='ok', title='', body='', **kwargs):
        col = {
            'ok':   C['ok'],
            'warn': C['wn'],
            'info': C['bl'],
            'med':  C['am'],
        }.get(rtype, C['am'])
        super().__init__(parent,
                         fg_color=C['s2'],
                         border_color=col,
                         border_width=1,
                         corner_radius=8,
                         **kwargs)
        ctk.CTkLabel(self, text=title,
                     font=('Courier', 10, 'bold'),
                     text_color=col
                     ).pack(anchor='w', padx=10, pady=(8, 2))
        if body:
            ctk.CTkLabel(self, text=body,
                         font=MONO_SM, text_color=C['mu'],
                         wraplength=640, justify='left'
                         ).pack(anchor='w', padx=10, pady=(0, 8))


# ── Btn ───────────────────────────────────────────────────────────

class Btn(ctk.CTkButton):
    def __init__(self, parent, label, command=None, variant='primary',
                 width=140, **kwargs):
        VARIANTS = {
            'primary': (C['ac'], C['ac']),
            'danger':  (C['wn'], C['wn']),
            'warning': (C['am'], C['am']),
            'success': (C['ok'], C['ok']),
            'ghost':   (C['br'], C['mu']),
            'blue':    (C['bl'], C['bl']),
        }
        border_col, text_col = VARIANTS.get(variant, (C['ac'], C['ac']))
        super().__init__(
            parent,
            text=label,
            font=('Courier', 9),
            fg_color='transparent',
            border_color=border_col,
            border_width=1,
            text_color=text_col,
            hover_color=C['br2'],
            corner_radius=4,
            height=36,
            width=width,
            command=command,
            **kwargs
        )


# ── Badge ─────────────────────────────────────────────────────────

class Badge(ctk.CTkFrame):
    def __init__(self, parent, label, color, **kwargs):
        super().__init__(parent,
                         fg_color=C['s2'],
                         border_color=color,
                         border_width=1,
                         corner_radius=3,
                         **kwargs)
        ctk.CTkLabel(self, text=label,
                     font=('Courier', 7, 'bold'),
                     text_color=color
                     ).pack(padx=6, pady=2)


# ── LiveBadge ─────────────────────────────────────────────────────

class LiveBadge(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color='transparent', **kwargs)
        self._dot = ctk.CTkLabel(self, text='●',
                                  font=('Courier', 10),
                                  text_color=C['ok'])
        self._dot.pack(side='left')
        ctk.CTkLabel(self, text='LIVE',
                     font=('Courier', 8),
                     text_color=C['ok']
                     ).pack(side='left', padx=2)
        self._on = True
        self._pulse()

    def _pulse(self):
        self._on = not self._on
        self._dot.configure(text_color=C['ok'] if self._on else C['mu'])
        self.after(800, self._pulse)


# ── PortBar ───────────────────────────────────────────────────────

class PortBar(ctk.CTkFrame):
    def __init__(self, parent, port, proto, state, process, **kwargs):
        RISK = {'23': 'Telnet', '4444': 'Metasploit', '1337': 'Suspicious'}
        WARN = {'21': 'FTP', '25': 'SMTP', '3306': 'MySQL',
                '27017': 'MongoDB', '6379': 'Redis'}
        SVCS = {
            '20': 'FTP-Data',  '21': 'FTP',       '22': 'SSH',
            '23': 'Telnet',    '25': 'SMTP',       '53': 'DNS',
            '80': 'HTTP',      '443': 'HTTPS',     '3306': 'MySQL',
            '5432': 'PostgreSQL', '6379': 'Redis', '8080': 'HTTP-Alt',
            '27017': 'MongoDB','4444': 'Metasploit⚠','1337': 'Suspicious⚠',
        }
        col = C['wn'] if port in RISK else C['am'] if port in WARN else C['mu']
        super().__init__(parent,
                         fg_color=C['sf'],
                         border_color=col,
                         border_width=1,
                         corner_radius=6,
                         **kwargs)
        top = ctk.CTkFrame(self, fg_color='transparent')
        top.pack(fill='x', padx=10, pady=(8, 2))
        ctk.CTkLabel(top, text=f":{port}",
                     font=('Courier', 12, 'bold'),
                     text_color=col).pack(side='left')
        ctk.CTkLabel(top, text=f"  {SVCS.get(port, 'Unknown')}",
                     font=MONO_SM, text_color=C['tx']).pack(side='left')
        ctk.CTkLabel(top, text=proto,
                     font=('Courier', 8),
                     text_color=C['mu']).pack(side='right')
        ctk.CTkLabel(self,
                     text=f"Process: {process}  State: {state}",
                     font=('Courier', 8), text_color=C['mu']
                     ).pack(anchor='w', padx=10, pady=(0, 6))
