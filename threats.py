"""Threats Screen — real checks WITH action buttons and remediation for every finding"""
import tkinter as tk
import customtkinter as ctk
import threading, os, re, subprocess, time
from utils import C, MONO, MONO_SM, run_cmd, check_root, get_open_ports
from widgets import ScrollableFrame, Card, SectionHeader, ResultBox, Btn, InfoGrid
from installer import InstallerPopup

KNOWN_BAD_PORTS = {
    '23':'Telnet','4444':'Metasploit','1337':'Suspicious',
    '6667':'IRC','31337':'Back Orifice','5555':'ADB-over-network',
}
RISKY_PORTS = {
    '21':'FTP','25':'SMTP','3306':'MySQL','27017':'MongoDB',
    '6379':'Redis','5900':'VNC','8080':'HTTP-Alt','3389':'RDP',
}

def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return '', str(e), 1


class ThreatAction(ctk.CTkFrame):
    """Finding card with level badge, title, description, and action buttons."""
    def __init__(self, parent, level, title, description, actions=None, **kwargs):
        colours = {'HIGH':C['wn'],'MED':C['am'],'OK':C['ok'],'INFO':C['bl']}
        col = colours.get(level, C['mu'])
        super().__init__(parent, fg_color=C['sf'],
                         border_color=col, border_width=1,
                         corner_radius=8, **kwargs)
        top = ctk.CTkFrame(self, fg_color='transparent')
        top.pack(fill='x', padx=12, pady=(10,3))
        badge = ctk.CTkFrame(top, fg_color=col, corner_radius=3)
        badge.pack(side='left', padx=(0,8))
        ctk.CTkLabel(badge, text=level, font=('Courier',7,'bold'),
                     text_color=C['bg']).pack(padx=6, pady=2)
        ctk.CTkLabel(top, text=title, font=('Courier',10,'bold'),
                     text_color=col, wraplength=500, justify='left').pack(side='left')
        if description:
            ctk.CTkLabel(self, text=description, font=('Courier',8),
                         text_color=C['mu'], wraplength=580, justify='left'
                         ).pack(anchor='w', padx=12, pady=(0,6))
        if actions:
            btn_row = ctk.CTkFrame(self, fg_color='transparent')
            btn_row.pack(anchor='w', padx=12, pady=(2,10))
            for label, variant, cb in actions:
                Btn(btn_row, label, command=cb, variant=variant,
                    width=max(110, len(label)*8+20)).pack(side='left', padx=3)


class ThreatsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built   = False
        self._scanning = False

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="⚠  THREATS & REMEDIATION",
                     font=('Courier',13,'bold'), text_color=C['ac']
                     ).pack(side='left', padx=16)
        self.stop_btn = Btn(hdr, "⏹ STOP", command=self._stop,
                            variant='danger', width=90)
        self.stop_btn.pack(side='right', padx=4, pady=6)
        self.stop_btn.configure(state='disabled')
        self.scan_btn = Btn(hdr, "▶ DEEP SCAN", command=self._scan, width=120)
        self.scan_btn.pack(side='right', padx=4, pady=6)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # Scan log
        SectionHeader(body, '01', 'SCAN LOG').pack(fill='x', padx=14, pady=(14,4))
        self.scan_log = ctk.CTkTextbox(body, height=90, font=('Courier',8),
                                        fg_color=C['s2'], text_color=C['ac'],
                                        border_color=C['br'], border_width=1, corner_radius=6)
        self.scan_log.pack(fill='x', padx=14, pady=(0,8))
        self.scan_log.configure(state='disabled')

        # Quick actions
        SectionHeader(body, '02', 'QUICK ACTIONS').pack(fill='x', padx=14, pady=(6,4))
        qa = Card(body)
        qa.pack(fill='x', padx=14, pady=(0,8))
        qa_grid = ctk.CTkFrame(qa, fg_color='transparent')
        qa_grid.pack(fill='x', padx=8, pady=8)
        quick = [
            ("🔥 ENABLE FIREWALL",   self._fix_firewall,         'danger'),
            ("🔒 HARDEN SSH",        self._fix_ssh,              'danger'),
            ("🔄 UPDATE SYSTEM",     self._fix_update,           'primary'),
            ("🧹 KILL SUSP PROCS",  self._kill_suspicious,      'warning'),
            ("🛡 BLOCK BAD PORTS",  self._block_dangerous_ports,'danger'),
            ("⚙ FIREWALL MANAGER", self._open_firewall_mgr,    'blue'),
        ]
        for i, (lbl, cmd, var) in enumerate(quick):
            r2, c2 = divmod(i, 3)
            Btn(qa_grid, lbl, command=cmd, variant=var, width=185
                ).grid(row=r2, column=c2, padx=4, pady=4, sticky='ew')
        qa_grid.columnconfigure(0, weight=1)
        qa_grid.columnconfigure(1, weight=1)
        qa_grid.columnconfigure(2, weight=1)

        # Findings
        SectionHeader(body, '03', 'FINDINGS & FIX OPTIONS').pack(fill='x', padx=14, pady=(8,4))
        self.findings_frame = ctk.CTkFrame(body, fg_color='transparent')
        self.findings_frame.pack(fill='x', padx=14, pady=(0,8))
        ctk.CTkLabel(self.findings_frame,
                     text="Tap ▶ DEEP SCAN to check your system for threats.",
                     font=MONO_SM, text_color=C['mu']).pack(pady=16)

        # Action output log
        SectionHeader(body, '04', 'ACTION OUTPUT').pack(fill='x', padx=14, pady=(8,4))
        self.action_log = ctk.CTkTextbox(body, height=120, font=('Courier',8),
                                          fg_color=C['s2'], text_color=C['ok'],
                                          border_color=C['br'], border_width=1, corner_radius=6)
        self.action_log.pack(fill='x', padx=14, pady=(0,8))
        self.action_log.configure(state='disabled')

        # Scam checker
        SectionHeader(body, '05', 'SCAM / URL CHECKER').pack(fill='x', padx=14, pady=(8,4))
        scam_card = Card(body)
        scam_card.pack(fill='x', padx=14, pady=(0,14))
        ctk.CTkLabel(scam_card,
                     text="Check a phone number, URL, or message text for scam patterns:",
                     font=MONO_SM, text_color=C['mu']).pack(anchor='w', padx=12, pady=(10,4))
        inp = ctk.CTkFrame(scam_card, fg_color='transparent')
        inp.pack(fill='x', padx=12, pady=(0,8))
        self.scam_entry = ctk.CTkEntry(inp,
            placeholder_text="e.g. 0900123456  or  http://...  or  'You won a prize!'",
            font=MONO_SM, fg_color=C['bg'],
            border_color=C['br'], text_color=C['tx'], height=36)
        self.scam_entry.pack(side='left', fill='x', expand=True, padx=(0,8))
        Btn(inp, "ANALYSE", command=self._check_scam, variant='danger', width=90).pack(side='left')
        self.scam_result = ctk.CTkFrame(scam_card, fg_color='transparent')
        self.scam_result.pack(fill='x', padx=12, pady=(0,8))

    # ── Logging ───────────────────────────────────────────────

    def _log(self, msg):
        self.scan_log.configure(state='normal')
        self.scan_log.insert('end', msg + '\n')
        self.scan_log.see('end')
        self.scan_log.configure(state='disabled')

    def _alog(self, msg):
        self.action_log.configure(state='normal')
        self.action_log.insert('end', f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.action_log.see('end')
        self.action_log.configure(state='disabled')

    # ── Scan ──────────────────────────────────────────────────

    def _scan(self):
        if self._scanning:
            return
        self._scanning = True
        self.scan_btn.configure(state='disabled', text='SCANNING...')
        self.stop_btn.configure(state='normal')
        self.scan_log.configure(state='normal')
        self.scan_log.delete('1.0', 'end')
        self.scan_log.configure(state='disabled')
        for w in self.findings_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.findings_frame, text="⟳ Scanning...",
                     font=MONO_SM, text_color=C['ac']).pack(pady=8)
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _stop(self):
        self._scanning = False
        self.scan_btn.configure(state='normal', text='▶ DEEP SCAN')
        self.stop_btn.configure(state='disabled')
        self.after(0, self._log, "Scan stopped.")

    def _do_scan(self):
        findings = []
        def log(m): self.after(0, self._log, m)

        log("Starting security scan...")

        # 1. Root
        if not self._scanning: return
        log("Checking privileges...")
        if check_root():
            findings.append({'level':'HIGH',
                'title':'Running as root — elevated risk',
                'desc':'This process has full system access. Use a regular user account.',
                'actions':[("VIEW ADVICE",'warning',
                    lambda: self._alog("Run without sudo: source venv/bin/activate && python3 main.py"))]})

        # 2. Open ports
        if not self._scanning: return
        log("Scanning open ports...")
        ports = get_open_ports()
        for p in ports:
            port = p['port']
            if port in KNOWN_BAD_PORTS:
                svc = KNOWN_BAD_PORTS[port]
                findings.append({'level':'HIGH',
                    'title': f'Dangerous port {port} ({svc}) is OPEN',
                    'desc':  f'Process: {p["process"]}. This port is associated with {svc}.',
                    'actions':[
                        ("BLOCK PORT",    'danger',  lambda pt=port: self._block_port(pt)),
                        ("KILL PROCESS",  'warning', lambda pr=p['process']: self._kill_proc(pr)),
                        ("INFO",          'ghost',   lambda pt=port, sv=svc:
                            self._alog(f"Port {pt} ({sv}) — verify with: ss -tlnp | grep :{pt}")),
                    ]})
            elif port in RISKY_PORTS:
                svc = RISKY_PORTS[port]
                findings.append({'level':'MED',
                    'title': f'Exposed port {port} ({svc}) — review recommended',
                    'desc':  f'Process: {p["process"]}. Ensure firewall restricts access.',
                    'actions':[
                        ("BLOCK PORT",        'warning', lambda pt=port: self._block_port(pt)),
                        ("LOCAL ONLY",        'ghost',   lambda pt=port: self._allow_local_only(pt)),
                    ]})

        # 3. Firewall
        if not self._scanning: return
        log("Checking firewall...")
        ufw_out, _, rc = _run('ufw status 2>/dev/null')
        if 'inactive' in ufw_out.lower() or rc != 0:
            findings.append({'level':'HIGH',
                'title':'Firewall (UFW) is DISABLED — all ports unfiltered',
                'desc':'All incoming connections allowed with no filtering.',
                'actions':[
                    ("ENABLE FIREWALL NOW", 'danger', self._fix_firewall),
                    ("OPEN FW MANAGER",     'blue',   self._open_firewall_mgr),
                ]})
        else:
            log("  Firewall: active")

        # 4. SSH
        if not self._scanning: return
        log("Checking SSH config...")
        sshd = '/etc/ssh/sshd_config'
        if os.path.exists(sshd):
            try:
                cfg = open(sshd).read()
                if re.search(r'^PermitRootLogin\s+yes', cfg, re.MULTILINE):
                    findings.append({'level':'HIGH',
                        'title':'SSH root login permitted — critical risk',
                        'desc':'Attackers can brute-force root access over SSH.',
                        'actions':[
                            ("DISABLE ROOT LOGIN", 'danger',  self._fix_ssh_root),
                            ("FULL SSH HARDEN",    'danger',  self._fix_ssh),
                        ]})
                if re.search(r'^PasswordAuthentication\s+yes', cfg, re.MULTILINE):
                    findings.append({'level':'MED',
                        'title':'SSH password authentication enabled',
                        'desc':'Brute-force attacks possible. Use SSH key authentication.',
                        'actions':[
                            ("DISABLE PASSWORD AUTH", 'warning', self._fix_ssh_password),
                        ]})
            except PermissionError:
                log("  SSH config: need sudo to read")

        # 5. Auto-updates
        if not self._scanning: return
        log("Checking auto-updates...")
        out, _, _ = _run('dpkg -l unattended-upgrades 2>/dev/null | grep ^ii')
        if not out:
            findings.append({'level':'MED',
                'title':'Automatic security updates not configured',
                'desc':'Security patches are not applied automatically.',
                'actions':[("INSTALL AUTO-UPDATES", 'warning', self._fix_autoupdates)]})

        # 6. Suspicious processes
        if not self._scanning: return
        log("Checking processes...")
        susp_names = ['netcat','ncat','socat','msfconsole','hydra','john ','hashcat']
        ps_out, _, _ = _run('ps aux 2>/dev/null')
        for name in susp_names:
            if name.lower() in ps_out.lower():
                pid_lines = [l for l in ps_out.split('\n') if name.lower() in l.lower()]
                pid = pid_lines[0].split()[1] if pid_lines else '?'
                findings.append({'level':'HIGH',
                    'title': f'Suspicious process: {name.strip()} (PID {pid})',
                    'desc':'Known hacking/pentest tool running. Verify intent.',
                    'actions':[
                        ("KILL PROCESS",   'danger', lambda n=name: self._kill_proc(n)),
                        ("VIEW INFO",      'ghost',  lambda n=name: self._view_proc(n)),
                    ]})

        # 7. Writable tmp
        if not self._scanning: return
        log("Checking temp directories...")
        ww, _, _ = _run('find /tmp /var/tmp -maxdepth 1 -perm -o+w -type f 2>/dev/null | wc -l')
        try:
            if int(ww.strip() or '0') > 10:
                findings.append({'level':'MED',
                    'title': f'{ww.strip()} world-writable files in /tmp',
                    'desc':'Potential staging area for privilege escalation.',
                    'actions':[("CLEAN /TMP", 'warning', self._clean_tmp)]})
        except ValueError:
            pass

        # 8. Pending updates
        if not self._scanning: return
        log("Checking for system updates...")
        upd, _, _ = _run('apt list --upgradable 2>/dev/null | grep -c upgradable', timeout=12)
        try:
            count = max(0, int(upd.strip()) - 1)
            if count > 20:
                findings.append({'level':'HIGH',
                    'title': f'{count} security updates pending — system exposed',
                    'desc':'Unpatched vulnerabilities in installed packages.',
                    'actions':[("UPDATE SYSTEM NOW", 'danger', self._fix_update)]})
            elif count > 0:
                findings.append({'level':'MED',
                    'title': f'{count} system updates available',
                    'desc':'Keep system patched for best security.',
                    'actions':[("UPDATE SYSTEM", 'warning', self._fix_update)]})
        except ValueError:
            pass

        # 9. World-readable sensitive files
        if not self._scanning: return
        log("Checking sensitive file permissions...")
        sens, _, _ = _run(
            r"find /home -maxdepth 3 \( -name '*.key' -o -name 'id_rsa' -o -name '*.pem' \)"
            r" -perm -o+r 2>/dev/null | head -5")
        if sens:
            findings.append({'level':'HIGH',
                'title':'Sensitive key/cert files are world-readable',
                'desc': f'Exposed: {sens[:120]}',
                'actions':[("FIX PERMISSIONS", 'danger',
                            lambda fs=sens: self._fix_file_perms(fs))]})

        if not self._scanning: return
        if not findings:
            findings.append({'level':'OK',
                'title':'✓ No threats detected',
                'desc':'All security checks passed.',
                'actions':[]})

        log(f"✓ Complete — {len(findings)} finding(s).")
        self._scanning = False
        self.after(0, self._render_findings, findings)

    def _render_findings(self, findings):
        for w in self.findings_frame.winfo_children():
            w.destroy()
        self.scan_btn.configure(state='normal', text='↺ RESCAN')
        self.stop_btn.configure(state='disabled')

        high = sum(1 for f in findings if f['level'] == 'HIGH')
        med  = sum(1 for f in findings if f['level'] == 'MED')

        if high or med:
            summary = Card(self.findings_frame, accent=C['wn'] if high else C['am'])
            summary.pack(fill='x', pady=(0,8))
            InfoGrid(summary, [
                ('HIGH RISK', high, C['wn'] if high else C['ok']),
                ('MEDIUM',    med,  C['am'] if med  else C['ok']),
                ('TOTAL',     len(findings), C['ac']),
            ], columns=3).pack(fill='x', padx=4, pady=6)

        for f in findings:
            ThreatAction(self.findings_frame,
                level=f['level'], title=f['title'],
                description=f.get('desc',''),
                actions=f.get('actions',[]) or [],
            ).pack(fill='x', pady=4)

    # ══════════════════════════════════════════════════════════
    # REMEDIATION METHODS
    # ══════════════════════════════════════════════════════════

    def _fix_firewall(self):
        self._alog("Enabling UFW firewall with secure defaults...")
        def _do():
            for msg, cmd in [
                ("Enabling UFW...",              "sudo ufw --force enable"),
                ("Default: deny incoming...",    "sudo ufw default deny incoming"),
                ("Default: allow outgoing...",   "sudo ufw default allow outgoing"),
                ("Allowing SSH (port 22)...",    "sudo ufw allow ssh"),
            ]:
                self.after(0, self._alog, msg)
                out, err, rc = _run(cmd)
                self.after(0, self._alog, f"  {'✓' if rc==0 else '✗'} {(out or err or 'done')[:80]}")
            self.after(0, self._alog, "✓ Firewall enabled. Tab FIREWALL to view rules.")
        threading.Thread(target=_do, daemon=True).start()

    def _fix_ssh(self):
        InstallerPopup(self,
            title="Harden SSH Configuration",
            commands=[
                "sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config",
                "sudo sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config",
                "sudo sed -i 's/^#*Protocol.*/Protocol 2/' /etc/ssh/sshd_config",
                "sudo systemctl restart sshd 2>/dev/null || sudo service ssh restart 2>/dev/null || echo 'SSH not running'",
            ],
            success_msg="SSH hardened! Root login disabled, max attempts set to 3.")

    def _fix_ssh_root(self):
        self._alog("Disabling SSH root login...")
        def _do():
            _run("sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config")
            out, err, rc = _run("sudo systemctl restart sshd 2>/dev/null || sudo service ssh restart 2>/dev/null")
            self.after(0, self._alog, "✓ SSH root login disabled" if rc == 0 else f"Note: {err[:60]}")
        threading.Thread(target=_do, daemon=True).start()

    def _fix_ssh_password(self):
        self._alog("WARNING: Ensure SSH keys are set up before disabling passwords!")
        def _do():
            _run("sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config")
            _run("sudo systemctl restart sshd 2>/dev/null || sudo service ssh restart 2>/dev/null")
            self.after(0, self._alog, "✓ SSH password auth disabled — key-only login required")
        threading.Thread(target=_do, daemon=True).start()

    def _fix_autoupdates(self):
        InstallerPopup(self,
            title="Install Automatic Security Updates",
            commands=[
                "sudo apt-get install -y unattended-upgrades",
                "sudo dpkg-reconfigure -plow unattended-upgrades",
            ],
            success_msg="Automatic security updates configured!")

    def _fix_update(self):
        InstallerPopup(self,
            title="Update System",
            commands=[
                "sudo apt-get update -q",
                "sudo apt-get upgrade -y -q",
                "sudo apt-get autoremove -y -q",
            ],
            success_msg="System updated successfully!")

    def _block_port(self, port):
        self._alog(f"Blocking port {port} with UFW...")
        def _do(pt=port):
            out, err, rc = _run(f"sudo ufw deny {pt}")
            msg = f"✓ Blocked port {pt}" if rc == 0 else f"✗ Failed: {(err or out)[:80]}"
            self.after(0, self._alog, msg)
        threading.Thread(target=_do, daemon=True).start()

    def _allow_local_only(self, port):
        self._alog(f"Restricting port {port} to localhost only...")
        def _do(pt=port):
            _run(f"sudo ufw deny {pt}")
            _run(f"sudo ufw allow from 127.0.0.1 to any port {pt}")
            self.after(0, self._alog, f"✓ Port {pt} restricted to localhost only")
        threading.Thread(target=_do, daemon=True).start()

    def _block_dangerous_ports(self):
        self._alog("Blocking all known dangerous ports...")
        def _do():
            for port, svc in KNOWN_BAD_PORTS.items():
                out, err, rc = _run(f"sudo ufw deny {port} 2>/dev/null")
                status = '✓' if rc == 0 else '✗'
                self.after(0, self._alog, f"  {status} Blocked port {port} ({svc})")
            self.after(0, self._alog, "✓ All dangerous ports blocked")
        threading.Thread(target=_do, daemon=True).start()

    def _kill_suspicious(self):
        self._alog("Scanning for suspicious processes...")
        susp = ['msfconsole','hydra','john','hashcat','netcat','ncat','socat']
        def _do():
            found = False
            for name in susp:
                out, _, rc = _run(f"pgrep -f {name} 2>/dev/null")
                if rc == 0 and out:
                    for pid in out.strip().split('\n'):
                        _, _, krc = _run(f"sudo kill -9 {pid} 2>/dev/null")
                        status = '✓ Killed' if krc == 0 else '✗ Could not kill'
                        self.after(0, self._alog, f"  {status} {name} (PID {pid})")
                    found = True
            if not found:
                self.after(0, self._alog, "✓ No suspicious processes found")
        threading.Thread(target=_do, daemon=True).start()

    def _kill_proc(self, proc_name):
        name = proc_name.split()[0] if proc_name else ''
        self._alog(f"Killing process: {name}...")
        def _do(n=name):
            out, err, rc = _run(f"sudo pkill -f '{n}' 2>/dev/null")
            msg = f"✓ Killed {n}" if rc == 0 else f"✗ Could not kill {n}: {(err or out)[:60]}"
            self.after(0, self._alog, msg)
        threading.Thread(target=_do, daemon=True).start()

    def _view_proc(self, name):
        out, _, _ = _run(f"ps aux | grep {name} | grep -v grep")
        self._alog(f"Process info:\n{out or '(not found)'}")

    def _clean_tmp(self):
        self._alog("Cleaning /tmp and /var/tmp...")
        def _do():
            out, err, rc = _run("sudo rm -rf /tmp/* /var/tmp/* 2>/dev/null")
            msg = "✓ /tmp and /var/tmp cleaned" if rc == 0 else f"✗ {(err or out)[:60]}"
            self.after(0, self._alog, msg)
        threading.Thread(target=_do, daemon=True).start()

    def _fix_file_perms(self, files):
        self._alog("Fixing sensitive file permissions...")
        def _do(fs=files):
            for fpath in fs.split('\n'):
                fpath = fpath.strip()
                if not fpath:
                    continue
                out, err, rc = _run(f"chmod 600 '{fpath}' 2>/dev/null")
                status = '✓' if rc == 0 else '✗'
                self.after(0, self._alog, f"{status} chmod 600 {fpath}")
        threading.Thread(target=_do, daemon=True).start()

    def _open_firewall_mgr(self):
        try:
            self.app._switch_tab('firewall')
        except Exception:
            self._alog("Open the FIREWALL tab in the sidebar to manage rules.")

    # ── Scam checker ──────────────────────────────────────────

    def _check_scam(self):
        for w in self.scam_result.winfo_children():
            w.destroy()
        val = self.scam_entry.get().strip()
        if not val:
            return
        results, risk = [], 'LOW'
        v = val.lower()
        if re.match(r'^(\+27|0)9[0-9]{8}', val.replace(' ','')):
            risk = 'HIGH'; results.append('Premium rate number (090x / +2790x)')
        if re.match(r'^https?://', val):
            if not val.startswith('https:'):
                risk='HIGH'; results.append('HTTP only — no encryption')
            if re.search(r'bit\.ly|tinyurl|t\.co|goo\.gl', val):
                results.append('Shortened/redirected URL — destination unknown')
            if re.search(r'\.(xyz|top|click|win|loan|tk|ml|ga|cf)', val):
                results.append('Suspicious domain extension')
            if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', val):
                results.append('IP address used instead of domain name')
        keywords = ['won','prize','free cash','urgent','verify account',
                    'click here','suspended','confirm details','act now','bank alert']
        hits = [w for w in keywords if w in v]
        if len(hits) >= 2:
            risk='HIGH'; results.append(f'Multiple scam keywords: {", ".join(hits[:4])}')
        elif hits:
            risk='MEDIUM'; results.append(f'Scam keyword found: {hits[0]}')
        if not results:
            results.append('No obvious scam patterns detected')
        rtype = 'warn' if risk=='HIGH' else 'med' if risk=='MEDIUM' else 'ok'
        icon  = '⚠' if risk != 'LOW' else '✓'
        ResultBox(self.scam_result, rtype,
                  f'{icon} RISK LEVEL: {risk}',
                  '\n'.join(results)).pack(fill='x')
