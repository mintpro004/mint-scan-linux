"""
Wireless Sync Server — handles incoming data from Companion App.
Endpoints: /sync/device, /sync/battery, /sync/network, /sync/location
"""
import tkinter as tk
import customtkinter as ctk
import threading, json, time, os, socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from widgets import ScrollableFrame, Card, SectionHeader, InfoGrid, ResultBox, Btn, C, MONO, MONO_SM
from utils import get_local_ip

# Global store for synced data
SYNC_DATA = {
    'device':  {},
    'battery': {},
    'network': {},
    'location':{},
    'last_sync': None
}

class SyncHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            path = self.path
            
            if path == '/sync/device':
                SYNC_DATA['device'] = data
            elif path == '/sync/battery':
                SYNC_DATA['battery'] = data
            elif path == '/sync/network':
                SYNC_DATA['network'] = data
            elif path == '/sync/location':
                SYNC_DATA['location'] = data
            
            SYNC_DATA['last_sync'] = time.time()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        return # Silent logs

class WirelessScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built = False
        self._server = None
        self._running = False

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True
        self._update_display()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="📶  WIRELESS SYNC", font=('Courier',13,'bold'),
                     text_color=C['ac']).pack(side='left', padx=16)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # ── 01 Server Status ──────────────────────────────────
        SectionHeader(body, '01', 'SYNC SERVER').pack(fill='x', padx=14, pady=(14,4))
        srv_card = Card(body)
        srv_card.pack(fill='x', padx=14, pady=(0,8))
        
        self.srv_lbl = ctk.CTkLabel(srv_card, text="SERVER: STOPPED", font=('Courier',11,'bold'), text_color=C['mu'])
        self.srv_lbl.pack(pady=(12,4))
        
        self.addr_lbl = ctk.CTkLabel(srv_card, text="Address: —", font=MONO_SM, text_color=C['mu'])
        self.addr_lbl.pack(pady=(0,12))
        
        self.srv_btn = Btn(srv_card, "▶ START SERVER", command=self._toggle_server, width=160)
        self.srv_btn.pack(pady=(0,12))

        # ── 02 Synced Data ────────────────────────────────────
        SectionHeader(body, '02', 'SYNCED DEVICE DATA').pack(fill='x', padx=14, pady=(10,4))
        self.data_frame = ctk.CTkFrame(body, fg_color='transparent')
        self.data_frame.pack(fill='x', padx=14, pady=(0,8))
        
        # ── 03 Instructions ───────────────────────────────────
        SectionHeader(body, '03', 'INSTRUCTIONS').pack(fill='x', padx=14, pady=(10,4))
        ins_card = Card(body)
        ins_card.pack(fill='x', padx=14, pady=(0,14))
        ctk.CTkLabel(ins_card, text="1. Start this server\n2. Open Companion App on phone\n3. Ensure phone is on same Wi-Fi\n4. Data will appear here automatically",
                     font=MONO_SM, text_color=C['mu'], justify='left').pack(padx=12, pady=12)

    def _toggle_server(self):
        if self._running:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        ip = get_local_ip()
        if ip == '—':
            self.srv_lbl.configure(text="ERROR: NO NETWORK", text_color=C['wn'])
            return
        
        try:
            self._server = HTTPServer((ip, 8080), SyncHandler)
            self._running = True
            threading.Thread(target=self._server.serve_forever, daemon=True).start()
            self.srv_lbl.configure(text="SERVER: RUNNING", text_color=C['ok'])
            self.addr_lbl.configure(text=f"Address: http://{ip}:8080", text_color=C['ac'])
            self.srv_btn.configure(text="⏹ STOP SERVER", variant='danger')
            self._tick()
        except Exception as e:
            self.srv_lbl.configure(text=f"ERROR: {e}", text_color=C['wn'])

    def _stop_server(self):
        if self._server:
            self._server.shutdown()
            self._server = None
        self._running = False
        self.srv_lbl.configure(text="SERVER: STOPPED", text_color=C['mu'])
        self.addr_lbl.configure(text="Address: —", text_color=C['mu'])
        self.srv_btn.configure(text="▶ START SERVER", variant='primary')

    def _tick(self):
        if self._running:
            self._update_display()
            self.after(2000, self._tick)

    def _update_display(self):
        for w in self.data_frame.winfo_children(): w.destroy()
        
        if not SYNC_DATA['last_sync']:
            ctk.CTkLabel(self.data_frame, text="Waiting for data from phone...", font=MONO_SM, text_color=C['mu']).pack(pady=10)
            return

        ts = time.strftime('%H:%M:%S', time.localtime(SYNC_DATA['last_sync']))
        ctk.CTkLabel(self.data_frame, text=f"Last Sync: {ts}", font=MONO_SM, text_color=C['ac']).pack(anchor='w', pady=(0,6))

        # Device
        d = SYNC_DATA['device']
        if d:
            Card(self.data_frame).pack(fill='x', pady=4) # Container
            InfoGrid(self.data_frame.winfo_children()[-1], [
                ('PLATFORM', d.get('platform','—')),
                ('BROWSER', d.get('browser','—')),
                ('CORES', d.get('cores','—')),
                ('MEMORY', d.get('memory','—'))
            ], columns=4).pack(fill='x', padx=4, pady=4)

        # Battery
        b = SYNC_DATA['battery']
        if b:
            col = C['ok'] if b.get('level', 0) > 50 else C['am'] if b.get('level', 0) > 20 else C['wn']
            ResultBox(self.data_frame, 'ok', '🔋 BATTERY STATUS', 
                      f"Level: {b.get('level','—')}% | Charging: {b.get('charging','—')}").pack(fill='x', pady=4)

        # Network
        n = SYNC_DATA['network']
        if n:
            InfoGrid(self.data_frame, [
                ('TYPE', n.get('type','—')),
                ('DOWNLINK', n.get('downlink','—')),
                ('RTT', n.get('rtt','—'))
            ], columns=3).pack(fill='x', pady=4)

        # Location
        l = SYNC_DATA['location']
        if l:
            ResultBox(self.data_frame, 'info', '📍 DEVICE LOCATION',
                      f"Lat: {l.get('lat','—')} | Lon: {l.get('lon','—')} (Acc: {l.get('acc','—')}m)").pack(fill='x', pady=4)
