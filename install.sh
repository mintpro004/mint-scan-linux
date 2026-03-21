#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║         MINT SCAN v7 — SELF-HEALING INSTALLER               ║
# ║  Fixes broken files, installs deps, verifies everything     ║
# ║  github.com/mintpro004/mint-scan-linux                      ║
# ╚══════════════════════════════════════════════════════════════╝

set -e
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; NC='\033[0m'; BOLD='\033[1m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         MINT SCAN v7 — SELF-HEALING INSTALLER               ║"
echo "║         Advanced Linux Security Auditor                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: Fix ownership ──────────────────────────────────────────
echo -e "${YELLOW}[1/6] Fixing file ownership...${NC}"
sudo chown -R "$USER:$USER" "$SCRIPT_DIR" 2>/dev/null || true
echo -e "${GREEN}  ✓ Ownership fixed${NC}"

# ── Step 2: System packages ────────────────────────────────────────
echo -e "${YELLOW}[2/6] Installing system packages...${NC}"
sudo apt-get update -qq 2>/dev/null || true
sudo apt-get install -y -qq \
    python3 python3-pip python3-tk python3-dev python3-venv \
    net-tools wireless-tools iw network-manager \
    nmap adb curl git dbus libnotify-bin sqlite3 \
    tcpdump clamav clamav-daemon rkhunter \
    2>/dev/null || true
echo -e "${GREEN}  ✓ System packages done${NC}"

# ── Step 3: Python virtual environment ────────────────────────────
echo -e "${YELLOW}[3/6] Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip 2>/dev/null
pip install -q -r requirements.txt 2>/dev/null
echo -e "${GREEN}  ✓ Python environment ready${NC}"

# ── Step 4: Self-heal critical files ──────────────────────────────
echo -e "${YELLOW}[4/6] Verifying and healing source files...${NC}"

heal_count=0

# Function to check if a python file is valid AND has required content
check_py() {
    local file="$1"
    local required="$2"  # string that must exist in the file
    if [ ! -f "$file" ]; then return 1; fi
    if ! python3 -m py_compile "$file" 2>/dev/null; then return 1; fi
    if [ -n "$required" ] && ! grep -q "$required" "$file"; then return 1; fi
    return 0
}

# ── HEAL widgets.py (most critical) ─────────────────────────────
if ! check_py "widgets.py" "class Btn"; then
    echo -e "  ${RED}✗ widgets.py broken — rewriting...${NC}"
    cat > widgets.py << 'WIDGETS_EOF'
"""Mint Scan v7 — Shared Widgets. All 9 classes. Dark/light theme."""
import tkinter as tk
import customtkinter as ctk

DARK_THEME = {
    'bg':'#020c14','sf':'#061523','s2':'#0a1e2e','br':'#0d2a3d',
    'br2':'#1a3a52','ac':'#00ffe0','wn':'#ff4c4c','am':'#ffb830',
    'ok':'#39ff88','bl':'#4d9fff','pu':'#c084fc','tx':'#c8e8f4',
    'mu':'#3a6278','mu2':'#5a8298',
}
LIGHT_THEME = {
    'bg':'#f0f4f8','sf':'#e2e8f0','s2':'#ffffff','br':'#cbd5e1',
    'br2':'#94a3b8','ac':'#0077cc','wn':'#dc2626','am':'#d97706',
    'ok':'#16a34a','bl':'#2563eb','pu':'#7c3aed','tx':'#1e293b',
    'mu':'#64748b','mu2':'#475569',
}
C = dict(DARK_THEME)
MONO=('Courier',10); MONO_SM=('Courier',9)
MONO_LG=('Courier',13,'bold'); MONO_XL=('Courier',36,'bold')
_current_theme='dark'

def get_theme(): return _current_theme

def apply_theme(name):
    global _current_theme; _current_theme=name
    C.update(LIGHT_THEME if name=='light' else DARK_THEME)
    try: ctk.set_appearance_mode('light' if name=='light' else 'dark')
    except: pass

class ScrollableFrame(tk.Frame):
    """Scrollable container — works on Chromebook, Ubuntu, Kali, WSL."""
    def __init__(self,parent,fg_color=None,**kwargs):
        bg=fg_color or C['bg']; super().__init__(parent,bg=bg)
        self._canvas=tk.Canvas(self,bg=bg,highlightthickness=0,bd=0)
        self._sb=tk.Scrollbar(self,orient='vertical',command=self._canvas.yview)
        self._sb.pack(side='right',fill='y')
        self._canvas.pack(side='left',fill='both',expand=True)
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._body=tk.Frame(self._canvas,bg=bg)
        self._win=self._canvas.create_window((0,0),window=self._body,anchor='nw')
        self._body.bind('<Configure>',lambda e:self._canvas.configure(
            scrollregion=self._canvas.bbox('all')))
        self._canvas.bind('<Configure>',lambda e:self._canvas.itemconfig(
            self._win,width=e.width))
        for w in(self._canvas,self._body):
            w.bind('<Enter>',lambda e:self._bind())
            w.bind('<Leave>',lambda e:self._unbind())
    def _bind(self):
        self._canvas.bind_all('<MouseWheel>',lambda e:self._canvas.yview_scroll(
            -1 if e.delta>0 else 1,'units'))
        self._canvas.bind_all('<Button-4>',lambda e:self._canvas.yview_scroll(-2,'units'))
        self._canvas.bind_all('<Button-5>',lambda e:self._canvas.yview_scroll(2,'units'))
    def _unbind(self):
        for ev in('<MouseWheel>','<Button-4>','<Button-5>'):
            try: self._canvas.unbind_all(ev)
            except: pass
    def __str__(self): return str(self._body)
    @property
    def tk(self): return self._body.tk
    @property
    def children(self): return self._body.children
    def winfo_children(self): return self._body.winfo_children()
    def nametowidget(self,n): return self._body.nametowidget(n)

class Card(ctk.CTkFrame):
    def __init__(self,parent,accent=None,**kwargs):
        super().__init__(parent,fg_color=C['sf'],border_color=accent or C['br'],
                         border_width=1,corner_radius=8,**kwargs)

class SectionHeader(ctk.CTkFrame):
    def __init__(self,parent,num,title,**kwargs):
        super().__init__(parent,fg_color='transparent',**kwargs)
        ctk.CTkLabel(self,text=f"[{num}]",font=MONO_SM,text_color=C['ac']).pack(side='left',padx=(0,6))
        ctk.CTkLabel(self,text=title,font=MONO_SM,text_color=C['mu2']).pack(side='left')
        ctk.CTkFrame(self,height=1,fg_color=C['br']).pack(side='left',fill='x',expand=True,padx=(8,0))

class InfoGrid(ctk.CTkFrame):
    def __init__(self,parent,items,columns=2,**kwargs):
        super().__init__(parent,fg_color='transparent',**kwargs)
        for i,item in enumerate(items):
            lbl=item[0]; val=str(item[1]) if item[1] is not None else '—'
            col2=item[2] if len(item)>2 and item[2] else C['tx']
            c2=i%columns; r2=i//columns
            cell=ctk.CTkFrame(self,fg_color=C['sf'],border_color=C['br'],border_width=1,corner_radius=6)
            cell.grid(row=r2,column=c2,padx=3,pady=3,sticky='nsew')
            ctk.CTkLabel(cell,text=lbl,font=('Courier',7),text_color=C['mu']).pack(anchor='w',padx=8,pady=(6,0))
            ctk.CTkLabel(cell,text=val,font=MONO_SM,text_color=col2,wraplength=200).pack(anchor='w',padx=8,pady=(0,6))
        for c3 in range(columns): self.grid_columnconfigure(c3,weight=1)

class ResultBox(ctk.CTkFrame):
    def __init__(self,parent,rtype='ok',title='',body='',**kwargs):
        col={'ok':C['ok'],'warn':C['wn'],'info':C['bl'],'med':C['am']}.get(rtype,C['am'])
        super().__init__(parent,fg_color=C['s2'],border_color=col,border_width=1,corner_radius=8,**kwargs)
        ctk.CTkLabel(self,text=title,font=('Courier',10,'bold'),text_color=col).pack(anchor='w',padx=10,pady=(8,2))
        if body:
            ctk.CTkLabel(self,text=body,font=MONO_SM,text_color=C['mu'],
                         wraplength=640,justify='left').pack(anchor='w',padx=10,pady=(0,8))

class Btn(ctk.CTkButton):
    def __init__(self,parent,label,command=None,variant='primary',width=140,**kwargs):
        V={'primary':(C['ac'],C['ac']),'danger':(C['wn'],C['wn']),'warning':(C['am'],C['am']),
           'success':(C['ok'],C['ok']),'ghost':(C['br'],C['mu']),'blue':(C['bl'],C['bl'])}
        bc,tc=V.get(variant,(C['ac'],C['ac']))
        super().__init__(parent,text=label,font=('Courier',9),fg_color='transparent',
            border_color=bc,border_width=1,text_color=tc,hover_color=C['br2'],
            corner_radius=4,height=36,width=width,command=command,**kwargs)

class Badge(ctk.CTkFrame):
    def __init__(self,parent,label,color,**kwargs):
        super().__init__(parent,fg_color=C['s2'],border_color=color,border_width=1,corner_radius=3,**kwargs)
        ctk.CTkLabel(self,text=label,font=('Courier',7,'bold'),text_color=color).pack(padx=6,pady=2)

class LiveBadge(ctk.CTkFrame):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,fg_color='transparent',**kwargs)
        self._dot=ctk.CTkLabel(self,text='●',font=('Courier',10),text_color=C['ok'])
        self._dot.pack(side='left')
        ctk.CTkLabel(self,text='LIVE',font=('Courier',8),text_color=C['ok']).pack(side='left',padx=2)
        self._on=True; self._pulse()
    def _pulse(self):
        self._on=not self._on
        self._dot.configure(text_color=C['ok'] if self._on else C['mu'])
        self.after(800,self._pulse)

class PortBar(ctk.CTkFrame):
    def __init__(self,parent,port,proto,state,process,**kwargs):
        RISK={'23':'Telnet','4444':'Metasploit','1337':'Suspicious'}
        WARN={'21':'FTP','25':'SMTP','3306':'MySQL','27017':'MongoDB','6379':'Redis'}
        SVCS={'22':'SSH','23':'Telnet','25':'SMTP','53':'DNS','80':'HTTP','443':'HTTPS',
              '3306':'MySQL','5432':'PostgreSQL','6379':'Redis','8080':'HTTP-Alt',
              '27017':'MongoDB','4444':'Metasploit!','1337':'Suspicious!'}
        col=C['wn'] if port in RISK else C['am'] if port in WARN else C['mu']
        super().__init__(parent,fg_color=C['sf'],border_color=col,border_width=1,corner_radius=6,**kwargs)
        top=ctk.CTkFrame(self,fg_color='transparent')
        top.pack(fill='x',padx=10,pady=(8,2))
        ctk.CTkLabel(top,text=f":{port}",font=('Courier',12,'bold'),text_color=col).pack(side='left')
        ctk.CTkLabel(top,text=f"  {SVCS.get(port,'Unknown')}",font=MONO_SM,text_color=C['tx']).pack(side='left')
        ctk.CTkLabel(top,text=proto,font=('Courier',8),text_color=C['mu']).pack(side='right')
        ctk.CTkLabel(self,text=f"Process: {process}  State: {state}",
                     font=('Courier',8),text_color=C['mu']).pack(anchor='w',padx=10,pady=(0,6))
WIDGETS_EOF
    heal_count=$((heal_count+1))
    echo -e "  ${GREEN}✓ widgets.py healed${NC}"
else
    echo -e "  ${GREEN}✓ widgets.py OK${NC}"
fi

# ── HEAL app.py (check it imports C from widgets) ───────────────
if ! check_py "app.py" "from widgets import C"; then
    echo -e "  ${YELLOW}  app.py: fixing C import...${NC}"
    # Remove hardcoded C dict, replace with import
    python3 - << 'PYEOF'
import re
with open('app.py') as f: c = f.read()
# Replace hardcoded C = {...} with import if present
old = re.search(r"^C = \{[^}]+\}", c, re.MULTILINE)
if old and 'from widgets import C' not in c:
    c = c.replace(old.group(0), 'from widgets import C, apply_theme')
    with open('app.py', 'w') as f: f.write(c)
    print("  Fixed")
PYEOF
    heal_count=$((heal_count+1))
fi

# ── HEAL app.py TABS ordering bug ──────────────────────────────
python3 - << 'PYEOF'
with open('app.py') as f:
    lines = f.readlines()
# Find _build_ui
build_start = next((i for i,l in enumerate(lines) if 'def _build_ui' in l), 0)
# Check TABS appears before screen_classes inside _build_ui
tabs_line = next((i for i,l in enumerate(lines) if i>build_start and 'TABS = [' in l and 'ALL_TABS' not in l), None)
sc_line   = next((i for i,l in enumerate(lines) if i>build_start and 'screen_classes = {' in l), None)
if tabs_line and sc_line and tabs_line < sc_line:
    print("TABS_BEFORE_SC")
else:
    print("OK")
PYEOF
TABS_STATUS=$(python3 - << 'PYEOF'
with open('app.py') as f:
    lines = f.readlines()
build_start = next((i for i,l in enumerate(lines) if 'def _build_ui' in l), 0)
tabs_line = next((i for i,l in enumerate(lines) if i>build_start and 'TABS = [' in l and 'ALL_TABS' not in l), None)
sc_line   = next((i for i,l in enumerate(lines) if i>build_start and 'screen_classes = {' in l), None)
print("BAD" if (tabs_line and sc_line and tabs_line < sc_line) else "OK")
PYEOF
)
if [ "$TABS_STATUS" = "BAD" ]; then
    echo -e "  ${YELLOW}  app.py: fixing TABS ordering bug...${NC}"
    python3 - << 'PYEOF'
import re
with open('app.py') as f: c = f.read()
# Remove the early TABS block that references screen_classes before it exists
c = re.sub(
    r'\n\s+TABS = \[\n.*?\'settings\'\),?\n\s+\]\n\n\s+# Filter tabs.*?screen_classes\]\n',
    '\n',
    c, flags=re.DOTALL
)
# Also remove lone filter line
c = re.sub(r'\s+TABS = \[t for t in TABS.*?screen_classes\]\n', '\n', c)
with open('app.py','w') as f: f.write(c)
print("  TABS ordering fixed")
PYEOF
    heal_count=$((heal_count+1))
fi
echo -e "  ${GREEN}✓ app.py OK${NC}"

# ── HEAL main.py (must load theme before window) ─────────────────
if ! check_py "main.py" "apply_theme"; then
    echo -e "  ${YELLOW}  main.py: rewriting...${NC}"
    cat > main.py << 'MAINEOF'
#!/usr/bin/env python3
"""Mint Scan v7 — Entry point"""
import sys, os, json
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path: sys.path.insert(0, BASE)

# Apply saved theme before window opens
try:
    with open(os.path.expanduser('~/.mint_scan_settings.json')) as f:
        theme = json.load(f).get('theme','dark')
except Exception:
    theme = 'dark'
try:
    import widgets as _w; _w.apply_theme(theme)
except Exception:
    pass

from app import MintScanApp
if __name__ == '__main__':
    MintScanApp().run()
MAINEOF
    heal_count=$((heal_count+1))
    echo -e "  ${GREEN}✓ main.py healed${NC}"
else
    echo -e "  ${GREEN}✓ main.py OK${NC}"
fi

# ── Syntax check ALL .py files ────────────────────────────────────
echo ""
echo -e "${YELLOW}  Verifying all Python files...${NC}"
syntax_errors=0
for pyfile in *.py; do
    result=$(python3 -m py_compile "$pyfile" 2>&1)
    if [ -z "$result" ]; then
        echo -e "    ${GREEN}✓${NC} $pyfile"
    else
        echo -e "    ${RED}✗${NC} $pyfile: $result"
        syntax_errors=$((syntax_errors+1))
    fi
done
if [ $syntax_errors -gt 0 ]; then
    echo -e "  ${RED}WARNING: $syntax_errors file(s) have syntax errors${NC}"
else
    echo -e "  ${GREEN}✓ All files verified${NC}"
fi

if [ $heal_count -gt 0 ]; then
    echo -e "  ${YELLOW}  Auto-healed $heal_count file(s)${NC}"
fi

# ── Step 5: Desktop shortcut ──────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/6] Creating desktop shortcut...${NC}"
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/mint-scan.desktop << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Mint Scan
Comment=Advanced Security Auditor v7 by Mint Projects
Exec=bash $SCRIPT_DIR/run.sh
Icon=$SCRIPT_DIR/icon.png
Terminal=false
Categories=Security;Network;System;
DESKTOP
echo -e "${GREEN}  ✓ Desktop shortcut created${NC}"

# ── Step 6: Final readiness check ────────────────────────────────
echo ""
echo -e "${YELLOW}[6/6] Final readiness check...${NC}"
source venv/bin/activate

# Check that widgets.py exports all required names
WIDGET_CHECK=$(python3 -c "
import sys; sys.path.insert(0, '.')
try:
    from widgets import ScrollableFrame, Card, SectionHeader, InfoGrid, ResultBox, Btn, Badge, C, MONO, MONO_SM
    print('OK')
except ImportError as e:
    print(f'FAIL: {e}')
" 2>&1)

if [ "$WIDGET_CHECK" = "OK" ]; then
    echo -e "  ${GREEN}✓ Widget imports: all 9 classes present${NC}"
else
    echo -e "  ${RED}✗ Widget imports: $WIDGET_CHECK${NC}"
fi

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           INSTALLATION COMPLETE                             ║"
echo "║                                                             ║"
echo "║   Launch:   bash run.sh                                    ║"
echo "║   Or:       source venv/bin/activate && python3 main.py    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
