import tkinter as tk
from _typeshed import Incomplete

class Plot1DFullIQWindow(tk.Toplevel):
    parent: Incomplete
    cloud_group: Incomplete
    exp_id: Incomplete
    exp_detail: Incomplete
    sweeps: Incomplete
    res_obj: Incomplete
    keys: Incomplete
    fig_title: Incomplete
    figure: Incomplete
    canvas: Incomplete
    toolbar: Incomplete
    control_frame: Incomplete
    play_button: Incomplete
    stop_button: Incomplete
    speed_var: Incomplete
    speed_menu: Incomplete
    progress_var: Incomplete
    progress_scale: Incomplete
    index_var: Incomplete
    status_var: Incomplete
    canvas_widget: Incomplete
    ax: Incomplete
    current_data_index: int
    complex_points: Incomplete
    total_points: int
    dim0_label: Incomplete
    dim1_label: Incomplete
    animation_active: bool
    last_update_time: Incomplete
    update_interval: int
    animation_id: Incomplete
    max_wait_time: float
    wait_start_time: int
    speed_mapping: Incomplete
    def __init__(self, parent, title, cloud_group, exp_id, exp_detail, sweeps, res_obj, keys, dim0_label, dim1_label, x_ticks, y_ticks) -> None: ...
    def initialize_plot(self) -> None: ...
    def on_progress_change(self, event=None) -> None: ...
    def update_index_display(self) -> None: ...
    def start_animation(self) -> None: ...
    def stop_animation(self) -> None: ...
    def update_plot(self) -> None: ...
    def redraw(self) -> None: ...
