from typing import Sequence, Literal
from collections import OrderedDict

import pandas as pd
import numpy as np
import scanpy as sc
from anndata import AnnData
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
  
def violin(
    adata: AnnData,
    keys: str | Sequence[str],
    groupby: str | None = None,
    log: bool = False,
    use_raw: bool | None = None,
    # stripplot: bool = False,
    jitter: float | bool = True,
    size: int = 1,
    layer: str | None = None,
    scale: Literal["area", "count", "width"] = "width",
    order: Sequence[str] | None = None,
    multi_panel: bool = False,
    xlabel: str = "",
    ylabel: str = "",
    ncols: int | None = None,
    rotation: float | None = None,
    **kwds,
) -> go.Figure:
    """\
    Violin plot.

    Parameters
    ----------
    
    Parameters
    ----------
    adata
        Annotated data matrix.
    keys
        Keys for accessing variables of `.var_names` or fields of `.obs`.
    groupby
        The key of the observation grouping to consider.
    log
        Plot on logarithmic axis.
    use_raw
        Whether to use `raw` attribute of `adata`. Defaults to `True` if `.raw` is present.
    stripplot
        Add a stripplot on top of the violin plot.
        See :func:`~seaborn.stripplot`.
    jitter
        Add jitter to the stripplot (only when stripplot is True)
        See :func:`~seaborn.stripplot`.
    size
        Size of the jitter points.
    layer
        Name of the AnnData object layer that wants to be plotted. By
        default adata.raw.X is plotted. If `use_raw=False` is set,
        then `adata.X` is plotted. If `layer` is set to a valid layer name,
        then the layer is plotted. `layer` takes precedence over `use_raw`.
    scale
        The method used to scale the width of each violin.
        If 'width' (the default), each violin will have the same width.
        If 'area', each violin will have the same area.
        If 'count', a violin’s width corresponds to the number of observations.
    order
        Order in which to show the categories.
    multi_panel
        Display keys in multiple panels also when `groupby is not None`.
    xlabel
        Label of the x axis. Defaults to `groupby` if `rotation` is `None`,
        otherwise, no label is shown.
    ylabel
        Label of the y axis. If `None` and `groupby` is `None`, defaults
        to `'value'`. If `None` and `groubpy` is not `None`, defaults to `keys`.
    ncols
        Number of columns for the multi-panel display.
    rotation
        Rotation of xtick labels.
    **kwds
        Are passed to :func:`~plotly.express.violin`.

    Returns
    -------
    A :class:`~plotly.graph_objects.Figure` object.
    
    Examples
    --------
    TODO
    """

    sc._utils.sanitize_anndata(adata)
    use_raw = sc._utils._check_use_raw(adata, use_raw)
    if isinstance(keys, str):
        keys = [keys]
    keys = list(OrderedDict.fromkeys(keys))  # remove duplicates, preserving the order

    if isinstance(ylabel, (str, type(None))):
        ylabel = [ylabel] * (1 if groupby is None else len(keys))
    if groupby is None:
        if len(ylabel) != 1:
            raise ValueError(
                f"Expected number of y-labels to be `1`, found `{len(ylabel)}`."
            )
    elif len(ylabel) != len(keys):
        raise ValueError(
            f"Expected number of y-labels to be `{len(keys)}`, "
            f"found `{len(ylabel)}`."
        )

    if groupby is not None:
        obs_df = sc.get.obs_df(adata, keys=[groupby] + keys, layer=layer, use_raw=use_raw)
        if kwds.get("palette", None) is None:
            if not isinstance(adata.obs[groupby].dtype, pd.api.types.CategoricalDtype):
                raise ValueError(
                    f"The column `adata.obs[{groupby!r}]` needs to be categorical, "
                    f"but is of dtype {adata.obs[groupby].dtype}."
                )
            sc._utils.add_colors_for_categorical_sample_annotation(adata, groupby)
            kwds["palette"] = dict(
                zip(obs_df[groupby].cat.categories, adata.uns[f"{groupby}_colors"])
            )
    else:
        obs_df = sc.get.obs_df(adata, keys=keys, layer=layer, use_raw=use_raw)
    if groupby is None:
        obs_tidy = pd.melt(obs_df, value_vars=keys)
        x = "variable"
        ys = ["value"]
    else:
        obs_tidy = obs_df
        x = groupby
        ys = keys
        raise NotImplementedError()

    # oopsc contribution
    # Create a multi-panel figure
    if ncols is None:
        ncols = obs_tidy["variable"].unique().shape[0]
    nrows=obs_tidy["variable"].unique().shape[0] // ncols
    nrows=nrows if nrows > 0 else 1
    fig = make_subplots(
        cols=ncols,
        rows=nrows,
        shared_xaxes=False,
        shared_yaxes=False,
    )
    for i, variable in enumerate(pd.unique(obs_tidy["variable"])):
        col = i % ncols + 1
        row = i // ncols + 1
        fig.add_trace(
            go.Violin(x=obs_tidy["variable"][obs_tidy["variable"] == variable],
                      y=obs_tidy["value"][obs_tidy["variable"] == variable],
                      pointpos=0,
                    ), col=col, row=row,)
    return fig