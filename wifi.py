"""Wi-Fi Scanner Screen — real nmcli/iwlist scanning"""
import tkinter as tk
import customtkinter as ctk
import threading
from utils import C, MONO, MONO_SM, get_wifi_networks, get_current_wifi, get_wifi_interface, get_network_interfaces
from widgets import ScrollableFrame, Card, SectionHeader, InfoGrid, ResultBox, Btn


def sig_color(sig):
    if sig >= 75: return C['ok']
    if sig >= 50: return C['ac']
    if sig >= 25: return C['am']
    return C['wn']

def sec_color(sec):
    sec = sec.upper()
    if 'WPA3' in sec: return C['ok']
    if 'WPA2' in sec: return C['ac']
    if 'WPA'  in sec: return C['am']
    if 'WEP'  in sec: return C['wn']
    return C['wn']  # OPEN


class WifiScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C['bg'], corner_radius=0)
        self.app = app
        self._built = False

    def on_focus(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=C['sf'], height=48, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text="📶  WI-FI SCANNER", font=('Courier', 13, 'bold'),
                     text_color=C['ac']).pack(side='left', padx=16)
        self.status_lbl = ctk.CTkLabel(hdr, text="Idle", font=MONO_SM,
                                        text_color=C['mu'])
        self.status_lbl.pack(side='left', padx=8)
        self.scan_btn = Btn(hdr, "📡  SCAN NOW", command=self._scan, width=130)
        self.scan_btn.pack(side='right', padx=12, pady=6)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll

        # Current connection
        SectionHeader(body, '01', 'CURRENT CONNECTION').pack(
            fill='x', padx=14, pady=(14, 4))
        self.curr_card = Card(body)
        self.curr_card.pack(fill='x', padx=14, pady=(0, 6))
        self.curr_info = InfoGrid(self.curr_card, [
            ('STATUS', '—'), ('INTERFACE', '—'), ('SSID', '—'), ('LOCAL IP', '—')
        ], columns=4)
        self.curr_info.pack(fill='x', padx=4, pady=4)

        # Scan results container
        SectionHeader(body, '02', 'NEARBY NETWORKS').pack(
            fill='x', padx=14, pady=(10, 4))
        self.results_frame = ctk.CTkFrame(body, fg_color='transparent')
        self.results_frame.pack(fill='x', padx=14)

        self.hint = ctk.CTkLabel(self.results_frame,
                                  text="Tap SCAN NOW to discover all Wi-Fi networks in range.\n"
                                       "Uses nmcli (NetworkManager) for real live scanning.",
                                  font=MONO_SM, text_color=C['mu'])
        self.hint.pack(pady=20)

        # Load current connection immediately
        threading.Thread(target=self._load_current, daemon=True).start()

    def _load_current(self):
        iface    = get_wifi_interface()
        ssid     = get_current_wifi()
        ifaces   = get_network_interfaces()
        local_ip = next((i['ip4'] for i in ifaces if i['ip4'] != '—' and not i['ip4'].startswith('127')), '—')
        self.after(0, self._render_current, iface, ssid, local_ip)

    def _render_current(self, iface, ssid, local_ip):
        self.curr_info.destroy()
        connected = bool(ssid)
        self.curr_info = InfoGrid(self.curr_card, [
            ('STATUS',    'CONNECTED' if connected else 'DISCONNECTED',
             C['ok'] if connected else C['wn']),
            ('INTERFACE', iface or '—', C['ac']),
            ('SSID',      ssid or 'Unknown', C['ok'] if connected else C['mu']),
            ('LOCAL IP',  local_ip, C['am']),
        ], columns=4)
        self.curr_info.pack(fill='x', padx=4, pady=4)

    def _scan(self):
        self.scan_btn.configure(state='disabled', text='SCANNING...')
        self.status_lbl.configure(text='Scanning...', text_color=C['ac'])
        self.hint.destroy() if hasattr(self, 'hint') else None
        # Clear old results
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.results_frame, text="⟳  Scanning nearby networks...",
                     font=MONO_SM, text_color=C['ac']).pack(pady=16)
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        networks = get_wifi_networks()
        self.after(0, self._render_networks, networks)

    def _render_networks(self, networks):
        for w in self.results_frame.winfo_children():
            w.destroy()

        if not networks:
            ResultBox(self.results_frame, 'warn',
                      '⚠ NO NETWORKS FOUND',
                      'Make sure Wi-Fi is enabled and NetworkManager is running.\n'
                      'Try: sudo nmcli device wifi rescan'
                      ).pack(fill='x', pady=4)
            self.scan_btn.configure(state='normal', text='📡  SCAN NOW')
            self.status_lbl.configure(text='No networks found', text_color=C['wn'])
            return

        open_nets = [n for n in networks if n['security'].upper() == 'OPEN']
        wep_nets  = [n for n in networks if 'WEP' in n['security'].upper()]

        # Summary card
        summary = Card(self.results_frame,
                       accent=C['wn'] if open_nets else C['ok'])
        summary.pack(fill='x', pady=(0, 8))
        InfoGrid(summary, [
            ('FOUND',    len(networks),        C['ac']),
            ('OPEN',     len(open_nets),        C['wn'] if open_nets else C['ok']),
            ('WEP',      len(wep_nets),         C['wn'] if wep_nets  else C['ok']),
            ('SECURE',   len(networks) - len(open_nets) - len(wep_nets), C['ok']),
        ], columns=4).pack(fill='x', padx=4, pady=4)

        if open_nets:
            ResultBox(summary, 'warn',
                      f'⚠ {len(open_nets)} OPEN NETWORK(S) IN RANGE',
                      'Unencrypted networks visible. Avoid banking or sensitive logins on these.'
                      ).pack(fill='x', padx=8, pady=(0, 8))

        # Network rows
        current_ssid = get_current_wifi()
        for net in networks:
            self._make_net_row(net, net['ssid'] == current_ssid)

        self.scan_btn.configure(state='normal', text='↺  RESCAN')
        self.status_lbl.configure(
            text=f"Found {len(networks)} networks", text_color=C['ok'])

    def _make_net_row(self, net, is_current):
        sec = net['security'].upper()
        col = sec_color(sec)
        sig = net['signal']
        sc  = sig_color(sig)

        row = ctk.CTkFrame(self.results_frame, fg_color=C['sf'],
                            border_color=C['ok'] if is_current else col,
                            border_width=1, corner_radius=8)
        row.pack(fill='x', pady=3)

        left = ctk.CTkFrame(row, fg_color='transparent')
        left.pack(side='left', padx=12, pady=8)

        icon = '🔓' if sec == 'OPEN' else '⚠️' if 'WEP' in sec else '🔒'
        ctk.CTkLabel(left, text=icon, font=('Courier', 20)).pack()

        mid = ctk.CTkFrame(row, fg_color='transparent')
        mid.pack(side='left', fill='both', expand=True, padx=4, pady=8)

        ssid_row = ctk.CTkFrame(mid, fg_color='transparent')
        ssid_row.pack(fill='x')
        ctk.CTkLabel(ssid_row, text=net['ssid'],
                     font=('Courier', 11, 'bold'),
                     text_color=C['ok'] if is_current else C['tx']
                     ).pack(side='left')
        if is_current:
            ctk.CTkLabel(ssid_row, text="  ✓ CONNECTED",
                         font=('Courier', 8), text_color=C['ok']).pack(side='left')

        ctk.CTkLabel(mid,
                     text=f"{sec}  ·  CH {net['channel']}  ·  {net['freq']}  ·  BSSID: {net['bssid']}",
                     font=('Courier', 8), text_color=C['mu']).pack(anchor='w')

        if sec == 'OPEN':
            ctk.CTkLabel(mid, text="⚠ No encryption — avoid sensitive activity",
                         font=('Courier', 8), text_color=C['wn']).pack(anchor='w')
        elif 'WEP' in sec:
            ctk.CTkLabel(mid, text="⚠ WEP is broken — treat as open network",
                         font=('Courier', 8), text_color=C['wn']).pack(anchor='w')

        right = ctk.CTkFrame(row, fg_color='transparent')
        right.pack(side='right', padx=12, pady=8)

        # Security badge
        badge = ctk.CTkFrame(right, fg_color=col + '22',
                              border_color=col, border_width=1, corner_radius=3)
        badge.pack(pady=(0, 4))
        ctk.CTkLabel(badge, text=sec[:8],
                     font=('Courier', 7, 'bold'),
                     text_color=col).pack(padx=6, pady=2)

        # Signal bars
        bar_frame = ctk.CTkFrame(right, fg_color='transparent')
        bar_frame.pack()
        bars = 4 if sig >= 75 else 3 if sig >= 50 else 2 if sig >= 25 else 1
        for b in range(4):
            h = (b + 1) * 5 + 3
            c_col = sc if b < bars else C['br']
            ctk.CTkFrame(bar_frame, width=5, height=h,
                         fg_color=c_col, corner_radius=1
                         ).pack(side='left', padx=1, anchor='s')

        ctk.CTkLabel(right, text=f"{sig}%", font=('Courier', 8),
                     text_color=sc).pack()
