"""USB Phone Sync — ADB bridge for Android phone integration"""
import tkinter as tk
import customtkinter as ctk
import threading, subprocess, os, time, re
from installer import install_adb
from widgets import ScrollableFrame, Card, SectionHeader, InfoGrid, ResultBox, Btn, C, MONO, MONO_SM


def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return '', str(e), 1


class UsbScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built = False
        self._device = None

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True
        threading.Thread(target=self._detect, daemon=True).start()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="📱  USB PHONE SYNC", font=('Courier',13,'bold'),
                     text_color=C['ac']).pack(side='left', padx=16)
        self.status_dot = ctk.CTkLabel(hdr, text='● DETECTING...',
                                        font=('Courier',9), text_color=C['mu'])
        self.status_dot.pack(side='left', padx=8)
        Btn(hdr, "↺ RESCAN", command=lambda: threading.Thread(
            target=self._detect, daemon=True).start(),
            variant='ghost', width=100).pack(side='right', padx=12, pady=6)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # Setup instructions
        SectionHeader(body, '01', 'SETUP — ENABLE ADB ON PHONE').pack(fill='x', padx=14, pady=(14,4))
        setup = Card(body, accent=C['bl'])
        setup.pack(fill='x', padx=14, pady=(0,8))
        ctk.CTkLabel(setup,
            text="STEP 1 — Enable Developer Options on your Android phone:\n"
                 "  Settings → About Phone → tap Build Number 7 times\n\n"
                 "STEP 2 — Enable USB Debugging:\n"
                 "  Settings → Developer Options → USB Debugging → ON\n\n"
                 "STEP 3 — Connect phone to Chromebook via USB cable\n\n"
                 "STEP 4 — On your phone: tap 'Allow USB Debugging' → OK\n\n"
                 "STEP 5 — Tap RESCAN above",
            font=MONO_SM, text_color=C['mu'], justify='left'
        ).pack(anchor='w', padx=12, pady=(10,10))
        Btn(setup, "INSTALL ADB: sudo apt install adb",
            command=self._install_adb, variant='blue', width=320
        ).pack(anchor='w', padx=12, pady=(0,10))

        # Device info
        SectionHeader(body, '02', 'CONNECTED DEVICE').pack(fill='x', padx=14, pady=(10,4))
        self.dev_card = Card(body)
        self.dev_card.pack(fill='x', padx=14, pady=(0,8))
        self.dev_info = ctk.CTkLabel(self.dev_card,
            text="No device detected. Connect phone via USB and enable USB debugging.",
            font=MONO_SM, text_color=C['mu'])
        self.dev_info.pack(padx=12, pady=12)

        # Sync actions
        SectionHeader(body, '03', 'SYNC & DATA').pack(fill='x', padx=14, pady=(10,4))
        act_card = Card(body)
        act_card.pack(fill='x', padx=14, pady=(0,8))

        grid = ctk.CTkFrame(act_card, fg_color='transparent')
        grid.pack(fill='x', padx=8, pady=8)
        actions = [
            ("📋 PULL CALL LOG",    self._pull_calls,   'primary'),
            ("💬 PULL SMS LOG",     self._pull_sms,     'primary'),
            ("📇 PULL CONTACTS",   self._pull_contacts,'blue'),
            ("📸 PULL SCREENSHOTS",self._pull_screenshots,'ghost'),
            ("📶 GET WIFI NETWORKS",self._pull_wifi,    'warning'),
            ("🔋 PHONE BATTERY",   self._phone_battery,'ghost'),
            ("📱 DEVICE INFO",     self._phone_info,   'ghost'),
            ("🔁 START SYNC",      self._start_sync,   'success'),
        ]
        for i, (label, cmd, variant) in enumerate(actions):
            r, c = divmod(i, 2)
            Btn(grid, label, command=cmd, variant=variant, width=220
                ).grid(row=r, column=c, padx=4, pady=4, sticky='ew')
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # Output log
        SectionHeader(body, '04', 'OUTPUT').pack(fill='x', padx=14, pady=(10,4))
        self.log = ctk.CTkTextbox(body, height=200, font=('Courier',9),
                                   fg_color=C['s2'], text_color=C['ok'],
                                   border_color=C['br'], border_width=1,
                                   corner_radius=6)
        self.log.pack(fill='x', padx=14, pady=(0,14))
        self.log.configure(state='disabled')

    def _log(self, msg, color=None):
        self.log.configure(state='normal')
        self.log.insert('end', f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log.see('end')
        self.log.configure(state='disabled')

    def _detect(self):
        out, _, rc = run('adb devices 2>/dev/null')
        if rc != 0 or 'adb' not in out.lower() and not out:
            self.after(0, lambda: (
                self.status_dot.configure(text='● ADB NOT INSTALLED', text_color=C['wn']),
                self.dev_info.configure(text='ADB not found.\nRun: sudo apt install adb\nthen reconnect phone.')
            ))
            return

        lines = [l for l in out.split('\n')[1:] if l.strip() and 'offline' not in l]
        devices = [l.split('\t')[0] for l in lines if '\t' in l]

        if not devices:
            self.after(0, lambda: (
                self.status_dot.configure(text='● NO DEVICE', text_color=C['wn']),
                self.dev_info.configure(
                    text='No Android device detected.\n\n'
                         '1. Make sure USB cable is connected\n'
                         '2. USB Debugging is ON in Developer Options\n'
                         '3. You tapped "Allow" on your phone')
            ))
            return

        serial = devices[0]
        self._device = serial

        # Get device details
        model,  _, _ = run(f'adb -s {serial} shell getprop ro.product.model')
        brand,  _, _ = run(f'adb -s {serial} shell getprop ro.product.brand')
        android,_, _ = run(f'adb -s {serial} shell getprop ro.build.version.release')
        api,    _, _ = run(f'adb -s {serial} shell getprop ro.build.version.sdk')
        bat_out,_, _ = run(f'adb -s {serial} shell dumpsys battery | grep level')
        bat = re.search(r'level: (\d+)', bat_out)
        bat_pct = bat.group(1) if bat else '—'

        info_text = (f"✓ CONNECTED: {brand} {model}\n"
                     f"Android {android}  •  API {api}  •  Battery {bat_pct}%\n"
                     f"Serial: {serial}")

        self.after(0, lambda: (
            self.status_dot.configure(text=f'● CONNECTED: {brand} {model}', text_color=C['ok']),
            self.dev_info.configure(text=info_text, text_color=C['ok'])
        ))
        self.after(0, self._log, f"Device connected: {brand} {model} (Android {android})")

    def _need_device(self):
        if not self._device:
            self._log("No device connected. Connect phone and tap RESCAN.")
            return False
        return True

    def _pull_calls(self):
        if not self._need_device(): return
        threading.Thread(target=self._do_pull_calls, daemon=True).start()

    def _do_pull_calls(self):
        self.after(0, self._log, "Pulling call log from phone...")
        out, err, rc = run(
            f'adb -s {self._device} shell content query '
            '--uri content://call_log/calls '
            '--projection number:date:duration:type:name '
            '2>/dev/null | head -50', timeout=15)
        if rc == 0 and out:
            lines = out.strip().split('\n')
            self.after(0, self._log, f"Got {len(lines)} call records")
            for line in lines[:10]:
                self.after(0, self._log, f"  {line[:80]}")
            # Save to file
            with open(os.path.expanduser('~/mint-scan-calls.txt'), 'w') as f:
                f.write(out)
            self.after(0, self._log, "Saved to ~/mint-scan-calls.txt")
        else:
            self.after(0, self._log, f"Failed: {err[:100]}")
            self.after(0, self._log, "Note: Some phones restrict call log access via ADB.")

    def _pull_sms(self):
        if not self._need_device(): return
        threading.Thread(target=self._do_pull_sms, daemon=True).start()

    def _do_pull_sms(self):
        self.after(0, self._log, "Pulling SMS messages...")
        out, err, rc = run(
            f'adb -s {self._device} shell content query '
            '--uri content://sms/inbox '
            '--projection address:date:body '
            '2>/dev/null | head -30', timeout=15)
        if rc == 0 and out:
            lines = out.strip().split('\n')
            self.after(0, self._log, f"Got {len(lines)} SMS messages")
            with open(os.path.expanduser('~/mint-scan-sms.txt'), 'w') as f:
                f.write(out)
            self.after(0, self._log, "Saved to ~/mint-scan-sms.txt")
        else:
            self.after(0, self._log, f"Failed to read SMS: {err[:80]}")

    def _pull_contacts(self):
        if not self._need_device(): return
        threading.Thread(target=self._do_pull_contacts, daemon=True).start()

    def _do_pull_contacts(self):
        self.after(0, self._log, "Pulling contacts...")
        out, err, rc = run(
            f'adb -s {self._device} shell content query '
            '--uri content://contacts/phones/ '
            '--projection display_name:number '
            '2>/dev/null | head -50', timeout=15)
        if rc == 0 and out:
            lines = out.strip().split('\n')
            self.after(0, self._log, f"Got {len(lines)} contacts")
            with open(os.path.expanduser('~/mint-scan-contacts.txt'), 'w') as f:
                f.write(out)
            self.after(0, self._log, "Saved to ~/mint-scan-contacts.txt")
        else:
            self.after(0, self._log, f"Failed: {err[:80]}")

    def _pull_wifi(self):
        if not self._need_device(): return
        threading.Thread(target=self._do_pull_wifi, daemon=True).start()

    def _do_pull_wifi(self):
        self.after(0, self._log, "Reading Wi-Fi networks from phone...")
        # Try wpa_supplicant.conf (requires root on modern Android)
        out, _, rc = run(
            f'adb -s {self._device} shell su -c '
            '"cat /data/misc/wifi/WifiConfigStore.xml" 2>/dev/null', timeout=10)
        if rc == 0 and 'SSID' in out:
            ssids = re.findall(r'<string name="SSID">&quot;(.+?)&quot;</string>', out)
            pwds  = re.findall(r'<string name="PreSharedKey">&quot;(.+?)&quot;</string>', out)
            self.after(0, self._log, f"Found {len(ssids)} saved networks (root)")
            for i, ssid in enumerate(ssids[:20]):
                pwd = pwds[i] if i < len(pwds) else '(no password/enterprise)'
                self.after(0, self._log, f"  {ssid}: {pwd}")
            with open(os.path.expanduser('~/mint-scan-wifi.txt'), 'w') as f:
                for i, ssid in enumerate(ssids):
                    pwd = pwds[i] if i < len(pwds) else '(no password)'
                    f.write(f"{ssid}\t{pwd}\n")
            self.after(0, self._log, "Saved to ~/mint-scan-wifi.txt")
        else:
            # Try non-root backup method
            out2, _, _ = run(
                f'adb -s {self._device} shell cmd wifi list-networks 2>/dev/null', timeout=10)
            if out2:
                self.after(0, self._log, f"Networks (no passwords - requires root for passwords):\n{out2[:500]}")
            else:
                self.after(0, self._log,
                    "Wi-Fi password access requires root on Android 10+.\n"
                    "Network names listed above. Passwords require rooted device.")

    def _pull_screenshots(self):
        if not self._need_device(): return
        threading.Thread(target=self._do_screenshots, daemon=True).start()

    def _do_screenshots(self):
        self.after(0, self._log, "Taking screenshot...")
        run(f'adb -s {self._device} shell screencap -p /sdcard/mint_scan_screen.png', timeout=10)
        out, err, rc = run(
            f'adb -s {self._device} pull /sdcard/mint_scan_screen.png '
            f'{os.path.expanduser("~/mint-scan-screenshot.png")}', timeout=15)
        if rc == 0:
            self.after(0, self._log, "Screenshot saved: ~/mint-scan-screenshot.png")
        else:
            self.after(0, self._log, f"Failed: {err[:80]}")

    def _phone_battery(self):
        if not self._need_device(): return
        out, _, _ = run(f'adb -s {self._device} shell dumpsys battery', timeout=8)
        self.after(0, self._log, f"Battery info:\n{out[:400]}")

    def _phone_info(self):
        if not self._need_device(): return
        threading.Thread(target=self._do_phone_info, daemon=True).start()

    def _do_phone_info(self):
        props = [
            ('ro.product.brand',          'Brand'),
            ('ro.product.model',          'Model'),
            ('ro.build.version.release',  'Android'),
            ('ro.build.version.sdk',      'API Level'),
            ('ro.product.cpu.abi',        'CPU ABI'),
            ('ro.build.fingerprint',      'Build'),
            ('gsm.network.type',          'Network Type'),
            ('gsm.sim.operator.alpha',    'Carrier'),
        ]
        for prop, label in props:
            val, _, _ = run(f'adb -s {self._device} shell getprop {prop}')
            self.after(0, self._log, f"  {label}: {val or '—'}")

    def _start_sync(self):
        if not self._need_device(): return
        self._log("Starting full sync...")
        self._do_pull_calls()
        time.sleep(1)
        self._do_pull_sms()
        time.sleep(1)
        self._do_pull_contacts()
        self._log("✓ Full sync complete. Files saved to home directory.")

    def _install_adb(self):
        install_adb(self, on_done=lambda: self.after(500,
            threading.Thread(target=self._detect, daemon=True).start))
