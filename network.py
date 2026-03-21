"""Network Screen — real speed test, ping graph, connections"""
import tkinter as tk
import customtkinter as ctk
import threading
import time
import socket
from src.utils import C, MONO, MONO_SM, get_network_interfaces, get_public_ip_info, get_local_ip, get_active_connections, ping, run_cmd
from src.widgets import ScrollableFrame, Card, SectionHeader, InfoGrid, ResultBox, Btn, LiveBadge


class NetworkScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built = False
        self._ping_history = []
        self._ping_running = False

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True
        self._start_ping_loop()
        threading.Thread(target=self._load, daemon=True).start()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="📡  NETWORK", font=('Courier', 13, 'bold'),
                     text_color=C['ac']).pack(side='left', padx=16)
        self.speed_btn = Btn(hdr, "▶  SPEED TEST", command=self._run_speed, width=130)
        self.speed_btn.pack(side='right', padx=12, pady=6)
        self.refresh_btn = Btn(hdr, "↺  REFRESH", command=lambda: threading.Thread(target=self._load, daemon=True).start(), variant='ghost', width=100)
        self.refresh_btn.pack(side='right', padx=4, pady=6)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # Live ping graph
        SectionHeader(body, '01', 'LIVE RTT LATENCY').pack(fill='x', padx=14, pady=(14,4))
        ping_card = Card(body)
        ping_card.pack(fill='x', padx=14, pady=(0,6))

        top_row = ctk.CTkFrame(ping_card, fg_color='transparent')
        top_row.pack(fill='x', padx=8, pady=(8,0))
        LiveBadge(top_row).pack(side='left')
        self.ping_val = ctk.CTkLabel(top_row, text="—ms", font=('Courier', 13, 'bold'),
                                      text_color=C['ok'])
        self.ping_val.pack(side='right')

        # Canvas for ping graph
        self.ping_canvas = tk.Canvas(ping_card, height=80, bg=C['bg'],
                                      highlightthickness=0)
        self.ping_canvas.pack(fill='x', padx=8, pady=4)

        stats_row = ctk.CTkFrame(ping_card, fg_color='transparent')
        stats_row.pack(fill='x', padx=8, pady=(0,8))
        self.ping_min = ctk.CTkLabel(stats_row, text="MIN: —", font=('Courier',8), text_color=C['mu'])
        self.ping_min.pack(side='left', padx=8)
        self.ping_avg = ctk.CTkLabel(stats_row, text="AVG: —", font=('Courier',8), text_color=C['mu'])
        self.ping_avg.pack(side='left', padx=8)
        self.ping_max = ctk.CTkLabel(stats_row, text="MAX: —", font=('Courier',8), text_color=C['mu'])
        self.ping_max.pack(side='left', padx=8)

        # Speed Test results
        SectionHeader(body, '02', 'SPEED TEST').pack(fill='x', padx=14, pady=(10,4))
        speed_card = Card(body)
        speed_card.pack(fill='x', padx=14, pady=(0,6))
        spd_row = ctk.CTkFrame(speed_card, fg_color='transparent')
        spd_row.pack(fill='x', padx=8, pady=8)
        for attr, label in [('spd_dl','▼ DOWNLOAD'), ('spd_ul','▲ UPLOAD'),
                             ('spd_ping','◉ PING'), ('spd_grade','★ GRADE')]:
            box = ctk.CTkFrame(spd_row, fg_color=C['s2'],
                                border_color=C['br'], border_width=1, corner_radius=6)
            box.pack(side='left', expand=True, fill='x', padx=4)
            val = ctk.CTkLabel(box, text='—', font=('Courier', 22, 'bold'), text_color=C['ac'])
            val.pack(pady=(8,0))
            ctk.CTkLabel(box, text=label, font=('Courier',7), text_color=C['mu']).pack(pady=(0,8))
            setattr(self, attr, val)

        # Interfaces
        SectionHeader(body, '03', 'NETWORK INTERFACES').pack(fill='x', padx=14, pady=(10,4))
        self.iface_frame = ctk.CTkFrame(body, fg_color='transparent')
        self.iface_frame.pack(fill='x', padx=14, pady=(0,6))

        # Public IP
        SectionHeader(body, '04', 'PUBLIC IDENTITY').pack(fill='x', padx=14, pady=(10,4))
        self.pub_grid_frame = ctk.CTkFrame(body, fg_color='transparent')
        self.pub_grid_frame.pack(fill='x', padx=14, pady=(0,6))

        # Active connections
        SectionHeader(body, '05', 'ACTIVE CONNECTIONS').pack(fill='x', padx=14, pady=(10,4))
        self.conn_frame = ctk.CTkFrame(body, fg_color='transparent')
        self.conn_frame.pack(fill='x', padx=14, pady=(0,14))

    def _load(self):
        ifaces  = get_network_interfaces()
        ipinfo  = get_public_ip_info()
        conns   = get_active_connections()
        self.after(0, self._render, ifaces, ipinfo, conns)

    def _render(self, ifaces, ipinfo, conns):
        # Interfaces
        for w in self.iface_frame.winfo_children(): w.destroy()
        items = []
        for iface in ifaces[:8]:
            items.extend([
                (f"{iface['name']} IPv4", iface['ip4'], C['am']),
                (f"{iface['name']} MAC",  iface['mac']),
            ])
        InfoGrid(self.iface_frame, items, columns=4).pack(fill='x')

        # Public identity
        for w in self.pub_grid_frame.winfo_children(): w.destroy()
        InfoGrid(self.pub_grid_frame, [
            ('PUBLIC IP',  ipinfo.get('ip','—'),           C['wn']),
            ('ISP',        ipinfo.get('org','—')),
            ('COUNTRY',    ipinfo.get('country_name','—')),
            ('CITY',       ipinfo.get('city','—')),
            ('REGION',     ipinfo.get('region','—')),
            ('TIMEZONE',   ipinfo.get('timezone','—')),
            ('ASN',        ipinfo.get('asn','—')),
            ('LATITUDE',   str(ipinfo.get('latitude','—'))),
            ('LONGITUDE',  str(ipinfo.get('longitude','—'))),
        ], columns=3).pack(fill='x')

        # Active connections
        for w in self.conn_frame.winfo_children(): w.destroy()
        if conns:
            for conn in conns[:15]:
                row = ctk.CTkFrame(self.conn_frame, fg_color=C['sf'],
                                    border_color=C['br'], border_width=1,
                                    corner_radius=6)
                row.pack(fill='x', pady=2)
                ctk.CTkLabel(row, text=conn['local'], font=MONO_SM,
                             text_color=C['ac']).pack(side='left', padx=8, pady=6)
                ctk.CTkLabel(row, text='→', font=MONO_SM,
                             text_color=C['mu']).pack(side='left')
                ctk.CTkLabel(row, text=conn['remote'], font=MONO_SM,
                             text_color=C['am']).pack(side='left', padx=8)
                ctk.CTkLabel(row, text=conn['process'], font=('Courier',8),
                             text_color=C['mu']).pack(side='right', padx=8)
        else:
            ctk.CTkLabel(self.conn_frame, text="No active connections found",
                         font=MONO_SM, text_color=C['mu']).pack(pady=8)

    def _start_ping_loop(self):
        if self._ping_running: return
        self._ping_running = True
        threading.Thread(target=self._ping_worker, daemon=True).start()

    def _ping_worker(self):
        while self._ping_running:
            ms = ping('1.1.1.1', 1)
            if ms is not None:
                self._ping_history = self._ping_history[-49:] + [ms]
                self.after(0, self._update_ping_graph)
            time.sleep(2)

    def _update_ping_graph(self):
        data = self._ping_history
        if not data: return

        last  = data[-1]
        col   = C['ok'] if last < 80 else C['am'] if last < 200 else C['wn']
        self.ping_val.configure(text=f"{last:.0f}ms", text_color=col)

        mn = min(data)
        mx = max(data)
        avg = sum(data)/len(data)
        self.ping_min.configure(text=f"MIN: {mn:.0f}ms")
        self.ping_avg.configure(text=f"AVG: {avg:.0f}ms")
        self.ping_max.configure(text=f"MAX: {mx:.0f}ms")

        # Draw graph
        c = self.ping_canvas
        c.delete('all')
        w = c.winfo_width() or 600
        h = 80
        seg = w / max(len(data)-1, 1)
        peak = max(data) or 1
        # Grid lines
        for frac in [0.25, 0.5, 0.75]:
            y = h - frac * h
            c.create_line(0, y, w, y, fill=C['br'], dash=(2,4))
        # Filled area
        pts = []
        for i, v in enumerate(data):
            pts.extend([i*seg, h - (v/peak)*h*0.9])
        if len(pts) >= 4:
            c.create_line(*pts, fill=col, width=2, smooth=True)
        # Current dot
        if data:
            lx = (len(data)-1)*seg
            ly = h - (data[-1]/peak)*h*0.9
            c.create_oval(lx-4, ly-4, lx+4, ly+4, fill=col, outline='')

    def _run_speed(self):
        self.speed_btn.configure(state='disabled', text='TESTING...')
        for attr in ['spd_dl','spd_ul','spd_ping','spd_grade']:
            getattr(self, attr).configure(text='—', text_color=C['mu'])
        threading.Thread(target=self._do_speed, daemon=True).start()

    def _do_speed(self):
        # Real ping
        ms = ping('1.1.1.1', 3)
        self.after(0, lambda: self.spd_ping.configure(
            text=f"{ms:.0f}" if ms else 'ERR',
            text_color=C['am'] if ms else C['wn']
        ))

        # Try speedtest-cli
        dl = ul = None
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            dl = st.download() / 1e6
            ul = st.upload() / 1e6
        except Exception:
            # Fallback: timed fetch
            try:
                import urllib.request, time
                url = 'http://speedtest.ftp.otenet.gr/files/test1Mb.db'
                t0 = time.time()
                urllib.request.urlretrieve(url, '/dev/null')
                elapsed = time.time() - t0
                dl = (1 * 8) / elapsed  # 1MB file → Mbps
            except Exception:
                pass

        grade = '—'
        if dl:
            grade = 'A+' if dl>50 else 'A' if dl>25 else 'B' if dl>10 else 'C' if dl>5 else 'D'

        self.after(0, lambda: (
            self.spd_dl.configure(text=f"{dl:.1f}" if dl else 'N/A',
                                  text_color=C['ac'] if dl else C['wn']),
            self.spd_ul.configure(text=f"{ul:.1f}" if ul else 'N/A',
                                  text_color=C['bl'] if ul else C['wn']),
            self.spd_grade.configure(text=grade,
                                      text_color=C['ok'] if grade in ('A+','A') else C['am']),
            self.speed_btn.configure(state='normal', text='↺  RETEST'),
        ))
