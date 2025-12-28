import tkinter as tk
from _typeshed import Incomplete

class Plot1DRealWindow(tk.Toplevel):
    parent: Incomplete
    cloud_group: Incomplete
    exp_obj: Incomplete
    exp_id: Incomplete
    exp_detail: Incomplete
    sweeps: Incomplete
    res_obj: Incomplete
    keys: Incomplete
    fig_title: Incomplete
    control_frame: Incomplete
    dim0_options: Incomplete
    figure: Incomplete
    canvas: Incomplete
    toolbar: Incomplete
    canvas_widget: Incomplete
    ax: Incomplete
    lines: Incomplete
    dim0_label: Incomplete
    dim1_label: Incomplete
    animation_active: bool
    last_update_time: Incomplete
    last_res_obj_update_time: Incomplete
    last_res_obj_update_index: int
    points_per_second: int
    current_point: int
    update_interval: int
    animation_id: Incomplete
    def __init__(self, parent, title, cloud_group, exp_obj, exp_id, exp_detail, sweeps, res_obj, keys, dim0_label, dim1_label, x_ticks, y_ticks) -> None: ...
    def initialize_plot(self) -> None: ...
    x_var: Incomplete
    x_selector: Incomplete
    def create_dimension_selectors(self): ...
    x_label: Incomplete
    def update_axes_from_selection(self) -> None: ...
    def redraw_plot(self) -> None: ...
    def start_animation(self) -> None: ...
    def stop_animation(self) -> None: ...
    def update_plot_incremental(self) -> None: ...
    def redraw(self) -> None: ...
