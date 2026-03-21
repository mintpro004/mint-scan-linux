"""Threats Screen — real Linux security checks"""
import tkinter as tk
import customtkinter as ctk
import threading, os, re
from src.utils import C, MONO, MONO_SM, run_cmd, check_root, get_open_ports
from src.widgets import ScrollableFrame, Card, SectionHeader, ResultBox, Btn


KNOWN_BAD_PORTS = {'23': 'Telnet', '4444': 'Metasploit', '1337': 'Suspicious',
                   '6667': 'IRC', '31337': 'Back Orifice'}
RISKY_PORTS     = {'21': 'FTP', '25': 'SMTP', '3306': 'MySQL',
                   '27017': 'MongoDB', '6379': 'Redis', '5900': 'VNC'}


class ThreatsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built = False

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="⚠  THREATS", font=('Courier', 13, 'bold'),
                     text_color=C['ac']).pack(side='left', padx=16)
        self.scan_btn = Btn(hdr, "▶  DEEP SCAN", command=self._scan, width=130)
        self.scan_btn.pack(side='right', padx=12, pady=6)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        SectionHeader(body, '01', 'THREAT SCAN').pack(fill='x', padx=14, pady=(14,4))
        self.scan_log = ctk.CTkTextbox(body, height=120, font=('Courier',9),
                                        fg_color=C['s2'], text_color=C['ac'],
                                        border_color=C['br'], border_width=1,
                                        corner_radius=6)
        self.scan_log.pack(fill='x', padx=14, pady=(0,8))
        self.scan_log.configure(state='disabled')

        SectionHeader(body, '02', 'FINDINGS').pack(fill='x', padx=14, pady=(10,4))
        self.findings_frame = ctk.CTkFrame(body, fg_color='transparent')
        self.findings_frame.pack(fill='x', padx=14, pady=(0,8))

        # Scam checker
        SectionHeader(body, '03', 'SCAM / URL CHECKER').pack(fill='x', padx=14, pady=(10,4))
        scam_card = Card(body)
        scam_card.pack(fill='x', padx=14, pady=(0,14))
        ctk.CTkLabel(scam_card, text="Check a phone number, URL, or message text:",
                     font=MONO_SM, text_color=C['mu']).pack(anchor='w', padx=12, pady=(10,4))
        inp_row = ctk.CTkFrame(scam_card, fg_color='transparent')
        inp_row.pack(fill='x', padx=12, pady=(0,8))
        self.scam_entry = ctk.CTkEntry(inp_row, placeholder_text="Number, URL, or message...",
                                        font=MONO_SM, fg_color=C['bg'],
                                        border_color=C['br'], text_color=C['tx'], height=36)
        self.scam_entry.pack(side='left', fill='x', expand=True, padx=(0,8))
        Btn(inp_row, "ANALYSE", command=self._check_scam,
            variant='danger', width=90).pack(side='left')
        self.scam_result = ctk.CTkFrame(scam_card, fg_color='transparent')
        self.scam_result.pack(fill='x', padx=12, pady=(0,8))

        ctk.CTkLabel(body, text="Tap DEEP SCAN to run real security checks",
                     font=MONO_SM, text_color=C['mu']).pack(pady=8)

    def _log(self, msg, color=None):
        self.scan_log.configure(state='normal')
        self.scan_log.insert('end', msg + '\n')
        self.scan_log.see('end')
        self.scan_log.configure(state='disabled')

    def _scan(self):
        self.scan_btn.configure(state='disabled', text='SCANNING...')
        self.scan_log.configure(state='normal')
        self.scan_log.delete('1.0', 'end')
        self.scan_log.configure(state='disabled')
        for w in self.findings_frame.winfo_children(): w.destroy()
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        findings = []

        def log(msg): self.after(0, self._log, msg)

        log("Starting real security scan...")

        # 1. Root check
        log("Checking root status...")
        is_root = check_root()
        if is_root:
            findings.append(('HIGH', '⚠ Running as root',
                              'Process has full system access. Run as a regular user.'))

        # 2. Open ports
        log("Scanning open ports...")
        ports = get_open_ports()
        for p in ports:
            port = p['port']
            if port in KNOWN_BAD_PORTS:
                findings.append(('HIGH',
                                  f"⚠ Dangerous port open: {port} ({KNOWN_BAD_PORTS[port]})",
                                  f"Process: {p['process']}. Close this immediately."))
            elif port in RISKY_PORTS:
                findings.append(('MED',
                                  f"Port {port} ({RISKY_PORTS[port]}) exposed",
                                  f"Process: {p['process']}. Ensure firewall rules are in place."))

        # 3. SSH root login
        log("Checking SSH config...")
        sshd = '/etc/ssh/sshd_config'
        if os.path.exists(sshd):
            try:
                cfg = open(sshd).read()
                if re.search(r'^PermitRootLogin\s+yes', cfg, re.MULTILINE):
                    findings.append(('HIGH', '⚠ SSH root login permitted',
                                      'Edit /etc/ssh/sshd_config: set PermitRootLogin no'))
                if re.search(r'^PasswordAuthentication\s+yes', cfg, re.MULTILINE):
                    findings.append(('MED', 'SSH password auth enabled',
                                      'Consider using key-based auth only.'))
            except PermissionError:
                log("  SSH config not readable (need sudo)")

        # 4. Firewall
        log("Checking firewall...")
        ufw, _, rc = run_cmd('ufw status 2>/dev/null')
        if 'inactive' in ufw.lower() or rc != 0:
            iptables, _, _ = run_cmd('iptables -L 2>/dev/null | grep -c ACCEPT')
            if not iptables or int(iptables or '0') > 10:
                findings.append(('HIGH', '⚠ Firewall not active',
                                  'Run: sudo ufw enable && sudo ufw default deny incoming'))

        # 5. Unattended upgrades
        log("Checking auto-updates...")
        out, _, _ = run_cmd('dpkg -l unattended-upgrades 2>/dev/null | grep ^ii')
        if not out:
            findings.append(('MED', 'Auto-updates not installed',
                              'Install: sudo apt install unattended-upgrades'))

        # 6. Suspicious processes
        log("Checking running processes...")
        susp_names = ['nc ', 'netcat', 'ncat', 'socat', 'msfconsole', 'hydra', 'john']
        ps_out, _, _ = run_cmd('ps aux 2>/dev/null')
        for name in susp_names:
            if name in ps_out.lower():
                findings.append(('HIGH', f"⚠ Suspicious process: {name.strip()}",
                                  'Known hacking/pentest tool running. Verify intent.'))

        # 7. World-writable directories
        log("Checking writable dirs...")
        ww, _, _ = run_cmd('find /tmp /var/tmp -maxdepth 1 -perm -o+w 2>/dev/null | wc -l')
        if ww and int(ww) > 5:
            findings.append(('MED', f"{ww} world-writable files in /tmp",
                              'Some risk — temp files may be accessible to all users.'))

        # All clear
        if not findings:
            findings.append(('OK', '✓ No threats detected',
                              'All real-time security checks passed.'))

        log("✓ Scan complete.")
        self.after(0, self._render_findings, findings)

    def _render_findings(self, findings):
        for w in self.findings_frame.winfo_children(): w.destroy()
        high = sum(1 for f in findings if f[0] == 'HIGH')
        if high:
            ResultBox(self.findings_frame, 'warn',
                      f'⚠ {high} HIGH-RISK FINDING(S)',
                      'Review items below immediately.').pack(fill='x', pady=(0,8))
        for lvl, title, desc in findings:
            rtype = 'warn' if lvl=='HIGH' else 'med' if lvl=='MED' else 'ok'
            ResultBox(self.findings_frame, rtype, title, desc).pack(fill='x', pady=3)
        self.scan_btn.configure(state='normal', text='↺  RESCAN')

    def _check_scam(self):
        for w in self.scam_result.winfo_children(): w.destroy()
        val = self.scam_entry.get().strip()
        if not val: return

        results, risk = [], 'LOW'
        if re.match(r'^0900', val.replace(' ', '')): risk='HIGH'; results.append('⚠ Premium rate number')
        if re.match(r'^https?://', val):
            if not val.startswith('https:'): risk='HIGH'; results.append('⚠ HTTP — no encryption')
            if re.search(r'bit\.ly|tinyurl', val): risk='MEDIUM'; results.append('⚠ Shortened URL')
            if re.search(r'\.(xyz|top|click|win|loan)', val): results.append('⚠ Suspicious TLD')
        hits = [w for w in ['won','prize','free cash','urgent','verify account','click here']
                if w in val.lower()]
        if len(hits)>=2: risk='HIGH'; results.append(f'⚠ Multiple scam keywords: {", ".join(hits)}')
        elif hits: risk='MEDIUM'; results.append(f'⚠ Scam keyword: {hits[0]}')
        if not results: results.append('✓ No obvious scam patterns detected')

        rtype = 'warn' if risk=='HIGH' else 'med' if risk=='MEDIUM' else 'ok'
        ResultBox(self.scam_result, rtype, f'RISK: {risk}', '\n'.join(results)).pack(fill='x')
