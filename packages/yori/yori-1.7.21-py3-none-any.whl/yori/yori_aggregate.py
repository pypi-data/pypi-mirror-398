import sys
import warnings

# from datetime import datetime
from importlib.metadata import distribution

import netCDF4 as nc
import numpy as np

import yori.aggrtools as tools
import yori.config_reader as cfg
import yori.IOtools as IO

NC_FILL_DOUBLE = -9999.0
VERSION = distribution("yori").version


########################################
#               FUNCTION               #
########################################
#
def aggregate(
    flist,
    fname_out,
    satellite="",
    daily="",
    compression=5,
    verbose=False,
    force=False,
    use_min_pixel_counts=False,
    use_min_valid_days=False,
    batch_size=2,
    final=False,
):
    warnings.simplefilter("module")

    f0 = nc.Dataset(flist[0])
    group_list = list(f0.groups)

    latdim = f0.dimensions["latitude"].size
    londim = f0.dimensions["longitude"].size

    grid_vers = f0.getncattr("Yori_version")
    if grid_vers != str(VERSION):
        message = (
            "Current yori-aggr version (v"
            + str(grid_vers)
            + ") doesn't match the version used to create the gridded "
            + "files that are being aggregated"
        )
        warnings.warn(message, DeprecationWarning)

    config_str = f0.getncattr("YAML_config")
    config_str = str(config_str[:])
    ymlSet = cfg.ConfigReader(config_str)

    latkey = "latitude"
    lonkey = "longitude"

    gridsize = ymlSet.grid_settings["gridsize"]

    if "fill_value" in ymlSet.grid_settings:
        fv = ymlSet.grid_settings["fill_value"]
    else:
        fv = NC_FILL_DOUBLE

    if (fv - np.trunc(fv)) != 0:
        warnings.warn(
            "Yori does not support the definition of non-integer fill values. "
            + f"For now the code will use the truncated value {np.trunc(fv)} "
            + "instead, but using a non-integer fill value will cause an error in "
            + "future versions",
            DeprecationWarning,
        )
        fv = np.trunc(fv)
        # raise IOError('The fill value must be an integer')

    lat = f0[latkey][:]
    lon = f0[lonkey][:]

    for f in flist:
        fin = nc.Dataset(f)
        if hasattr(fin, "daily_defn_of_day_adjustment"):
            if fin.getncattr("daily_defn_of_day_adjustment") == "True":
                message = (
                    "The input files have been created with the "
                    + "--daily flag active. This could lead to small "
                    + "differences in the creation of the aggregated "
                    + "files when compared to monthly products created "
                    + "without using this flag. See documentation for "
                    + "more details"
                )
                warnings.warn(message)

        fin.close()

    if daily != "":
        dmask = tools.daily_mask(satellite, daily, flist, gridsize)
    else:
        dmask = np.ones((londim, latdim))

    f0.close()

    # initialize output file
    nc0 = nc.Dataset(fname_out, mode="w", format="NETCDF4")
    nc0.createDimension("latitude", len(lat))
    nc0.createDimension("longitude", len(lon))
    nc0.createVariable("latitude", "f8", ("latitude",), fill_value=fv)
    nc0.createVariable("longitude", "f8", ("longitude",), fill_value=fv)
    nc0["latitude"][:] = lat
    nc0["longitude"][:] = lon

    # initialize flags that will be used to avoid repeating warnings at each iteration
    warned_min_pixel = False
    warned_min_days = False

    # aggregate the variable groups in batches to keep memory footprint down
    batching = batch_size

    for batch_idx in range(0, len(group_list), batching):
        group_batch = group_list[batch_idx : batch_idx + batching]
        if verbose:
            print("processing: " + ", ".join(group_batch))

        # process all the files for the current batch
        arrays_initialized = False
        for fin in flist:
            file_in = nc.Dataset(fin)

            if not arrays_initialized:
                var_in = tools.initialize_arrays(
                    group_batch, file_in, latkey, lonkey, fv
                )
                arrays_initialized = True

            # look for global attribute that describes the subset of the full
            # global grid that actually contains data; enables working with much
            # smaller arrays even when Pixel_Counts are not present
            granule_edges = getattr(file_in, "granule_edges", None)
            if granule_edges is not None:
                left, right, bottom, top = granule_edges
                x_slice = slice(left, right + 1)
                y_slice = slice(bottom, top + 1)
                granule_edges = x_slice, y_slice

            if daily != "":
                try:
                    timeattr = file_in.getncattr("time_coverage_start")
                except AttributeError:
                    raise AttributeError(
                        'Global attribute "time_coverage_start"'
                        + "not found in input file "
                        + fin
                    )
                if satellite == "aqua":
                    dmask = np.asarray(
                        tools.aqua_daily_aggr(timeattr, daily, gridsize), bool
                    )
                if satellite == "terra":
                    dmask = np.asarray(
                        tools.terra_daily_aggr(timeattr, daily, gridsize), bool
                    )
            else:
                dmask = np.ones((londim, latdim), bool)

            # initialize the days and months arrays that are used to check whether the
            # files passed to aggregate belong to the same day/month. This is useful
            # when the min_pixel_counts and min_valid_days are used.
            days, months = [], []

            # Note: the reason to append a random value to days/months if the attribute
            # 'time_coverage_start' is not defined is to make sure that the following
            # check (every file belongs to same day/month) throws a warning if this one
            # throws a warning
            if use_min_pixel_counts is True:
                try:
                    timeattr = file_in.getncattr("time_coverage_start")
                    days.append(timeattr.day)
                except AttributeError:
                    message = (
                        'Global attribute "time_coverage_start" not found in '
                        + "input file {0}. Yori is unable to verify if the input "
                        + "files are all from the same day. Please double check "
                        + "your inputs. This message will not be repeated for "
                        + "other files."
                    ).format(fin)
                    if warned_min_pixel is False:
                        warnings.warn(message)
                        warned_min_pixel = True
                    days.append(np.random.randint(-100000, -1))

            if use_min_valid_days is True:
                try:
                    timeattr = file_in.getncattr("time_coverage_start")
                    months.append(timeattr.month)
                except AttributeError:
                    message = (
                        'Global attribute "time_coverage_start" not found in '
                        + "input file {0}. Yori is unable to verify if the input "
                        + "files are all from the same month. Please double "
                        + "check your inputs. This message will not be repeated "
                        + "for other files"
                    ).format(fin)
                    if warned_min_days is False:
                        warnings.warn(message)
                        warned_min_days = True
                    months.append(np.random.randint(-100000, -1))

            var_add = {}
            var_add = tools.prepare_vars(var_add, group_batch, file_in, granule_edges)
            for k in group_batch:
                if k == latkey or k == lonkey or k not in var_add:
                    pass
                else:
                    # use optimized aggregation function that avoids large array
                    # copies
                    var_in[k] = tools.gq_aggregate(var_in[k], var_add[k], dmask, fv)
            file_in.close()

        # check that all the files belong to the same day or month when the
        # min_pixel_counts or min_valid_days flags are used
        if use_min_pixel_counts is True:
            if len(set(days)) != 1:
                message = (
                    "Warning: not all files belong to the same day. Please "
                    + "verify your inputs. If this is intended please disregard "
                    + "this message"
                )
                warnings.warn(message)
        if use_min_valid_days is True:
            if len(set(months)) != 1:
                message = (
                    "Warning: not all files belong to the same month. Please "
                    + "verify your inputs. If this is intended please disregard "
                    + "this message"
                )
                warnings.warn(message)

        # replace fill and compute mean and stddev now, instead of each
        # time through the loop
        # var_in gets updated with the newly computed and modified values
        tools.compute_aggr_stats(var_in, fv)

        # for grp in group_batch:
        #     if "Median" in var_in[grp].keys():
        #         var_in[grp]["Median"] = np.nanmedian(var_in[grp]["Median"], axis=2)

        # filter the output variables based on the minimum number of valid pixels allowed
        # by the user. This option should only be used when creating D3 files. A warning
        # is thrown if the dates don't belong to the same day
        if use_min_pixel_counts is True:
            for grp in var_in.values():
                if "Pixel_Counts" not in grp:
                    continue
                if "min_pixel_counts" in grp:
                    min_pixel_counts = grp["min_pixel_counts"]
                    for k in grp.keys():
                        if k == "min_pixel_counts":
                            continue
                        grp["Pixel_Counts"][grp["Pixel_Counts"] < min_pixel_counts] = 0
                        if k not in [
                            "Pixel_Counts",
                            "min_valid_days",
                            "edges",
                            "min_pixel_counts",
                            "Num_Days",
                        ]:
                            grp[k][grp["Pixel_Counts"] < min_pixel_counts] = fv

                    grp.pop("min_pixel_counts")

        if use_min_valid_days is True:
            for grp in var_in.values():
                if "Num_Days" not in grp:
                    continue
                if "min_valid_days" in grp:
                    min_valid_days = grp["min_valid_days"]
                    for k in grp.keys():
                        if k == "min_valid_days":
                            continue
                        grp["Num_Days"][grp["Num_Days"] < min_valid_days] = 0
                        if k not in [
                            "Pixel_Counts",
                            "min_valid_days",
                            "edges",
                            "min_pixel_counts",
                            "Num_Days",
                        ]:
                            grp[k][grp["Num_Days"] < min_valid_days] = fv

                    grp.pop("min_valid_days")

        for grp in var_in.values():
            if "min_pixel_counts" in list(grp):
                grp.pop("min_pixel_counts")
            if "min_valid_days" in list(grp):
                grp.pop("min_valid_days")
            if "Num_Days" in list(grp) and use_min_valid_days is False:
                grp.pop("Num_Days")
            if "edges" in list(grp):
                grp.pop("edges")

            if final is True:
                if "Sum" in list(grp):
                    grp.pop("Sum")
                if "Sum_Squares" in list(grp):
                    grp.pop("Sum_Squares")
                if "Weighted_Sum" in list(grp):
                    grp.pop("Weighted_Sum")
                if "Weighted_Sum_Squares" in list(grp):
                    grp.pop("Weighted_Sum_Squares")
                if "Median_Distribution" in list(grp):
                    grp.pop("Median_Distribution")

        var_in = tools.restructDict(var_in)

        grid_size = ymlSet.grid_settings["gridsize"]
        IO.write_output(nc0, var_in, compression, grid_size, ymlSet, fv)

    # write the config file into a variable inside the netcdf output file
    nc0.setncattr("YAML_config", ymlSet.yaml_str)
    nc0.setncattr("Yori_version", str(VERSION))
    nc0.setncattr("input_files", ",".join(flist))
    nc0.setncattr("daily_defn_of_day_adjustment", str(False))
    if daily != "":
        nc0.setncattr("daily_defn_of_day_adjustment", str(True))

    for i in range(len(ymlSet.var_settings)):
        settings = ymlSet.var_settings[i]
        IO.append_attributes(nc0, settings, final)

    setattr(nc0.variables[latkey], "units", "degrees_north")
    setattr(nc0.variables[lonkey], "units", "degrees_east")

    nc0.close()


# main
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("usage: yori_aggregate.py <file_list> <output_file>")
        sys.exit(1)

    file_list = sys.argv[1]
    fname_out = sys.argv[2]

    aggregate(file_list, fname_out)
