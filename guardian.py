"""Guardian — Auto-Remediation, Panic Button, USB Lockdown"""
import customtkinter as ctk
import threading, subprocess, time, os, shutil
from widgets import ScrollableFrame, Card, SectionHeader, InfoGrid, ResultBox, Btn, C, MONO, MONO_SM
from utils import run_cmd as run, get_sudo_cmd

class GuardianScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built = False
        self._guardian_active = False

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="🛡  GUARDIAN AUTO-DEFENSE", font=('Courier',13,'bold'),
                     text_color=C['ac']).pack(side='left', padx=16)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # ── 01 Guardian Mode ──────────────────────────────────
        SectionHeader(body, '01', 'GUARDIAN MODE').pack(fill='x', padx=14, pady=(14,4))
        mode_card = Card(body)
        mode_card.pack(fill='x', padx=14, pady=(0,8))
        
        self.status_lbl = ctk.CTkLabel(mode_card, text="STATUS: INACTIVE", font=('Courier',12,'bold'), text_color=C['mu'])
        self.status_lbl.pack(pady=(12,4))
        
        ctk.CTkLabel(mode_card, text="Automatically block IPs scanning ports and kill high-risk processes.",
                     font=MONO_SM, text_color=C['mu']).pack(pady=(0,12))
        
        self.toggle_btn = Btn(mode_card, "ENABLE GUARDIAN", command=self._toggle_guardian, width=160)
        self.toggle_btn.pack(pady=(0,12))

        # ── 02 Panic Button ───────────────────────────────────
        SectionHeader(body, '02', 'EMERGENCY CONTROLS').pack(fill='x', padx=14, pady=(10,4))
        panic_card = Card(body, accent=C['wn'])
        panic_card.pack(fill='x', padx=14, pady=(0,8))
        
        ctk.CTkLabel(panic_card, text="⚠ PANIC BUTTON", font=('Courier',14,'bold'), text_color=C['wn']).pack(pady=(12,4))
        ctk.CTkLabel(panic_card, text="Instantly kill network interfaces and lock screen.", font=MONO_SM, text_color=C['mu']).pack(pady=(0,12))
        
        Btn(panic_card, "☢ EXECUTE PANIC", command=self._panic, variant='danger', width=180).pack(pady=(0,12))

        # ── 03 USB Lockdown ───────────────────────────────────
        SectionHeader(body, '03', 'USB LOCKDOWN').pack(fill='x', padx=14, pady=(10,4))
        usb_card = Card(body)
        usb_card.pack(fill='x', padx=14, pady=(0,8))
        
        ctk.CTkLabel(usb_card, text="Block all NEW USB devices. Currently connected devices will remain working.", font=MONO_SM, text_color=C['mu']).pack(pady=(12,4))
        
        self.usb_status = ctk.CTkLabel(usb_card, text="USB Port: Open", font=MONO_SM, text_color=C['ok'])
        self.usb_status.pack(pady=(0,4))
        
        self.usb_btn = Btn(usb_card, "🔒 LOCK USB PORTS", command=self._toggle_usb_lock, variant='ghost', width=180)
        self.usb_btn.pack(pady=(0,12))

    def _toggle_guardian(self):
        self._guardian_active = not self._guardian_active
        if self._guardian_active:
            self.status_lbl.configure(text="STATUS: ACTIVE", text_color=C['ok'])
            self.toggle_btn.configure(text="DISABLE GUARDIAN", variant='success')
            threading.Thread(target=self._guardian_loop, daemon=True).start()
        else:
            self.status_lbl.configure(text="STATUS: INACTIVE", text_color=C['mu'])
            self.toggle_btn.configure(text="ENABLE GUARDIAN", variant='primary')

    def _guardian_loop(self):
        while self._guardian_active:
            # Simple threat auto-remediation: 
            # Check for suspicious processes from a blacklist
            blacklist = ['nc', 'netcat', 'ncat', 'socat', 'msfconsole']
            for proc in blacklist:
                if not self._guardian_active: break
                _, _, rc = run(f"pgrep -x {proc}")
                if rc == 0:
                    run(f"sudo pkill -9 -x {proc}")
                    # Log to threats or show notification could be added here
            time.sleep(5)

    def _panic(self):
        # Kill network
        run("sudo nmcli networking off")
        run("sudo rfkill block all")
        # Lock screen
        run("loginctl lock-session")
        ResultBox(self.scroll, 'warn', 'PANIC EXECUTED', 'Network killed. Radio blocked. Screen locked.').pack(fill='x', padx=14, pady=10)

    def _toggle_usb_lock(self):
        current = self.usb_btn.cget('text')
        if "LOCK" in current:
            # LOCKING
            if shutil.which('usbguard'):
                # Use USBGuard to block new devices
                run("sudo usbguard generate-policy | sudo tee /etc/usbguard/rules.conf")
                run("sudo systemctl start usbguard")
                msg = "USBGuard Active: New devices blocked."
            else:
                # Kernel fallback: disable new ports
                # This is more aggressive and might not be supported on all kernels
                run("sudo bash -c 'echo 0 > /sys/bus/usb/drivers_autoprobe'")
                msg = "Kernel Lockdown: Autoprobe disabled (New devices won't be initialized)."
            
            self.usb_status.configure(text="USB Port: LOCKED", text_color=C['wn'])
            self.usb_btn.configure(text="🔓 UNLOCK USB PORTS", variant='warning')
            ResultBox(self.scroll, 'warn', 'USB LOCKED', msg).pack(fill='x', padx=14, pady=10)
        else:
            # UNLOCKING
            if shutil.which('usbguard'):
                run("sudo systemctl stop usbguard")
                msg = "USBGuard Stopped: Ports open."
            else:
                run("sudo bash -c 'echo 1 > /sys/bus/usb/drivers_autoprobe'")
                msg = "Kernel Lockdown: Autoprobe enabled."
            
            self.usb_status.configure(text="USB Port: Open", text_color=C['ok'])
            self.usb_btn.configure(text="🔒 LOCK USB PORTS", variant='ghost')
            ResultBox(self.scroll, 'ok', 'USB UNLOCKED', msg).pack(fill='x', padx=14, pady=10)
