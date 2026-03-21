"""APK Installer — push and install APK files to Android phone via USB"""
import tkinter as tk
import customtkinter as ctk
import threading, subprocess, os, re, time
from widgets import ScrollableFrame, Card, SectionHeader, InfoGrid, ResultBox, Btn, C, MONO, MONO_SM


def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return '', str(e), 1


class ApkScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built = False
        self._device = None
        self._apk_path = None

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True
        threading.Thread(target=self._detect_device, daemon=True).start()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="📦  APK INSTALLER", font=('Courier',13,'bold'),
                     text_color=C['ac']).pack(side='left', padx=16)
        self.dev_lbl = ctk.CTkLabel(hdr, text="● Detecting device...",
                                     font=MONO_SM, text_color=C['mu'])
        self.dev_lbl.pack(side='left', padx=8)
        Btn(hdr, "↺ RESCAN", command=lambda: threading.Thread(
            target=self._detect_device, daemon=True).start(),
            variant='ghost', width=90).pack(side='right', padx=12, pady=6)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # ── HOW IT WORKS ────────────────────────────────────
        SectionHeader(body, '01', 'SETUP').pack(fill='x', padx=14, pady=(14,4))
        setup = Card(body, accent=C['bl'])
        setup.pack(fill='x', padx=14, pady=(0,8))
        ctk.CTkLabel(setup,
            text="Install any APK file onto your Android phone via USB.\n\n"
                 "Requirements:\n"
                 "  • USB cable connected to Chromebook\n"
                 "  • USB Debugging enabled on phone\n"
                 "  • Settings → Security → Unknown Sources → Allow\n"
                 "  • ADB installed on Chromebook",
            font=MONO_SM, text_color=C['mu'], justify='left'
        ).pack(anchor='w', padx=12, pady=(10,10))
        Btn(setup, "INSTALL ADB: sudo apt install adb",
            command=self._install_adb, variant='blue', width=300
        ).pack(anchor='w', padx=12, pady=(0,10))

        # ── DEVICE STATUS ────────────────────────────────────
        SectionHeader(body, '02', 'CONNECTED DEVICE').pack(fill='x', padx=14, pady=(10,4))
        self.dev_card = Card(body)
        self.dev_card.pack(fill='x', padx=14, pady=(0,8))
        self.dev_info = ctk.CTkLabel(self.dev_card,
            text="Scanning for connected Android device...",
            font=MONO_SM, text_color=C['mu'])
        self.dev_info.pack(padx=12, pady=12)

        # ── APK FILE SELECTION ───────────────────────────────
        SectionHeader(body, '03', 'SELECT APK FILE').pack(fill='x', padx=14, pady=(10,4))
        apk_card = Card(body)
        apk_card.pack(fill='x', padx=14, pady=(0,8))

        ctk.CTkLabel(apk_card,
            text="Enter the full path to your APK file, or browse:",
            font=MONO_SM, text_color=C['mu']
        ).pack(anchor='w', padx=12, pady=(10,4))

        inp_row = ctk.CTkFrame(apk_card, fg_color='transparent')
        inp_row.pack(fill='x', padx=12, pady=(0,8))
        self.apk_entry = ctk.CTkEntry(inp_row,
            placeholder_text="e.g. /home/mint/Downloads/myapp.apk",
            font=MONO_SM, fg_color=C['bg'], border_color=C['br'],
            text_color=C['tx'], height=36)
        self.apk_entry.pack(side='left', fill='x', expand=True, padx=(0,8))
        Btn(inp_row, "BROWSE", command=self._browse_apk,
            variant='ghost', width=80).pack(side='left')

        # APK info display
        self.apk_info = ctk.CTkFrame(apk_card, fg_color='transparent')
        self.apk_info.pack(fill='x', padx=12, pady=(0,8))

        # ── INSTALL OPTIONS ──────────────────────────────────
        SectionHeader(body, '04', 'INSTALL OPTIONS').pack(fill='x', padx=14, pady=(10,4))
        opts_card = Card(body)
        opts_card.pack(fill='x', padx=14, pady=(0,8))

        opt_row1 = ctk.CTkFrame(opts_card, fg_color='transparent')
        opt_row1.pack(fill='x', padx=12, pady=(10,4))
        self.allow_downgrade = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt_row1, text="Allow version downgrade (-d flag)",
                        variable=self.allow_downgrade, font=MONO_SM,
                        text_color=C['tx'], checkmark_color=C['bg'],
                        fg_color=C['ac'], border_color=C['br']
                        ).pack(side='left')

        opt_row2 = ctk.CTkFrame(opts_card, fg_color='transparent')
        opt_row2.pack(fill='x', padx=12, pady=(4,4))
        self.grant_perms = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_row2, text="Grant all permissions on install (-g flag)",
                        variable=self.grant_perms, font=MONO_SM,
                        text_color=C['tx'], checkmark_color=C['bg'],
                        fg_color=C['ac'], border_color=C['br']
                        ).pack(side='left')

        opt_row3 = ctk.CTkFrame(opts_card, fg_color='transparent')
        opt_row3.pack(fill='x', padx=12, pady=(4,10))
        self.replace_existing = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_row3, text="Replace existing installation (-r flag)",
                        variable=self.replace_existing, font=MONO_SM,
                        text_color=C['tx'], checkmark_color=C['bg'],
                        fg_color=C['ac'], border_color=C['br']
                        ).pack(side='left')

        # ── INSTALL BUTTON ───────────────────────────────────
        SectionHeader(body, '05', 'INSTALL').pack(fill='x', padx=14, pady=(10,4))
        inst_card = Card(body)
        inst_card.pack(fill='x', padx=14, pady=(0,8))

        btn_row = ctk.CTkFrame(inst_card, fg_color='transparent')
        btn_row.pack(fill='x', padx=12, pady=10)
        self.install_btn = Btn(btn_row, "📦 INSTALL APK TO PHONE",
                                command=self._install_apk, width=240)
        self.install_btn.pack(side='left', padx=(0,8))
        Btn(btn_row, "📋 LIST INSTALLED APPS",
            command=self._list_apps, variant='ghost', width=180
            ).pack(side='left')

        # Progress / output
        self.progress = ctk.CTkProgressBar(inst_card, height=6,
                                            progress_color=C['ac'], fg_color=C['br'])
        self.progress.pack(fill='x', padx=12, pady=(0,6))
        self.progress.set(0)

        self.output = ctk.CTkTextbox(inst_card, height=160, font=('Courier',9),
                                      fg_color=C['bg'], text_color=C['ok'],
                                      border_width=0)
        self.output.pack(fill='x', padx=8, pady=(0,8))
        self.output.configure(state='disabled')

        ctk.CTkLabel(body, text="", height=20).pack()

    def _log(self, msg, color=None):
        self.output.configure(state='normal')
        self.output.insert('end', f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.output.see('end')
        self.output.configure(state='disabled')

    def _detect_device(self):
        out, _, rc = run('adb devices 2>/dev/null')
        if rc != 0:
            self.after(0, lambda: (
                self.dev_lbl.configure(text='● ADB NOT INSTALLED', text_color=C['wn']),
                self.dev_info.configure(
                    text='ADB not found. Run: sudo apt install adb', text_color=C['wn'])
            ))
            return

        lines = [l for l in out.split('\n')[1:] if '\t' in l and 'offline' not in l]
        if not lines:
            self.after(0, lambda: (
                self.dev_lbl.configure(text='● NO DEVICE DETECTED', text_color=C['wn']),
                self.dev_info.configure(
                    text='No device found.\n1. Connect USB cable\n2. Enable USB Debugging\n3. Tap Allow on phone', text_color=C['wn'])
            ))
            self._device = None
            return

        serial = lines[0].split('\t')[0]
        self._device = serial
        model, _, _ = run(f'adb -s {serial} shell getprop ro.product.model')
        brand, _, _ = run(f'adb -s {serial} shell getprop ro.product.brand')
        android, _, _ = run(f'adb -s {serial} shell getprop ro.build.version.release')

        self.after(0, lambda: (
            self.dev_lbl.configure(text=f'● {brand} {model}', text_color=C['ok']),
            self.dev_info.configure(
                text=f'✓ Connected: {brand} {model}  |  Android {android}  |  Serial: {serial}',
                text_color=C['ok'])
        ))

    def _browse_apk(self):
        """Open file dialog to select APK"""
        try:
            import tkinter.filedialog as fd
            path = fd.askopenfilename(
                title="Select APK file",
                filetypes=[("Android Package", "*.apk"), ("All files", "*.*")],
                initialdir=os.path.expanduser("~/Downloads")
            )
            if path:
                self.apk_entry.delete(0, 'end')
                self.apk_entry.insert(0, path)
                self._show_apk_info(path)
        except Exception as e:
            self._log(f"Browse error: {e}")

    def _show_apk_info(self, path):
        for w in self.apk_info.winfo_children():
            w.destroy()
        if not os.path.exists(path):
            ResultBox(self.apk_info, 'warn', '⚠ FILE NOT FOUND', path).pack(fill='x')
            return
        size_mb = os.path.getsize(path) / 1024 / 1024
        fname = os.path.basename(path)
        # Try to get package name with aapt
        pkg, _, _ = run(f"aapt dump badging '{path}' 2>/dev/null | grep 'package: name' | head -1")
        pkg_name = re.search(r"name='([^']+)'", pkg)
        pkg_ver  = re.search(r"versionName='([^']+)'", pkg)
        InfoGrid(self.apk_info, [
            ('FILE',     fname,                          C['ac']),
            ('SIZE',     f"{size_mb:.1f} MB"),
            ('PACKAGE',  pkg_name.group(1) if pkg_name else 'Unknown'),
            ('VERSION',  pkg_ver.group(1)  if pkg_ver  else 'Unknown'),
        ], columns=4).pack(fill='x')

    def _install_apk(self):
        if not self._device:
            self._log("No device connected. Connect phone and tap RESCAN.")
            return
        path = self.apk_entry.get().strip()
        if not path:
            self._log("No APK selected. Enter or browse for an APK file.")
            return
        if not os.path.exists(path):
            self._log(f"File not found: {path}")
            return
        self.install_btn.configure(state='disabled', text='INSTALLING...')
        self.progress.set(0.1)
        threading.Thread(target=self._do_install, args=(path,), daemon=True).start()

    def _do_install(self, path):
        self.after(0, self._log, f"Preparing to install: {os.path.basename(path)}")
        self.after(0, lambda: self.progress.set(0.3))

        # Build flags
        flags = []
        if self.replace_existing.get():   flags.append('-r')
        if self.grant_perms.get():         flags.append('-g')
        if self.allow_downgrade.get():     flags.append('-d')
        flag_str = ' '.join(flags)

        self.after(0, self._log, f"Running: adb install {flag_str} ...")
        self.after(0, lambda: self.progress.set(0.5))

        out, err, rc = run(
            f"adb -s {self._device} install {flag_str} '{path}'",
            timeout=120)

        self.after(0, lambda: self.progress.set(1.0))

        if 'Success' in out or rc == 0:
            self.after(0, self._log, f"✓ INSTALLATION SUCCESSFUL")
            self.after(0, self._log, f"  {out}")
        else:
            self.after(0, self._log, f"✗ INSTALLATION FAILED")
            self.after(0, self._log, f"  {out or err}")
            if 'INSTALL_FAILED_UNKNOWN_SOURCES' in (out+err):
                self.after(0, self._log,
                    "Fix: Settings → Security → Install Unknown Apps → Allow")
            elif 'INSTALL_FAILED_VERSION_DOWNGRADE' in (out+err):
                self.after(0, self._log,
                    "Fix: Enable 'Allow version downgrade' option above")

        self.after(0, lambda: self.install_btn.configure(
            state='normal', text='📦 INSTALL APK TO PHONE'))

    def _list_apps(self):
        if not self._device:
            self._log("No device connected.")
            return
        threading.Thread(target=self._do_list_apps, daemon=True).start()

    def _do_list_apps(self):
        self.after(0, self._log, "Listing installed packages...")
        out, _, _ = run(f"adb -s {self._device} shell pm list packages -3 2>/dev/null")
        if out:
            pkgs = [l.replace('package:', '') for l in out.split('\n') if l.strip()]
            self.after(0, self._log, f"Found {len(pkgs)} third-party apps:")
            for p in pkgs[:30]:
                self.after(0, self._log, f"  {p}")
        else:
            self.after(0, self._log, "No packages found or permission denied")

    def _install_adb(self):
        subprocess.Popen(['x-terminal-emulator', '-e',
                         'bash -c "sudo apt install -y adb && echo Done; read"'])
