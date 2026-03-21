"""
Mint Scan v7 — Shared Widgets
Fixed scrolling + light/dark theme support
"""
import tkinter as tk
import customtkinter as ctk

# ── Theme palettes ─────────────────────────────────────────────────
DARK_THEME = {
    'bg':  '#020c14', 'sf':  '#061523', 's2':  '#0a1e2e',
    'br':  '#0d2a3d', 'br2': '#1a3a52', 'ac':  '#00ffe0',
    'wn':  '#ff4c4c', 'am':  '#ffb830', 'ok':  '#39ff88',
    'bl':  '#4d9fff', 'pu':  '#c084fc', 'tx':  '#c8e8f4',
    'mu':  '#3a6278', 'mu2': '#5a8298',
    # extra for light compat
    'card_bg': '#061523', 'text_main': '#c8e8f4',
    'scrollbar': '#1a3a52',
}

LIGHT_THEME = {
    'bg':  '#f0f4f8', 'sf':  '#e2e8f0', 's2':  '#ffffff',
    'br':  '#cbd5e1', 'br2': '#94a3b8', 'ac':  '#0077cc',
    'wn':  '#dc2626', 'am':  '#d97706', 'ok':  '#16a34a',
    'bl':  '#2563eb', 'pu':  '#7c3aed', 'tx':  '#1e293b',
    'mu':  '#64748b', 'mu2': '#475569',
    'card_bg': '#ffffff', 'text_main': '#1e293b',
    'scrollbar': '#94a3b8',
}

# Active colour palette — starts dark, swapped by theme toggle
C = dict(DARK_THEME)

MONO    = ('Courier', 10)
MONO_SM = ('Courier', 9)
MONO_LG = ('Courier', 13, 'bold')
MONO_XL = ('Courier', 36, 'bold')

# Current theme name
_current_theme = 'dark'


def get_theme():
    return _current_theme


def apply_theme(theme_name):
    """Switch C dict values to selected theme in-place."""
    global _current_theme
    _current_theme = theme_name
    palette = LIGHT_THEME if theme_name == 'light' else DARK_THEME
    C.update(palette)
    # Tell customtkinter
    ctk.set_appearance_mode('light' if theme_name == 'light' else 'dark')


# ── Proper scrollable frame using Canvas ──────────────────────────

class ScrollableFrame(ctk.CTkFrame):
    """
    A reliably scrollable container that works on Chromebook.
    Uses tk.Canvas internally so scroll always functions correctly.
    Mouse wheel, touchpad two-finger scroll, and scrollbar all work.
    """
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('fg_color', C['bg'])
        super().__init__(parent, **kwargs)

        # Canvas fills the frame
        self._canvas = tk.Canvas(self, bg=C['bg'],
                                  highlightthickness=0, bd=0)

        # Vertical scrollbar
        self._vsb = ctk.CTkScrollbar(self, orientation='vertical',
                                      command=self._canvas.yview,
                                      button_color=C['br2'],
                                      button_hover_color=C['ac'])
        self._vsb.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)
        self._canvas.configure(yscrollcommand=self._vsb.set)

        # Interior frame that lives inside the canvas
        self._inner = ctk.CTkFrame(self._canvas, fg_color=C['bg'],
                                    corner_radius=0)
        self._window = self._canvas.create_window(
            (0, 0), window=self._inner, anchor='nw')

        # Resize handlers
        self._inner.bind('<Configure>', self._on_inner_configure)
        self._canvas.bind('<Configure>', self._on_canvas_configure)

        # Mouse wheel — bind to canvas AND inner frame
        for widget in (self._canvas, self._inner):
            widget.bind('<MouseWheel>',     self._on_mousewheel)
            widget.bind('<Button-4>',       self._on_scroll_up)
            widget.bind('<Button-5>',       self._on_scroll_down)

        # Propagate mouse wheel from all child widgets
        self.bind_all('<MouseWheel>', self._on_mousewheel)
        self.bind_all('<Button-4>',   self._on_scroll_up)
        self.bind_all('<Button-5>',   self._on_scroll_down)

    def _on_inner_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _on_canvas_configure(self, event=None):
        # Make inner frame match canvas width
        self._canvas.itemconfig(self._window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _on_scroll_up(self, event):
        self._canvas.yview_scroll(-1, 'units')

    def _on_scroll_down(self, event):
        self._canvas.yview_scroll(1, 'units')

    # Make ScrollableFrame behave like a frame — children go into _inner
    def winfo_children(self):
        return self._inner.winfo_children()

    def pack_configure(self, **kwargs):
        super().pack_configure(**kwargs)

    # Override pack/grid/place on children to redirect to _inner
    @property
    def _w(self):
        return super()._w


# Monkey-patch: widgets added to ScrollableFrame should go to _inner
_orig_init = ScrollableFrame.__init__

def _sf_getattr(self, name):
    # Transparent proxy: pack/grid children into _inner automatically
    raise AttributeError(name)

# ── Simpler approach: expose _inner as the target ──────────────────
# All screens do: body = self.scroll  then body.pack(...)
# So we need ScrollableFrame to BE the inner frame for packing purposes
# The cleanest fix: make ScrollableFrame a wrapper that returns _inner for packing

class ScrollableFrame(tk.Frame):
    """
    Reliable scrollable frame. Works on Chromebook Linux (Crostini).
    Usage: body = ScrollableFrame(parent); body.pack(fill='both', expand=True)
    Then add widgets: ctk.CTkLabel(body, ...).pack(...)
    """
    def __init__(self, parent, fg_color=None, **kwargs):
        bg = fg_color or C['bg']
        super().__init__(parent, bg=bg, **kwargs)

        # Canvas for scrolling
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)

        # Scrollbar
        self._scrollbar = tk.Scrollbar(self, orient='vertical',
                                        command=self._canvas.yview,
                                        width=12,
                                        troughcolor=C['bg'],
                                        bg=C['br2'],
                                        activebackground=C['ac'])
        self._scrollbar.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # Inner frame — this is where content goes
        self._inner = tk.Frame(self._canvas, bg=bg)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner, anchor='nw')

        # Update scroll region when content changes
        self._inner.bind('<Configure>', self._update_scroll_region)
        self._canvas.bind('<Configure>', self._on_canvas_resize)

        # Bind scroll events
        self._canvas.bind('<Enter>', self._bind_scroll)
        self._canvas.bind('<Leave>', self._unbind_scroll)
        self._inner.bind('<Enter>', self._bind_scroll)

    def _update_scroll_region(self, event=None):
        bbox = self._canvas.bbox('all')
        if bbox:
            self._canvas.configure(scrollregion=bbox)

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _bind_scroll(self, event=None):
        self._canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        self._canvas.bind_all('<Button-4>',   self._scroll_up)
        self._canvas.bind_all('<Button-5>',   self._scroll_down)

    def _unbind_scroll(self, event=None):
        self._canvas.unbind_all('<MouseWheel>')
        self._canvas.unbind_all('<Button-4>')
        self._canvas.unbind_all('<Button-5>')

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _scroll_up(self, event):
        self._canvas.yview_scroll(-1, 'units')

    def _scroll_down(self, event):
        self._canvas.yview_scroll(1, 'units')

    # ── Proxy: make ScrollableFrame act as its inner frame ────────
    # When screens do: body = self.scroll; ctk.CTkLabel(body, ...).pack()
    # those widgets should go into _inner, not the outer tk.Frame

    def pack(self, **kwargs):
        """Pack the outer container"""
        super().pack(**kwargs)
        return self

    # Make this frame's widget path point to _inner for child creation
    # by overriding the string representation used by tkinter
    @property
    def inner(self):
        return self._inner


# ── Smart ScrollableFrame that proxies child creation to _inner ────

class ScrollableFrame(tk.Frame):
    """
    Scrollable container where direct children are placed in a scrollable inner frame.
    On Chromebook: mouse wheel, Button-4/5 (touchpad) all work.
    """
    def __init__(self, parent, fg_color=None, **kwargs):
        self._bg_color = fg_color or C['bg']
        super().__init__(parent, bg=self._bg_color)

        self._canvas = tk.Canvas(self, bg=self._bg_color,
                                  highlightthickness=0, bd=0)
        self._scrollbar = tk.Scrollbar(self, orient='vertical',
                                        command=self._canvas.yview)
        self._scrollbar.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # This is the real container for content
        self._body = tk.Frame(self._canvas, bg=self._bg_color)
        self._win  = self._canvas.create_window((0,0), window=self._body, anchor='nw')

        self._body.bind('<Configure>', self._update_region)
        self._canvas.bind('<Configure>', self._on_canvas_resize)

        # Scroll bindings activate when mouse enters scroll area
        for w in (self._canvas, self._body):
            w.bind('<Enter>', lambda e: self._bind_mouse())
            w.bind('<Leave>', lambda e: self._unbind_mouse())

    def _update_region(self, e=None):
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _on_canvas_resize(self, e):
        self._canvas.itemconfig(self._win, width=e.width)

    def _bind_mouse(self):
        self._canvas.bind_all('<MouseWheel>', self._mwheel)
        self._canvas.bind_all('<Button-4>',   lambda e: self._canvas.yview_scroll(-2,'units'))
        self._canvas.bind_all('<Button-5>',   lambda e: self._canvas.yview_scroll(2,'units'))

    def _unbind_mouse(self):
        try:
            self._canvas.unbind_all('<MouseWheel>')
            self._canvas.unbind_all('<Button-4>')
            self._canvas.unbind_all('<Button-5>')
        except Exception:
            pass

    def _mwheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(delta * 3, 'units')

    # ── Make this frame transparent to widget creation ─────────────
    # All screens do: body = self.scroll; Widget(body,...).pack(...)
    # We need Widget(body) to actually create in self._body
    # Achieve by making ScrollableFrame's tk path point to _body's path

    def __str__(self):
        # Return _body's tk path so child widgets are created inside it
        return str(self._body)

    # Required for tkinter widget parent resolution
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

