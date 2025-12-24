from datetime import datetime
from importlib.metadata import distribution

import netCDF4 as nc
import numpy as np

import yori.gridtools as grd

VERSION = distribution("yori").version
NC_FILL_DOUBLE = -9999.0

np.seterr(
    divide="ignore", invalid="ignore"
)  # ignore divide by zero and invalid operations


def daily_mask(satellite, daily, flist, gridsize):
    if satellite == "":
        raise ValueError("--daily requires the --method option")
    daily_flist = []
    try:
        indate = datetime.strptime(daily, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            "Date not recognized. The prescribed format is: " + "YYYY-MM-DD"
        )

    for fname in flist:
        f = nc.Dataset(fname)
        try:
            timeattr = f.getncattr("time_coverage_start")
            ftime = parse_time_attr(timeattr)
        except AttributeError:
            raise AttributeError(
                'Global attribute "time_coverage_start" '
                + "not found in input file "
                + fname
            )

        diff_time = ftime - indate
        if np.abs(diff_time.days) > 1:
            raise IOError(
                "Input date and file date don't match. "
                + "Time difference is greater than one day"
            )

        if np.abs(diff_time.days) == 0:
            daily_flist.append(fname)
        elif (diff_time.days == -1) and (
            np.abs(diff_time.total_seconds() / 60.0) < 181
        ):
            daily_flist.append(fname)
        elif (diff_time.days == 1) and (
            np.abs((diff_time.total_seconds() - 86400.0) / 60.0) < 180
        ):
            daily_flist.append(fname)
        f.close()

    flist = daily_flist
    if satellite == "c6aqua":
        dmask = aqua_daily_aggr(timeattr, daily, gridsize)
    if satellite == "c6terra":
        dmask = terra_daily_aggr(timeattr, daily, gridsize)

    return dmask


def prepare_vars(var_add, group_batch, ncfile, granule_edges):
    for grp in group_batch:
        var_add[grp] = {}
        # define a bounding box to limit I/O by scanning Pixel_Counts
        # for nonzero entries
        #        if 'min_pixel_counts' in grp:
        #            var_add[grp]['min_pixel_counts'] = ncfile[grp]['min_pixel_counts']
        if "Median" in ncfile[grp].variables:
            x_slice = slice(None)
            y_slice = slice(None)
            cnt = ncfile[grp]["Pixel_Counts"][:]
            var_add[grp]["_slices"] = (x_slice, y_slice)
            var_add[grp]["Num_Days"] = compute_valid_days(cnt)[x_slice, y_slice]
        elif (
            "Pixel_Counts" in ncfile[grp].variables
            and "Median" not in ncfile[grp].variables
        ):
            cnt = ncfile[grp]["Pixel_Counts"][:]
            x, y = cnt.nonzero()
            if len(x) == 0:
                del var_add[grp]
                continue
            x_slice = slice(x.min(), x.max() + 1)
            y_slice = slice(y.min(), y.max() + 1)
            var_add[grp]["Pixel_Counts"] = cnt[x_slice, y_slice]
            var_add[grp]["_slices"] = (x_slice, y_slice)
            var_add[grp]["Num_Days"] = compute_valid_days(cnt)[x_slice, y_slice]
        elif granule_edges:
            x_slice, y_slice = granule_edges
            var_add[grp]["_slices"] = (x_slice, y_slice)
        else:
            x_slice = slice(None)  # gotta read the whole grid...
            y_slice = slice(None)

        for w in ncfile[grp].variables:
            if w != ["Pixel_Counts", "min_pixel_counts", "min_valid_days"]:
                if w != ["Median_Distribution"]:
                    var_add[grp][w] = ncfile[grp][w][x_slice, y_slice]
    #               else:
    #                    var_add['edges'] = ncfile[grp][w].Median_Bins

    return var_add


def initialize_arrays(group_batch, ncfile, latkey, lonkey, fv):
    var_in = {}
    for grp in group_batch:
        if grp == latkey or grp == lonkey:
            pass
        else:
            var_in[grp] = {}
            if hasattr(ncfile[grp], "min_pixel_counts"):
                var_in[grp]["min_pixel_counts"] = ncfile[grp].min_pixel_counts
            if hasattr(ncfile[grp], "min_valid_days"):
                var_in[grp]["min_valid_days"] = ncfile[grp].min_valid_days
                var_in[grp]["Num_Days"] = np.zeros(
                    (ncfile[lonkey][:].shape[0], ncfile[latkey][:].shape[0])
                )
                # var_in[grp]["Num_Days"] = ncfile[grp]["Pixel_Counts"][:] * 0.0
            for v in ncfile[grp].variables:
                if hasattr(ncfile[grp][v], "Median_Bins"):
                    var_in[grp]["edges"] = ncfile[grp][v].Median_Bins
                if v == "Min":
                    var_in[grp][v] = np.full_like(ncfile[grp][v][:], 2.0e10)
                else:
                    var_in[grp][v] = ncfile[grp][v][:] * 0.0
        # multipled by 0 so that the first var_in doesn't need to be masked
        # for the daily aggregation. This wouldn't be necessary for non-daily
        # aggregations

    # zero out fill values now, instead of at each loop iteration
    # perhaps even better would be to not use a fill value, but rather
    # user zero as the default value for all arrays that simply sum up
    # results (everything except mean and stdev)
    for group_vals in var_in.values():
        for var, arr in group_vals.items():
            if var not in ["min_pixel_counts", "min_valid_days"]:
                arr = arr.view(np.ndarray)  # converts from masked array without copying
                if var == "Min":
                    arr[arr == fv] = 5.0e10
                else:
                    arr[arr == fv] = 0
                group_vals[var] = arr

    return var_in


def gq_aggregate(curr_vals, new_vals, daily_mask, fill_value):
    """This function is an attempt to speed up the aggregation logic

    Mimics yori.aggregator.aggregator. Unlike that function, the return value
    contains the same arrays as are passed in via curr_vals, not copies.
    """
    slices = new_vals.pop("_slices", (slice(None), slice(None)))
    daily_mask = np.asarray(daily_mask, bool)[slices]
    derived_vars = [
        "Mean",
        "Standard_Deviation",
        "Median",
        "Weighted_Mean",
        "Weighted_Standard_Deviation",
        "min_pixel_counts",
        "min_valid_days",
        "edges",
        # "Num_Days",
    ]
    for var in curr_vals:
        if var in derived_vars:
            continue
        curr = curr_vals[var][slices]
        new = new_vals[var].view(np.ndarray)
        if var == "Min":
            # need to turn zeros into NaNs to get the min, otherwise every time the min()
            # will always pick the zero, while that should be a value to not take into
            # account.
            # curr[curr == 0] = np.nan
            # new[new == 0] = np.nan
            new[new == fill_value] = 3.0e10
            curr[curr == fill_value] = 4.0e10
            curr[daily_mask] = np.nanmin([curr, new], axis=0)[daily_mask]
        elif var == "Max":
            new[new == fill_value] = -1.0e10
            curr[daily_mask] = np.nanmax([curr, new], axis=0)[daily_mask]
        else:
            new[new == fill_value] = 0
            curr[daily_mask] += new[daily_mask]

    return curr_vals


def compute_valid_days(pixel_counts):
    valid_days = np.zeros(pixel_counts.shape)
    valid_days[pixel_counts != 0] = 1
    return valid_days


def compute_aggr_stats(var_in, fv):
    for vals in var_in.values():
        if "Pixel_Counts" not in vals:
            continue
        vals["Mean"] = vals["Sum"] / vals["Pixel_Counts"]
        vals["Standard_Deviation"] = np.sqrt(
            vals["Sum_Squares"] / vals["Pixel_Counts"]
            - (vals["Sum"] * vals["Sum"])
            / (vals["Pixel_Counts"] * vals["Pixel_Counts"])
        )

        if "Median" in vals:
            edges = vals["edges"]
            resolution = np.diff(vals["edges"])[0]
            vals["Median"] = aggregate_median(
                vals["Median_Distribution"], edges, resolution
            )

        if "Weights" in vals:
            vals["Weighted_Mean"] = vals["Weighted_Sum"] / vals["Weights"]
            vals["Weighted_Standard_Deviation"] = np.sqrt(
                vals["Weighted_Sum_Squares"] / vals["Weights"]
                - (vals["Weighted_Sum"] / vals["Weights"]) ** 2
            )
            # these quantities should already be NaN if weights = 0
            # but adding an additional check just to be sure...
            vals["Weighted_Mean"][vals["Weights"] == 0] = np.nan
            vals["Weighted_Standard_Deviation"][vals["Weights"] == 0] = np.nan

        """
        if 'min_pixel_counts' in vals:
            vals['min_pixel_counts'] = vals['min_pixel_counts']
        if 'min_valid_days' in vals:
            vals['min_valid_days'] = vals['min_valid_days']
        """

        no_data = vals["Pixel_Counts"] == 0

        for k in list(vals):
            if k in [
                "Pixel_Counts",
                "Weights",
                "min_pixel_counts",
                "min_valid_days",
                "edges",
            ]:
                continue
            else:
                vals[k][no_data] = fv
                vals[k][np.isnan(vals[k])] = fv


def restructDict(temp_var):
    tmp_out_var = {}
    for k in list(temp_var):
        if type(temp_var[k]) is dict:
            for kk in list(temp_var[k]):
                if k[-1] == "/":
                    k_short = k[:-1]
                else:
                    k_short = k
                tmp_out_var[k_short + "/" + kk] = temp_var[k][kk]
        else:
            tmp_out_var[k] = temp_var[k]

    return tmp_out_var


def aggregate_median(median_dist, edges, res):
    dims = median_dist.shape
    var = np.reshape(median_dist, (dims[0] * dims[1], dims[2]))
    aggr_median = np.zeros((dims[0] * dims[1]))
    for i in range(dims[0] * dims[1]):
        if np.sum(var[i, :]) > 0.0:
            aggr_median[i] = grd.estimate_median(var[i, :], edges, res)["est_median"]

    return aggr_median.reshape(dims[0], dims[1])


########################################
#               FUNCTION               #
########################################
#
def parse_time_attr(value):
    for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f"]:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    raise ValueError("could not parse time attr", value)


########################################
#               FUNCTION               #
########################################
#
def aqua_daily_aggr(timeattr, daily, gridsize):
    ftime = parse_time_attr(timeattr)
    indate = datetime.strptime(daily, "%Y-%m-%d")

    diff_time = ftime - indate

    # -180 to 180
    if (diff_time.days == 0) and (ftime.hour >= 3.0) and (ftime.hour < 24.0):
        coords_idx = np.array(range(0, int(360 / gridsize)))

    # -90 to 0 and 90 to 180
    elif (diff_time.days == 0) and (ftime.hour < 3.0):
        coords_idx = np.array(range(int(90 / gridsize), int(180 / gridsize)))
        coords_idx = np.append(
            coords_idx, range(int(270 / gridsize), int(360 / gridsize))
        )

    # -180 to -90 and 0 to 90
    elif (diff_time.days == 1) and (ftime.hour < 3.0):
        coords_idx = np.array(range(0, int(90 / gridsize)))
        coords_idx = np.append(
            coords_idx, range(int(180 / gridsize), int(270 / gridsize))
        )

    else:
        raise IOError(
            "The hour in the time_coverage_start attribute " + "is out of range"
        )

    daily_mask = np.zeros((int(360 / gridsize), int(180 / gridsize)))
    daily_mask[coords_idx, :] = 1

    return np.array(daily_mask)


def terra_daily_aggr(timeattr, daily, gridsize):
    ftime = parse_time_attr(timeattr)
    indate = datetime.strptime(daily, "%Y-%m-%d")

    diff_time = ftime - indate

    # -180 to 180
    if (diff_time.days == 0) and (ftime.hour >= 0.0) and (ftime.hour < 21.0):
        coords_idx = np.array(range(0, int(360 / gridsize)))

    # -180 to -90 and 0 to 90
    elif (diff_time.days == 0) and (ftime.hour >= 21.0):
        coords_idx = np.array(range(int(0 / gridsize), int(90 / gridsize)))
        coords_idx = np.append(
            coords_idx, range(int(180 / gridsize), int(270 / gridsize))
        )

    # -90 to 0 and 90 to 180
    elif (diff_time.days == -1) and (ftime.hour >= 21.0):
        coords_idx = np.array(range(int(90 / gridsize), int(180 / gridsize)))
        coords_idx = np.append(
            coords_idx, range(int(270 / gridsize), int(360 / gridsize))
        )

    else:
        raise IOError(
            "The hour in the time_coverage_start attribute " + "is out of range"
        )

    #   .--.      .-'.      .--.      .--.      .--.      .--.      .`-.      .--.
    # :::::.\::::::::.\::::::::.\::::::::.\::::::::.\::::::::.\::::::::.\::::::::.\
    # '      `--'      `.-'      `--'      `--'      `--'      `-.'      `--'
    #
    #     # This is the MODIS implementation of the daily aggregation
    #
    #     # -180 to 180
    #     if (diff_time.days == 0) and (ftime.hour >= 3.) and (ftime.hour <= 24.):
    #         coords_idx = np.array(range(0, int(360/gridsize)))
    #
    #     # -180 to -90 and 0 to 90
    # #     elif (diff_time.days == 0) and (ftime.hour >= 21.):
    # #         coords_idx = np.array(range(int(0/gridsize), int(90/gridsize)))
    # #         coords_idx = np.append(coords_idx, range(int(180/gridsize),
    # #                                                  int(270/gridsize)))
    #
    #     # -90 to 0 and 90 to 180
    #     elif (diff_time.days == 0) and (ftime.hour < 3.):
    #         coords_idx = np.array(range(int(90/gridsize), int(180/gridsize)))
    #         coords_idx = np.append(coords_idx, range(int(270/gridsize),
    #                                                 int(360/gridsize)))
    #
    #     # -180 to -90 and 0 to 90
    #     elif (diff_time.days == 1) and (ftime.hour < 3.):
    #         coords_idx = np.array(range(0, int(90/gridsize)))
    #         coords_idx = np.append(coords_idx, range(int(180/gridsize),
    #                                                  int(270/gridsize)))
    #
    #     # -90 to 0 and 90 to 180
    # #     elif (diff_time.days == -1) and (ftime.hour >= 21.):
    # #         coords_idx = np.array(range(int(90/gridsize), int(180/gridsize)))
    # #         coords_idx = np.append(coords_idx, range(int(270/gridsize),
    # #                                                  int(360/gridsize)))
    #
    #     else:
    #         raise IOError('The hour in the time_coverage_start attribute' +
    #                       'is out of range')
    #
    #   .--.      .-'.      .--.      .--.      .--.      .--.      .`-.      .--.
    # :::::.\::::::::.\::::::::.\::::::::.\::::::::.\::::::::.\::::::::.\::::::::.\
    # '      `--'      `.-'      `--'      `--'      `--'      `-.'      `--'

    daily_mask = np.zeros((int(360 / gridsize), int(180 / gridsize)))
    daily_mask[coords_idx, :] = 1

    # probably check if all the files are provided (30 hours)
    # use datetime.datetime.strptime()
    # date string format '%Y-%m-%dT%H:%M:%S.000Z'

    # Longitude intervals:
    #     0   - 90   21:00 - 21:00
    #     90  - 180  03:00 - 03:00
    #     180 - 270  21:00 - 21:00
    #     270 - 360  03:00 - 03:00

    # Longitude intervals:
    #     0   - 90   03:00 - 03:00
    #     90  - 180  21:00 - 21:00
    #     180 - 270  03:00 - 03:00
    #     270 - 360  21:00 - 21:00

    return np.array(daily_mask)
