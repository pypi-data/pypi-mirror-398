import html
from collections.abc import Sequence

from .extension import Z_MAX, Component, ExtrusionSpec, LayerSpec, PortSpec, Technology
from .tidy3d_model import _tidy3d_to_str


class _Tree:
    """Tree viewer for components.

    Create a tree view of the component dependency tree for console and
    notebook visualization.

    Args:
        component: Root component of the tree.
        by_reference: If ``True`` shows all references (with index) within
          a component. Otherwise, only shows unique dependencies.
        interactive: If ``True``, the notebook visualization will use
          interactive folds and includes SVG previews.
    """

    def __init__(
        self,
        component: Component,
        by_reference: bool = False,
        interactive: bool = False,
    ):
        self.component = component
        self.by_reference = by_reference
        self.interactive = interactive

    @staticmethod
    def _inner_tree(component: Component, prefix: str, index: str, by_reference: bool) -> list[str]:
        result = [f"{prefix}{index}{component.name}"]
        if by_reference:
            dependencies = [reference.component for reference in component.references]
        else:
            dependencies = []
            for reference in component.references:
                ref_component = reference.component
                if ref_component not in dependencies:
                    dependencies.append(ref_component)

        ref_prefix = (
            "".join("│" if p == "│" or p == "├" else " " for p in prefix) + " " * len(index) + "├─"
        )
        n = len(dependencies)
        num_digits = len(str(n - 1))
        index = " "
        for i, dependency in enumerate(dependencies):
            if by_reference:
                index = "[" + str(i).rjust(num_digits) + "] "
            if i == n - 1:
                ref_prefix = ref_prefix[:-2] + "└─"
            result.extend(_Tree._inner_tree(dependency, ref_prefix, index, by_reference))
        return result

    def __repr__(self) -> str:
        return "\n".join(_Tree._inner_tree(self.component, "", "", self.by_reference))

    @staticmethod
    def _inner_html_tree(
        component: Component, prefix: str, index: str, by_reference: bool
    ) -> list[str]:
        result = [f'<span style="color:gray">{prefix}{index}</span>{component.name}<br>']
        if by_reference:
            dependencies = [reference.component for reference in component.references]
        else:
            dependencies = []
            for reference in component.references:
                ref_component = reference.component
                if ref_component not in dependencies:
                    dependencies.append(ref_component)

        ref_prefix = (
            "".join("│" if p == "│" or p == "├" else " " for p in prefix) + " " * len(index) + "├─"
        )
        n = len(dependencies)
        num_digits = len(str(n - 1))
        index = " "
        for i, dependency in enumerate(dependencies):
            if by_reference:
                index = "[" + str(i).rjust(num_digits, " ") + "] "
            if i == n - 1:
                ref_prefix = ref_prefix[:-2] + "└─"
            result.extend(_Tree._inner_html_tree(dependency, ref_prefix, index, by_reference))
        return result

    @staticmethod
    def _inner_interactive_html_tree(
        component: Component, index: int, by_reference: bool
    ) -> list[str]:
        if by_reference:
            dependencies = [reference.component for reference in component.references]
        else:
            dependencies = []
            for reference in component.references:
                ref_component = reference.component
                if ref_component not in dependencies:
                    dependencies.append(ref_component)

        margin = "1em" if index >= 0 else "0"
        details = "details open" if index < 0 else "details"
        title = f'<span style="color:black">{component.name}</span>'
        if by_reference and index >= 0:
            title = f'<spam style="font-family:monospace;color:gray">[{index}] </span>{title}'

        result = [
            f'<{details} style="border:1px solid #bdbdbd;border-radius:3px;margin-left:{margin}">'
            f'<summary style="padding:0.8ex;background-color:#f5f5f5;cursor:pointer">'
            f'{title}</summary><iframe style="border:0;width:100%;min-height:300px" '
            f'srcdoc="{html.escape(component._repr_svg_())}"></iframe>',
        ]
        for i, dependency in enumerate(dependencies):
            result.extend(_Tree._inner_interactive_html_tree(dependency, i, by_reference))
        result.append("</details>")

        return result

    def _repr_html_(self) -> str:
        if self.interactive:
            contents = ["<div>"]
            contents.extend(
                _Tree._inner_interactive_html_tree(self.component, -1, self.by_reference)
            )
        else:
            contents = ['<div style="font-family:monospace">']
            contents.extend(_Tree._inner_html_tree(self.component, "", "", self.by_reference))
        contents.append("</div>")
        return "".join(contents)


_max_len = 32


def _console_table(titles: list[str], rows: list[list[str]], alignments: str) -> str:
    lengths = [len(title) for title in titles]
    for row in rows:
        lengths = [max(w, len(data)) for w, data in zip(lengths, row, strict=False)]
    lengths = [min(w, _max_len) for w in lengths]

    for row in rows:
        for i, (w, alignment) in enumerate(zip(lengths, alignments, strict=False)):
            if alignment == "l":
                row[i] = row[i].ljust(w)
            elif alignment == "r":
                row[i] = row[i].rjust(w)
            else:
                row[i] = row[i].center(w)
            if len(row[i]) > _max_len:
                row[i] = row[i][: _max_len - 1] + "…"

    lines = [
        "  ".join(x.center(w) for x, w in zip(titles, lengths, strict=False)),
        "-" * (sum(lengths) + (len(lengths) - 1) * 2),
        *("  ".join(row) for row in rows),
    ]
    return "\n".join(lines)


def _html_table(titles: list[str], rows: list[list[str]], alignments: str) -> str:
    a = {"l": "left", "r": "right"}
    alignments = [a.get(x, "center") for x in alignments]
    contents = ["<table><thead><tr>"]
    contents.extend(f'<th style="text-align:center">{html.escape(t)}</th>' for t in titles)
    contents.append("</tr></thead><tbody>")
    for row in rows:
        contents.append("<tr>")
        for i, (title, alignment) in enumerate(zip(titles, alignments, strict=False)):
            data = html.escape(row[i])
            if len(data) > _max_len:
                for c in " =:+-*^@}{][)(;,_":
                    j = data[_max_len // 3 : _max_len].rfind(c)
                    if j >= 0:
                        j += _max_len // 3
                        if c not in " ([{":
                            j += 1
                        break
                else:
                    j = _max_len // 2
                summary = data[:j]
                data = data[j:]
                data = f"<details><summary>{summary}…</summary>…{data}</details>"
            s = ""
            if title == "Color":
                s = f";background-color:{row[i][:7]}"
            contents.append(f'<td style="text-align:{alignment}{s}">{data}</td>')
        contents.append("</tr>")
    contents.append("</tbody></table>")
    return "".join(contents)


def _modes_str(port_spec) -> str:
    s = str(port_spec.num_modes)
    if port_spec.added_solver_modes > 0:
        s += f" + {port_spec.added_solver_modes}"
    pol = port_spec.polarization
    if len(pol) > 0:
        s += f" ({pol})"
    return s


def _path_profile_str(path_profiles, technology) -> str:
    names = {}
    if technology is not None:
        names = {v.layer: k for k, v in technology.layers.items()}
    p = []
    if isinstance(path_profiles, dict):
        data = [(f"{k!r}@", *v) for k, v in path_profiles.items()]
    else:
        data = [("", *v) for v in path_profiles]
    for name, width, offset, layer in data:
        s = f"{name}{names.get(layer, layer)!r}: {width:g}"
        if offset != 0:
            s += f" ({offset:+g})"
        p.append(s)
    return ", ".join(p)


def _z_str(z) -> str:
    return "inf" if z > Z_MAX else ("-inf" if z < -Z_MAX else f"{z:g}")


class LayerTable(dict):
    """Layer specification table viewer.

    Create a table of layer specifications for console and notebook
    visualization.

    Args:
        obj: Technology instance or dictionary of layer specifications.
        sort_by_name: Flag to select sorting by name or by layer number.
    """

    def __init__(self, obj: Technology | dict[str, LayerSpec], sort_by_name: bool = False):
        if isinstance(obj, Technology):
            obj = obj._layers
        elif not isinstance(obj, dict) or not all(
            isinstance(k, str) and isinstance(v, LayerSpec) for k, v in obj.items()
        ):
            raise TypeError(
                "Expected a Technology instance or a dictionary of layer specifications."
            )
        super().__init__(obj)
        self._sort_by_name = sort_by_name

    def _table_data(self) -> tuple[list[str], list[list[str]], str]:
        titles = ["Name", "Layer", "Description", "Color", "Pattern"]
        rows = [
            [k, str(v.layer), v.description, "#" + "".join(f"{c:02x}" for c in v.color), v.pattern]
            for k, v in sorted(
                self.items(), key=(lambda x: x[0]) if self._sort_by_name else (lambda x: x[1].layer)
            )
        ]
        alignments = "lclcc"
        return titles, rows, alignments

    def _repr_html_(self) -> str:
        return _html_table(*self._table_data())

    def __repr__(self) -> str:
        return _console_table(*self._table_data())


class PortSpecTable(dict):
    """Port specification table viewer.

    Create a table of port specifications for console and notebook
    visualization.

    Args:
        obj: Technology instance or dictionary of port specifications.
    """

    def __init__(self, obj: Technology | dict[str, PortSpec]):
        technology = None
        if isinstance(obj, Technology):
            technology = obj
            obj = obj._ports
        elif not isinstance(obj, dict) or not all(
            isinstance(k, str) and isinstance(v, PortSpec) for k, v in obj.items()
        ):
            raise TypeError(
                "Expected a Technology instance or a dictionary of port specifications."
            )
        super().__init__(obj)
        self._technology = technology

    def _table_data(self) -> tuple[list[str], list[list[str]], str]:
        titles = [
            "Name",
            "Classification",
            "Description",
            "Width (μm)",
            "Limits (μm)",
            "Radius (μm)",
            "Modes",
            "Target n_eff",
            "Path profiles (μm)",
            "Voltage path",
            "Current path",
        ]
        rows = [
            [
                k,
                v.classification,
                v.description,
                f"{v.width:g}",
                f"{_z_str(v.limits[0])}, {_z_str(v.limits[1])}",
                f"{v.default_radius:g}",
                _modes_str(v),
                f"{v.target_neff:g}",
                _path_profile_str(v.path_profiles, self._technology),
                " ".join(f"({x[0]:g}, {x[1]:g})" for x in v.voltage_path)
                if v.classification == "electrical"
                else "",
                " ".join(f"({x[0]:g}, {x[1]:g})" for x in v.current_path)
                if v.classification == "electrical"
                else "",
            ]
            for k, v in sorted(self.items(), key=lambda x: (x[1].classification, x[0]))
        ]
        alignments = "lclccccclll"
        return titles, rows, alignments

    def _repr_html_(self) -> str:
        return _html_table(*self._table_data())

    def __repr__(self) -> str:
        return _console_table(*self._table_data())


class ExtrusionTable(list):
    """Extrusion specification table viewer.

    Create a table of extrusion specifications for console and notebook
    visualization.

    Args:
        obj: Technology instance or sequence of extrusion specifications.
    """

    def __init__(self, obj: Technology | Sequence[ExtrusionSpec]):
        layer_names = {}
        technology = None
        if isinstance(obj, Technology):
            layer_names = None
            technology = obj
            obj = obj._extrusion_specs
        elif not isinstance(obj, (list, tuple)) or not all(
            isinstance(x, ExtrusionSpec) for x in obj
        ):
            raise TypeError(
                "Expected a Technology instance or a sequence of extrusion specifications."
            )
        super().__init__(obj)
        self._format_args = (layer_names, technology)

    def _table_data(self) -> tuple[list[str], list[list[str]], str]:
        titles = [
            "#",
            "Mask",
            "Limits (μm)",
            "Sidewal (°)",
            "Opt. Medium",
            "Elec. Medium",
        ]
        rows = [
            [
                str(i),
                x.mask_spec.format(*self._format_args),
                f"{_z_str(x.limits[0])}, {_z_str(x.limits[1])}",
                f"{x.sidewall_angle:g}",
                _tidy3d_to_str(x.get_medium("optical")),
                _tidy3d_to_str(x.get_medium("electrical")),
            ]
            for i, x in enumerate(self)
        ]
        alignments = "rlccll"
        return titles, rows, alignments

    def _repr_html_(self) -> str:
        return _html_table(*self._table_data())

    def __repr__(self) -> str:
        return _console_table(*self._table_data())
