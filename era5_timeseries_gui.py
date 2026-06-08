import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import calendar
import csv
import json
import math
import os
import queue
import sys
import threading
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ERA5_DATASET = 'reanalysis-era5-single-levels-timeseries'
DEFAULT_CDS_URL = 'https://cds.climate.copernicus.eu/api'
TIME_DIMS = ['time', 'date', 'valid_time']
OSM_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
MAP_TILE_SIZE = 256
MAP_MIN_ZOOM = 1
MAP_MAX_LOCAL_SPAN_DEGREES = 3.0
WEB_MERCATOR_MAX_LAT = 85.05112878
ERA5_GRID_DEGREES = 0.25

ERA5_VARIABLE_OPTIONS = [
    {
        'request': 'mean_sea_level_pressure',
        'label': 'Air pressure',
        'short': 'msl',
        'source': 'atmospheric',
        'default': True,
    },
    {
        'request': 'total_precipitation',
        'label': 'Precipitation',
        'short': 'tp',
        'source': 'atmospheric',
        'default': True,
    },
    {
        'request': '10m_u_component_of_wind',
        'label': '10m U wind',
        'short': 'u10',
        'source': 'atmospheric',
        'default': True,
    },
    {
        'request': '10m_v_component_of_wind',
        'label': '10m V wind',
        'short': 'v10',
        'source': 'atmospheric',
        'default': True,
    },
    {
        'request': 'significant_height_of_combined_wind_waves_and_swell',
        'label': 'Wave height',
        'short': 'swh',
        'source': 'oceanic',
        'default': True,
    },
    {
        'request': 'mean_wave_period',
        'label': 'Wave period',
        'short': 'mwp',
        'source': 'oceanic',
        'default': True,
    },
    {
        'request': 'mean_wave_direction',
        'label': 'Wave direction',
        'short': 'mwd',
        'source': 'oceanic',
        'default': True,
    },
    {
        'request': '2m_temperature',
        'label': '2m temperature',
        'short': 't2m',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': '2m_dewpoint_temperature',
        'label': '2m dewpoint',
        'short': 'd2m',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'surface_pressure',
        'label': 'Surface pressure',
        'short': 'sp',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'skin_temperature',
        'label': 'Skin temperature',
        'short': 'skt',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'sea_surface_temperature',
        'label': 'Sea temperature',
        'short': 'sst',
        'source': 'oceanic',
        'default': False,
    },
    {
        'request': '10m_wind_gust_since_previous_post_processing',
        'label': '10m wind gust',
        'short': 'fg10',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': '100m_u_component_of_wind',
        'label': '100m U wind',
        'short': 'u100',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': '100m_v_component_of_wind',
        'label': '100m V wind',
        'short': 'v100',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'surface_solar_radiation_downwards',
        'label': 'Solar radiation',
        'short': 'ssrd',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'total_sky_direct_solar_radiation_at_surface',
        'label': 'Direct solar radiation',
        'short': 'fdir',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'surface_thermal_radiation_downwards',
        'label': 'Thermal radiation',
        'short': 'strd',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'boundary_layer_height',
        'label': 'Boundary layer height',
        'short': 'blh',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'cloud_base_height',
        'label': 'Cloud base height',
        'short': 'cbh',
        'source': 'atmospheric',
        'default': False,
    },
    {
        'request': 'total_cloud_cover',
        'label': 'Cloud cover',
        'short': 'tcc',
        'source': 'atmospheric',
        'default': False,
    },
]

REQUEST_TO_SOURCE = {item['request']: item['source'] for item in ERA5_VARIABLE_OPTIONS}
SHORT_TO_SOURCE = {item['short']: item['source'] for item in ERA5_VARIABLE_OPTIONS}
SECTOR_LABELS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
SECTOR_WIDTH_DEGREES = 22.5


class ERA5TimeSeriesApp:
    def __init__(self, master):
        self.master = master
        master.title('ERA5 Time Series Viewer')

        self.atm_ds = None
        self.ocn_ds = None
        self.current_source = tk.StringVar(value='atmospheric')
        self.selected_variable = tk.StringVar(value='')
        self.full_series = None
        self.current_var_name = None
        self.plot_available = False
        self.download_queue = queue.Queue()
        self.download_thread = None
        self.coord_update_pending = False

        settings = self.load_settings()
        default_end = (datetime.now(timezone.utc).date() - timedelta(days=7)).strftime('%Y-%m-%d')
        self.latitude_var = tk.StringVar(value=settings.get('latitude', '0.0000'))
        self.longitude_var = tk.StringVar(value=settings.get('longitude', '0.0000'))
        self.start_date_var = tk.StringVar(value=settings.get('start_date', '1940-01-01'))
        self.end_date_var = tk.StringVar(value=settings.get('end_date', default_end))
        self.download_dir_var = tk.StringVar(value=settings.get('download_dir', str(self.default_download_dir())))
        self.cds_url_var = tk.StringVar(value=settings.get('cds_url', DEFAULT_CDS_URL))
        self.cds_key_var = tk.StringVar(value=settings.get('cds_key', ''))
        self.show_key_var = tk.BooleanVar(value=False)
        self.analysis_start_date_var = tk.StringVar(value='')
        self.analysis_end_date_var = tk.StringVar(value='')
        self.map_tile_images = []
        self.map_tile_error_shown = False
        self.map_center_lat, self.map_center_lon = self.initial_map_center()
        self.ssl_configured = False
        self.configure_ssl_certificates()

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill='both', expand=True)
        self.download_tab = tk.Frame(self.notebook)
        self.analysis_tab = tk.Frame(self.notebook)
        self.notebook.add(self.download_tab, text='ERA5 request')
        self.notebook.add(self.analysis_tab, text='Data analysis')

        self.create_cds_download_panel(self.download_tab)
        analysis_parent = self.analysis_tab

        top_frame = tk.Frame(analysis_parent)
        top_frame.pack(fill='x', padx=8, pady=(8, 4))
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=0)
        top_frame.columnconfigure(2, weight=1)

        controls = tk.Frame(top_frame)
        controls.grid(row=0, column=0, sticky='nsew', padx=(0, 14))

        self.atm_path_label = tk.Label(controls, text='Atmospheric file: not loaded', anchor='w')
        self.atm_path_label.grid(row=0, column=0, columnspan=3, sticky='we', pady=2)
        self.ocn_path_label = tk.Label(controls, text='Oceanic file: not loaded', anchor='w')
        self.ocn_path_label.grid(row=1, column=0, columnspan=3, sticky='we', pady=2)

        atm_btn = tk.Button(controls, text='Select atmospheric file', command=lambda: self.load_file('atmospheric'))
        atm_btn.grid(row=2, column=0, padx=4, pady=4, sticky='we')
        ocn_btn = tk.Button(controls, text='Select oceanic file', command=lambda: self.load_file('oceanic'))
        ocn_btn.grid(row=2, column=1, padx=4, pady=4, sticky='we')

        source_frame = tk.LabelFrame(controls, text='Data source')
        source_frame.grid(row=2, column=2, padx=4, pady=4, sticky='we')
        atm_radio = tk.Radiobutton(source_frame, text='Atmospheric', variable=self.current_source, value='atmospheric', command=self.update_variable_menu)
        ocn_radio = tk.Radiobutton(source_frame, text='Oceanic', variable=self.current_source, value='oceanic', command=self.update_variable_menu)
        atm_radio.pack(anchor='w', padx=4)
        ocn_radio.pack(anchor='w', padx=4)

        date_frame = tk.LabelFrame(top_frame, text='Analysis period')
        date_frame.grid(row=0, column=1, sticky='ns', padx=14)
        tk.Label(date_frame, text='Start Date').grid(row=0, column=0, sticky='e', padx=(8, 4), pady=5)
        self.analysis_start_entry = tk.Entry(date_frame, textvariable=self.analysis_start_date_var, width=12)
        self.analysis_start_entry.grid(row=0, column=1, sticky='w', pady=5)
        tk.Button(date_frame, text='v', width=2, command=lambda: self.open_date_picker(self.analysis_start_date_var)).grid(row=0, column=2, padx=(2, 8), pady=5)
        tk.Label(date_frame, text='End Date').grid(row=1, column=0, sticky='e', padx=(8, 4), pady=5)
        self.analysis_end_entry = tk.Entry(date_frame, textvariable=self.analysis_end_date_var, width=12)
        self.analysis_end_entry.grid(row=1, column=1, sticky='w', pady=5)
        tk.Button(date_frame, text='v', width=2, command=lambda: self.open_date_picker(self.analysis_end_date_var)).grid(row=1, column=2, padx=(2, 8), pady=5)
        tk.Button(date_frame, text='Apply dates', command=self.apply_analysis_dates).grid(row=2, column=0, columnspan=3, sticky='we', padx=8, pady=(2, 8))

        stats_frame = tk.LabelFrame(top_frame, text='Statistics')
        stats_frame.grid(row=0, column=2, sticky='nsew', padx=(14, 0))
        stats_frame.rowconfigure(0, weight=1)
        stats_frame.columnconfigure(0, weight=1)
        self.stats_text = tk.Text(stats_frame, height=6, width=56, wrap='word')
        self.stats_text.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        stats_scroll = tk.Scrollbar(stats_frame, orient='vertical', command=self.stats_text.yview)
        stats_scroll.grid(row=0, column=1, sticky='ns', pady=4)
        self.stats_text.config(yscrollcommand=stats_scroll.set)

        variable_frame = tk.Frame(analysis_parent)
        variable_frame.pack(fill='x', padx=8, pady=4)
        tk.Label(variable_frame, text='Select variable:').grid(row=0, column=0, sticky='w')
        self.variable_menu = tk.OptionMenu(variable_frame, self.selected_variable, '')
        self.variable_menu.grid(row=0, column=1, sticky='we', padx=4)
        variable_frame.columnconfigure(1, weight=1)

        action_frame = tk.Frame(analysis_parent)
        action_frame.pack(fill='x', padx=8, pady=4)
        plot_btn = tk.Button(action_frame, text='Plot time series', command=self.plot_time_series)
        plot_btn.pack(side='left', padx=4)
        stats_btn = tk.Button(action_frame, text='Show statistics', command=self.update_current_stats)
        stats_btn.pack(side='left', padx=4)
        save_plot_btn = tk.Button(action_frame, text='Save plot', command=self.save_plot)
        save_plot_btn.pack(side='left', padx=4)
        save_data_btn = tk.Button(action_frame, text='Save data', command=self.save_data)
        save_data_btn.pack(side='left', padx=4)
        wave_rose_btn = tk.Button(action_frame, text='Wave Rose', command=self.plot_wave_rose)
        wave_rose_btn.pack(side='left', padx=4)
        wind_rose_btn = tk.Button(action_frame, text='Wind Rose', command=self.plot_wind_rose)
        wind_rose_btn.pack(side='left', padx=4)
        directional_btn = tk.Button(action_frame, text='Directional Data', command=self.export_directional_data)
        directional_btn.pack(side='left', padx=4)

        output_frame = tk.Frame(analysis_parent)
        output_frame.pack(fill='both', padx=8, pady=4, expand=True)

        self.figure = Figure(figsize=(7, 3.5), tight_layout=True)
        self.ax = self.figure.add_subplot(111)
        self.ax.callbacks.connect('xlim_changed', self.on_xlim_changed)
        self.canvas = FigureCanvasTkAgg(self.figure, master=output_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.info_label = tk.Label(analysis_parent, text='Load both atmospheric and oceanic ERA5 .nc files, then select a source and variable.', anchor='w')
        self.info_label.pack(fill='x', padx=8, pady=2)

    def settings_path(self):
        appdata = os.environ.get('APPDATA')
        base_dir = Path(appdata) if appdata else Path.home()
        return base_dir / 'ERA5_TimeSeries_Viewer' / 'settings.json'

    def default_download_dir(self):
        documents = Path.home() / 'Documents'
        if documents.exists():
            return documents / 'ERA5_Data'
        return Path.home() / 'ERA5_Data'

    def load_settings(self):
        path = self.settings_path()
        if not path.exists():
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as settings_file:
                data = json.load(settings_file)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save_settings(self, silent=False):
        settings = {
            'latitude': self.latitude_var.get().strip(),
            'longitude': self.longitude_var.get().strip(),
            'start_date': self.start_date_var.get().strip(),
            'end_date': self.end_date_var.get().strip(),
            'download_dir': self.download_dir_var.get().strip(),
            'cds_url': self.cds_url_var.get().strip() or DEFAULT_CDS_URL,
            'cds_key': self.cds_key_var.get().strip(),
        }
        path = self.settings_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as settings_file:
                json.dump(settings, settings_file, indent=2)
            if not silent:
                messagebox.showinfo('Settings saved', f'Settings saved to {path}')
        except Exception as exc:
            if not silent:
                messagebox.showerror('Settings error', f'Could not save settings:\n{exc}')

    def parse_calendar_date(self, text):
        try:
            return datetime.strptime(str(text).strip(), '%Y-%m-%d').date()
        except Exception:
            return None

    def open_date_picker(self, target_var):
        selected = self.parse_calendar_date(target_var.get())
        if selected is None:
            selected = datetime.now(timezone.utc).date()

        picker = tk.Toplevel(self.master)
        picker.title('Select date')
        picker.transient(self.master)
        picker.resizable(False, False)

        state = {'year': selected.year, 'month': selected.month}
        nav_frame = tk.Frame(picker)
        nav_frame.pack(fill='x', padx=6, pady=6)
        nav_frame.columnconfigure(1, weight=1)
        tk.Button(nav_frame, text='<', width=3, command=lambda: shift_month(-1)).grid(row=0, column=0, sticky='w')
        title_label = tk.Label(nav_frame, width=18)
        title_label.grid(row=0, column=1, sticky='we')
        tk.Button(nav_frame, text='>', width=3, command=lambda: shift_month(1)).grid(row=0, column=2, sticky='e')
        days_frame = tk.Frame(picker)
        days_frame.pack(padx=6, pady=(0, 6))

        def shift_month(delta):
            month = state['month'] + delta
            year = state['year']
            if month < 1:
                month = 12
                year -= 1
            elif month > 12:
                month = 1
                year += 1
            state['year'] = year
            state['month'] = month
            redraw_calendar()

        def choose_day(day):
            target_var.set(f'{state["year"]:04d}-{state["month"]:02d}-{day:02d}')
            picker.destroy()

        def redraw_calendar():
            for child in days_frame.winfo_children():
                child.destroy()

            year = state['year']
            month = state['month']
            title_label.config(text=f'{calendar.month_name[month]} {year}')
            for col, label in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
                tk.Label(days_frame, text=label, width=4).grid(row=0, column=col, padx=1, pady=1)

            cal = calendar.Calendar(firstweekday=0)
            for row, week in enumerate(cal.monthdayscalendar(year, month), start=1):
                for col, day in enumerate(week):
                    if day == 0:
                        tk.Label(days_frame, text='', width=4).grid(row=row, column=col, padx=1, pady=1)
                    else:
                        tk.Button(days_frame, text=str(day), width=4, command=lambda value=day: choose_day(value)).grid(row=row, column=col, padx=1, pady=1)

        redraw_calendar()

    def set_stats_text(self, text):
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert(tk.END, text)

    def get_dataset_time_bounds(self, ds):
        if ds is None:
            return None

        for time_dim in TIME_DIMS:
            if time_dim not in ds.coords and time_dim not in ds.variables:
                continue
            try:
                time_index = pd.DatetimeIndex(pd.to_datetime(ds[time_dim].values)).dropna()
            except Exception:
                continue
            if len(time_index) > 0:
                return time_index.min(), time_index.max()
        return None

    def get_loaded_time_bounds(self):
        bounds = []
        for ds in [self.atm_ds, self.ocn_ds]:
            ds_bounds = self.get_dataset_time_bounds(ds)
            if ds_bounds is not None:
                bounds.append(ds_bounds)

        if not bounds:
            return None
        starts, ends = zip(*bounds)
        return min(starts), max(ends)

    def set_analysis_date_range_from_loaded_data(self):
        bounds = self.get_loaded_time_bounds()
        if bounds is None:
            return

        start, end = bounds
        self.analysis_start_date_var.set(pd.Timestamp(start).strftime('%Y-%m-%d'))
        self.analysis_end_date_var.set(pd.Timestamp(end).strftime('%Y-%m-%d'))

    def get_analysis_date_range(self, show_error=True):
        if not self.analysis_start_date_var.get().strip() or not self.analysis_end_date_var.get().strip():
            self.set_analysis_date_range_from_loaded_data()

        start_text = self.analysis_start_date_var.get().strip()
        end_text = self.analysis_end_date_var.get().strip()
        try:
            start = pd.Timestamp(pd.to_datetime(start_text)).normalize()
            end = pd.Timestamp(pd.to_datetime(end_text)).normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        except Exception:
            if show_error:
                messagebox.showerror('Date range', 'Use dates in YYYY-MM-DD format for the analysis period.')
            return None

        if end < start:
            if show_error:
                messagebox.showerror('Date range', 'End Date must be on or after Start Date.')
            return None
        return start, end

    def format_analysis_period(self, date_range=None):
        if date_range is None:
            date_range = self.get_analysis_date_range(show_error=False)
        if date_range is None:
            return 'selected dates'
        return f'{date_range[0].strftime("%Y-%m-%d")} to {date_range[1].strftime("%Y-%m-%d")}'

    def filter_series_by_analysis_dates(self, series, show_error=True):
        if series is None or series.empty:
            return series
        date_range = self.get_analysis_date_range(show_error=show_error)
        if date_range is None:
            return series.iloc[0:0]

        start, end = date_range
        index = pd.DatetimeIndex(pd.to_datetime(series.index))
        subset = series.loc[(index >= start) & (index <= end)]
        if subset.empty and show_error:
            messagebox.showwarning('Date range', f'No records were found from {self.format_analysis_period(date_range)}.')
        return subset

    def filter_dataframe_by_analysis_dates(self, df, show_error=True):
        if df is None or df.empty:
            return df
        date_range = self.get_analysis_date_range(show_error=show_error)
        if date_range is None:
            return df.iloc[0:0]

        start, end = date_range
        index = pd.DatetimeIndex(pd.to_datetime(df.index))
        subset = df.loc[(index >= start) & (index <= end)]
        if subset.empty and show_error:
            messagebox.showwarning('Date range', f'No records were found from {self.format_analysis_period(date_range)}.')
        return subset

    def apply_analysis_dates(self):
        date_range = self.get_analysis_date_range(show_error=True)
        if date_range is None:
            return

        if self.full_series is None:
            self.info_label.config(text=f'Analysis period set to {self.format_analysis_period(date_range)}.')
            return

        subset = self.filter_series_by_analysis_dates(self.full_series, show_error=True)
        if subset is None or subset.empty:
            return

        self.update_plot(subset)
        if self.current_var_name:
            self.show_statistics(subset, self.current_var_name)
        self.info_label.config(text=f'Plot and statistics use {self.format_analysis_period(date_range)}.')

    def create_cds_download_panel(self, master):
        cds_frame = tk.LabelFrame(master, text='Download ERA5 from Copernicus CDS')
        cds_frame.pack(fill='x', padx=8, pady=(8, 4))
        cds_frame.columnconfigure(1, weight=1)

        map_frame = tk.Frame(cds_frame)
        map_frame.grid(row=0, column=0, rowspan=4, sticky='nw', padx=6, pady=6)
        self.map_width = 480
        self.map_height = 320
        self.max_map_zoom = self.calculate_max_map_zoom()
        self.map_zoom = min(2, self.max_map_zoom)
        self.map_canvas = tk.Canvas(
            map_frame,
            width=self.map_width,
            height=self.map_height,
            bg='#dceef7',
            highlightthickness=1,
            highlightbackground='#8aa8b8',
        )
        self.map_canvas.grid(row=0, column=0, columnspan=4, sticky='w')
        self.map_canvas.bind('<Button-1>', self.on_map_click)
        self.map_canvas.bind('<MouseWheel>', self.on_map_mousewheel)
        self.map_canvas.bind('<Button-4>', lambda event: self.zoom_map_in())
        self.map_canvas.bind('<Button-5>', lambda event: self.zoom_map_out())

        map_control_frame = tk.Frame(map_frame)
        map_control_frame.grid(row=1, column=0, columnspan=4, sticky='we', pady=(4, 0))
        tk.Button(map_control_frame, text='-', width=3, command=self.zoom_map_out).pack(side='left')
        tk.Button(map_control_frame, text='+', width=3, command=self.zoom_map_in).pack(side='left', padx=4)
        tk.Button(map_control_frame, text='Center', command=self.center_map_on_entry).pack(side='left', padx=4)
        tk.Button(map_control_frame, text='World', command=self.reset_map_view).pack(side='left', padx=4)
        self.map_status_var = tk.StringVar(value='')
        tk.Label(map_control_frame, textvariable=self.map_status_var, anchor='w').pack(side='left', padx=8, fill='x', expand=True)

        tk.Label(map_frame, text='Lat').grid(row=2, column=0, sticky='w', pady=(4, 0))
        tk.Entry(map_frame, textvariable=self.latitude_var, width=11).grid(row=2, column=1, sticky='w', pady=(4, 0))
        tk.Label(map_frame, text='Lon').grid(row=2, column=2, sticky='w', padx=(8, 0), pady=(4, 0))
        tk.Entry(map_frame, textvariable=self.longitude_var, width=11).grid(row=2, column=3, sticky='w', pady=(4, 0))
        self.grid_point_var = tk.StringVar(value='')
        tk.Label(map_frame, textvariable=self.grid_point_var, anchor='w').grid(row=3, column=0, columnspan=4, sticky='we', pady=(2, 0))
        self.draw_world_map()

        form_frame = tk.Frame(cds_frame)
        form_frame.grid(row=0, column=1, sticky='nsew', padx=6, pady=6)
        form_frame.columnconfigure(1, weight=1)

        tk.Label(form_frame, text='Start date').grid(row=0, column=0, sticky='w', pady=2)
        tk.Entry(form_frame, textvariable=self.start_date_var, width=14).grid(row=0, column=1, sticky='w', padx=4, pady=2)
        tk.Label(form_frame, text='End date').grid(row=0, column=2, sticky='w', padx=(8, 0), pady=2)
        tk.Entry(form_frame, textvariable=self.end_date_var, width=14).grid(row=0, column=3, sticky='w', padx=4, pady=2)

        tk.Label(form_frame, text='Download folder').grid(row=1, column=0, sticky='w', pady=2)
        tk.Entry(form_frame, textvariable=self.download_dir_var).grid(row=1, column=1, columnspan=2, sticky='we', padx=4, pady=2)
        tk.Button(form_frame, text='Browse', command=self.browse_download_dir).grid(row=1, column=3, sticky='we', padx=4, pady=2)

        tk.Label(form_frame, text='CDS API URL').grid(row=2, column=0, sticky='w', pady=2)
        tk.Entry(form_frame, textvariable=self.cds_url_var).grid(row=2, column=1, columnspan=3, sticky='we', padx=4, pady=2)

        tk.Label(form_frame, text='API key').grid(row=3, column=0, sticky='w', pady=2)
        self.cds_key_entry = tk.Entry(form_frame, textvariable=self.cds_key_var, show='*')
        self.cds_key_entry.grid(row=3, column=1, columnspan=2, sticky='we', padx=4, pady=2)
        tk.Checkbutton(form_frame, text='Show', variable=self.show_key_var, command=self.toggle_key_visibility).grid(row=3, column=3, sticky='w', padx=4, pady=2)

        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=4, sticky='we', pady=(4, 0))
        self.request_btn = tk.Button(button_frame, text='Request and download', command=self.start_era5_download)
        self.request_btn.pack(side='left', padx=(0, 4))
        tk.Button(button_frame, text='Save settings', command=self.save_settings).pack(side='left', padx=4)
        self.download_progress = ttk.Progressbar(button_frame, mode='indeterminate', length=180)
        self.download_progress.pack(side='left', padx=8)

        self.download_status_var = tk.StringVar(value='Ready')
        tk.Label(form_frame, textvariable=self.download_status_var, anchor='w').grid(row=5, column=0, columnspan=4, sticky='we', pady=(4, 0))

        variable_frame = tk.LabelFrame(cds_frame, text='Variables')
        variable_frame.grid(row=0, column=2, rowspan=4, sticky='nsew', padx=6, pady=6)
        variable_frame.columnconfigure(0, weight=1)
        variable_frame.rowconfigure(0, weight=1)

        self.download_variable_list = tk.Listbox(
            variable_frame,
            selectmode='multiple',
            height=8,
            width=28,
            exportselection=False,
        )
        variable_scrollbar = tk.Scrollbar(variable_frame, orient='vertical', command=self.download_variable_list.yview)
        self.download_variable_list.configure(yscrollcommand=variable_scrollbar.set)
        self.download_variable_list.grid(row=0, column=0, sticky='nsew')
        variable_scrollbar.grid(row=0, column=1, sticky='ns')

        for item in ERA5_VARIABLE_OPTIONS:
            self.download_variable_list.insert('end', item['label'])
        self.select_default_download_variables()

        variable_button_frame = tk.Frame(variable_frame)
        variable_button_frame.grid(row=1, column=0, columnspan=2, sticky='we', pady=(4, 0))
        tk.Button(variable_button_frame, text='Standard', command=self.select_default_download_variables).pack(side='left', padx=(0, 4))
        tk.Button(variable_button_frame, text='All', command=self.select_all_download_variables).pack(side='left', padx=4)
        tk.Button(variable_button_frame, text='None', command=self.clear_download_variables).pack(side='left', padx=4)

        self.latitude_var.trace_add('write', lambda *_args: self.schedule_map_marker_update())
        self.longitude_var.trace_add('write', lambda *_args: self.schedule_map_marker_update())
        self.update_map_marker()

    def initial_map_center(self):
        try:
            lat = float(self.latitude_var.get())
            lon = float(self.longitude_var.get())
            return self.clamp_latitude(lat), self.normalize_longitude(lon)
        except Exception:
            return 0.0, 0.0

    def calculate_max_map_zoom(self):
        target = MAP_MAX_LOCAL_SPAN_DEGREES
        zoom = math.ceil(math.log2((360.0 * self.map_width) / (MAP_TILE_SIZE * target)))
        return max(MAP_MIN_ZOOM, min(12, zoom))

    def tile_cache_dir(self):
        return self.settings_path().parent / 'tile_cache'

    def draw_world_map(self):
        self.map_canvas.delete('all')
        self.map_tile_images = []
        self.map_canvas.create_rectangle(0, 0, self.map_width, self.map_height, fill='#dceef7', outline='')

        center_x, center_y = self.latlon_to_global_pixel(self.map_center_lat, self.map_center_lon, self.map_zoom)
        top_left_x = center_x - self.map_width / 2
        top_left_y = center_y - self.map_height / 2
        tile_min_x = math.floor(top_left_x / MAP_TILE_SIZE)
        tile_max_x = math.floor((top_left_x + self.map_width) / MAP_TILE_SIZE)
        tile_min_y = math.floor(top_left_y / MAP_TILE_SIZE)
        tile_max_y = math.floor((top_left_y + self.map_height) / MAP_TILE_SIZE)
        tile_count = 2 ** self.map_zoom

        for tile_y in range(tile_min_y, tile_max_y + 1):
            if tile_y < 0 or tile_y >= tile_count:
                continue
            for tile_x in range(tile_min_x, tile_max_x + 1):
                wrapped_x = tile_x % tile_count
                screen_x = int(round(tile_x * MAP_TILE_SIZE - top_left_x))
                screen_y = int(round(tile_y * MAP_TILE_SIZE - top_left_y))
                image = self.get_map_tile_image(self.map_zoom, wrapped_x, tile_y)
                if image is not None:
                    self.map_canvas.create_image(screen_x, screen_y, image=image, anchor='nw')
                    self.map_tile_images.append(image)
                else:
                    self.map_canvas.create_rectangle(
                        screen_x,
                        screen_y,
                        screen_x + MAP_TILE_SIZE,
                        screen_y + MAP_TILE_SIZE,
                        fill='#dceef7',
                        outline='#aac2cc',
                    )

        self.draw_map_grid()
        self.update_map_marker()
        self.map_canvas.create_rectangle(0, 0, self.map_width - 1, self.map_height - 1, outline='#8aa8b8')
        self.update_map_status()

    def get_map_tile_image(self, zoom, tile_x, tile_y):
        cache_path = self.tile_cache_dir() / str(zoom) / str(tile_x) / f'{tile_y}.png'
        if not cache_path.exists():
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                url = OSM_TILE_URL.format(z=zoom, x=tile_x, y=tile_y)
                request = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'ERA5-TimeSeries-Viewer/1.0'},
                )
                with urllib.request.urlopen(request, timeout=8) as response:
                    cache_path.write_bytes(response.read())
            except Exception:
                if not self.map_tile_error_shown:
                    self.map_tile_error_shown = True
                    self.map_status_var.set('Map tiles unavailable; coordinate grid shown.')
                return None

        try:
            return tk.PhotoImage(file=str(cache_path))
        except Exception:
            try:
                cache_path.unlink()
            except Exception:
                pass
            return None

    def draw_map_grid(self):
        lon_left, lat_top = self.canvas_to_latlon(0, 0)
        lon_right, lat_bottom = self.canvas_to_latlon(self.map_width, self.map_height)
        lat_min = max(-85.0, min(lat_bottom, lat_top))
        lat_max = min(85.0, max(lat_bottom, lat_top))
        lon_span = self.current_map_lon_span()
        step = self.grid_step_for_span(lon_span)

        first_lat = math.floor(lat_min / step) * step
        lat = first_lat
        while lat <= lat_max + step:
            x1, y = self.latlon_to_canvas(lat, self.map_center_lon)
            self.map_canvas.create_line(0, y, self.map_width, y, fill='#2f5968', dash=(2, 4), tags='grid')
            self.map_canvas.create_text(4, y - 2, text=f'{lat:.0f}°', anchor='sw', fill='#1f4552', tags='grid')
            lat += step

        lon_values = self.visible_grid_longitudes(step)
        for lon in lon_values:
            x, _ = self.latlon_to_canvas(self.map_center_lat, lon)
            self.map_canvas.create_line(x, 0, x, self.map_height, fill='#2f5968', dash=(2, 4), tags='grid')
            self.map_canvas.create_text(x + 3, self.map_height - 4, text=f'{lon:.0f}°', anchor='sw', fill='#1f4552', tags='grid')

    def visible_grid_longitudes(self, step):
        center = self.map_center_lon
        half_span = self.current_map_lon_span() / 2 + step
        start = math.floor((center - half_span) / step) * step
        values = []
        lon = start
        while lon <= center + half_span:
            normalized = self.normalize_longitude(lon)
            if all(abs(self.short_lon_delta(normalized, existing)) > step / 4 for existing in values):
                values.append(normalized)
            lon += step
        return values

    def grid_step_for_span(self, span):
        for step in [60, 30, 15, 10, 5, 2, 1, 0.5, 0.25]:
            if span / step <= 8:
                return step
        return 0.25

    def latlon_to_global_pixel(self, lat, lon, zoom):
        lat = self.clamp_latitude(lat)
        lon = self.normalize_longitude(lon)
        lat_rad = math.radians(lat)
        scale = MAP_TILE_SIZE * (2 ** zoom)
        x = (lon + 180.0) / 360.0 * scale
        y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * scale
        return x, y

    def global_pixel_to_latlon(self, x, y, zoom):
        scale = MAP_TILE_SIZE * (2 ** zoom)
        lon = x / scale * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / scale)))
        lat = math.degrees(lat_rad)
        return self.normalize_longitude(lon), self.clamp_latitude(lat)

    def latlon_to_canvas(self, lat, lon):
        center_x, center_y = self.latlon_to_global_pixel(self.map_center_lat, self.map_center_lon, self.map_zoom)
        point_x, point_y = self.latlon_to_global_pixel(lat, lon, self.map_zoom)
        scale = MAP_TILE_SIZE * (2 ** self.map_zoom)
        delta_x = point_x - center_x
        if delta_x > scale / 2:
            delta_x -= scale
        elif delta_x < -scale / 2:
            delta_x += scale
        x = self.map_width / 2 + delta_x
        y = self.map_height / 2 + point_y - center_y
        return x, y

    def canvas_to_latlon(self, x, y):
        center_x, center_y = self.latlon_to_global_pixel(self.map_center_lat, self.map_center_lon, self.map_zoom)
        global_x = center_x + x - self.map_width / 2
        global_y = center_y + y - self.map_height / 2
        return self.global_pixel_to_latlon(global_x, global_y, self.map_zoom)

    def on_map_click(self, event):
        lon, lat = self.canvas_to_latlon(event.x, event.y)
        grid_lat, grid_lon = self.snap_to_era5_grid(lat, lon)
        self.latitude_var.set(f'{grid_lat:.4f}')
        self.longitude_var.set(f'{grid_lon:.4f}')
        self.map_center_lat = grid_lat
        self.map_center_lon = grid_lon
        self.draw_world_map()

    def on_map_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_map_in()
        elif event.delta < 0:
            self.zoom_map_out()

    def zoom_map_in(self):
        self.center_map_on_entry(show_error=False)
        if self.map_zoom < self.max_map_zoom:
            self.map_zoom += 1
            self.draw_world_map()

    def zoom_map_out(self):
        if self.map_zoom > MAP_MIN_ZOOM:
            self.map_zoom -= 1
            self.draw_world_map()

    def center_map_on_entry(self, show_error=True):
        coords = self.get_coordinates(show_error=show_error)
        if coords is None:
            return
        lat, lon = coords
        self.map_center_lat = self.clamp_latitude(lat)
        self.map_center_lon = self.normalize_longitude(lon)
        self.draw_world_map()

    def reset_map_view(self):
        self.map_zoom = MAP_MIN_ZOOM
        coords = self.get_coordinates(show_error=False)
        if coords is None:
            self.map_center_lat = 0.0
            self.map_center_lon = 0.0
        else:
            self.map_center_lat, self.map_center_lon = coords
        self.draw_world_map()

    def current_map_lon_span(self):
        scale = MAP_TILE_SIZE * (2 ** self.map_zoom)
        return self.map_width / scale * 360.0

    def update_map_status(self):
        span = self.current_map_lon_span()
        self.map_status_var.set(f'Zoom {self.map_zoom}/{self.max_map_zoom}  view ~{span:.1f}° wide')

    def clamp_latitude(self, lat):
        return max(-WEB_MERCATOR_MAX_LAT, min(WEB_MERCATOR_MAX_LAT, float(lat)))

    def normalize_longitude(self, lon):
        lon = ((float(lon) + 180.0) % 360.0) - 180.0
        return 180.0 if lon == -180.0 else lon

    def short_lon_delta(self, lon_a, lon_b):
        return ((lon_a - lon_b + 180.0) % 360.0) - 180.0

    def schedule_map_marker_update(self):
        if self.coord_update_pending:
            return
        self.coord_update_pending = True
        self.master.after(150, self.update_map_marker)

    def update_map_marker(self):
        self.coord_update_pending = False
        self.map_canvas.delete('marker')
        coords = self.get_coordinates(show_error=False)
        if coords is None:
            self.grid_point_var.set('')
            return
        lat, lon = coords
        grid_lat, grid_lon = self.snap_to_era5_grid(lat, lon)
        self.grid_point_var.set(f'ERA5 grid point used: lat {grid_lat:.2f}, lon {grid_lon:.2f} (0.25°)')
        x, y = self.latlon_to_canvas(grid_lat, grid_lon)
        if x < -20 or x > self.map_width + 20 or y < -20 or y > self.map_height + 20:
            return
        self.map_canvas.create_line(x, 0, x, self.map_height, fill='#d94c45', dash=(3, 3), tags='marker')
        self.map_canvas.create_line(0, y, self.map_width, y, fill='#d94c45', dash=(3, 3), tags='marker')
        self.map_canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill='#d94c45', outline='white', width=2, tags='marker')

    def parse_float(self, value):
        return float(str(value).strip())

    def get_coordinates(self, show_error=True):
        try:
            lat = self.parse_float(self.latitude_var.get())
            lon = self.parse_float(self.longitude_var.get())
        except Exception:
            if show_error:
                messagebox.showerror('Coordinates', 'Latitude and longitude must be numeric.')
            return None

        if not -90.0 <= lat <= 90.0:
            if show_error:
                messagebox.showerror('Coordinates', 'Latitude must be between -90 and 90.')
            return None
        if not -180.0 <= lon <= 180.0:
            if show_error:
                messagebox.showerror('Coordinates', 'Longitude must be between -180 and 180.')
            return None
        return lat, lon

    def browse_download_dir(self):
        path = filedialog.askdirectory(title='Select ERA5 download folder')
        if path:
            self.download_dir_var.set(path)

    def toggle_key_visibility(self):
        self.cds_key_entry.config(show='' if self.show_key_var.get() else '*')

    def select_default_download_variables(self):
        self.clear_download_variables()
        for index, item in enumerate(ERA5_VARIABLE_OPTIONS):
            if item['default']:
                self.download_variable_list.selection_set(index)

    def select_all_download_variables(self):
        self.download_variable_list.selection_set(0, 'end')

    def clear_download_variables(self):
        self.download_variable_list.selection_clear(0, 'end')

    def get_selected_download_variables(self):
        return [
            ERA5_VARIABLE_OPTIONS[index]['request']
            for index in self.download_variable_list.curselection()
        ]

    def validate_download_inputs(self):
        coords = self.get_coordinates(show_error=True)
        if coords is None:
            return None

        selected_variables = self.get_selected_download_variables()
        if not selected_variables:
            messagebox.showwarning('Variables', 'Select at least one ERA5 variable to download.')
            return None

        try:
            start_date = pd.to_datetime(self.start_date_var.get().strip()).strftime('%Y-%m-%d')
            end_date = pd.to_datetime(self.end_date_var.get().strip()).strftime('%Y-%m-%d')
        except Exception:
            messagebox.showerror('Dates', 'Use dates in YYYY-MM-DD format.')
            return None

        if pd.Timestamp(end_date) < pd.Timestamp(start_date):
            messagebox.showerror('Dates', 'End date must be on or after start date.')
            return None

        output_dir = Path(self.download_dir_var.get().strip() or self.default_download_dir())
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror('Download folder', f'Could not create download folder:\n{exc}')
            return None

        url = self.cds_url_var.get().strip() or DEFAULT_CDS_URL
        key = self.cds_key_var.get().strip()
        if not key and not (Path.home() / '.cdsapirc').exists():
            messagebox.showwarning('CDS API key', 'Enter a CDS API key, or configure .cdsapirc in your user folder.')
            return None

        lat, lon = self.snap_to_era5_grid(*coords)
        return {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date,
            'variables': selected_variables,
            'output_dir': output_dir,
            'url': url,
            'key': key,
        }

    def start_era5_download(self):
        if self.download_thread is not None and self.download_thread.is_alive():
            messagebox.showinfo('Download running', 'An ERA5 request is already running.')
            return

        params = self.validate_download_inputs()
        if params is None:
            return

        self.request_btn.config(state='disabled')
        self.download_progress.start(12)
        self.download_status_var.set('Submitting request to Copernicus CDS...')
        self.download_thread = threading.Thread(target=self.download_era5_worker, args=(params,), daemon=True)
        self.download_thread.start()
        self.master.after(200, self.process_download_queue)

    def download_era5_worker(self, params):
        try:
            self.configure_ssl_certificates()
            try:
                import cdsapi
                import requests
            except ModuleNotFoundError as exc:
                message = (
                    f'The {exc.name} package is required in the Python environment running this script.\n\n'
                    f'Python executable:\n{sys.executable}\n\n'
                    'Install it with:\n'
                    f'"{sys.executable}" -m pip install -r requirements.txt'
                )
                raise RuntimeError(message) from exc

            date_range = f'{params["start_date"]}/{params["end_date"]}'
            request = {
                'variable': params['variables'],
                'date': [date_range],
                'location': {
                    'longitude': params['longitude'],
                    'latitude': params['latitude'],
                },
                'data_format': 'netcdf',
            }

            self.download_queue.put(('status', 'Submitting request and waiting for Copernicus CDS result...'))
            client_kwargs = {
                'quiet': True,
                'progress': False,
                'sleep_max': 10,
                'delete': False,
                'info_callback': self.cds_log_callback,
                'warning_callback': self.cds_log_callback,
                'error_callback': self.cds_log_callback,
            }
            if params['key']:
                client_kwargs.update({'url': params['url'], 'key': params['key']})
            client = cdsapi.Client(**client_kwargs)

            result = client.retrieve(ERA5_DATASET, request, target=None)
            download_url, content_length, content_type = self.extract_cds_download_info(result)
            if not download_url:
                raise RuntimeError(f'CDS completed, but no download URL was returned:\n{result!r}')

            target_path = self.make_download_target_path(params, download_url, content_type)
            self.download_queue.put(('status', f'Downloading CDS result: {Path(target_path).name}'))
            self.download_result_file(requests, download_url, target_path, content_length)
            nc_files = self.collect_downloaded_netcdf_files(target_path)
            if not nc_files:
                raise RuntimeError(f'No NetCDF files were found in the CDS result: {target_path}')

            payload = {
                'target_path': target_path,
                'nc_files': nc_files,
                'request': request,
            }
            self.download_queue.put(('done', payload))
        except Exception as exc:
            self.download_queue.put(('error', str(exc)))

    def cds_log_callback(self, *args, **_kwargs):
        message = self.format_log_message(*args)
        if message:
            self.download_queue.put(('status', message))

    def format_log_message(self, *args):
        if not args:
            return ''
        message = str(args[0])
        if len(args) > 1:
            try:
                message = message % args[1:]
            except Exception:
                message = ' '.join(str(arg) for arg in args)
        return message

    def extract_cds_download_info(self, result):
        location = getattr(result, 'location', None)
        content_length = getattr(result, 'content_length', None)
        content_type = getattr(result, 'content_type', None)
        if location:
            return location, self.safe_int(content_length), content_type

        if isinstance(result, dict):
            location = result.get('location') or result.get('href')
            content_length = (
                result.get('content_length')
                or result.get('contentLength')
                or result.get('file:size')
            )
            content_type = result.get('content_type') or result.get('contentType') or result.get('type')
            if location:
                return location, self.safe_int(content_length), content_type

            asset = result.get('asset')
            if isinstance(asset, dict):
                value = asset.get('value', asset)
                if isinstance(value, dict):
                    location = value.get('href') or value.get('location')
                    content_length = value.get('file:size') or value.get('contentLength')
                    content_type = value.get('type') or value.get('contentType')
                    if location:
                        return location, self.safe_int(content_length), content_type

        return None, None, None

    def safe_int(self, value):
        try:
            return int(value)
        except Exception:
            return None

    def configure_ssl_certificates(self):
        if self.ssl_configured:
            return

        try:
            import truststore
            truststore.inject_into_ssl()
            self.ssl_configured = True
            return
        except Exception:
            pass

        try:
            import certifi
            ca_bundle = certifi.where()
        except Exception:
            return

        if ca_bundle:
            os.environ.setdefault('SSL_CERT_FILE', ca_bundle)
            os.environ.setdefault('REQUESTS_CA_BUNDLE', ca_bundle)
            self.ssl_configured = True

    def snap_to_era5_grid(self, lat, lon):
        snapped_lat = round(float(lat) / ERA5_GRID_DEGREES) * ERA5_GRID_DEGREES
        snapped_lon = round(float(lon) / ERA5_GRID_DEGREES) * ERA5_GRID_DEGREES
        return self.clamp_latitude(snapped_lat), self.normalize_longitude(snapped_lon)

    def make_download_target_path(self, params, download_url=None, content_type=None):
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        lat_token = f'{params["latitude"]:.4f}'.replace('-', 'm').replace('.', 'p')
        lon_token = f'{params["longitude"]:.4f}'.replace('-', 'm').replace('.', 'p')
        suffix = self.infer_download_suffix(download_url, content_type)
        filename = (
            f'ERA5-timeseries_lat{lat_token}_lon{lon_token}_'
            f'{params["start_date"]}_{params["end_date"]}_{stamp}{suffix}'
        )
        return params['output_dir'] / filename

    def infer_download_suffix(self, download_url=None, content_type=None):
        content_type = (content_type or '').lower()
        if 'zip' in content_type:
            return '.zip'
        if 'netcdf' in content_type or 'x-netcdf' in content_type:
            return '.nc'

        if download_url:
            path = urllib.parse.urlparse(download_url).path.lower()
            if path.endswith('.zip'):
                return '.zip'
            if path.endswith('.nc'):
                return '.nc'
        return '.zip'

    def download_result_file(self, requests_module, url, target_path, expected_size=None):
        target_path = Path(target_path)
        part_path = target_path.with_suffix(target_path.suffix + '.part')
        if part_path.exists():
            part_path.unlink()

        with requests_module.get(url, stream=True, timeout=120) as response:
            response.raise_for_status()
            total_size = expected_size or self.safe_int(response.headers.get('Content-Length'))
            downloaded = 0
            last_update = 0.0

            with open(part_path, 'wb') as file_obj:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    file_obj.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_update >= 1.0:
                        self.download_queue.put(('status', self.format_download_progress(downloaded, total_size)))
                        last_update = now

        if expected_size is not None and downloaded != expected_size:
            raise RuntimeError(
                f'Download incomplete: got {downloaded} byte(s), expected {expected_size} byte(s).'
            )

        if target_path.exists():
            target_path.unlink()
        part_path.replace(target_path)
        self.download_queue.put(('status', f'Download complete: {target_path.name}'))

    def format_download_progress(self, downloaded, total_size):
        downloaded_mb = downloaded / (1024 * 1024)
        if total_size:
            total_mb = total_size / (1024 * 1024)
            return f'Downloading CDS result: {downloaded_mb:.1f} MB of {total_mb:.1f} MB'
        return f'Downloading CDS result: {downloaded_mb:.1f} MB'

    def collect_downloaded_netcdf_files(self, target_path):
        target_path = Path(target_path)
        if not target_path.exists():
            raise RuntimeError(f'CDS download did not create the expected file: {target_path}')

        if zipfile.is_zipfile(target_path):
            extract_dir = target_path.with_suffix('')
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_path, 'r') as zip_file:
                zip_file.extractall(extract_dir)
            return sorted(extract_dir.rglob('*.nc'))

        if target_path.suffix.lower() == '.nc':
            return [target_path]

        return []

    def process_download_queue(self):
        handled_terminal_message = False
        try:
            while True:
                kind, payload = self.download_queue.get_nowait()
                if kind == 'status':
                    self.download_status_var.set(payload)
                elif kind == 'done':
                    handled_terminal_message = True
                    self.finish_download_success(payload)
                elif kind == 'error':
                    handled_terminal_message = True
                    self.download_progress.stop()
                    self.request_btn.config(state='normal')
                    self.download_status_var.set('Download failed.')
                    messagebox.showerror('ERA5 download error', payload)
        except queue.Empty:
            pass

        if not handled_terminal_message and self.download_thread is not None and self.download_thread.is_alive():
            self.master.after(300, self.process_download_queue)

    def finish_download_success(self, payload):
        self.download_status_var.set('Download complete. Loading NetCDF data...')
        try:
            self.load_downloaded_netcdf_files(payload['nc_files'])
        except Exception as exc:
            self.download_progress.stop()
            self.request_btn.config(state='normal')
            self.download_status_var.set('Downloaded, but loading failed.')
            messagebox.showerror('NetCDF load error', f'Downloaded files could not be loaded:\n{exc}')
            return

        self.download_progress.stop()
        self.request_btn.config(state='normal')
        file_count = len(payload['nc_files'])
        self.download_status_var.set(f'Downloaded and loaded {file_count} NetCDF file(s).')
        messagebox.showinfo('ERA5 download complete', f'Downloaded and loaded {file_count} NetCDF file(s).')

    def load_downloaded_netcdf_files(self, paths):
        atm_parts = []
        ocn_parts = []

        for path in paths:
            ds = xr.open_dataset(path, decode_times=True)
            atm_ds, ocn_ds = self.split_dataset_by_source(ds)
            if atm_ds is not None:
                atm_parts.append(atm_ds)
            if ocn_ds is not None:
                ocn_parts.append(ocn_ds)

        loaded_sources = []
        if atm_parts:
            self.atm_ds = self.prepare_dataset(self.merge_dataset_parts(atm_parts), 'atmospheric')
            loaded_sources.append('atmospheric')
            self.atm_path_label.config(text=f'Atmospheric file: downloaded from CDS ({len(atm_parts)} file part(s))')

        if ocn_parts:
            self.ocn_ds = self.prepare_dataset(self.merge_dataset_parts(ocn_parts), 'oceanic')
            loaded_sources.append('oceanic')
            self.ocn_path_label.config(text=f'Oceanic file: downloaded from CDS ({len(ocn_parts)} file part(s))')

        if not loaded_sources:
            raise RuntimeError('Downloaded NetCDF files did not contain time-series variables.')

        self.current_source.set(loaded_sources[0])
        self.update_variable_menu()
        self.set_analysis_date_range_from_loaded_data()
        self.notebook.select(self.analysis_tab)
        self.info_label.config(text='CDS data loaded. Select a variable and click "Plot time series", or save as CSV/DFS0.')

    def split_dataset_by_source(self, ds):
        atm_vars = []
        ocn_vars = []
        for var_name in ds.data_vars.keys():
            da = ds[var_name]
            if not self.has_time_dimension(da):
                continue
            source = self.infer_variable_source(var_name)
            if source == 'oceanic':
                ocn_vars.append(var_name)
            else:
                atm_vars.append(var_name)

        atm_ds = ds[atm_vars] if atm_vars else None
        ocn_ds = ds[ocn_vars] if ocn_vars else None
        return atm_ds, ocn_ds

    def infer_variable_source(self, var_name):
        if var_name in SHORT_TO_SOURCE:
            return SHORT_TO_SOURCE[var_name]
        if var_name in REQUEST_TO_SOURCE:
            return REQUEST_TO_SOURCE[var_name]
        lower_name = var_name.lower()
        if any(token in lower_name for token in ['wave', 'swh', 'mwp', 'mwd', 'sst']):
            return 'oceanic'
        return 'atmospheric'

    def merge_dataset_parts(self, parts):
        if len(parts) == 1:
            return parts[0]
        return xr.merge(parts, compat='override')

    def has_time_dimension(self, da):
        return any(dim in TIME_DIMS for dim in da.dims)

    def prepare_dataset(self, ds, source):
        if source != 'atmospheric':
            return ds

        u_name = 'u10' if 'u10' in ds.data_vars else '10m_u_component_of_wind'
        v_name = 'v10' if 'v10' in ds.data_vars else '10m_v_component_of_wind'
        if u_name not in ds.data_vars or v_name not in ds.data_vars:
            return ds

        try:
            u = ds[u_name]
            v = ds[v_name]
            ws = np.hypot(u, v)
            wd = (np.degrees(np.arctan2(-u, -v)) + 360) % 360
            return ds.assign(wind_speed_10m=ws, wind_dir_10m=wd)
        except Exception as exc:
            messagebox.showwarning('Wind calc', f'Could not compute wind speed/direction:\n{exc}')
            return ds

    def load_file(self, source):
        path = filedialog.askopenfilename(
            title='Select NetCDF file',
            filetypes=[('NetCDF files', '*.nc'), ('All files', '*.*')]
        )
        if not path:
            return

        try:
            ds = xr.open_dataset(path, decode_times=True)
        except Exception as exc:
            messagebox.showerror('Open error', f'Unable to open NetCDF file:\n{exc}')
            return

        ds = self.prepare_dataset(ds, source)

        if source == 'atmospheric':
            self.atm_ds = ds
            self.atm_path_label.config(text=f'Atmospheric file: {path}')
            self.current_source.set('atmospheric')
        else:
            self.ocn_ds = ds
            self.ocn_path_label.config(text=f'Oceanic file: {path}')
            self.current_source.set('oceanic')

        self.update_variable_menu()
        self.set_analysis_date_range_from_loaded_data()
        self.notebook.select(self.analysis_tab)
        self.info_label.config(text='Dataset loaded. Select a variable and click "Plot time series".')

    def get_current_dataset(self):
        if self.current_source.get() == 'atmospheric':
            return self.atm_ds
        return self.ocn_ds

    def update_variable_menu(self):
        ds = self.get_current_dataset()
        menu = self.variable_menu['menu']
        menu.delete(0, 'end')
        self.selected_variable.set('')

        if ds is None:
            menu.add_command(label='No dataset loaded', command=lambda: self.selected_variable.set(''))
            return

        variables = sorted(var_name for var_name in ds.data_vars.keys() if self.has_time_dimension(ds[var_name]))
        if not variables:
            menu.add_command(label='No data variables found', command=lambda: self.selected_variable.set(''))
            return

        for var in variables:
            menu.add_command(label=var, command=lambda value=var: self.selected_variable.set(value))
        self.selected_variable.set(variables[0])

    def plot_time_series(self):
        ds = self.get_current_dataset()
        var_name = self.selected_variable.get()

        if ds is None:
            messagebox.showwarning('No dataset', 'Please load an atmospheric or oceanic dataset first.')
            return
        if not var_name:
            messagebox.showwarning('No variable selected', 'Please select a variable from the dropdown menu.')
            return
        if var_name not in ds:
            messagebox.showerror('Variable missing', f'Variable "{var_name}" is not available in the selected dataset.')
            return

        try:
            da = ds[var_name]
            da = self.reduce_to_time_series(da)
            time_index = self.extract_time_index(da)
            series = pd.Series(da.values, index=time_index)
        except Exception as exc:
            messagebox.showerror('Data error', f'Unable to extract a time series:\n{exc}')
            return

        if series.empty:
            messagebox.showwarning('Empty series', 'The selected variable produced an empty time series.')
            return

        self.full_series = series.sort_index()
        self.current_var_name = var_name
        self.current_var_display_name = self.get_display_name(var_name)
        self.current_var_units = self.get_display_unit(var_name)
        subset = self.filter_series_by_analysis_dates(self.full_series, show_error=True)
        if subset.empty:
            return
        self.update_plot(subset)
        self.show_statistics(subset, var_name)

    def reduce_to_time_series(self, da):
        time_dim = next((dim for dim in da.dims if dim in TIME_DIMS), None)
        if time_dim is None:
            raise ValueError('The selected variable has no supported time dimension.')

        spatial_dims = [dim for dim in da.dims if dim != time_dim]
        if spatial_dims:
            da = da.mean(dim=spatial_dims, skipna=True)

        if da.ndim != 1 or da.sizes.get(time_dim, 0) == 0:
            raise ValueError('Unable to reduce variable to a one-dimensional time series.')

        return da

    def extract_time_index(self, da):
        time_dim = next((dim for dim in da.dims if dim in TIME_DIMS), None)
        if time_dim is None:
            raise ValueError('No supported time coordinate found in the dataset.')

        time_values = da[time_dim].values
        time_index = pd.to_datetime(time_values)
        return time_index

    def update_current_stats(self):
        if self.full_series is None:
            return

        subset = self.filter_series_by_analysis_dates(self.full_series, show_error=True)
        if subset.empty:
            return

        self.show_statistics(subset, self.current_var_name)

    def update_plot(self, series):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.callbacks.connect('xlim_changed', self.on_xlim_changed)
        self.ax.plot(series.index, series.values, linestyle='-', color='tab:blue')
        title = self.current_var_display_name if hasattr(self, 'current_var_display_name') else self.current_var_name
        unit = self.current_var_units if hasattr(self, 'current_var_units') else ''
        ylabel = f'{title} ({unit})' if unit else title
        self.ax.set_title(f'{title} time series')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True)
        self.figure.autofmt_xdate()
        self.plot_available = True
        self.canvas.draw()

    def on_xlim_changed(self, ax):
        if self.full_series is None or self.current_var_name is None:
            return

        left, right = ax.get_xlim()
        left_dt = mdates.num2date(left).replace(tzinfo=None)
        right_dt = mdates.num2date(right).replace(tzinfo=None)
        date_subset = self.filter_series_by_analysis_dates(self.full_series, show_error=False)
        subset = date_subset.loc[(date_subset.index >= left_dt) & (date_subset.index <= right_dt)]
        if subset.empty:
            return

        self.show_statistics(subset, self.current_var_name)

    def get_current_subset(self):
        if self.full_series is None:
            return None
        return self.filter_series_by_analysis_dates(self.full_series, show_error=False)

    def plot_wave_rose(self):
        pair = self.get_wave_analysis_pair()
        if pair is None:
            messagebox.showwarning('Wave Rose', 'Wave rose requires wave height and mean wave direction in the oceanic dataset.')
            return

        df, value_label, direction_label, unit = pair
        self.plot_directional_rose_pair(
            df,
            value_label=value_label,
            direction_label=direction_label,
            unit=unit,
            kind='wave',
            csv_filename='representative year waves.csv',
        )

    def plot_wind_rose(self):
        pair = self.get_wind_analysis_pair()
        if pair is None:
            messagebox.showwarning('Wind Rose', 'Wind rose requires wind speed and wind direction in the atmospheric dataset.')
            return

        df, value_label, direction_label, unit = pair
        self.plot_directional_rose_pair(
            df,
            value_label=value_label,
            direction_label=direction_label,
            unit=unit,
            kind='wind',
            csv_filename='representative year winds.csv',
        )

    def get_wave_analysis_pair(self):
        if self.ocn_ds is None:
            return None
        value_var = self.find_first_variable(
            self.ocn_ds,
            ['swh', 'significant_height_of_combined_wind_waves_and_swell'],
        )
        direction_var = self.find_first_variable(self.ocn_ds, ['mwd', 'mean_wave_direction'])
        if value_var is None or direction_var is None:
            return None
        df = self.build_directional_pair_dataframe(self.ocn_ds, value_var, direction_var)
        return df, self.get_display_name(value_var), self.get_display_name(direction_var), self.get_display_unit(value_var)

    def get_wind_analysis_pair(self):
        if self.atm_ds is None:
            return None
        if 'wind_speed_10m' not in self.atm_ds.data_vars or 'wind_dir_10m' not in self.atm_ds.data_vars:
            self.atm_ds = self.prepare_dataset(self.atm_ds, 'atmospheric')
        value_var = self.find_first_variable(self.atm_ds, ['wind_speed_10m'])
        direction_var = self.find_first_variable(self.atm_ds, ['wind_dir_10m'])
        if value_var is None or direction_var is None:
            return None
        df = self.build_directional_pair_dataframe(self.atm_ds, value_var, direction_var)
        return df, self.get_display_name(value_var), self.get_display_name(direction_var), self.get_display_unit(value_var)

    def find_first_variable(self, ds, candidates):
        for candidate in candidates:
            if candidate in ds.data_vars:
                return candidate
        return None

    def build_directional_pair_dataframe(self, ds, value_var, direction_var):
        value_series = self.extract_series_from_dataset(ds, value_var)
        direction_series = self.extract_series_from_dataset(ds, direction_var)
        df = pd.concat(
            [
                value_series.rename('value'),
                direction_series.rename('direction'),
            ],
            axis=1,
        )
        df = df.sort_index()
        df['direction'] = df['direction'] % 360.0
        return df.replace([np.inf, -np.inf], np.nan).dropna()

    def extract_series_from_dataset(self, ds, var_name):
        da = self.reduce_to_time_series(ds[var_name])
        time_index = self.extract_time_index(da)
        return pd.Series(da.values, index=time_index, name=var_name).sort_index()

    def plot_directional_rose_pair(self, df, value_label, direction_label, unit, kind, csv_filename):
        df = self.filter_dataframe_by_analysis_dates(df, show_error=True)
        if df.empty:
            messagebox.showwarning('Rose plot', f'No valid directional data were found from {self.format_analysis_period()}.')
            return

        ranking_df, representative_year = self.compute_representative_year_ranking(df)
        output_path = None
        csv_error = None
        try:
            output_path = self.save_representative_year_csv(ranking_df, csv_filename)
        except Exception as exc:
            csv_error = f'{type(exc).__name__}: {exc}'
        representative_df = df[df.index.year == representative_year]
        bins = self.make_rose_bins(df['value'].to_numpy(dtype=float), kind)
        colors = self.rose_colors(len(bins) - 1, kind)

        self.figure.clear()
        ax_all = self.figure.add_subplot(121, projection='polar')
        ax_rep = self.figure.add_subplot(122, projection='polar')
        handles, labels = self.draw_rose(
            ax_all,
            df,
            f'All years\n{value_label} vs {direction_label}',
            value_label,
            unit,
            kind,
            bins,
            colors,
        )
        self.draw_rose(
            ax_rep,
            representative_df,
            f'Representative year {representative_year}\n{value_label} vs {direction_label}',
            value_label,
            unit,
            kind,
            bins,
            colors,
        )
        if handles:
            columns = min(4, max(1, len(handles)))
            self.figure.legend(
                handles,
                labels,
                title=value_label,
                loc='lower center',
                bbox_to_anchor=(0.5, 0.01),
                fontsize=8,
                title_fontsize=9,
                ncol=columns,
            )
        self.figure.tight_layout(rect=[0, 0.16, 1, 1])
        self.plot_available = True
        self.canvas.draw()

        top_rows = ranking_df.head(5)
        csv_line = f'Ranking CSV: {output_path}' if output_path else f'Ranking CSV not saved: {csv_error}'
        stats_lines = [
            f'Representative year selected: {representative_year}',
            csv_line,
            '',
            'Top ranked years:',
        ]
        for _, row in top_rows.iterrows():
            stats_lines.append(
                f'{int(row["rank"])}. {int(row["year"])}  score={row["total_score"]:.5g}  count={int(row["count"])}'
            )
        self.set_stats_text('\n'.join(stats_lines))
        if output_path:
            self.info_label.config(text=f'{kind.title()} rose plotted for {self.format_analysis_period()}. Representative-year ranking saved to {output_path}.')
        else:
            self.info_label.config(text=f'{kind.title()} rose plotted for {self.format_analysis_period()}. Representative-year ranking CSV could not be saved.')

    def draw_rose(self, ax, df, title, value_label, unit, kind, bins, colors):
        values = df['value'].to_numpy(dtype=float)
        directions = df['direction'].to_numpy(dtype=float) % 360.0
        valid = np.isfinite(values) & np.isfinite(directions)
        values = values[valid]
        directions = directions[valid]

        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_title(title, fontsize=10)
        ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])

        if len(values) == 0:
            ax.text(0.5, 0.5, 'No data', transform=ax.transAxes, ha='center', va='center')
            return [], []

        sector_indices = self.direction_to_sector_index(directions)
        magnitude_indices = np.digitize(values, bins, right=False) - 1
        magnitude_indices = np.clip(magnitude_indices, 0, len(bins) - 2)
        counts = np.zeros((len(SECTOR_LABELS), len(bins) - 1), dtype=float)
        for sector_index, magnitude_index in zip(sector_indices, magnitude_indices):
            counts[int(sector_index), int(magnitude_index)] += 1.0

        frequencies = counts / max(1.0, counts.sum()) * 100.0
        theta = np.deg2rad(np.arange(0, 360, SECTOR_WIDTH_DEGREES))
        width = np.deg2rad(SECTOR_WIDTH_DEGREES * 0.92)
        bottom = np.zeros(len(SECTOR_LABELS), dtype=float)
        labels = self.rose_bin_labels(bins, unit)
        handles = []

        for bin_index in range(frequencies.shape[1]):
            heights = frequencies[:, bin_index]
            bars = ax.bar(
                theta,
                heights,
                width=width,
                bottom=bottom,
                align='center',
                color=colors[bin_index % len(colors)],
                edgecolor='white',
                linewidth=0.6,
                label=labels[bin_index],
            )
            if len(bars) > 0:
                handles.append(bars[0])
            bottom += heights

        ax.set_rlabel_position(225)
        ax.grid(True)
        return handles, labels

    def rose_colors(self, count, kind):
        if count <= 0:
            return []
        if kind == 'wave':
            cmap = matplotlib.colormaps.get_cmap('rainbow')
            if count == 1:
                return [cmap(0.5)]
            return [cmap(index / (count - 1)) for index in range(count)]

        palette = ['#d9f0d3', '#addd8e', '#78c679', '#41ab5d', '#238443', '#006837', '#004529', '#253494']
        return [palette[index % len(palette)] for index in range(count)]

    def make_rose_bins(self, values, kind):
        max_value = float(np.nanmax(values)) if len(values) else 1.0
        if kind == 'wind':
            base = [0, 2, 4, 6, 8, 10, 15, 20, 30]
        else:
            base = [0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 6]

        bins = [value for value in base if value < max_value]
        if not bins or bins[0] > 0:
            bins.insert(0, 0)
        next_edge = next((value for value in base if value >= max_value), None)
        if next_edge is None:
            next_edge = math.ceil(max_value)
        if next_edge <= bins[-1]:
            next_edge = bins[-1] + 1
        bins.append(next_edge)
        bins.append(np.inf)
        return np.array(bins, dtype=float)

    def rose_bin_labels(self, bins, unit):
        labels = []
        suffix = f' {unit}' if unit else ''
        for start, end in zip(bins[:-1], bins[1:]):
            if np.isinf(end):
                labels.append(f'>= {start:g}{suffix}')
            else:
                labels.append(f'{start:g}-{end:g}{suffix}')
        return labels

    def compute_representative_year_ranking(self, df):
        full_values = df['value'].astype(float)
        full_directions = df['direction'].astype(float) % 360.0
        full_metrics = self.series_metrics(full_values)
        hist_bins = self.representative_histogram_bins(full_values)
        full_hist = self.normalized_histogram(full_values, hist_bins)
        full_sector = self.normalized_sector_distribution(full_directions)
        full_monthly = self.normalized_monthly_means(df)
        expected_year_count = max(float(df.groupby(df.index.year).size().median()), 1.0)

        rows = []
        for year, year_df in df.groupby(df.index.year):
            if year_df.empty:
                continue
            year_values = year_df['value'].astype(float)
            year_directions = year_df['direction'].astype(float) % 360.0
            metrics = self.series_metrics(year_values)

            metric_score = self.metric_difference_score(metrics, full_metrics)
            distribution_score = self.rmse(self.normalized_histogram(year_values, hist_bins), full_hist)
            direction_score = self.rmse(self.normalized_sector_distribution(year_directions), full_sector)
            seasonal_score = self.rmse(self.normalized_monthly_means(year_df), full_monthly)
            autocorr_score = abs(metrics['lag1_autocorr'] - full_metrics['lag1_autocorr'])
            outlier_penalty = self.outlier_penalty(metrics, full_metrics)
            count_score = abs(metrics['count'] - expected_year_count) / expected_year_count
            total_score = (
                0.35 * metric_score
                + 0.22 * distribution_score
                + 0.15 * seasonal_score
                + 0.11 * direction_score
                + 0.06 * autocorr_score
                + 0.04 * outlier_penalty
                + 0.07 * count_score
            )

            row = {
                'year': int(year),
                'count': int(metrics['count']),
                'expected_year_count': expected_year_count,
                'count_score': count_score,
                'metric_score': metric_score,
                'distribution_rmse': distribution_score,
                'seasonal_rmse': seasonal_score,
                'direction_rmse': direction_score,
                'autocorr_difference': autocorr_score,
                'outlier_penalty': outlier_penalty,
                'total_score': total_score,
            }
            for key, value in metrics.items():
                row[f'year_{key}'] = value
            for key, value in full_metrics.items():
                row[f'full_{key}'] = value
            rows.append(row)

        if not rows:
            raise ValueError('No calendar years were found in the directional dataset.')

        ranking_df = pd.DataFrame(rows).sort_values(['total_score', 'year']).reset_index(drop=True)
        ranking_df['rank'] = np.arange(1, len(ranking_df) + 1)
        ranking_df['selected_representative_year'] = ranking_df['rank'] == 1
        selected_year = int(ranking_df.iloc[0]['year'])
        return ranking_df, selected_year

    def series_metrics(self, series):
        clean = pd.Series(series).replace([np.inf, -np.inf], np.nan).dropna()
        if clean.empty:
            return {
                'count': 0,
                'mean': np.nan,
                'median': np.nan,
                'std': np.nan,
                'p05': np.nan,
                'p50': np.nan,
                'p95': np.nan,
                'p99': np.nan,
                'lag1_autocorr': 0.0,
            }
        return {
            'count': int(clean.count()),
            'mean': float(clean.mean()),
            'median': float(clean.median()),
            'std': float(clean.std(ddof=0)),
            'p05': float(clean.quantile(0.05)),
            'p50': float(clean.quantile(0.50)),
            'p95': float(clean.quantile(0.95)),
            'p99': float(clean.quantile(0.99)),
            'lag1_autocorr': self.safe_float(clean.autocorr(lag=1), default=0.0),
        }

    def representative_histogram_bins(self, series):
        clean = pd.Series(series).replace([np.inf, -np.inf], np.nan).dropna()
        if clean.empty or clean.min() == clean.max():
            return np.array([0.0, 1.0])
        low = float(clean.quantile(0.001))
        high = float(clean.quantile(0.999))
        if high <= low:
            low = float(clean.min())
            high = float(clean.max())
        return np.linspace(low, high, 25)

    def normalized_histogram(self, series, bins):
        clean = pd.Series(series).replace([np.inf, -np.inf], np.nan).dropna()
        if clean.empty:
            return np.zeros(len(bins) - 1, dtype=float)
        clipped = clean.clip(lower=bins[0], upper=bins[-1])
        counts, _ = np.histogram(clipped, bins=bins)
        total = counts.sum()
        if total == 0:
            return np.zeros(len(bins) - 1, dtype=float)
        return counts.astype(float) / total

    def normalized_sector_distribution(self, directions):
        clean = pd.Series(directions).replace([np.inf, -np.inf], np.nan).dropna()
        if clean.empty:
            return np.zeros(len(SECTOR_LABELS), dtype=float)
        sector_indices = self.direction_to_sector_index(clean.to_numpy(dtype=float))
        counts = np.bincount(sector_indices, minlength=len(SECTOR_LABELS)).astype(float)
        total = counts.sum()
        return counts / total if total else counts

    def normalized_monthly_means(self, df):
        values = df['value'].replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty:
            return np.zeros(12, dtype=float)
        monthly = values.groupby(values.index.month).mean().reindex(range(1, 13))
        global_mean = values.mean()
        monthly = monthly.fillna(global_mean)
        scale = values.std(ddof=0)
        if not np.isfinite(scale) or scale == 0:
            scale = max(abs(global_mean), 1.0)
        return ((monthly - global_mean) / scale).to_numpy(dtype=float)

    def metric_difference_score(self, metrics, full_metrics):
        keys = ['mean', 'median', 'std', 'p05', 'p50', 'p95', 'p99']
        weights = {
            'mean': 1.0,
            'median': 0.8,
            'std': 1.0,
            'p05': 0.7,
            'p50': 0.7,
            'p95': 1.0,
            'p99': 1.2,
        }
        total_weight = sum(weights.values())
        score = 0.0
        for key in keys:
            full_value = full_metrics.get(key, 0.0)
            year_value = metrics.get(key, 0.0)
            scale = abs(full_value)
            if key in ['std', 'p95', 'p99']:
                scale = max(scale, abs(full_metrics.get('mean', 0.0)), 1e-6)
            else:
                scale = max(scale, full_metrics.get('std', 0.0), 1e-6)
            score += weights[key] * abs(year_value - full_value) / scale
        return score / total_weight

    def outlier_penalty(self, metrics, full_metrics):
        full_spread = max(full_metrics.get('p99', 0.0) - full_metrics.get('p95', 0.0), full_metrics.get('std', 0.0), 1e-6)
        high_tail_difference = abs(metrics.get('p99', 0.0) - full_metrics.get('p99', 0.0)) / full_spread
        std_difference = abs(metrics.get('std', 0.0) - full_metrics.get('std', 0.0)) / max(full_metrics.get('std', 0.0), 1e-6)
        return max(0.0, high_tail_difference - 1.5) + max(0.0, std_difference - 1.5)

    def rmse(self, values, reference):
        values = np.asarray(values, dtype=float)
        reference = np.asarray(reference, dtype=float)
        return float(np.sqrt(np.nanmean((values - reference) ** 2)))

    def safe_float(self, value, default=0.0):
        try:
            value = float(value)
        except Exception:
            return default
        if not np.isfinite(value):
            return default
        return value

    def save_representative_year_csv(self, ranking_df, filename):
        output_dir = Path(self.download_dir_var.get().strip() or self.default_download_dir())
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / filename
        try:
            ranking_df.to_csv(path, index=False)
            return path
        except PermissionError:
            stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            fallback_path = output_dir / f'{path.stem}_{stamp}{path.suffix}'
            ranking_df.to_csv(fallback_path, index=False)
            return fallback_path

    def direction_to_sector_index(self, directions):
        directions = np.asarray(directions, dtype=float) % 360.0
        return np.floor((directions + SECTOR_WIDTH_DEGREES / 2.0) / SECTOR_WIDTH_DEGREES).astype(int) % len(SECTOR_LABELS)

    def sector_mask(self, directions, sector_index):
        directions = np.asarray(directions, dtype=float)
        mask = np.zeros(len(directions), dtype=bool)
        valid = np.isfinite(directions)
        if valid.any():
            mask[valid] = self.direction_to_sector_index(directions[valid]) == sector_index
        return mask

    def export_directional_data(self):
        context = self.get_selected_directional_export_context()
        if context is None:
            return
        ds, param_var, direction_var = context

        output_dir = filedialog.askdirectory(title='Select folder for 16 directional DFS0 files')
        if not output_dir:
            return
        output_dir = Path(output_dir)

        mikeio = self.load_mikeio_for_dfs0()
        if mikeio is None:
            return

        try:
            param_series = self.extract_series_from_dataset(ds, param_var)
            direction_series = self.extract_series_from_dataset(ds, direction_var) % 360.0
            combined = pd.concat(
                [
                    param_series.rename(self.get_display_name(param_var)),
                    direction_series.rename(self.get_display_name(direction_var)),
                ],
                axis=1,
            ).sort_index()
            combined = self.filter_dataframe_by_analysis_dates(combined, show_error=True)
            if combined.empty:
                return
            lat, lon = self.get_output_coordinate_tokens()
            param_token = self.safe_filename_token(self.get_display_name(param_var))
            generated_paths = []

            for sector_index, sector_label in enumerate(SECTOR_LABELS):
                mask = self.sector_mask(combined.iloc[:, 1].to_numpy(dtype=float), sector_index)
                sector_df = combined.copy()
                sector_df.loc[~mask, :] = np.nan
                items = self.get_mike_item_info(sector_df.columns, mikeio)
                ds_out = mikeio.from_pandas(sector_df, items=items)
                output_path = output_dir / f'ERA5_Lat{lat}_Lon{lon}_{param_token}_{sector_label}.dfs0'
                ds_out.to_dfs(str(output_path))
                generated_paths.append(output_path)

            messagebox.showinfo('Directional Data', f'Created {len(generated_paths)} DFS0 files in:\n{output_dir}')
            self.info_label.config(text=f'Directional DFS0 files for {self.format_analysis_period()} created in {output_dir}.')
        except Exception as exc:
            messagebox.showerror('Directional Data', f'Could not create directional DFS0 files:\n{exc}')

    def get_selected_directional_export_context(self):
        ds = self.get_current_dataset()
        param_var = self.selected_variable.get()
        if ds is None or not param_var:
            messagebox.showwarning('Directional Data', 'Load data and select a parameter first.')
            return None
        if param_var not in ds.data_vars:
            messagebox.showwarning('Directional Data', 'The selected parameter is not available in the current dataset.')
            return None

        if self.current_source.get() == 'oceanic':
            direction_var = self.find_first_variable(ds, ['mwd', 'mean_wave_direction'])
        else:
            if 'wind_dir_10m' not in ds.data_vars:
                self.atm_ds = self.prepare_dataset(ds, 'atmospheric')
                ds = self.atm_ds
            direction_var = self.find_first_variable(ds, ['wind_dir_10m'])

        if direction_var is None:
            messagebox.showwarning('Directional Data', 'No matching direction variable was found for the selected data source.')
            return None
        if param_var == direction_var:
            messagebox.showwarning('Directional Data', 'Select a non-direction parameter such as wave height or wind speed.')
            return None
        return ds, param_var, direction_var

    def get_output_coordinate_tokens(self):
        coords = self.get_coordinates(show_error=False)
        if coords is not None:
            lat, lon = self.snap_to_era5_grid(*coords)
            return f'{lat:.2f}', f'{lon:.2f}'
        return 'unknown', 'unknown'

    def safe_filename_token(self, value):
        token = str(value).strip().replace(' ', '_')
        return ''.join(char for char in token if char.isalnum() or char in ['_', '-', '.']) or 'Parameter'

    def save_plot(self):
        if not self.plot_available:
            messagebox.showwarning('No plot', 'No plot to save. Generate a plot first.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png'), ('PDF', '*.pdf'), ('All files', '*.*')])
        if not path:
            return
        try:
            self.figure.savefig(path)
            messagebox.showinfo('Saved', f'Plot saved to {path}')
        except Exception as exc:
            messagebox.showerror('Save error', f'Could not save plot:\n{exc}')

    def save_data(self):
        if self.atm_ds is None and self.ocn_ds is None:
            messagebox.showwarning('No data', 'Load atmospheric or oceanic data before saving.')
            return

        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('DHI MIKE dfs0', '*.dfs0'), ('CSV', '*.csv')])
        if not path:
            return

        try:
            df = self.build_combined_dataframe()
            if df is None or df.empty:
                messagebox.showwarning('No data', 'No time series variables could be converted for saving.')
                return

            time_range = self.get_current_save_time_range(df)
            if time_range is not None:
                df = df.loc[time_range[0]:time_range[1]]
                if df.empty:
                    messagebox.showwarning('No data', f'No data were found from {self.format_analysis_period(time_range)}.')
                    return

            if path.lower().endswith('.csv'):
                self.save_dataframe_to_csv(path, df)
                messagebox.showinfo('Saved', f'Data saved to {path}')
            elif path.lower().endswith('.dfs0'):
                mikeio = self.load_mikeio_for_dfs0()
                if mikeio is None:
                    return
                try:
                    variable_items = self.get_mike_item_info(df.columns, mikeio)
                    ds_out = mikeio.from_pandas(df, items=variable_items)
                    ds_out.to_dfs(path)
                    messagebox.showinfo('Saved', f'Data saved to {path}')
                except Exception as exc:
                    messagebox.showerror('DFS0 write error', f'Could not write DFS0 file:\n{exc}')
            else:
                self.save_dataframe_to_csv(path, df)
                messagebox.showinfo('Saved', f'Data saved to {path}')
        except Exception as exc:
            messagebox.showerror('Save error', f'Could not save data:\n{exc}')

    def save_dataframe_to_csv(self, path, df):
        export_df = df.copy()
        export_df.index.name = 'Time'
        units = [self.get_display_unit(col) for col in export_df.columns]

        try:
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Time'] + list(export_df.columns))
                writer.writerow([''] + units)
                for index, row in export_df.iterrows():
                    if hasattr(index, 'strftime'):
                        index_value = index.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        index_value = str(index)
                    writer.writerow([index_value] + list(row.values))
        except Exception as exc:
            messagebox.showerror('CSV save error', f'Could not write CSV file:\n{exc}')

    def load_mikeio_for_dfs0(self):
        try:
            import mikeio
            return mikeio
        except ModuleNotFoundError as exc:
            if exc.name == 'mikeio':
                message = 'Saving to .dfs0 requires the mikeio package. Install with: pip install mikeio'
            else:
                message = (
                    'The mikeio package is installed, but one of its dependencies '
                    f'could not be loaded:\n{exc.name}\n\n{exc}'
                )
        except Exception as exc:
            message = (
                'The mikeio package is installed, but it could not be initialized:\n'
                f'{type(exc).__name__}: {exc}'
            )

        messagebox.showerror('DFS0 save error', message)
        return None

    def get_current_save_time_range(self, df):
        if len(df) == 0:
            return None
        return self.get_analysis_date_range(show_error=True)

    def build_combined_dataframe(self):
        frames = []
        if self.atm_ds is not None:
            atm_df = self.build_dataset_dataframe(self.atm_ds)
            if atm_df is not None:
                frames.append(atm_df)
        if self.ocn_ds is not None:
            ocn_df = self.build_dataset_dataframe(self.ocn_ds)
            if ocn_df is not None:
                frames.append(ocn_df)

        if not frames:
            return None

        combined = pd.concat(frames, axis=1)
        combined = combined.sort_index()
        combined = self.rename_save_columns(combined)
        return combined

    def rename_save_columns(self, df):
        mapping = self.get_save_variable_mapping()
        renamed = df.rename(columns=mapping)
        # avoid duplicate columns after renaming
        cols = []
        counts = {}
        for col in renamed.columns:
            if col in cols:
                counts[col] = counts.get(col, 1) + 1
                new_col = f'{col}_{counts[col]}'
            else:
                counts[col] = 1
                new_col = col
            cols.append(new_col)
        renamed.columns = cols
        return renamed

    def get_save_variable_mapping(self):
        return {
            'swh': 'Significant wave height',
            'significant_height_of_combined_wind_waves_and_swell': 'Significant wave height',
            'mwp': 'Wave period',
            'mean_wave_period': 'Wave period',
            'mwd': 'Wave direction',
            'mean_wave_direction': 'Wave direction',
            'u10': 'U velocity',
            '10m_u_component_of_wind': 'U velocity',
            'v10': 'V velocity',
            '10m_v_component_of_wind': 'V velocity',
            'u100': '100m U velocity',
            '100m_u_component_of_wind': '100m U velocity',
            'v100': '100m V velocity',
            '100m_v_component_of_wind': '100m V velocity',
            'wind_speed_10m': 'Wind speed',
            'wind_dir_10m': 'Wind direction',
            'fg10': '10m wind gust',
            '10m_wind_gust_since_previous_post_processing': '10m wind gust',
            'tp': 'Precipitation rate',
            'total_precipitation': 'Precipitation rate',
            'msl': 'Air pressure',
            'mean_sea_level_pressure': 'Air pressure',
            'sp': 'Surface pressure',
            'surface_pressure': 'Surface pressure',
            't2m': '2m temperature',
            '2m_temperature': '2m temperature',
            'd2m': '2m dewpoint',
            '2m_dewpoint_temperature': '2m dewpoint',
            'skt': 'Skin temperature',
            'skin_temperature': 'Skin temperature',
            'sst': 'Sea surface temperature',
            'sea_surface_temperature': 'Sea surface temperature',
            'ssrd': 'Surface solar radiation',
            'surface_solar_radiation_downwards': 'Surface solar radiation',
            'fdir': 'Direct solar radiation',
            'total_sky_direct_solar_radiation_at_surface': 'Direct solar radiation',
            'strd': 'Surface thermal radiation',
            'surface_thermal_radiation_downwards': 'Surface thermal radiation',
            'blh': 'Boundary layer height',
            'boundary_layer_height': 'Boundary layer height',
            'cbh': 'Cloud base height',
            'cloud_base_height': 'Cloud base height',
            'tcc': 'Total cloud cover',
            'total_cloud_cover': 'Total cloud cover',
        }

    def get_save_variable_unit_mapping(self):
        return {
            'Significant wave height': 'm',
            'Wave period': 's',
            'Wave direction': '°',
            'U velocity': 'm/s',
            'V velocity': 'm/s',
            '100m U velocity': 'm/s',
            '100m V velocity': 'm/s',
            'Wind speed': 'm/s',
            'Wind direction': '°',
            '10m wind gust': 'm/s',
            'Precipitation rate': 'mm/hr',
            'Air pressure': 'Pa',
            'Surface pressure': 'Pa',
            '2m temperature': 'K',
            '2m dewpoint': 'K',
            'Skin temperature': 'K',
            'Sea surface temperature': 'K',
            'Surface solar radiation': 'J/m^2',
            'Direct solar radiation': 'J/m^2',
            'Surface thermal radiation': 'J/m^2',
            'Boundary layer height': 'm',
            'Cloud base height': 'm',
            'Total cloud cover': 'fraction',
        }

    def get_display_name(self, var_name):
        mapping = self.get_save_variable_mapping()
        return mapping.get(var_name, var_name)

    def get_display_unit(self, var_name):
        unit_mapping = self.get_save_variable_unit_mapping()
        if var_name in unit_mapping:
            return unit_mapping[var_name]
        display_name = self.get_display_name(var_name)
        return unit_mapping.get(display_name, '')

    def get_mike_item_info(self, columns, mikeio):
        mapping = {
            'Significant wave height': (mikeio.EUMType.Significant_wave_height, mikeio.EUMUnit.meter),
            'Wave period': (mikeio.EUMType.Wave_period, mikeio.EUMUnit.second),
            'Wave direction': (mikeio.EUMType.Wave_direction, mikeio.EUMUnit.degree),
            'U velocity': (mikeio.EUMType.u_velocity_component, mikeio.EUMUnit.meter_per_sec),
            'V velocity': (mikeio.EUMType.v_velocity_component, mikeio.EUMUnit.meter_per_sec),
            'Wind speed': (mikeio.EUMType.Wind_speed, mikeio.EUMUnit.meter_per_sec),
            'Wind direction': (mikeio.EUMType.Wind_Direction, mikeio.EUMUnit.degree),
            'Precipitation rate': (mikeio.EUMType.Precipitation_Rate, mikeio.EUMUnit.mm_per_hour),
            'Air pressure': (mikeio.EUMType.Air_Pressure, mikeio.EUMUnit.pascal),
        }

        items = []
        for col in columns:
            if col in mapping:
                eum_type, eum_unit = mapping[col]
                items.append(mikeio.ItemInfo(name=col, itemtype=eum_type, unit=eum_unit))
            else:
                items.append(mikeio.ItemInfo(name=col))
        return items

    def build_dataset_dataframe(self, ds):
        time_dim = next((dim for dim in ds.dims if dim in TIME_DIMS), None)
        if time_dim is None:
            return None

        series_list = []
        for var_name in sorted(ds.data_vars.keys()):
            da = ds[var_name]
            if time_dim not in da.dims:
                continue
            spatial_dims = [dim for dim in da.dims if dim != time_dim]
            if spatial_dims:
                da = da.mean(dim=spatial_dims, skipna=True)
            try:
                time_index = pd.to_datetime(da[time_dim].values)
            except Exception:
                continue
            series = pd.Series(da.values, index=time_index, name=var_name)
            series_list.append(series)

        if not series_list:
            return None

        df = pd.concat(series_list, axis=1)
        df = df.sort_index()
        return df

    def show_statistics(self, series, var_name):
        display_name = self.get_display_name(var_name)
        unit = self.get_display_unit(var_name)
        stats = series.describe(percentiles=[0.25, 0.5, 0.75])
        title_line = f'Statistics for {display_name} ({unit})\n' if unit else f'Statistics for {display_name}\n'
        stats_str = (
            title_line +
            f'Period: {series.index.min().strftime("%Y-%m-%d")} to {series.index.max().strftime("%Y-%m-%d")}\n'
            f'Count: {int(stats["count"])}\n'
            f'Mean: {stats["mean"]:.6g}\n'
            f'Std: {stats["std"]:.6g}\n'
            f'Min: {stats["min"]:.6g}\n'
            f'25%: {stats["25%"]:.6g}\n'
            f'50% (median): {stats["50%"]:.6g}\n'
            f'75%: {stats["75%"]:.6g}\n'
            f'Max: {stats["max"]:.6g}\n'
        )
        self.set_stats_text(stats_str)


def main():
    root = tk.Tk()
    app = ERA5TimeSeriesApp(root)
    root.geometry('1360x900')
    root.mainloop()


if __name__ == '__main__':
    main()
