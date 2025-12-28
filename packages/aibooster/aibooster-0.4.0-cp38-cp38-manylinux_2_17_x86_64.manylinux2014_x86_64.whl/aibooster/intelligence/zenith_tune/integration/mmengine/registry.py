try:
    # If the user uses mmengine, define mmengine registries
    from mmengine.registry import DATA_SAMPLERS as DEFAULT_DATA_SAMPLERS
    from mmengine.registry import FUNCTIONS as DEFAULT_FUNCTIONS
    from mmengine.registry import Registry

    DATA_SAMPLERS = Registry(
        "dataset", parent=DEFAULT_DATA_SAMPLERS, scope="zenith_tune"
    )
    FUNCTIONS = Registry("function", parent=DEFAULT_FUNCTIONS, scope="zenith_tune")
except Exception:
    pass
