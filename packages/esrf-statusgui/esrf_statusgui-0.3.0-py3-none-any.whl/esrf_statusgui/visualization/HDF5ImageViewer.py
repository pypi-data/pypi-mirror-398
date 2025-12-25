from __future__ import annotations

# mypy: allow-untyped-defs
import math
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display
from matplotlib.colors import LogNorm, Normalize, PowerNorm, SymLogNorm

try:
    from esrf_loadFile import loadFile
except ImportError:
    from esrf_statusgui.data_managment.loadFile import loadFile

# Always manage figures explicitly in widget contexts
plt.ioff()
_LAYOUT_WIDTH = "100%"  # Use valid CSS percentage


class HDF5ImageViewer:
    """
    HDF5ImageViewer

    A resilient Jupyter widget to browse n-D HDF5 datasets as 2D images along a chosen axis.
    """

    # ---- UI sizes
    BUTTON_WIDTH = "100px"
    SLIDER_WIDTH = "auto"
    SLIDER_MIN_WIDTH = "250px"
    CONTROLS_WIDTH = "260px"
    DROPDOWN_WIDTH = "220px"
    RANGE_SLIDER_WIDTH = "220px"

    def __init__(
        self,
        h5_file_path: str,
        dataset_name: str = "entry0000/reconstruction/results/data",
        *,
        title: str | None = None,
    ) -> None:
        self.dataset_name = dataset_name

        # Load dataset
        try:
            self.h5_file = loadFile(h5_file_path)
        except Exception as exc:
            raise RuntimeError(f"Could not open HDF5 file: {h5_file_path!r}") from exc

        try:
            data = self.h5_file.get_value(self.dataset_name)
        except Exception as exc:
            raise RuntimeError(
                f"Dataset {dataset_name!r} not found or unreadable in {h5_file_path!r}"
            ) from exc

        if data is None:
            raise RuntimeError(f"Dataset {dataset_name!r} returned None")

        self.images_dataset = np.asarray(data)
        if self.images_dataset.ndim < 2:
            raise ValueError(
                f"Expected at least 2-D data to form images; got shape {self.images_dataset.shape}"
            )

        # State
        self._updating = False
        self._cached_moveaxis: np.ndarray | None = None
        self._last_cached_axis: int | None = None

        # ---- Widgets
        max_index0 = max(0, self.images_dataset.shape[0] - 1)
        self.index_slider = widgets.IntSlider(
            value=0,
            min=0,
            max=max_index0,
            step=1,
            description="Index",
            layout=widgets.Layout(
                width=self.SLIDER_WIDTH,
                min_width=self.SLIDER_MIN_WIDTH,
                flex="1 1 auto",
            ),
        )
        self.left_button = widgets.Button(
            description="< 1",
            icon="arrow-left",
            layout=widgets.Layout(width=self.BUTTON_WIDTH),
        )
        self.right_button = widgets.Button(
            description="> 1",
            icon="arrow-right",
            layout=widgets.Layout(width=self.BUTTON_WIDTH),
        )
        self.left_10_button = widgets.Button(
            description="< 10",
            icon="arrow-left",
            layout=widgets.Layout(width=self.BUTTON_WIDTH),
        )
        self.right_10_button = widgets.Button(
            description="> 10",
            icon="arrow-right",
            layout=widgets.Layout(width=self.BUTTON_WIDTH),
        )

        self.dimension_picker = widgets.RadioButtons(
            options=[
                (f"Axis {i} (size {s})", i)
                for i, s in enumerate(self.images_dataset.shape)
            ],
            value=0,
            description="Browse axis:",
            layout=widgets.Layout(width=self.DROPDOWN_WIDTH),
        )

        # Colormap choices as a sorted list of names
        cmap_names = sorted([str(c) for c in plt.colormaps()])
        default_cmap = "viridis" if "viridis" in cmap_names else cmap_names[0]
        self.cmap_selector = widgets.Dropdown(
            options=cmap_names,
            description="Colormap:",
            value=default_cmap,
            layout=widgets.Layout(width=self.DROPDOWN_WIDTH),
        )

        self.scaling_selector = widgets.Dropdown(
            options=["linear", "log", "symlog", "sqrt"],
            description="Scaling:",
            value="linear",
            layout=widgets.Layout(width=self.DROPDOWN_WIDTH),
        )

        # Min/Max sliders + Autoscale toggles
        self.range_slider = widgets.FloatRangeSlider(
            description="Threshold",
            step=0.05,
            layout=widgets.Layout(width=self.RANGE_SLIDER_WIDTH),
            readout=False,
        )
        self.autoscale_min_button = widgets.Button(
            description="Min",
            layout=widgets.Layout(width=self.BUTTON_WIDTH),
        )
        self.autoscale_max_button = widgets.Button(
            description="Max",
            layout=widgets.Layout(width=self.BUTTON_WIDTH),
        )

        # Title
        self._title_html = widgets.HTML(
            value=f"<b>{title or 'HDF5 Image Viewer'}</b><br><small>{self.dataset_name}</small>"
        )

        # Matplotlib figure
        self.image_plot = None
        self.colorbar = None
        self.fig_output = widgets.Output(
            layout=widgets.Layout(width="auto", flex="1 1 auto")
        )
        with self.fig_output:
            self.fig, self.ax = plt.subplots(constrained_layout=True)
            self.canvas = self.fig.canvas
            display(self.canvas)

        # Autoscale state
        self.autoscale_min_active = True
        self.autoscale_max_active = True

        # Bind events
        self.index_slider.observe(self._on_index_change, names="value")
        self.dimension_picker.observe(self._on_dimension_change, names="value")
        self.cmap_selector.observe(self._on_any_visual_change, names="value")
        self.scaling_selector.observe(self._on_any_visual_change, names="value")
        self.range_slider.observe(self._on_range_change, names="value")

        self.autoscale_min_button.on_click(self._toggle_autoscale_min)
        self.autoscale_max_button.on_click(self._toggle_autoscale_max)

        self.left_button.on_click(lambda _: self._move(-1))
        self.right_button.on_click(lambda _: self._move(+1))
        self.left_10_button.on_click(lambda _: self._move(-10))
        self.right_10_button.on_click(lambda _: self._move(+10))

        # Layout
        navigation_row = widgets.HBox(
            [
                self.left_10_button,
                self.left_button,
                self.index_slider,
                self.right_button,
                self.right_10_button,
            ],
            layout=widgets.Layout(
                width=_LAYOUT_WIDTH,
                display="flex",
                flex_flow="row wrap",
                justify_content="space-between",
            ),
        )

        controls = widgets.VBox(
            [
                self._title_html,
                self.dimension_picker,
                widgets.HTML(value="<b>Colors</b>"),
                self.cmap_selector,
                self.scaling_selector,
                widgets.HTML(value="<b>Color threshold</b>"),
                self.range_slider,
                widgets.HTML(value="<b>Auto-threshold</b>"),
                widgets.HBox([self.autoscale_min_button, self.autoscale_max_button]),
            ],
            layout=widgets.Layout(width=self.CONTROLS_WIDTH),
        )

        content_row = widgets.HBox(
            [self.fig_output, controls],
            layout=widgets.Layout(
                width=_LAYOUT_WIDTH,
                display="flex",
                flex_flow="row wrap",
                justify_content="space-between",
            ),
        )

        self.ui = widgets.VBox(
            [navigation_row, content_row],
            layout=widgets.Layout(
                width=_LAYOUT_WIDTH,
                display="flex",
                flex_flow="column nowrap",
                align_items="stretch",
            ),
        )

        # Initial display
        self._refresh_index_bounds()
        self._display_image()

    # ------------------------- internal utils -------------------------

    @contextmanager
    def _suspend(self, *traits: widgets.Widget) -> Iterator[None]:
        """Temporarily unbind observers for the given widgets to avoid feedback loops."""

        try:
            self._updating = True
            yield
        finally:
            self._updating = False

    def _safe_minmax(self, arr: np.ndarray) -> tuple[float, float]:
        """Compute finite min/max; fall back to (0, 1) if empty or all non-finite."""
        a = np.asarray(arr)
        a = a[np.isfinite(a)]
        if a.size == 0:
            return (0.0, 1.0)
        vmin = float(np.nanmin(a))
        vmax = float(np.nanmax(a))
        if not np.isfinite(vmin) or not np.isfinite(vmax):
            return (0.0, 1.0)
        if vmin == vmax:
            # Expand a touch so matplotlib doesn't choke
            delta = 1.0 if vmin == 0.0 else 0.01 * abs(vmin) + 1e-9
            return (vmin - delta, vmax + delta)
        return (vmin, vmax)

    def _slice_to_2d(self, data: np.ndarray, axis: int, index: int) -> np.ndarray:
        """
        Take one index along `axis`, then reduce to 2D by keeping the last two axes.
        Any extra leading axes are indexed at 0 (deterministic & fast).
        """
        if axis < 0 or axis >= data.ndim:
            axis = 0  # guard

        img = np.take(data, indices=index, axis=axis)

        # If still higher than 2D, keep last two axes and take 0 on the rest.
        while img.ndim > 2:
            # choose the first axis except keep the last two intact
            drop_axis = 0 if img.ndim > 2 else None
            if drop_axis is None:
                break
            img = np.take(img, indices=0, axis=drop_axis)

        if img.ndim == 1:
            # Degenerate line: expand to (1, N) so imshow can render
            img = img[np.newaxis, :]

        return img

    def _choose_norm(self, vmin: float, vmax: float) -> Normalize | None:
        scaling = self.scaling_selector.value
        # Ensure vmin < vmax
        if not (math.isfinite(vmin) and math.isfinite(vmax)) or vmin >= vmax:
            vmin, vmax = min(vmin, vmax) - 1e-9, max(vmin, vmax) + 1e-9

        if scaling == "linear":
            return None
        elif scaling == "log":
            # Make positive
            vmin = max(vmin, 1e-12)
            vmax = max(vmax, vmin + 1e-9)
            # Also fix slider if needed
            self._ensure_slider_positive(vmin, vmax)
            return LogNorm(vmin=vmin, vmax=vmax)
        elif scaling == "symlog":
            # SymLog allows negatives but needs linthresh > 0
            linthresh = 1e-5
            # Ensure symmetric-ish around zero if both signs present
            # Otherwise just pass through.
            return SymLogNorm(linthresh=linthresh, vmin=vmin, vmax=vmax)
        elif scaling == "sqrt":
            # PowerNorm with gamma=0.5 assumes non-negative
            vmin = max(vmin, 0.0)
            vmax = max(vmax, vmin + 1e-9)
            self._ensure_slider_nonnegative(vmin, vmax)
            return PowerNorm(gamma=0.5, vmin=vmin, vmax=vmax)
        else:
            return None

    def _ensure_slider_positive(self, vmin: float, vmax: float) -> None:
        # Adjust slider to positive if needed
        with self._suspend(self.range_slider):
            self.range_slider.min = max(self.range_slider.min, 1e-12)
            self.range_slider.value = (
                max(self.range_slider.value[0], 1e-12),
                max(self.range_slider.value[1], 1e-12),
            )
            self.range_slider.max = max(
                self.range_slider.max, self.range_slider.value[1], vmax
            )

    def _ensure_slider_nonnegative(self, vmin: float, vmax: float) -> None:
        with self._suspend(self.range_slider):
            self.range_slider.min = max(self.range_slider.min, 0.0)
            lo, hi = self.range_slider.value
            self.range_slider.value = (max(lo, 0.0), max(hi, max(lo + 1e-9, vmax)))

    def _refresh_index_bounds(self) -> None:
        dim = int(self.dimension_picker.value)
        size = int(self.images_dataset.shape[dim])
        with self._suspend(self.index_slider):
            self.index_slider.max = max(0, size - 1)
            if self.index_slider.value > self.index_slider.max:
                self.index_slider.value = self.index_slider.max

    def _maybe_update_cache(self, axis: int) -> None:
        """
        If browsing along the last axis, cache a moveaxis()-ed view so moving the index is faster.
        """
        if axis == self.images_dataset.ndim - 1:
            if self._last_cached_axis != axis or self._cached_moveaxis is None:
                self._cached_moveaxis = np.moveaxis(self.images_dataset, axis, 0)
                self._last_cached_axis = axis
        else:
            self._cached_moveaxis = None
            self._last_cached_axis = None

    # ------------------------- event handlers -------------------------

    def _on_index_change(self, _change) -> None:
        if self._updating:
            return
        self._display_image()

    def _on_dimension_change(self, _change) -> None:
        if self._updating:
            return
        self._refresh_index_bounds()
        self._display_image()

    def _on_any_visual_change(self, _change) -> None:
        if self._updating:
            return
        self._display_image()

    def _on_range_change(self, change) -> None:
        if self._updating:
            return
        old_lo, old_hi = change.get("old", (None, None)) or (None, None)
        new_lo, new_hi = change.get("new", (None, None)) or (None, None)

        # Update autoscale toggles
        if new_lo is not None and new_lo != old_lo:
            self.autoscale_min_active = False
        if new_hi is not None and new_hi != old_hi:
            self.autoscale_max_active = False

        self.autoscale_min_button.button_style = (
            "success" if self.autoscale_min_active else ""
        )
        self.autoscale_max_button.button_style = (
            "success" if self.autoscale_max_active else ""
        )
        self._display_image()

    def _toggle_autoscale_min(self, _btn) -> None:
        self.autoscale_min_active = not self.autoscale_min_active
        self.autoscale_min_button.button_style = (
            "success" if self.autoscale_min_active else ""
        )
        self._display_image()

    def _toggle_autoscale_max(self, _btn) -> None:
        self.autoscale_max_active = not self.autoscale_max_active
        self.autoscale_max_button.button_style = (
            "success" if self.autoscale_max_active else ""
        )
        self._display_image()

    def _move(self, step: int) -> None:
        with self._suspend(self.index_slider):
            new_val = int(
                np.clip(
                    self.index_slider.value + step,
                    self.index_slider.min,
                    self.index_slider.max,
                )
            )
            self.index_slider.value = new_val
        self._display_image()

    # ------------------------- rendering -------------------------

    def _display_image(self) -> None:
        axis = int(self.dimension_picker.value)
        idx = int(self.index_slider.value)

        # Update cache plan based on axis choice
        self._maybe_update_cache(axis)

        # Slice efficiently
        if self._cached_moveaxis is not None:
            # Cached layout for browsing along last axis
            # Bring selected index to front already; now we need to drop it and end with 2D
            data = self._cached_moveaxis  # shape: (axis_size, ...)
            img = data[idx]
            # Reduce to 2D if needed
            while img.ndim > 2:
                img = img[0]
            if img.ndim == 1:
                img = img[np.newaxis, :]
        else:
            img = self._slice_to_2d(self.images_dataset, axis=axis, index=idx)

        # Statistics for sliders
        finite_img = img[np.isfinite(img)]
        if finite_img.size == 0:
            vmin, vmax = 0.0, 1.0
        else:
            vmin, vmax = self._safe_minmax(finite_img)

        # Update range slider bounds & values
        with self._suspend(self.range_slider):
            self.range_slider.min = float(vmin)
            self.range_slider.max = float(vmax)

            lo, hi = (
                self.range_slider.value
                if isinstance(self.range_slider.value, Sequence)
                else (None, None)
            )
            if self.autoscale_min_active and self.autoscale_max_active:
                self.range_slider.value = (vmin, vmax)
            elif self.autoscale_min_active and hi is not None:
                self.range_slider.value = (vmin, min(max(hi, vmin + 1e-9), vmax))
            elif self.autoscale_max_active and lo is not None:
                self.range_slider.value = (max(min(lo, vmax - 1e-9), vmin), vmax)
            else:
                # Clamp current values into [vmin, vmax]
                if lo is None or hi is None:
                    self.range_slider.value = (vmin, vmax)
                else:
                    lo = max(min(lo, vmax - 1e-9), vmin)
                    hi = max(min(hi, vmax), lo + 1e-9)
                    self.range_slider.value = (lo, hi)

        # Update autoscale button styles
        self.autoscale_min_button.button_style = (
            "success" if self.autoscale_min_active else ""
        )
        self.autoscale_max_button.button_style = (
            "success" if self.autoscale_max_active else ""
        )

        lo, hi = self.range_slider.value
        norm = self._choose_norm(lo, hi)

        # Draw / update
        if self.image_plot is not None:
            self.image_plot.set_data(img)
            self.image_plot.set_cmap(self.cmap_selector.value)
            if norm is None:
                # linear path: set_clim only
                self.image_plot.set_norm(Normalize(vmin=lo, vmax=hi))
            else:
                self.image_plot.set_norm(norm)
            self.image_plot.set_clim(lo, hi)
            if self.colorbar is not None:
                self.colorbar.update_normal(self.image_plot)
        else:
            self.ax.clear()
            self.ax.axis("off")
            self.image_plot = self.ax.imshow(
                img,
                cmap=self.cmap_selector.value,
                norm=norm,
                vmin=lo,
                vmax=hi,
            )
            self.colorbar = self.fig.colorbar(self.image_plot, ax=self.ax, shrink=0.75)

        self.canvas.draw_idle()

    # ------------------------- public API -------------------------

    def display(self) -> None:
        """Display the composed UI."""
        display(self.ui)
