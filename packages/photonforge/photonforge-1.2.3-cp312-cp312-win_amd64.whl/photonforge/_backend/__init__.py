import photonforge as _pf


def fallback_defaults():
    _pf.config.default_technology = _pf.basic_technology()
    port_spec = _pf.virtual_port_spec(1)
    kwargs = {
        "port_spec": port_spec,
        "radius": 50,
        "length": 10,
        "coupling_distance": 0.65,
        "s_bend_offset": 2,
    }
    inner_kwargs = {
        "crossing": {"arm_length": 5, "added_width": 0.5},
        "crossing45": {"arm_length": 5, "added_width": 0.5},
        "s_bend": {"offset": 2},
        "transition": {"port_spec1": port_spec, "port_spec2": port_spec},
        "rectangular_spiral": {"turns": 7},
        "circular_spiral": {"turns": 4},
    }

    kwargs.update(_pf.config.default_kwargs)
    for fname, kwds in inner_kwargs.items():
        fn_kwargs = kwargs.get(fname, {})
        for key, value in kwds.items():
            if key not in kwargs and key not in fn_kwargs:
                fn_kwargs[key] = value
        kwargs[fname] = fn_kwargs
    _pf.config.default_kwargs = kwargs

    _pf.config.svg_labels = False
    _pf.config.svg_port_names = False
