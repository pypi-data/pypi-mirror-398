import warnings
from collections.abc import Sequence
from typing import Any, Literal

import numpy
import tidy3d

from .extension import (
    Component,
    FiberPort,
    Port,
    PortSpec,
    SMatrix,
    Technology,
    config,
    frequency_classification,
)
from .tidy3d_model import Tidy3DModel
from .utils import C_0


def plot_s_matrix(
    s_matrix: SMatrix,
    input_ports: Sequence[str] = (),
    output_ports: Sequence[str] = (),
    x: Literal["wavelength", "frequency"] | None = None,
    y: Literal["magnitude", "phase", "real", "imag", "dB"] = "magnitude",
    threshold: float = 0.1,
) -> tuple[Any, Any]:
    """Helper function to plot a component S matrix.

    Args:
        s_matrix: S parameters t be plotted.
        input_ports: Sequence of port names that will be used as input for
          plotting. If empty, all available ports are used.
        output_ports: Sequence of port names that will be used as output for
          plotting. If empty, all available ports are used.
        x: Value used for the x axis. One of "wavelength" or "frequency".
          By default uses wavelengths for optics and frequency otherwise.
        y: Value to be plotted in the y axis. One of "magnitude", "phase",
          "real", "imag", or "dB".
        threshold: Threshold value for the squared magnitude of the S
          parameter. Curves below this threshold are plotted separately or
          ignored (for phase plots).

    Returns:
        fig, ax: Created matplotlib figure and axes.

    Note:
        This function requires the module ``matplotlib.pyplot``.
    """
    try:
        from matplotlib import pyplot  # noqa: PLC0415
    except ImportError as err:
        raise ImportError(
            "Unable to import matplotlib.pyplot. Function 'plot_s_matrix' is unavailable."
        ) from err

    if x is None:
        classification = frequency_classification(s_matrix.frequencies)
        x_ = s_matrix.wavelengths if classification == "optical" else s_matrix.frequencies
        x = "wavelength" if classification == "optical" else "frequency"
    else:
        x_ = s_matrix.wavelengths if x == "wavelength" else s_matrix.frequencies

    if len(input_ports) == 0:
        input_ports = sorted({k[0] for k in s_matrix.elements})
    else:
        input_ports = sorted(
            {k[0] for k in s_matrix.elements if any(k[0].startswith(p + "@") for p in input_ports)}
        )
    if len(output_ports) == 0:
        output_ports = sorted({k[1] for k in s_matrix.elements})
    else:
        output_ports = sorted(
            {k[1] for k in s_matrix.elements if any(k[1].startswith(p + "@") for p in output_ports)}
        )

    threshold = abs(threshold) ** 0.5

    num_cols = 1
    first_col = None
    cols = {}
    for port_in in input_ports:
        for port_out in output_ports:
            key = (port_in, port_out)
            cols[key] = 0 if y == "phase" or numpy.abs(s_matrix[key]).max() >= threshold else 1
            if first_col is None:
                first_col = cols[key]
            elif cols[key] != first_col:
                num_cols = 2
    if num_cols == 1 and y != "phase":
        cols = dict.fromkeys(cols, 0)

    fig, ax = pyplot.subplots(
        1, num_cols, figsize=(5 * num_cols, 3.5), tight_layout=True, squeeze=False
    )
    ax = ax[0, :]

    for port_in in input_ports:
        for port_out in output_ports:
            key = (port_in, port_out)
            a = ax[cols[key]]
            if y == "phase":
                if numpy.abs(s_matrix[key]).max() < threshold:
                    continue
                y_ = numpy.angle(s_matrix[key])
            elif y == "real":
                y_ = s_matrix[key].real
            elif y == "imag":
                y_ = s_matrix[key].imag
            elif y == "dB":
                y_ = numpy.abs(s_matrix[key])
                y_[y_ < 1e-6] = 1e-6
                y_ = 20 * numpy.log10(y_)
            else:
                y_ = numpy.abs(s_matrix[key]) ** 2
            a.plot(x_, y_, label=" → ".join(key))

    for a in ax:
        a.legend()
        if y == "phase":
            a.set_ylabel("∠S (rad)")
        elif y == "real":
            a.set_ylabel("Re{S}")
        elif y == "imag":
            a.set_ylabel("Im{S}")
        elif y == "dB":
            a.set_ylabel("|S| (dB)")
        else:
            a.set_ylabel("|S|²")
        if x == "wavelength":
            a.set_xlabel("Wavelength (µm)")
        else:
            a.set_xlabel("Frequency (Hz)")

    return fig, ax


def tidy3d_plot(
    obj: Component | Port | FiberPort | PortSpec,
    frequency: float | None = None,
    technology: Technology | None = None,
    plot_type: Literal["3d", "eps", "structures"] | None = None,
    plot_grid: bool = False,
    **kwargs: Any,
) -> Any:
    """Helper function to plot a component through Tidy3D.

    Args:
        obj: Object to be plotted (:class:`Component`, :class:`Port`,
          :class:`FiberPort`, or :class:`PortSpec`).
        frequency: Frequency to use when creating the simulation object and
          ploting media. If not set, it will be automatically selected from
          the technology media.
        technology: Technology to use. If not set, use the component's or
          the default technology.
        plot_type: Type of plot to use. Use default ``plot`` when not set.
        plot_grid: Flag to enable plotting the simulation grid.
        kwargs: Keyword arguments passed to the plot function.

    Returns:
        Matplotlib axis used for ploting.

    Example:
        >>> technology = pf.basic_technology()
        >>> component = pf.parametric.bend(
        ...     port_spec="Strip", radius=10, technology=technology
        ... )
        >>> pf.tidy3d_plot(component, z=0.1)
        <Axes: ...>

    Note:
        This function requires the module ``matplotlib.pyplot``.

        Instances of :class:`Port` and :class:`PortSpec` can only be
        plotted with Tidy3D versions 2.7.1 and above.
    """
    if technology is None:
        if isinstance(obj, Component):
            technology = obj.technology
        else:
            technology = config.default_technology

    if frequency is None:
        classification = (
            obj.classification if isinstance(obj, (PortSpec, Port, FiberPort)) else "optical"
        )
        frequency = C_0 / 1.55 if classification == "optical" else 10.0e9
        min_freq = -numpy.inf
        max_freq = numpy.inf
        for extrusion in technology.extrusion_specs:
            medium = extrusion.get_medium(classification)
            if isinstance(medium, tidy3d.MultiPhysicsMedium):
                medium = medium.optical
            freq_range = medium.frequency_range
            if freq_range is not None:
                if min_freq < freq_range[0]:
                    min_freq = freq_range[0]
                if max_freq > freq_range[1]:
                    max_freq = freq_range[1]
        if numpy.isfinite(min_freq) and numpy.isfinite(max_freq) and min_freq <= max_freq:
            frequency = 0.5 * (min_freq + max_freq)

    if isinstance(obj, Component):
        model = Tidy3DModel()
        for m in obj.models.values():
            if isinstance(m, Tidy3DModel):
                model = m
                break
        tidy3d_obj = model.get_simulations(obj, [frequency])
        if isinstance(tidy3d_obj, dict):
            tidy3d_obj = tidy3d_obj[sorted(tidy3d_obj)[0]]
    elif isinstance(obj, (Port, FiberPort)):
        tidy3d_obj = obj.to_tidy3d_mode_solver([frequency], technology=technology)
    elif isinstance(obj, PortSpec):
        tidy3d_obj = obj.to_tidy3d([frequency], technology=technology)
    else:
        raise TypeError("Plotting only works for instances of Component, Port, and PortSpec.")

    if plot_type == "3d" and hasattr(tidy3d_obj, "plot_3d"):
        ax = tidy3d_obj.plot_3d(**kwargs)
        if plot_grid:
            plot_grid = False
            warnings.warn("Grid plotting is not supported for 'plot_type == \"3d\".'", stacklevel=2)
    elif plot_type == "eps" and hasattr(tidy3d_obj, "plot_eps"):
        ax = tidy3d_obj.plot_eps(**kwargs)
    elif plot_type == "structures" and hasattr(tidy3d_obj, "plot_structures"):
        ax = tidy3d_obj.plot_structures(**kwargs)
    elif hasattr(tidy3d_obj, "plot"):
        ax = tidy3d_obj.plot(**kwargs)
    else:
        raise TypeError(
            "Tidy3D object does not support plotting. Please make sure you have a recent version"
            "of tidy3d installed. To upgrade, use 'pip install --user --upgrade tidy3d'."
        )

    if plot_grid:
        kwargs = dict(kwargs)
        kwargs["ax"] = ax
        tidy3d_obj.plot_grid(**kwargs)

    return ax
