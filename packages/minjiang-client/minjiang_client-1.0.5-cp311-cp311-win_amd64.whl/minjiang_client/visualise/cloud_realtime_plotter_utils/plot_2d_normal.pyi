import tkinter as tk
from _typeshed import Incomplete

class Plot2DWindow(tk.Toplevel):
    parent: Incomplete
    cloud_group: Incomplete
    exp_obj: Incomplete
    exp_id: Incomplete
    exp_detail: Incomplete
    sweeps: Incomplete
    res_obj: Incomplete
    keys: Incomplete
    fig_title: Incomplete
    sweeps_info: Incomplete
    control_frame: Incomplete
    dim0_options: Incomplete
    dim1_options: Incomplete
    figure: Incomplete
    canvas: Incomplete
    toolbar: Incomplete
    canvas_widget: Incomplete
    ax: Incomplete
    images: Incomplete
    cbar: Incomplete
    initialized: Incomplete
    display_data: Incomplete
    x_label: Incomplete
    y_label: Incomplete
    x_ticks: Incomplete
    y_ticks: Incomplete
    original_x_label: Incomplete
    original_y_label: Incomplete
    original_x_ticks: Incomplete
    original_y_ticks: Incomplete
    animation_active: bool
    last_update_time: Incomplete
    update_interval: int
    animation_id: Incomplete
    pending_points: Incomplete
    displayed_mask: Incomplete
    points_per_second: int
    last_res_obj_update_time: Incomplete
    last_loaded_count: int
    data_shape: Incomplete
    vmin: Incomplete
    vmax: Incomplete
    set_xy_lim: bool
    norm: Incomplete
    latest_step: int
    def __init__(self, parent, title, cloud_group, exp_obj, exp_id, exp_detail, sweeps, res_obj, keys, x_label, y_label, x_ticks, y_ticks) -> None: ...
    x_var: Incomplete
    x_selector: Incomplete
    y_var: Incomplete
    y_selector: Incomplete
    def create_dimension_selectors(self): ...
    def update_axes_from_selection(self) -> None: ...
    def redraw_plot(self) -> None: ...
    def plot_heatmap_2d_by_col(self, x_coords, y_coords, vectors) -> None: ...
    def initialize_plot(self) -> None: ...
    def redraw(self) -> None: ...
