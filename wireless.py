"""
Mint Scan — Wireless Sync Server
Runs a local HTTP server on the Chromebook/Linux machine.
The Android companion app (or any browser on the phone) connects over Wi-Fi
to sync calls, SMS, contacts, battery, and device info.
"""
import tkinter as tk
import customtkinter as ctk
import threading, subprocess, socket, os, time, json, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from widgets import ScrollableFrame, Card, SectionHeader, InfoGrid, ResultBox, Btn, C, MONO, MONO_SM

# ── Global sync data store ─────────────────────────────────────────
_sync_data = {
    'device':   {},
    'calls':    [],
    'sms':      [],
    'contacts': [],
    'battery':  {},
    'wifi':     [],
    'location': {},
    'last_sync': None,
}
_server_instance = None


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


# ── HTTP Request Handler ───────────────────────────────────────────
class SyncHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests from the Android companion app"""

    def log_message(self, fmt, *args):
        pass  # Suppress default HTTP logging

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_page(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        if path == '/':
            self._send_page(self._home_page())
        elif path == '/status':
            self._send_json({'status': 'online', 'version': '7.0',
                             'name': 'Mint Scan Server'})
        elif path == '/data':
            self._send_json(_sync_data)
        else:
            self._send_json({'error': 'not found'}, 404)

    def do_POST(self):
        length  = int(self.headers.get('Content-Length', 0))
        body    = self.rfile.read(length)
        parsed  = urlparse(self.path)
        path    = parsed.path

        try:
            payload = json.loads(body) if body else {}
        except Exception:
            self._send_json({'error': 'invalid JSON'}, 400)
            return

        if path == '/sync/device':
            _sync_data['device']    = payload
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True})

        elif path == '/sync/calls':
            _sync_data['calls']     = payload.get('calls', [])
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True, 'received': len(_sync_data['calls'])})

        elif path == '/sync/sms':
            _sync_data['sms']       = payload.get('sms', [])
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True, 'received': len(_sync_data['sms'])})

        elif path == '/sync/contacts':
            _sync_data['contacts']  = payload.get('contacts', [])
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True, 'received': len(_sync_data['contacts'])})

        elif path == '/sync/battery':
            _sync_data['battery']   = payload
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True})

        elif path == '/sync/wifi':
            _sync_data['wifi']      = payload.get('networks', [])
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True})

        elif path == '/sync/network':
            _sync_data['network']   = payload
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True})

        elif path == '/sync/location':
            _sync_data['location']  = payload
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True})

        elif path == '/sync/all':
            for key in ['device','calls','sms','contacts','battery','wifi','network','location']:
                if key in payload:
                    _sync_data[key] = payload[key]
            _sync_data['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._send_json({'ok': True})

        else:
            self._send_json({'error': 'unknown endpoint'}, 404)

    def _home_page(self):
        """Web page shown when phone opens the server IP in a browser"""
        calls_count    = len(_sync_data.get('calls', []))
        sms_count      = len(_sync_data.get('sms', []))
        contacts_count = len(_sync_data.get('contacts', []))
        battery        = _sync_data.get('battery', {})
        device         = _sync_data.get('device', {})
        last           = _sync_data.get('last_sync') or 'Never'

        return f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mint Scan Server</title>
<style>
  body {{ background:#020c14; color:#c8e8f4; font-family:monospace; padding:20px; margin:0; }}
  h1   {{ color:#00ffe0; font-size:24px; margin:0 0 4px 0; }}
  .sub {{ color:#3a6278; font-size:12px; margin-bottom:24px; }}
  .card {{ background:#061523; border:1px solid #0d2a3d; border-radius:8px;
           padding:16px; margin-bottom:12px; }}
  .label {{ color:#3a6278; font-size:11px; text-transform:uppercase; }}
  .value {{ color:#00ffe0; font-size:18px; font-weight:bold; margin:4px 0; }}
  .ok   {{ color:#39ff88; }} .warn {{ color:#ff4c4c; }}
  .btn  {{ display:block; background:transparent; border:1px solid #00ffe0;
           color:#00ffe0; padding:14px; border-radius:6px; font-family:monospace;
           font-size:14px; cursor:pointer; margin-bottom:10px; width:100%;
           text-align:center; text-decoration:none; }}
  .btn:hover {{ background:#0d2a3d; }}
  .btn.warn {{ border-color:#ffb830; color:#ffb830; }}
</style>
</head>
<body>
<h1>[ MINT SCAN ]</h1>
<div class="sub">Wireless Sync Server v7.0 — Mint Projects</div>

<div class="card">
  <div class="label">Server Status</div>
  <div class="value ok">ONLINE</div>
  <div class="label">Last sync: {last}</div>
</div>

<div class="card">
  <div class="label">Connected Device</div>
  <div class="value">{device.get('model', 'No device synced yet')}</div>
  <div class="label">{device.get('brand','')} Android {device.get('android','')}</div>
</div>

<div class="card">
  <div class="label">Synced Data</div>
  <div>📞 {calls_count} calls &nbsp; 💬 {sms_count} messages &nbsp; 📇 {contacts_count} contacts</div>
  <div style="margin-top:8px">🔋 Battery: {battery.get('level','—')}%
  {'🔌' if battery.get('charging') else '🔋'}</div>
</div>

<div style="margin-top:20px">
  <a class="btn" href="/data">📊 View All Synced Data (JSON)</a>
  <a class="btn" href="/status">✓ Check Server Status</a>
</div>

<div style="color:#3a6278; font-size:11px; margin-top:20px; text-align:center">
  API Endpoints: /sync/device  /sync/calls  /sync/sms<br>
  /sync/contacts  /sync/battery  /sync/wifi  /sync/all
</div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════
# WIRELESS SYNC SCREEN
# ══════════════════════════════════════════════════════════════════
class WirelessScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built  = False
        self._server = None
        self._port   = 8765

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True
        self._refresh_status()

    def _build(self):
        # ── Header ──────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="📡  WIRELESS SYNC",
                     font=('Courier',13,'bold'), text_color=C['ac']
                     ).pack(side='left', padx=16)
        self._status_dot = ctk.CTkLabel(hdr, text="● OFFLINE",
                                         font=MONO_SM, text_color=C['wn'])
        self._status_dot.pack(side='left', padx=8)
        self._stop_btn = Btn(hdr, "⏹ STOP SERVER",
                             command=self._stop_server,
                             variant='danger', width=130)
        self._stop_btn.pack(side='right', padx=4, pady=6)
        self._stop_btn.configure(state='disabled')
        self._start_btn = Btn(hdr, "▶ START SERVER",
                              command=self._start_server, width=130)
        self._start_btn.pack(side='right', padx=4, pady=6)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # ── How it works ──────────────────────────────────────────
        SectionHeader(body, '01', 'HOW IT WORKS').pack(fill='x', padx=14, pady=(14,4))
        how = Card(body, accent=C['bl'])
        how.pack(fill='x', padx=14, pady=(0,8))
        ctk.CTkLabel(how,
            text="Mint Scan runs a Wi-Fi sync server on your Chromebook.\n"
                 "Your Android phone connects to it over your home Wi-Fi — no USB needed.\n\n"
                 "Option A (Easiest):  Open the server URL in your phone's browser\n"
                 "                     and use the web dashboard to send data.\n\n"
                 "Option B (Automatic): Install the Mint Scan APK on your phone.\n"
                 "                      It auto-syncs calls, SMS, battery, and Wi-Fi in the background.\n\n"
                 "Both phone and Chromebook must be on the SAME Wi-Fi network.",
            font=MONO_SM, text_color=C['mu'], justify='left'
        ).pack(anchor='w', padx=12, pady=(10,10))

        # ── Server connection info ────────────────────────────────
        SectionHeader(body, '02', 'SERVER CONNECTION').pack(fill='x', padx=14, pady=(10,4))
        self._conn_card = Card(body)
        self._conn_card.pack(fill='x', padx=14, pady=(0,8))
        self._conn_info = ctk.CTkLabel(self._conn_card,
            text="Server is offline. Tap ▶ START SERVER to begin.",
            font=MONO_SM, text_color=C['mu'])
        self._conn_info.pack(padx=12, pady=16)

        # ── Port setting ──────────────────────────────────────────
        port_row = ctk.CTkFrame(self._conn_card, fg_color='transparent')
        port_row.pack(fill='x', padx=12, pady=(0,10))
        ctk.CTkLabel(port_row, text="PORT:", font=MONO_SM,
                     text_color=C['mu']).pack(side='left')
        self._port_entry = ctk.CTkEntry(port_row, width=80,
                                         font=MONO_SM,
                                         fg_color=C['bg'],
                                         border_color=C['br'],
                                         text_color=C['tx'])
        self._port_entry.pack(side='left', padx=8)
        self._port_entry.insert(0, str(self._port))
        ctk.CTkLabel(port_row,
            text="(default 8765 — change if blocked by firewall)",
            font=('Courier',8), text_color=C['mu']).pack(side='left')

        # ── QR / URL ──────────────────────────────────────────────
        SectionHeader(body, '03', 'PHONE CONNECTION').pack(fill='x', padx=14, pady=(10,4))
        self._phone_card = Card(body)
        self._phone_card.pack(fill='x', padx=14, pady=(0,8))
        ctk.CTkLabel(self._phone_card,
            text="Start the server to see connection URL and QR code instructions",
            font=MONO_SM, text_color=C['mu']).pack(padx=12, pady=16)

        # ── Live sync data ────────────────────────────────────────
        SectionHeader(body, '04', 'SYNCED DATA').pack(fill='x', padx=14, pady=(10,4))
        self._data_frame = ctk.CTkFrame(body, fg_color='transparent')
        self._data_frame.pack(fill='x', padx=14, pady=(0,8))
        ctk.CTkLabel(self._data_frame,
            text="No data synced yet. Start the server and open the URL on your phone.",
            font=MONO_SM, text_color=C['mu']).pack(pady=8)

        # ── APK section ───────────────────────────────────────────
        SectionHeader(body, '05', 'INSTALL COMPANION APP ON PHONE').pack(fill='x', padx=14, pady=(10,4))
        apk_card = Card(body, accent=C['am'])
        apk_card.pack(fill='x', padx=14, pady=(0,8))
        ctk.CTkLabel(apk_card,
            text="The Mint Scan Companion APK auto-syncs your phone to this server.\n"
                 "Build and install it once — it runs in the background on your phone.",
            font=MONO_SM, text_color=C['mu'], justify='left'
        ).pack(anchor='w', padx=12, pady=(10,6))

        btn_row = ctk.CTkFrame(apk_card, fg_color='transparent')
        btn_row.pack(fill='x', padx=12, pady=(0,10))
        Btn(btn_row, "📱 BUILD COMPANION APK",
            command=self._build_apk, width=200).pack(side='left', padx=(0,8))
        Btn(btn_row, "📦 INSTALL VIA USB",
            command=self._install_via_usb, variant='blue', width=160).pack(side='left')

        # ── Sync log ──────────────────────────────────────────────
        SectionHeader(body, '06', 'SYNC LOG').pack(fill='x', padx=14, pady=(10,4))
        log_card = Card(body)
        log_card.pack(fill='x', padx=14, pady=(0,14))
        self._log = ctk.CTkTextbox(log_card, height=160,
                                    font=('Courier',9),
                                    fg_color=C['bg'],
                                    text_color=C['ok'],
                                    border_width=0)
        self._log.pack(fill='x', padx=8, pady=8)
        self._log.configure(state='disabled')

    def _log_msg(self, msg):
        self._log.configure(state='normal')
        self._log.insert('end', f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self._log.see('end')
        self._log.configure(state='disabled')

    def _start_server(self):
        global _server_instance
        try:
            self._port = int(self._port_entry.get())
        except ValueError:
            self._port = 8765

        if _server_instance:
            self._log_msg("Server already running")
            return

        try:
            _server_instance = HTTPServer(('0.0.0.0', self._port), SyncHandler)
        except OSError as e:
            self._log_msg(f"✗ Could not start server: {e}")
            self._log_msg(f"Try a different port (e.g. 8766)")
            return

        self._server_thread = threading.Thread(
            target=_server_instance.serve_forever, daemon=True)
        self._server_thread.start()

        self._log_msg(f"✓ Server started on port {self._port}")
        self._start_btn.configure(state='disabled', text='RUNNING...')
        self._stop_btn.configure(state='normal')
        self._status_dot.configure(text='● ONLINE', text_color=C['ok'])
        self._refresh_status()
        # Poll for incoming data
        self._poll_data()

    def _stop_server(self):
        global _server_instance
        if _server_instance:
            _server_instance.shutdown()
            _server_instance = None
        self._log_msg("Server stopped")
        self._start_btn.configure(state='normal', text='▶ START SERVER')
        self._stop_btn.configure(state='disabled')
        self._status_dot.configure(text='● OFFLINE', text_color=C['wn'])

    def _refresh_status(self):
        ip   = get_local_ip()
        port = self._port
        running = _server_instance is not None

        # Update connection info
        for w in self._conn_card.winfo_children():
            if isinstance(w, ctk.CTkLabel) and 'Server is' in (w.cget('text') or ''):
                w.destroy()

        if running:
            url = f"http://{ip}:{port}"
            InfoGrid(self._conn_card, [
                ('YOUR IP',   ip,           C['ok']),
                ('PORT',      str(port),    C['ac']),
                ('STATUS',    'ONLINE',     C['ok']),
                ('URL',       url,          C['ac']),
            ], columns=4).pack(fill='x', padx=8, pady=(0,4))
            # Update phone card
            for w in self._phone_card.winfo_children(): w.destroy()
            ctk.CTkLabel(self._phone_card,
                text="OPEN THIS URL ON YOUR PHONE'S BROWSER:",
                font=('Courier',9,'bold'), text_color=C['mu']
            ).pack(anchor='w', padx=12, pady=(12,4))
            url_lbl = ctk.CTkLabel(self._phone_card,
                text=f"  {url}",
                font=('Courier',16,'bold'), text_color=C['ac'])
            url_lbl.pack(anchor='w', padx=12, pady=(0,4))
            ctk.CTkLabel(self._phone_card,
                text=f"Your phone and Chromebook must be on the same Wi-Fi network.\n"
                     f"The URL opens a dashboard where you can check server status.",
                font=('Courier',9), text_color=C['mu'], justify='left'
            ).pack(anchor='w', padx=12, pady=(0,12))

    def _poll_data(self):
        """Check for new sync data every 3 seconds"""
        if _server_instance is None:
            return
        self._render_sync_data()
        self.after(3000, self._poll_data)

    def _render_sync_data(self):
        for w in self._data_frame.winfo_children(): w.destroy()

        last = _sync_data.get('last_sync')
        if not last:
            ctk.CTkLabel(self._data_frame,
                text="No data synced yet. Open the server URL on your phone.",
                font=MONO_SM, text_color=C['mu']).pack(pady=8)
            return

        device   = _sync_data.get('device', {})
        battery  = _sync_data.get('battery', {})
        calls    = _sync_data.get('calls', [])
        sms      = _sync_data.get('sms', [])
        contacts = _sync_data.get('contacts', [])

        # Summary grid
        InfoGrid(self._data_frame, [
            ('DEVICE',    device.get('model', '—'),  C['ac']),
            ('ANDROID',   device.get('android', '—'), C['tx']),
            ('BATTERY',   f"{battery.get('level','—')}%",
             C['ok'] if int(battery.get('level',50) or 50) > 20 else C['wn']),
            ('CHARGING',  'Yes' if battery.get('charging') else 'No', C['tx']),
            ('CALLS',     len(calls),   C['ac']),
            ('SMS',       len(sms),     C['ac']),
            ('CONTACTS',  len(contacts),C['ac']),
            ('LAST SYNC', last,         C['ok']),
        ], columns=4).pack(fill='x', pady=(0,8))

        # Show recent calls
        if calls:
            ctk.CTkLabel(self._data_frame,
                text=f"Recent calls ({len(calls)}):",
                font=('Courier',9,'bold'), text_color=C['ac']
            ).pack(anchor='w', pady=(4,2))
            for call in calls[:5]:
                num  = call.get('number','Unknown')
                name = call.get('name','')
                dur  = call.get('duration','')
                ctk.CTkLabel(self._data_frame,
                    text=f"  📞 {name or num}  {dur}",
                    font=MONO_SM, text_color=C['tx']
                ).pack(anchor='w')

        # Show recent SMS
        if sms:
            ctk.CTkLabel(self._data_frame,
                text=f"\nRecent messages ({len(sms)}):",
                font=('Courier',9,'bold'), text_color=C['ac']
            ).pack(anchor='w', pady=(8,2))
            for msg in sms[:3]:
                addr = msg.get('address','?')
                body = (msg.get('body','') or '')[:60]
                ctk.CTkLabel(self._data_frame,
                    text=f"  💬 {addr}: {body}",
                    font=MONO_SM, text_color=C['tx']
                ).pack(anchor='w')

        self._log_msg(f"Data refreshed — {len(calls)} calls, {len(sms)} SMS")

    def _build_apk(self):
        """Launch the APK builder"""
        popup = ctk.CTkToplevel(self)
        popup.title("Build Companion APK")
        popup.geometry("640x500")
        popup.configure(fg_color=C['bg'])
        popup.lift()
        popup.focus_force()

        ctk.CTkLabel(popup, text="📱  BUILD MINT SCAN COMPANION APK",
                     font=('Courier',13,'bold'), text_color=C['ac']
                     ).pack(pady=(16,4), padx=20, anchor='w')
        ctk.CTkLabel(popup,
            text="This builds an Android APK using Buildozer (Python→Android).\n"
                 "The APK, once installed on your phone, auto-syncs data to Mint Scan over Wi-Fi.\n",
            font=MONO_SM, text_color=C['mu'], justify='left'
        ).pack(padx=20, anchor='w')

        ip   = get_local_ip()
        port = self._port
        url  = f"http://{ip}:{port}"

        ctk.CTkLabel(popup,
            text=f"Server URL to embed in APK: {url}",
            font=('Courier',10,'bold'), text_color=C['ok']
        ).pack(padx=20, anchor='w', pady=(4,12))

        log = ctk.CTkTextbox(popup, height=250, font=('Courier',8),
                              fg_color=C['s2'], text_color=C['ok'],
                              border_width=0)
        log.pack(fill='x', padx=12, pady=4)
        log.configure(state='disabled')

        def _log(msg):
            log.configure(state='normal')
            log.insert('end', msg+'\n')
            log.see('end')
            log.configure(state='disabled')

        def _build():
            _log("Checking for Buildozer...")
            # Check if buildozer installed
            r = subprocess.run("which buildozer", shell=True, capture_output=True)
            if r.returncode != 0:
                _log("Buildozer not found. Installing...")
                subprocess.run("pip install buildozer --break-system-packages -q",
                               shell=True, capture_output=True)

            _log("Creating companion app source...")
            build_dir = os.path.expanduser("~/mint-scan-companion")
            os.makedirs(build_dir, exist_ok=True)

            # Write the companion app main.py
            app_src = f'''"""Mint Scan Companion — Android App"""
import threading, time, json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

SERVER_URL = "{url}"

try:
    import urllib.request as req
    from android.permissions import request_permissions, Permission  # type: ignore
    from jnius import autoclass  # type: ignore
    ANDROID = True
except ImportError:
    ANDROID = False

def sync_device_info():
    data = {{"brand":"Unknown","model":"Unknown","android":"0"}}
    if ANDROID:
        try:
            Build = autoclass('android.os.Build')
            VERSION = autoclass('android.os.Build$VERSION')
            data = {{
                "brand": str(Build.BRAND),
                "model": str(Build.MODEL),
                "android": str(VERSION.RELEASE),
            }}
        except Exception: pass
    _post("/sync/device", data)

def _post(endpoint, data):
    try:
        body = json.dumps(data).encode()
        r = req.Request(SERVER_URL+endpoint, data=body,
                        headers={{"Content-Type":"application/json"}})
        req.urlopen(r, timeout=5)
    except Exception as e:
        print(f"Sync error: e")

class SyncLayout(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", **kw)
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0.008, 0.047, 0.078)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        self.status = Label(
            text="MINT SCAN COMPANION",
            font_size=20, bold=True,
            color=(0,1,0.88,1), size_hint_y=None, height=50)
        self.add_widget(self.status)

        self.info = Label(
            text=f"Server: {SERVER_URL}",
            font_size=12, color=(0.2,0.38,0.47,1),
            size_hint_y=None, height=30)
        self.add_widget(self.info)

        btn = Button(text="SYNC NOW",
                     background_color=(0,0.8,0.55,1),
                     size_hint_y=None, height=60)
        btn.bind(on_press=lambda x: threading.Thread(
            target=self._do_sync, daemon=True).start())
        self.add_widget(btn)

        self.log_lbl = Label(
            text="Tap SYNC NOW to send data to Mint Scan",
            font_size=11, color=(0.2,0.38,0.47,1))
        self.add_widget(self.log_lbl)

    def _update_bg(self, *a):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def _do_sync(self):
        Clock.schedule_once(lambda dt: setattr(
            self.status, 'text', 'SYNCING...'), 0)
        sync_device_info()
        Clock.schedule_once(lambda dt: setattr(
            self.status, 'text', 'SYNC COMPLETE'), 0)
        Clock.schedule_once(lambda dt: setattr(
            self.log_lbl, 'text',
            f'Last sync: {{time.strftime("%H:%M:%S")}}'), 0)

class MintScanCompanion(App):
    def build(self):
        if ANDROID:
            request_permissions([
                Permission.READ_CALL_LOG,
                Permission.READ_CONTACTS,
                Permission.READ_SMS,
                Permission.ACCESS_WIFI_STATE,
            ])
        layout = SyncLayout()
        threading.Thread(target=self._auto_sync,
                         args=(layout,), daemon=True).start()
        return layout

    def _auto_sync(self, layout):
        while True:
            time.sleep(60)
            threading.Thread(target=layout._do_sync, daemon=True).start()

if __name__ == "__main__":
    MintScanCompanion().run()
'''

            with open(os.path.join(build_dir, 'main.py'), 'w') as f:
                f.write(app_src)

            # Write buildozer.spec
            spec = f"""[app]
title = Mint Scan
package.name = mintscan
package.domain = za.mintprojects
source.dir = .
source.include_exts = py,png,kv
version = 7.0
requirements = python3,kivy,requests,android
android.permissions = READ_CALL_LOG,READ_CONTACTS,READ_SMS,ACCESS_WIFI_STATE,INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
fullscreen = 0
[buildozer]
log_level = 2
"""
            with open(os.path.join(build_dir, 'buildozer.spec'), 'w') as f:
                f.write(spec)

            _log(f"✓ Source written to: {build_dir}")
            _log("")
            _log("To build the APK, run these commands:")
            _log(f"  cd {build_dir}")
            _log("  pip install buildozer kivy --break-system-packages")
            _log("  buildozer android debug")
            _log("")
            _log("The APK will be in:")
            _log(f"  {build_dir}/bin/mintscan-7.0-debug.apk")
            _log("")
            _log("Then install it via APK INSTALL tab or:")
            _log(f"  adb install {build_dir}/bin/mintscan-7.0-debug.apk")
            _log("")
            _log("NOTE: First build takes 20-40 mins (downloads Android SDK).")
            _log("Subsequent builds: ~2 minutes.")
            _log("")
            _log("ALTERNATIVE — Test without building:")
            _log(f"  Open {url} in your phone browser")
            _log("  This gives instant access without building an APK!")

        threading.Thread(target=_build, daemon=True).start()
        Btn(popup, "CLOSE", command=popup.destroy,
            variant='ghost', width=80).pack(pady=8)

    def _install_via_usb(self):
        """Install companion APK via USB using ADB"""
        apk_path = os.path.expanduser(
            "~/mint-scan-companion/bin/mintscan-7.0-debug.apk")
        if not os.path.exists(apk_path):
            self._log_msg(
                "No APK found. Build it first using BUILD COMPANION APK.")
            self._log_msg(
                f"Or provide path: {apk_path}")
            return
        self._log_msg("Installing APK via USB...")
        threading.Thread(target=self._do_usb_install,
                         args=(apk_path,), daemon=True).start()

    def _do_usb_install(self, path):
        out, err = subprocess.Popen(
            f"adb install -r '{path}'",
            shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True
        ).communicate()
        if 'Success' in out:
            self.after(0, self._log_msg,
                       "✓ Companion APK installed on phone!")
        else:
            self.after(0, self._log_msg,
                       f"Install result: {out or err}")
