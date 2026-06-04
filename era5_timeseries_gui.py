import tkinter as tk
from tkinter import filedialog, messagebox
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import csv


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
        self.updating_sliders = False

        controls = tk.Frame(master)
        controls.pack(fill='x', padx=8, pady=8)

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

        variable_frame = tk.Frame(master)
        variable_frame.pack(fill='x', padx=8, pady=4)
        tk.Label(variable_frame, text='Select variable:').grid(row=0, column=0, sticky='w')
        self.variable_menu = tk.OptionMenu(variable_frame, self.selected_variable, '')
        self.variable_menu.grid(row=0, column=1, sticky='we', padx=4)
        variable_frame.columnconfigure(1, weight=1)

        action_frame = tk.Frame(master)
        action_frame.pack(fill='x', padx=8, pady=4)
        plot_btn = tk.Button(action_frame, text='Plot time series', command=self.plot_time_series)
        plot_btn.pack(side='left', padx=4)
        stats_btn = tk.Button(action_frame, text='Show statistics', command=self.update_current_stats)
        stats_btn.pack(side='left', padx=4)
        save_plot_btn = tk.Button(action_frame, text='Save plot', command=self.save_plot)
        save_plot_btn.pack(side='left', padx=4)
        save_data_btn = tk.Button(action_frame, text='Save data', command=self.save_data)
        save_data_btn.pack(side='left', padx=4)

        output_frame = tk.Frame(master)
        output_frame.pack(fill='both', padx=8, pady=4, expand=True)

        self.figure = Figure(figsize=(7, 3.5), tight_layout=True)
        self.ax = self.figure.add_subplot(111)
        self.ax.callbacks.connect('xlim_changed', self.on_xlim_changed)
        self.canvas = FigureCanvasTkAgg(self.figure, master=output_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # slider frame moved just below plot
        self.slider_frame = tk.Frame(master)
        self.slider_frame.pack(fill='x', padx=8, pady=4)
        tk.Label(self.slider_frame, text='Subset range:').grid(row=0, column=0, sticky='w')
        self.start_label = tk.Label(self.slider_frame, text='Start: -', anchor='w')
        self.start_label.grid(row=1, column=0, sticky='w')
        self.end_label = tk.Label(self.slider_frame, text='End: -', anchor='w')
        self.end_label.grid(row=2, column=0, sticky='w')
        self.start_scale = tk.Scale(self.slider_frame, from_=0, to=0, orient='horizontal', command=self.on_slider_change, state='disabled')
        self.start_scale.grid(row=1, column=1, sticky='we', padx=4)
        self.end_scale = tk.Scale(self.slider_frame, from_=0, to=0, orient='horizontal', command=self.on_slider_change, state='disabled')
        self.end_scale.grid(row=2, column=1, sticky='we', padx=4)
        self.slider_frame.columnconfigure(1, weight=1)

        self.stats_text = tk.Text(master, height=10, wrap='word')
        self.stats_text.pack(fill='both', padx=8, pady=4, expand=False)

        self.info_label = tk.Label(master, text='Load both atmospheric and oceanic ERA5 .nc files, then select a source and variable.', anchor='w')
        self.info_label.pack(fill='x', padx=8, pady=2)

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

        # If atmospheric data contains u10 and v10, compute wind speed and direction
        if source == 'atmospheric' and {'u10', 'v10'}.issubset(set(ds.data_vars)):
            try:
                u = ds['u10']
                v = ds['v10']
                # wind speed (m/s)
                ws = np.hypot(u, v)
                # wind direction (degrees, meteorological: direction FROM which the wind blows, clockwise from North)
                wd = (np.degrees(np.arctan2(-u, -v)) + 360) % 360
                # assign new variables into the dataset (preserve original ds variable)
                ds = ds.assign(wind_speed_10m=ws, wind_dir_10m=wd)
            except Exception as exc:
                messagebox.showwarning('Wind calc', f'Could not compute wind speed/direction:\n{exc}')

        if source == 'atmospheric':
            self.atm_ds = ds
            self.atm_path_label.config(text=f'Atmospheric file: {path}')
            self.current_source.set('atmospheric')
        else:
            self.ocn_ds = ds
            self.ocn_path_label.config(text=f'Oceanic file: {path}')
            self.current_source.set('oceanic')

        self.update_variable_menu()
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

        variables = sorted(ds.data_vars.keys())
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
        self.setup_sliders()
        self.update_plot(self.full_series)
        self.show_statistics(self.full_series, var_name)

    def reduce_to_time_series(self, da):
        time_dim = next((dim for dim in da.dims if dim in ['time', 'date', 'valid_time']), None)
        if time_dim is None:
            raise ValueError('The selected variable has no supported time dimension.')

        spatial_dims = [dim for dim in da.dims if dim != time_dim]
        if spatial_dims:
            da = da.mean(dim=spatial_dims, skipna=True)

        if da.ndim != 1 or da.sizes.get(time_dim, 0) == 0:
            raise ValueError('Unable to reduce variable to a one-dimensional time series.')

        return da

    def extract_time_index(self, da):
        time_dim = next((dim for dim in da.dims if dim in ['time', 'date', 'valid_time']), None)
        if time_dim is None:
            raise ValueError('No supported time coordinate found in the dataset.')

        time_values = da[time_dim].values
        time_index = pd.to_datetime(time_values)
        return time_index

    def setup_sliders(self):
        length = len(self.full_series)
        if length == 0:
            self.start_scale.config(state='disabled')
            self.end_scale.config(state='disabled')
            return

        self.updating_sliders = True
        self.start_scale.config(from_=0, to=max(0, length - 1), state='normal')
        self.end_scale.config(from_=0, to=max(0, length - 1), state='normal')
        self.start_scale.set(0)
        self.end_scale.set(length - 1)
        self.update_slider_labels(0, length - 1)
        self.updating_sliders = False

    def update_slider_labels(self, start_idx, end_idx):
        if self.full_series is None or len(self.full_series) == 0:
            self.start_label.config(text='Start: -')
            self.end_label.config(text='End: -')
            return

        start_dt = self.full_series.index[start_idx]
        end_dt = self.full_series.index[end_idx]
        self.start_label.config(text=f'Start: {start_dt.strftime("%Y-%m-%d %H:%M")}')
        self.end_label.config(text=f'End: {end_dt.strftime("%Y-%m-%d %H:%M")}')

    def on_slider_change(self, _value):
        if self.full_series is None or self.updating_sliders:
            return

        start = int(self.start_scale.get())
        end = int(self.end_scale.get())
        if end < start:
            end = start
            self.updating_sliders = True
            self.end_scale.set(end)
            self.updating_sliders = False

        self.apply_index_range(start, end)

    def apply_index_range(self, start, end):
        subset = self.full_series.iloc[start:end + 1]
        if subset.empty:
            return

        self.update_plot(subset)
        self.show_statistics(subset, self.current_var_name)
        self.update_slider_labels(start, end)

    def update_current_stats(self):
        if self.full_series is None:
            return

        start = int(self.start_scale.get())
        end = int(self.end_scale.get())
        subset = self.full_series.iloc[start:end + 1]
        if subset.empty:
            return

        self.show_statistics(subset, self.current_var_name)
        self.update_slider_labels(start, end)

    def update_plot(self, series):
        self.ax.clear()
        self.ax.plot(series.index, series.values, linestyle='-', color='tab:blue')
        title = self.current_var_display_name if hasattr(self, 'current_var_display_name') else self.current_var_name
        unit = self.current_var_units if hasattr(self, 'current_var_units') else ''
        ylabel = f'{title} ({unit})' if unit else title
        self.ax.set_title(f'{title} time series')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True)
        self.figure.autofmt_xdate()
        self.canvas.draw()

    def on_xlim_changed(self, ax):
        if self.full_series is None or self.current_var_name is None:
            return

        left, right = ax.get_xlim()
        left_dt = mdates.num2date(left).replace(tzinfo=None)
        right_dt = mdates.num2date(right).replace(tzinfo=None)
        subset = self.full_series.loc[(self.full_series.index >= left_dt) & (self.full_series.index <= right_dt)]
        if subset.empty:
            return

        self.show_statistics(subset, self.current_var_name)

        start = int(np.searchsorted(self.full_series.index, subset.index[0]))
        end = int(np.searchsorted(self.full_series.index, subset.index[-1], side='right') - 1)
        if 0 <= start < len(self.full_series) and 0 <= end < len(self.full_series):
            self.updating_sliders = True
            self.start_scale.set(start)
            self.end_scale.set(end)
            self.update_slider_labels(start, end)
            self.updating_sliders = False

    def get_current_subset(self):
        if self.full_series is None:
            return None
        try:
            start = int(self.start_scale.get())
            end = int(self.end_scale.get())
        except Exception:
            start = 0
            end = len(self.full_series) - 1
        if end < start:
            end = start
        return self.full_series.iloc[start:end + 1]

    def save_plot(self):
        if self.full_series is None:
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

            if path.lower().endswith('.csv'):
                self.save_dataframe_to_csv(path, df)
                messagebox.showinfo('Saved', f'Data saved to {path}')
            elif path.lower().endswith('.dfs0'):
                try:
                    import mikeio
                except Exception:
                    messagebox.showerror('DFS0 save error', 'Saving to .dfs0 requires the mikeio package. Install with: pip install mikeio')
                    return
                try:
                    variable_items = self.get_mike_item_info(df.columns)
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

    def get_current_save_time_range(self, df):
        if self.full_series is None or len(df) == 0:
            return None
        try:
            start = int(self.start_scale.get())
            end = int(self.end_scale.get())
        except Exception:
            return None
        if end < start:
            end = start
        if start < 0 or end >= len(self.full_series):
            return None
        start_ts = self.full_series.index[start]
        end_ts = self.full_series.index[end]
        return start_ts, end_ts

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
            'mwp': 'Wave period',
            'mwd': 'Wave direction',
            'u10': 'U velocity',
            'v10': 'V velocity',
            'wind_speed_10m': 'Wind speed',
            'wind_dir_10m': 'Wind direction',
            'tp': 'Precipitation rate',
            'msl': 'Air pressure',
        }

    def get_save_variable_unit_mapping(self):
        return {
            'Significant wave height': 'm',
            'Wave period': 's',
            'Wave direction': '°',
            'U velocity': 'm/s',
            'V velocity': 'm/s',
            'Wind speed': 'm/s',
            'Wind direction': '°',
            'Precipitation rate': 'mm/hr',
            'Air pressure': 'Pa',
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

    def get_mike_item_info(self, columns):
        try:
            import mikeio
        except Exception:
            return None

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
        time_dim = next((dim for dim in ds.dims if dim in ['time', 'date', 'valid_time']), None)
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
            f'Count: {int(stats["count"])}\n'
            f'Mean: {stats["mean"]:.6g}\n'
            f'Std: {stats["std"]:.6g}\n'
            f'Min: {stats["min"]:.6g}\n'
            f'25%: {stats["25%"]:.6g}\n'
            f'50% (median): {stats["50%"]:.6g}\n'
            f'75%: {stats["75%"]:.6g}\n'
            f'Max: {stats["max"]:.6g}\n'
        )
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert(tk.END, stats_str)


def main():
    root = tk.Tk()
    app = ERA5TimeSeriesApp(root)
    root.geometry('900x720')
    root.mainloop()


if __name__ == '__main__':
    main()
