"""Reusable GUI widgets for Mint Scan Linux"""
import tkinter as tk
import customtkinter as ctk
from src.utils import C, MONO, MONO_SM, MONO_LG


class ScrollableFrame(ctk.CTkScrollableFrame):
    """A dark-themed scrollable container."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=C['bg'],
                         scrollbar_button_color=C['br'],
                         scrollbar_button_hover_color=C['br2'], **kwargs)


class Card(ctk.CTkFrame):
    def __init__(self, parent, accent=None, **kwargs):
        super().__init__(parent,
                         fg_color=C['sf'],
                         border_color=accent or C['br'],
                         border_width=1,
                         corner_radius=8,
                         **kwargs)


class SectionHeader(ctk.CTkFrame):
    def __init__(self, parent, num, title, **kwargs):
        super().__init__(parent, fg_color='transparent', **kwargs)
        ctk.CTkLabel(self, text=f"[{num}]", font=MONO_SM,
                     text_color=C['ac']).pack(side='left', padx=(0, 6))
        ctk.CTkLabel(self, text=title, font=MONO_SM,
                     text_color=C['mu2']).pack(side='left')
        ctk.CTkFrame(self, height=1, fg_color=C['br']).pack(
            side='left', fill='x', expand=True, padx=(8, 0))


class InfoGrid(ctk.CTkFrame):
    """A 2-column grid of label/value pairs."""
    def __init__(self, parent, items, columns=2, **kwargs):
        super().__init__(parent, fg_color='transparent', **kwargs)
        for i, item in enumerate(items):
            label = item[0]
            value = str(item[1]) if item[1] is not None else '—'
            color = item[2] if len(item) > 2 else C['tx']
            col = i % columns
            row = i // columns
            cell = ctk.CTkFrame(self, fg_color=C['sf'],
                                border_color=C['br'], border_width=1,
                                corner_radius=6)
            cell.grid(row=row, column=col, padx=3, pady=3, sticky='nsew')
            ctk.CTkLabel(cell, text=label, font=('Courier', 7),
                         text_color=C['mu']).pack(anchor='w', padx=8, pady=(6,0))
            ctk.CTkLabel(cell, text=value, font=MONO_SM,
                         text_color=color, wraplength=180).pack(
                             anchor='w', padx=8, pady=(0,6))
        for c in range(columns):
            self.grid_columnconfigure(c, weight=1)


class ResultBox(ctk.CTkFrame):
    """Coloured result/alert box."""
    def __init__(self, parent, rtype='ok', title='', body='', **kwargs):
        col = {'ok': C['ok'], 'warn': C['wn'], 'info': C['bl'],
               'med': C['am']}.get(rtype, C['am'])
        super().__init__(parent, fg_color=col + '18',
                         border_color=col, border_width=1,
                         corner_radius=8, **kwargs)
        ctk.CTkLabel(self, text=title, font=('Courier', 10, 'bold'),
                     text_color=col).pack(anchor='w', padx=10, pady=(8,2))
        if body:
            ctk.CTkLabel(self, text=body, font=MONO_SM,
                         text_color=C['mu'], wraplength=600,
                         justify='left').pack(anchor='w', padx=10, pady=(0,8))


class Btn(ctk.CTkButton):
    def __init__(self, parent, label, command=None, variant='primary',
                 width=140, **kwargs):
        colors = {
            'primary': (C['ac'] + '28', C['ac'],  C['ac']),
            'danger':  (C['wn'] + '28', C['wn'],  C['wn']),
            'warning': (C['am'] + '28', C['am'],  C['am']),
            'success': (C['ok'] + '28', C['ok'],  C['ok']),
            'ghost':   ('transparent',  C['br2'], C['mu']),
            'blue':    (C['bl'] + '28', C['bl'],  C['bl']),
        }.get(variant, (C['ac'] + '28', C['ac'], C['ac']))
        super().__init__(
            parent, text=label,
            font=('Courier', 9),
            fg_color=colors[0],
            border_color=colors[1],
            border_width=1,
            text_color=colors[2],
            hover_color=colors[1] + '44',
            corner_radius=4,
            height=36,
            width=width,
            command=command,
            **kwargs
        )


class LiveBadge(ctk.CTkFrame):
    """Pulsing LIVE indicator."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color='transparent', **kwargs)
        self._dot = ctk.CTkLabel(self, text='●', font=('Courier', 10),
                                  text_color=C['ok'])
        self._dot.pack(side='left')
        ctk.CTkLabel(self, text='LIVE', font=('Courier', 8),
                     text_color=C['ok']).pack(side='left', padx=2)
        self._on = True
        self._pulse()

    def _pulse(self):
        self._on = not self._on
        self._dot.configure(text_color=C['ok'] if self._on else C['mu'])
        self.after(800, self._pulse)


class PortBar(ctk.CTkFrame):
    """Visual port risk bar."""
    def __init__(self, parent, port, proto, state, process, **kwargs):
        risk_ports = {
            '21': 'FTP', '22': 'SSH', '23': 'Telnet', '25': 'SMTP',
            '80': 'HTTP', '443': 'HTTPS', '3306': 'MySQL', '5432': 'PostgreSQL',
            '6379': 'Redis', '27017': 'MongoDB', '8080': 'HTTP-Alt',
            '4444': 'Metasploit', '1337': 'Suspicious',
        }
        col = C['wn'] if port in ['23','4444','1337'] else \
              C['am'] if port in ['21','25','3306','27017','6379'] else \
              C['ac'] if port in ['22','443'] else C['mu']
        super().__init__(parent, fg_color=C['sf'],
                         border_color=col, border_width=1,
                         corner_radius=6, **kwargs)
        top = ctk.CTkFrame(self, fg_color='transparent')
        top.pack(fill='x', padx=10, pady=(8,2))
        ctk.CTkLabel(top, text=f":{port}", font=('Courier', 12, 'bold'),
                     text_color=col).pack(side='left')
        service = risk_ports.get(port, 'Unknown')
        ctk.CTkLabel(top, text=f"  {service}", font=MONO_SM,
                     text_color=C['tx']).pack(side='left')
        ctk.CTkLabel(top, text=proto, font=('Courier', 8),
                     text_color=C['mu']).pack(side='right')
        ctk.CTkLabel(self, text=f"Process: {process}  State: {state}",
                     font=('Courier', 8), text_color=C['mu']
                     ).pack(anchor='w', padx=10, pady=(0,6))
