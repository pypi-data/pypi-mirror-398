import re
import warnings
from importlib.metadata import distribution

import numpy as np

import yori.config_reader as cfg

VERSION = distribution("yori").version
_int_variables = ["Pixel_Counts", "Num_Days"]
_fv_re_str = re.compile("_?fill_?value_?", re.IGNORECASE)
_yori_doc = "https://sips.ssec.wisc.edu/docs/yori.html"


def write_output(
    fout, gridvar, compression, grid_size, ymlSet, fv, edges=[], write_edges=False
):
    if "latitude" not in fout.variables:
        fout.createDimension("latitude", 180 / grid_size)
        fout.createVariable("latitude", "f8", ("latitude",), fill_value=fv)
        fout["latitude"][:] = gridvar["latitude"]
        setattr(fout.variables["latitude"], "units", "degrees_north")
    if "longitude" not in fout.variables:
        fout.createDimension("longitude", 360 / grid_size)
        fout.createVariable("longitude", "f8", ("longitude",), fill_value=fv)
        fout["longitude"][:] = gridvar["longitude"]
        setattr(fout.variables["longitude"], "units", "degrees_east")

    for k in list(gridvar):
        if k == "latitude" or k == "longitude":
            continue
        if k.split("/")[-1] in _int_variables or gridvar[k].ndim > 2:
            vartype = "i4"
        else:
            vartype = "f8"

        dims = create_dims(fout, gridvar, k)
        fout.createVariable(
            k, vartype, dims, complevel=int(compression), zlib=True, fill_value=fv
        )
        if edges == []:
            fout[k][:] = gridvar[k]
        else:
            fout[k][edges[0] : edges[1] + 1, edges[2] : edges[3] + 1] = gridvar[k][
                edges[0] : edges[1] + 1, edges[2] : edges[3] + 1
            ]

    if write_edges:
        fout.granule_edges = np.array(edges, "i4")


def create_dims(fout, variable, k):
    default_dims_name = ("longitude", "latitude")
    dim_list = tuple(fout.dimensions.keys())
    dims = default_dims_name

    # histo_dim_name, jhisto_dim_name = '', ''
    histo_dim_name, jhisto_primary_name, jhisto_joint_name = "", "", ""
    if variable[k].ndim == 3:
        histo_dim_name = "Histo_{0}_{1}".format(
            k.split("/")[0], variable[k].shape[2]
        ).lower()
    if variable[k].ndim == 4:
        primary_var = k.split("/")[0]
        joint_var = k.split("/")[-1].replace("JHisto_vs_", "")
        jhisto_primary_name = "jhisto_{0}_{1}".format(
            primary_var, variable[k].shape[2]
        ).lower()
        jhisto_joint_name = "jhisto_{0}_{1}".format(
            joint_var, variable[k].shape[3]
        ).lower()
        # jhisto_dim_name = 'JHisto_{0}_{1}'.format(k.split('/')[-1],
        #                                           variable[k].shape[3]).lower()

    if histo_dim_name not in dim_list and variable[k].ndim == 3:
        fout.createDimension(histo_dim_name, variable[k].shape[2])
    if jhisto_primary_name not in dim_list and variable[k].ndim == 4:
        fout.createDimension(jhisto_primary_name, variable[k].shape[2])
    if jhisto_joint_name not in dim_list and variable[k].ndim == 4:
        fout.createDimension(jhisto_joint_name, variable[k].shape[3])
        # fout.createDimension(jhisto_dim_name, variable[k].shape[3])

    if histo_dim_name != "":
        dims += (histo_dim_name,)
    if jhisto_primary_name != "":
        dims += (jhisto_primary_name,)
    if jhisto_joint_name != "":
        dims += (jhisto_joint_name,)

    return dims


def append_attributes(fout, var_settings, final=False):
    grp = fout.groups[var_settings["name_out"]]
    for var in list(grp.variables):
        setattr(grp[var], "title", var_settings["name_out"] + ": " + var)

    for attr in var_settings.get("attributes", []):
        if re.search(_fv_re_str, attr["name"]) is not None:
            if np.array(attr["name"]).dtype == "int64":
                warnings.warn(
                    "FILLVALUE_MISMATCH: There is a mismatch between the FillValue defined "
                    + f"in the grid_settings and the {attr['name']} defined in the attributes, "
                    + "please double check your configuration file. See documentation at "
                    + f"{_yori_doc} for more info about this warning",
                    UserWarning,
                )
        setattr(grp, attr["name"], attr["value"])

        if attr["name"] == "units":
            if "Mean" in list(grp.variables):
                setattr(grp["Mean"], attr["name"], attr["value"])
            if "Standard_Deviation" in list(grp.variables):
                setattr(grp["Standard_Deviation"], attr["name"], attr["value"])
            if "Median" in list(grp.variables):
                setattr(grp["Median"], attr["name"], attr["value"])

        if attr["name"] in ["valid_min", "valid_max"]:
            if "Mean" in list(grp.variables):
                setattr(grp["Mean"], attr["name"], attr["value"])
            if "Median" in list(grp.variables):
                setattr(grp["Median"], attr["name"], attr["value"])

    if "histograms" in var_settings:
        if "edges" in var_settings["histograms"]:
            hist_bins = var_settings["histograms"]["edges"]
            setattr(
                grp["Histogram_Counts"],
                "Histogram_Bin_Boundaries",
                np.array(hist_bins, dtype="f8"),
            )
        else:
            setattr(
                grp["Histogram_Counts"],
                "Histogram_Bin_Boundaries",
                compute_hist_bins(var_settings["histograms"]),
            )

    if "median" in var_settings and final is False:
        setattr(
            grp["Median_Distribution"],
            "Median_Bins",
            compute_median_hist_bins(var_settings["median"]),
        )

    if "2D_histograms" in var_settings:
        for hist2d in var_settings["2D_histograms"]:
            if "edges" in hist2d["primary_var"]:
                setattr(
                    grp[hist2d["name_out"]],
                    "JHisto_Bin_Boundaries",
                    np.array(hist2d["primary_var"]["edges"], "f8"),
                )
            else:
                setattr(
                    grp[hist2d["name_out"]],
                    "JHisto_Bin_Boundaries",
                    compute_hist_bins(hist2d["primary_var"]),
                )
            if "edges" in hist2d["joint_var"]:
                setattr(
                    grp[hist2d["name_out"]],
                    "JHisto_Bin_Boundaries_Joint_Parameter",
                    np.array(hist2d["joint_var"]["edges"], "f8"),
                )
            else:
                setattr(
                    grp[hist2d["name_out"]],
                    "JHisto_Bin_Boundaries_Joint_Parameter",
                    compute_hist_bins(hist2d["joint_var"]),
                )

    if "min_pixel_counts" in var_settings:
        setattr(grp, "min_pixel_counts", var_settings["min_pixel_counts"])
    if "min_valid_days" in var_settings:
        setattr(grp, "min_valid_days", var_settings["min_valid_days"])


def compute_hist_bins(hist_data):
    hist_bins = np.arange(
        hist_data["start"], hist_data["stop"], hist_data["interval"], dtype="f8"
    )
    return hist_bins


def compute_median_hist_bins(histBlock):
    if "edges" in histBlock:
        varbins = list(histBlock["edges"])

    elif all(key in histBlock for key in ["start", "stop", "interval"]):
        if "log_scale" in histBlock:
            if histBlock["log_scale"] is True:
                varbins = np.geomspace(
                    histBlock["start"] + 1,
                    histBlock["stop"] * 100 + 1,
                    histBlock["interval"],
                )
                varbins = (varbins - 1) / 100
            else:
                varbins = list(
                    np.arange(
                        histBlock["start"], histBlock["stop"], histBlock["interval"]
                    )
                )
        else:
            varbins = list(
                np.arange(histBlock["start"], histBlock["stop"], histBlock["interval"])
            )
    else:
        raise IOError("in YAML file, histogram is not defined correctly")

    return varbins
