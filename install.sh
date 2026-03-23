#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║     MINT SCAN v7 — SELF-HEALING INSTALLER                   ║
# ║     github.com/mintpro004/mint-scan-linux                   ║
# ╚══════════════════════════════════════════════════════════════╝
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     MINT SCAN v7 — SELF-HEALING INSTALLER                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}[1/6] Fixing ownership...${NC}"
sudo chown -R "$USER:$USER" "$SCRIPT_DIR" 2>/dev/null || true
echo -e "${GREEN}  ✓ Done${NC}"

echo -e "${YELLOW}[2/6] Installing system packages...${NC}"
sudo apt-get update -qq 2>/dev/null || true
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    python3 python3-pip python3-tk python3-dev python3-venv \
    net-tools wireless-tools iw network-manager \
    nmap adb curl git dbus libnotify-bin sqlite3 \
    tcpdump clamav clamav-daemon rkhunter ufw iptables-persistent \
    auditd tshark 2>/dev/null || true
echo -e "${GREEN}  ✓ Done${NC}"

echo -e "${YELLOW}[3/6] Setting up Python environment...${NC}"
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip 2>/dev/null
pip install -q -r requirements.txt 2>/dev/null
echo -e "${GREEN}  ✓ Done${NC}"

echo -e "${YELLOW}[4/6] Healing critical files...${NC}"

# Detect broken widgets.py (wrong class, missing Btn, old __str__ proxy, _root bug)
NEEDS_HEAL=false
python3 -m py_compile widgets.py 2>/dev/null || NEEDS_HEAL=true
grep -q "class Btn"           widgets.py 2>/dev/null || NEEDS_HEAL=true
grep -q "class Card"          widgets.py 2>/dev/null || NEEDS_HEAL=true
grep -q "def __str__"         widgets.py 2>/dev/null && NEEDS_HEAL=true
grep -q "self\._root ="       widgets.py 2>/dev/null && NEEDS_HEAL=true
grep -q "CTkScrollableFrame"  widgets.py 2>/dev/null || NEEDS_HEAL=true
grep -q "apply_theme(name, accent=None, font_size=10)" widgets.py 2>/dev/null || NEEDS_HEAL=true

if [ "$NEEDS_HEAL" = true ]; then
    echo -e "  ${YELLOW}widgets.py healing...${NC}"
    cat > widgets.py << 'WIDGETS_HEREDOC'
"""
Mint Scan v7 — Shared Widgets
Uses CTkScrollableFrame (simple + reliable) with proper mouse wheel binding.
Dark / light theme support included.
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

C = dict(DARK_THEME)
MONO    = ('Courier', 10)
MONO_SM = ('Courier', 9)
MONO_LG = ('Courier', 13, 'bold')
MONO_XL = ('Courier', 36, 'bold')
_current_theme = 'dark'


def get_theme():
    return _current_theme


def apply_theme(name, accent=None, font_size=10):
    global _current_theme, MONO, MONO_SM, MONO_LG, MONO_XL
    _current_theme = name
    
    # Update color dictionary
    base_colors = LIGHT_THEME if name == 'light' else DARK_THEME
    C.update(base_colors)
    if accent:
        C['ac'] = accent
        
    # Update font constants
    fs = font_size
    MONO    = ('Courier', fs)
    MONO_SM = ('Courier', max(7, fs - 1))
    MONO_LG = ('Courier', fs + 3, 'bold')
    MONO_XL = ('Courier', fs + 26, 'bold')
    
    try:
        ctk.set_appearance_mode('light' if name == 'light' else 'dark')
    except Exception:
        pass


def load_theme_settings():
    """Helper to load and apply all settings at once"""
    import json, os
    settings_file = os.path.expanduser('~/.mint_scan_settings.json')
    try:
        if os.path.exists(settings_file):
            with open(settings_file) as f:
                s = json.load(f)
                theme = s.get('theme', 'dark')
                accent = s.get('accent_color', None)
                font_size = s.get('font_size', 10)
                scale = s.get('ui_scale', 1.0)
                apply_theme(theme, accent, font_size)
                return scale
    except Exception:
        pass
    apply_theme('dark')
    return 1.0


# ── ScrollableFrame ───────────────────────────────────────────────
# Uses CTkScrollableFrame — no proxy tricks, no __str__ override.
# Mouse wheel is bound globally on <Enter> so touchpad works too.

class ScrollableFrame(ctk.CTkScrollableFrame):
    """
    Scrollable container that works on Chromebook, Ubuntu, Kali, WSL.
    Mouse wheel and touchpad two-finger scroll both work.
    """
    def __init__(self, parent, **kwargs):
        fg = kwargs.pop('fg_color', C['bg'])
        sbc = kwargs.pop('scrollbar_button_color', C['br2'])
        sbhc = kwargs.pop('scrollbar_button_hover_color', C['ac'])
        cr = kwargs.pop('corner_radius', 0)
        super().__init__(
            master=parent,
            fg_color=fg,
            scrollbar_button_color=sbc,
            scrollbar_button_hover_color=sbhc,
            corner_radius=cr,
            **kwargs
        )
        # Bind mouse wheel when mouse enters this frame
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _on_enter(self, event=None):
        # Bind to root window so scroll works anywhere inside
        self._toplevel = self.winfo_toplevel()
        self._toplevel.bind_all('<MouseWheel>', self._on_mousewheel, add='+')
        self._toplevel.bind_all('<Button-4>',   self._scroll_up,    add='+')
        self._toplevel.bind_all('<Button-5>',   self._scroll_down,  add='+')

    def _on_leave(self, event=None):
        try:
            self._toplevel.unbind_all('<MouseWheel>')
            self._toplevel.unbind_all('<Button-4>')
            self._toplevel.unbind_all('<Button-5>')
        except Exception:
            pass

    def _on_mousewheel(self, event):
        # Windows/macOS: event.delta; Linux: Button-4/5
        try:
            if event.delta:
                self._parent_canvas.yview_scroll(
                    int(-1 * (event.delta / 120)), 'units')
        except Exception:
            pass

    def _scroll_up(self, event):
        try:
            self._parent_canvas.yview_scroll(-2, 'units')
        except Exception:
            pass

    def _scroll_down(self, event):
        try:
            self._parent_canvas.yview_scroll(2, 'units')
        except Exception:
            pass


# ── Card ──────────────────────────────────────────────────────────

class Card(ctk.CTkFrame):
    def __init__(self, parent, accent=None, **kwargs):
        fg = kwargs.pop('fg_color', C['sf'])
        bc = kwargs.pop('border_color', accent or C['br'])
        bw = kwargs.pop('border_width', 1)
        cr = kwargs.pop('corner_radius', 8)
        super().__init__(
            parent,
            fg_color=fg,
            border_color=bc,
            border_width=bw,
            corner_radius=cr,
            **kwargs
        )


# ── SectionHeader ─────────────────────────────────────────────────

class SectionHeader(ctk.CTkFrame):
    def __init__(self, parent, num, title, **kwargs):
        fg = kwargs.pop('fg_color', 'transparent')
        super().__init__(parent, fg_color=fg, **kwargs)
        ctk.CTkLabel(
            self, text=f"[{num}]",
            font=MONO_SM, text_color=C['ac']
        ).pack(side='left', padx=(0, 6))
        ctk.CTkLabel(
            self, text=title,
            font=MONO_SM, text_color=C['mu2']
        ).pack(side='left')
        ctk.CTkFrame(
            self, height=1, fg_color=C['br']
        ).pack(side='left', fill='x', expand=True, padx=(8, 0))


# ── InfoGrid ──────────────────────────────────────────────────────

class InfoGrid(ctk.CTkFrame):
    def __init__(self, parent, items, columns=2, **kwargs):
        fg = kwargs.pop('fg_color', 'transparent')
        super().__init__(parent, fg_color=fg, **kwargs)
        for i, item in enumerate(items):
            label = item[0]
            value = str(item[1]) if item[1] is not None else '—'
            color = item[2] if len(item) > 2 and item[2] else C['tx']
            col   = i % columns
            row   = i // columns
            cell  = ctk.CTkFrame(
                self,
                fg_color=C['sf'],
                border_color=C['br'],
                border_width=1,
                corner_radius=6
            )
            cell.grid(row=row, column=col, padx=3, pady=3, sticky='nsew')
            ctk.CTkLabel(
                cell, text=label,
                font=('Courier', 7), text_color=C['mu']
            ).pack(anchor='w', padx=8, pady=(6, 0))
            ctk.CTkLabel(
                cell, text=value,
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
        fg = kwargs.pop('fg_color', C['s2'])
        bc = kwargs.pop('border_color', col)
        bw = kwargs.pop('border_width', 1)
        cr = kwargs.pop('corner_radius', 8)
        super().__init__(
            parent,
            fg_color=fg,
            border_color=bc,
            border_width=bw,
            corner_radius=cr,
            **kwargs
        )
        ctk.CTkLabel(
            self, text=title,
            font=('Courier', 10, 'bold'),
            text_color=col
        ).pack(anchor='w', padx=10, pady=(8, 2))
        if body:
            ctk.CTkLabel(
                self, text=body,
                font=MONO_SM, text_color=C['mu'],
                wraplength=640, justify='left'
            ).pack(anchor='w', padx=10, pady=(0, 8))


# ── Btn ───────────────────────────────────────────────────────────

class Btn(ctk.CTkButton):
    def __init__(self, parent, label, command=None,
                 variant='primary', width=140, **kwargs):
        VARIANTS = {
            'primary': (C['ac'], C['ac']),
            'danger':  (C['wn'], C['wn']),
            'warning': (C['am'], C['am']),
            'success': (C['ok'], C['ok']),
            'ghost':   (C['br'], C['mu']),
            'blue':    (C['bl'], C['bl']),
        }
        border_col, text_col = VARIANTS.get(variant, (C['ac'], C['ac']))
        
        fg = kwargs.pop('fg_color', 'transparent')
        bc = kwargs.pop('border_color', border_col)
        bw = kwargs.pop('border_width', 1)
        tc = kwargs.pop('text_color', text_col)
        hc = kwargs.pop('hover_color', C['br2'])
        cr = kwargs.pop('corner_radius', 4)
        ht = kwargs.pop('height', 36)
        wd = kwargs.pop('width', width)
        
        super().__init__(
            parent,
            text=label,
            font=('Courier', 9),
            fg_color=fg,
            border_color=bc,
            border_width=bw,
            text_color=tc,
            hover_color=hc,
            corner_radius=cr,
            height=ht,
            width=wd,
            command=command,
            **kwargs
        )


# ── Badge ─────────────────────────────────────────────────────────

class Badge(ctk.CTkFrame):
    def __init__(self, parent, label, color, **kwargs):
        fg = kwargs.pop('fg_color', C['s2'])
        bc = kwargs.pop('border_color', color)
        bw = kwargs.pop('border_width', 1)
        cr = kwargs.pop('corner_radius', 3)
        super().__init__(
            parent,
            fg_color=fg,
            border_color=bc,
            border_width=bw,
            corner_radius=cr,
            **kwargs
        )
        ctk.CTkLabel(
            self, text=label,
            font=('Courier', 7, 'bold'),
            text_color=color
        ).pack(padx=6, pady=2)


# ── LiveBadge ─────────────────────────────────────────────────────

class LiveBadge(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        fg = kwargs.pop('fg_color', 'transparent')
        super().__init__(parent, fg_color=fg, **kwargs)
        self._dot = ctk.CTkLabel(
            self, text='●',
            font=('Courier', 10),
            text_color=C['ok']
        )
        self._dot.pack(side='left')
        ctk.CTkLabel(
            self, text='LIVE',
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
            '20': 'FTP-Data', '21': 'FTP',      '22': 'SSH',
            '23': 'Telnet',   '25': 'SMTP',     '53': 'DNS',
            '80': 'HTTP',     '443': 'HTTPS',   '3306': 'MySQL',
            '5432': 'PgSQL',  '6379': 'Redis',  '8080': 'HTTP-Alt',
            '27017': 'MongoDB','4444': 'Meterp!','1337': 'Suspic!',
        }
        col = C['wn'] if port in RISK else C['am'] if port in WARN else C['mu']
        
        fg = kwargs.pop('fg_color', C['sf'])
        bc = kwargs.pop('border_color', col)
        bw = kwargs.pop('border_width', 1)
        cr = kwargs.pop('corner_radius', 6)
        
        super().__init__(
            parent,
            fg_color=fg,
            border_color=bc,
            border_width=bw,
            corner_radius=cr,
            **kwargs
        )
        top = ctk.CTkFrame(self, fg_color='transparent')
        top.pack(fill='x', padx=10, pady=(8, 2))
        ctk.CTkLabel(
            top, text=f":{port}",
            font=('Courier', 12, 'bold'),
            text_color=col
        ).pack(side='left')
        ctk.CTkLabel(
            top, text=f"  {SVCS.get(port, 'Unknown')}",
            font=MONO_SM, text_color=C['tx']
        ).pack(side='left')
        ctk.CTkLabel(
            top, text=proto,
            font=('Courier', 8),
            text_color=C['mu']
        ).pack(side='right')
        ctk.CTkLabel(
            self,
            text=f"Process: {process}  State: {state}",
            font=('Courier', 8),
            text_color=C['mu']
        ).pack(anchor='w', padx=10, pady=(0, 6))
WIDGETS_HEREDOC
    echo -e "  \033[0;32m✓ widgets.py healed\033[0m"
else
    echo -e "  \033[0;32m✓ widgets.py OK\033[0m"
fi

# Heal main.py if missing theme support
grep -q "load_theme_settings" main.py 2>/dev/null || {
    echo -e "  ${YELLOW}main.py healing...${NC}"
    cat > main.py << 'MAINEOF'
#!/usr/bin/env python3
"""
Mint Scan v7 — Entry Point
Loads saved theme before window opens, then launches app.
"""
import sys, os

# Add this directory to path first
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# Apply saved theme BEFORE importing ctk or creating window
def _load_and_apply_theme():
    import widgets as _w
    scale = _w.load_theme_settings()
    return scale

UI_SCALE = _load_and_apply_theme()

import customtkinter as ctk
try:
    ctk.set_widget_scaling(UI_SCALE)
except Exception:
    pass

from app import MintScanApp

if __name__ == '__main__':
    app = MintScanApp()
    app.run()
MAINEOF
    echo -e "  ${GREEN}✓ main.py healed${NC}"
}

echo -e "${YELLOW}[5/6] Verifying Python files...${NC}"
errors=0
for pyfile in *.py; do
    result=$(python3 -m py_compile "$pyfile" 2>&1)
    if [ -z "$result" ]; then
        echo -e "    ${GREEN}✓${NC} $pyfile"
    else
        echo -e "    ${RED}✗${NC} $pyfile — $result"
        errors=$((errors+1))
    fi
done
[ $errors -gt 0 ] && echo -e "  ${RED}WARNING: $errors file(s) have errors${NC}"

WIDGET_OK=$(python3 -c "
import sys; sys.path.insert(0,'.')
try:
    from widgets import ScrollableFrame, Card, Btn, SectionHeader, InfoGrid, ResultBox
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
" 2>&1)
[ "$WIDGET_OK" = "OK" ] \
    && echo -e "  ${GREEN}✓ All widget classes verified${NC}" \
    || echo -e "  ${RED}✗ $WIDGET_OK${NC}"

echo -e "${YELLOW}[6/6] Creating desktop shortcut...${NC}"
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/mint-scan.desktop << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Mint Scan
Comment=Advanced Security Auditor v7 — Mint Projects
Exec=bash $SCRIPT_DIR/run.sh
Icon=$SCRIPT_DIR/icon.png
Terminal=false
Categories=Security;Network;System;
DESKTOP
echo -e "${GREEN}  ✓ Done${NC}"

echo ""
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   INSTALLATION COMPLETE                                     ║"
echo "║   Run:  bash run.sh                                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
