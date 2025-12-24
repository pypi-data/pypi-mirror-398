import warnings

import numpy

try:
    import rioxarray
    import xarray
    import xarray.backends
except ImportError:
    raise ImportError(f"Can't load {__name__}, missing xarray or rioxarray extensions. Please install pywrb[xarray]")

from pywrb.constants import WRB_BLOCK_MEANING
from pywrb.entrypoint import open as pywrb_open


def _block_iter(arr):
    dims = set(arr.dims) - {"x", "y"}
    if not dims:
        yield arr
    else:
        arr = arr.stack(tmp=dims)
        yield from (arr.isel(tmp=i) for i in range(arr.sizes["tmp"]))


def xarray_to_wrb(dataset, filename: str, strict: bool = False, **kwargs):
    try:
        x_dim, y_dim = dataset.rio.x_dim, dataset.rio.y_dim
    except AttributeError:
        x_dim, y_dim = "x", "y"

    bounds = [float(dataset[x_dim][0]), float(dataset[y_dim][0]), float(dataset[y_dim][-1]), float(dataset[x_dim][-1])]
    bounds = dict(zip(("minx", "miny", "maxy", "maxx"), bounds))

    resolution = {
        "resolutionx": abs(float(dataset[x_dim][1] - dataset[x_dim][0])),
        "resolutiony": abs(float(dataset[y_dim][1] - dataset[y_dim][0])),
    }

    dataset = dataset.transpose(..., y_dim, x_dim)

    heights = dataset["heights"].values if "heights" in dataset else []
    wind_speeds = dataset["wind_speeds"].values if "wind_speeds" in dataset else []
    directions = dataset["directions"].values if "directions" in dataset else []

    with pywrb_open(
        filename,
        mode="w",
        **bounds,
        **resolution,
        crs=dataset.rio.crs.to_string(),
        heights=heights,
        directions=len(directions),
        wind_speeds=wind_speeds,
    ) as handle:
        for name, da in dataset.data_vars.items():
            try:
                meaning = _translate_xarray_to_wrb(name)
            except KeyError as e:
                if not strict:
                    warnings.warn(f"Cannot map variable name: {name} to one of {WRB_BLOCK_MEANING}")
                    continue
                raise ValueError(f"Cannot map variable name: {name} to one of {WRB_BLOCK_MEANING}") from e

            for da in _block_iter(da):
                kwargs = {
                    var[:-1]: da[var].item() for var in ("heights", "directions", "wind_speeds") if var in da.coords
                }

                handle.add_block(da.data, meaning=meaning, **kwargs)
        handle.write()

    return dataset


def _translate_wrb_to_xarray(meaning):
    return meaning.name.lower()


def _translate_xarray_to_wrb(name):
    return WRB_BLOCK_MEANING[name.upper()]


def xarray_from_wrb(filename, **kwargs):
    vars, attrs, coords = {}, {}, {}
    with pywrb_open(filename, mode="r", **kwargs) as handle:

        if len(handle.heights) > 0:
            coords["heights"] = sorted(tuple(handle.heights))
        if len(handle.directions) > 0:
            coords["directions"] = sorted(tuple(handle.directions))
        if len(handle.wind_speeds) > 0:
            coords["wind_speeds"] = sorted(tuple(handle.wind_speeds))
        coords["y"] = handle.y
        coords["x"] = handle.x

        shape = tuple(map(lambda a: max(1, len(a)), coords.values()))

        for block, data in handle:
            name = _translate_wrb_to_xarray(block["meaning"])
            if name not in vars:
                empty = numpy.full(shape, numpy.nan)
                vars[name] = xarray.DataArray(
                    empty, dims=coords.keys(), coords=coords
                )  # attrs=dict(unit=block["unit"]))

            index = []
            for dim in ["heights", "directions", "wind_speeds"]:
                if dim not in coords:
                    continue
                value = block[dim[:-1]]  # singular form in block
                if value is not None:
                    index.append(coords[dim].index(value))
                else:
                    index.append(0)

            vars[name].data[tuple(index)][:] = data

    # Normalize dataset, but keep dimensions provided as singleton
    for name, var in vars.items():
        dims = "x", "y"
        for dim in tuple(set(var.dims) - set(dims)):
            new_var = var.dropna(dim=dim, how="all")
            if new_var.sizes[dim] == 1 and new_var.sizes[dim] != len(coords[dim]):
                var = new_var.squeeze(dim, drop=True)
        vars[name] = var

    # Normalize surface variables
    for name in ["elevation", "roughness_length"]:
        try:
            vars[name] = vars[name].squeeze("heights", drop=True)
        except KeyError:
            pass

    ds = xarray.Dataset(vars, attrs=attrs, coords=coords)
    ds = ds.rio.write_crs(handle.crs)

    return ds


class WrbBackend(xarray.backends.BackendEntrypoint):
    """
    A simple example backend that loads and saves datasets.
    """

    def open_dataset(
        self,
        filename,
        *,
        drop_variables=None,
        decode_times=True,
        decode_timedelta=True,
        decode_coords=True,
        my_backend_option=None,
    ) -> xarray.Dataset:
        """
        Read a dataset from a custom format.
        """
        ds = xarray_from_wrb(filename)
        return ds

    def guess_can_open(self, filename: str) -> bool:
        """
        Guess if the backend can open the file.
        """
        return filename.endswith(".wrb")  # Change based on real format


@xarray.register_dataset_accessor("pywrb")
class WrbAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def to_wrb(self, filename, **kwargs):
        return xarray_to_wrb(self._obj, filename, **kwargs)
