import warnings

import numpy as np
import pyproj


class Grid:
    def __init__(self, lat, lon, gridsize, proj, fillvalue):
        if (proj == "conformal") or (proj == "equal_angle"):
            self.x1, self.y1 = 180.0, 90.0
        elif proj == "equal_area":
            eqAngle = pyproj.Proj(proj="longlat")
            eqArea = pyproj.Proj(proj="cea")
            self.x1, self.y1 = pyproj.transform(eqAngle, eqArea, 180, 90)
            lon, lat = pyproj.transform(eqAngle, eqArea, lon, lat)
        else:
            raise ValueError(
                f'Unkonwn projection "{proj}". Possible options are '
                + '"equal_angle" or "equal_area"'
            )

        self.lat = reformat_vector(lat)
        self.lon = reformat_vector(lon)
        self.gridsize = np.array(gridsize, dtype="f8")
        self.proj = proj
        self.fillvalue = fillvalue

    # function for creating gridded indexes
    def create_index(self):
        """ """
        if self.proj == "equal_area":
            gridsize = 2 * self.y1 / np.floor(2 * self.y1 / self.gridsize)
        else:
            gridsize = self.gridsize
        # convert coordinates to positive values
        lattemp = self.lat + self.y1
        lontemp = self.lon + self.x1

        # define the sizes of the output matrix depending on the gridsize
        latdim = np.array(np.ceil(2 * self.y1 / gridsize), dtype="i8")
        londim = np.array(np.ceil(2 * self.x1 / gridsize), dtype="i8")

        # define the latitude and longitude indexes according to gridsize
        latidx = np.array(np.ceil(lattemp / gridsize) - 1, dtype="i8")
        lonidx = np.array(np.ceil(lontemp / gridsize) - 1, dtype="i8")

        # remove any zero indexes in latidx and lonidx
        idx = np.where(latidx < 0)
        latidx[idx] = 0
        idx = np.where(lonidx < 0)
        lonidx[idx] = 0
        self.edges = [np.min(lonidx), np.max(lonidx), np.min(latidx), np.max(latidx)]

        # THIS PART WAS DEFINED FOR THE EQUAL_AREA PROJECTION
        # WHENEVER WE BELIEVE WE ARE READY TO MOVE BACK TO IT
        # WE CAN POSSIBLY START FROM HERE
        # define the latitude and longitude grids, given the gridsize
        latgrid = np.arange(
            -self.y1 + gridsize / 2, self.y1 + gridsize - gridsize / 2, gridsize
        )
        longrid = np.arange(
            -self.x1 + gridsize / 2, self.x1 + gridsize - gridsize / 2, gridsize
        )

        if self.proj == "equal_area":
            eqArea = pyproj.Proj(proj="cea")
            eqAngle = pyproj.Proj(proj="longlat")
            _, latgrid = pyproj.transform(
                eqArea, eqAngle, np.ones((len(latgrid), 1)) * longrid[0], latgrid
            )
            longrid, _ = pyproj.transform(
                eqArea, eqAngle, longrid, np.ones((len(longrid), 1)) * latgrid[0]
            )

        grididx = np.ravel_multi_index([[lonidx], [latidx]], (londim, latdim))[0]

        grid = {}
        grid["idx"] = grididx
        grid["matrixsize"] = (londim, latdim)
        grid["latgrid"] = latgrid
        grid["longrid"] = longrid

        return grid


class ComputeVariables(Grid):
    def __init__(self, lat, lon, gridsize, proj, fillvalue):
        super().__init__(lat, lon, gridsize, proj, fillvalue)

        self.grid = Grid.create_index(self)
        self.init_size = self.grid["matrixsize"][0] * self.grid["matrixsize"][1]

        # sort indexes
        self.srt_idx = np.sort(self.grid["idx"], kind="mergesort")
        self.sortidx = np.argsort(self.grid["idx"], kind="mergesort")

        # create indexes for the output
        diff_vec = np.diff(self.srt_idx)
        diff_vec = np.insert(diff_vec, 0, 1)
        diff_vec = np.append(diff_vec, 1)
        self.box_idx = np.array(np.where(diff_vec > 0))[0]

    #         self.vargrid = {}

    # function for creating gridded variables
    def compute_stats(self, var, varname=""):
        """ """
        var = reformat_vector(var)

        # check if the sizes of the coordinates passed to the function are consistent
        if np.shape(self.lat) != np.shape(self.lon) or np.shape(self.lat) != np.shape(
            var
        ):
            raise ValueError("Input coordinates have different size")

        # initialize output variables
        varmean = np.zeros(self.init_size) * np.nan
        varstd = np.zeros(self.init_size) * np.nan
        varsum = np.zeros(self.init_size) * np.nan
        varnpts = np.zeros(self.init_size) * np.nan
        varssum = np.zeros(self.init_size) * np.nan

        # loop for the computation of the output variables
        for i in range(len(self.box_idx)):
            if len(self.box_idx) <= 1:
                continue
            elif i != len(self.box_idx) - 1:
                start = i
                end = i + 1
            else:
                continue

            # grab data from var, make sure there are no nans
            xx = var[self.sortidx[self.box_idx[start] : self.box_idx[end]]]
            xx = xx[~np.isnan(xx)]
            if len(xx) > 0:
                varmean[self.srt_idx[self.box_idx[i]]] = np.mean(xx)
                varstd[self.srt_idx[self.box_idx[i]]] = np.std(xx)
                varsum[self.srt_idx[self.box_idx[i]]] = np.sum(xx)
                varnpts[self.srt_idx[self.box_idx[i]]] = len(xx)
                varssum[self.srt_idx[self.box_idx[i]]] = np.sum(xx**2)
            elif len(xx) == 0:
                varmean[self.srt_idx[self.box_idx[i]]] = np.nan
                varstd[self.srt_idx[self.box_idx[i]]] = np.nan
                varsum[self.srt_idx[self.box_idx[i]]] = np.nan
                varnpts[self.srt_idx[self.box_idx[i]]] = np.nan
                varssum[self.srt_idx[self.box_idx[i]]] = np.nan
            else:
                warnings.warn(
                    "The code should not be entering this condition", UserWarning
                )
                continue

        # Set all NaN values to fill, see issue-15
        varmean[np.isnan(varmean)] = self.fillvalue
        varstd[np.isnan(varstd)] = self.fillvalue
        varsum[np.isnan(varsum)] = self.fillvalue
        varnpts[np.isnan(varnpts)] = 0  # self.fillvalue
        varssum[np.isnan(varssum)] = self.fillvalue

        if varname != "":
            varname += "/"
        # write the outputs into the output dictionary
        vargrid = {}
        vargrid[varname + "Mean"] = np.reshape(varmean, self.grid["matrixsize"])
        vargrid[varname + "Standard_Deviation"] = np.reshape(
            varstd, self.grid["matrixsize"]
        )
        vargrid[varname + "Sum"] = np.reshape(varsum, self.grid["matrixsize"])
        vargrid[varname + "Pixel_Counts"] = np.reshape(varnpts, self.grid["matrixsize"])
        vargrid[varname + "Sum_Squares"] = np.reshape(varssum, self.grid["matrixsize"])

        return vargrid

    # function for creating gridded variables
    # def compute_median(self, var, varname):
    def compute_median(self, var, varname, varbins, resolution):
        """ """
        var = reformat_vector(var)

        # check if the sizes of the coordinates passed to the function are consistent
        if np.shape(self.lat) != np.shape(self.lon) or np.shape(self.lat) != np.shape(
            var
        ):
            raise ValueError("Input coordinates have different size")

        # initialize output variables
        varmedian = np.zeros(self.init_size) * np.nan
        median_hist = np.zeros((self.init_size, np.size(varbins) - 1))
        # loop for the computation of the output variables
        for i in range(len(self.box_idx)):
            if len(self.box_idx) <= 1:
                continue
            elif i != len(self.box_idx) - 1:
                start = i
                end = i + 1
            else:
                continue

            # grab data from var, make sure there are no nans
            xx = var[self.sortidx[self.box_idx[start] : self.box_idx[end]]]
            xx = xx[~np.isnan(xx)]
            if len(xx) > 0:
                median_dict, edges = yori_median(xx, varbins, resolution)
                # varmedian[self.srt_idx[self.box_idx[i]]] = remedian(xx)
                varmedian[self.srt_idx[self.box_idx[i]]] = median_dict["est_median"]
                median_hist[self.srt_idx[self.box_idx[i]], :] = median_dict["hist"]
            elif len(xx) == 0:
                varmedian[self.srt_idx[self.box_idx[i]]] = np.nan
                median_hist[self.srt_idx[self.box_idx[i]], :] = np.nan
            else:
                continue

        # Set all NaN values to fill, see issue-15
        varmedian[np.isnan(varmedian)] = self.fillvalue
        median_hist[np.isnan(median_hist)] = self.fillvalue

        # write the outputs into the output dictionary
        vargrid = {}
        vargrid[varname + "/Median"] = np.reshape(varmedian, self.grid["matrixsize"])
        vargrid[varname + "/Median_Distribution"] = np.reshape(
            median_hist,
            (
                self.grid["matrixsize"][0],
                self.grid["matrixsize"][1],
                np.size(varbins) - 1,
            ),
        )

        return vargrid

    # function for creating weighted stats
    def compute_wgt_stats(self, var, varname="", weight=""):
        """ """
        if weight == "":
            raise ValueError(
                "Weight not specified when requesting the weighted "
                + "stats in the configuration file"
            )

        var = reformat_vector(var)
        weight = reformat_vector(weight)
        # check if the sizes of the coordinates passed to the function are consistent
        if np.shape(self.lat) != np.shape(self.lon) or np.shape(self.lat) != np.shape(
            var
        ):
            raise ValueError("Input coordinates have different size")

        # initialize output variables
        var_wgt = np.zeros(self.init_size) * np.nan
        var_wgt_sum = np.zeros(self.init_size) * np.nan
        var_wgt_ssum = np.zeros(self.init_size) * np.nan
        var_wgt_mean = np.zeros(self.init_size) * np.nan
        var_wgt_std = np.zeros(self.init_size) * np.nan

        # loop for the computation of the output variables
        for i in range(len(self.box_idx)):
            if len(self.box_idx) <= 1:
                continue
            elif i != len(self.box_idx) - 1:
                start = i
                end = i + 1
            else:
                continue

            # grab data from var, make sure there are no nans
            xx = var[self.sortidx[self.box_idx[start] : self.box_idx[end]]]
            wgt = weight[self.sortidx[self.box_idx[start] : self.box_idx[end]]]
            not_nan = ~np.isnan(xx)
            xx = xx[not_nan]
            wgt = wgt[not_nan]
            mean_wgt = np.sum(xx * wgt) / np.sum(wgt)
            std_wgt = np.sqrt(np.sum(wgt * ((xx - mean_wgt) ** 2)) / np.sum(wgt))
            if len(xx) > 0:
                var_wgt[self.srt_idx[self.box_idx[i]]] = np.sum(wgt)
                var_wgt_sum[self.srt_idx[self.box_idx[i]]] = np.sum(xx * wgt)
                var_wgt_ssum[self.srt_idx[self.box_idx[i]]] = np.sum(wgt * xx**2)
                var_wgt_mean[self.srt_idx[self.box_idx[i]]] = mean_wgt
                var_wgt_std[self.srt_idx[self.box_idx[i]]] = std_wgt
            elif len(xx) == 0:
                var_wgt[self.srt_idx[self.box_idx[i]]] = np.nan
                var_wgt_sum[self.srt_idx[self.box_idx[i]]] = np.nan
                var_wgt_ssum[self.srt_idx[self.box_idx[i]]] = np.nan
                var_wgt_mean[self.srt_idx[self.box_idx[i]]] = np.nan
                var_wgt_std[self.srt_idx[self.box_idx[i]]] = np.nan
            else:
                continue

        # Set all NaN values to fill, see issue-15
        var_wgt_mean[np.isnan(var_wgt_mean)] = self.fillvalue
        var_wgt_std[np.isnan(var_wgt_std)] = self.fillvalue
        var_wgt_sum[np.isnan(var_wgt_sum)] = self.fillvalue
        var_wgt[np.isnan(var_wgt)] = 0
        var_wgt_ssum[np.isnan(var_wgt_ssum)] = self.fillvalue

        if varname != "":
            varname += "/"
        # write the outputs into the output dictionary
        vargrid = {}
        vargrid[varname + "Weights"] = np.reshape(var_wgt, self.grid["matrixsize"])
        vargrid[varname + "Weighted_Sum"] = np.reshape(
            var_wgt_sum, self.grid["matrixsize"]
        )
        vargrid[varname + "Weighted_Sum_Squares"] = np.reshape(
            var_wgt_ssum, self.grid["matrixsize"]
        )
        vargrid[varname + "Weighted_Mean"] = np.reshape(
            var_wgt_mean, self.grid["matrixsize"]
        )
        vargrid[varname + "Weighted_Standard_Deviation"] = np.reshape(
            var_wgt_std, self.grid["matrixsize"]
        )

        return vargrid

    def compute_histogram(self, var, binvec, varname):
        var = reformat_vector(var)

        varstat = np.zeros((self.init_size, np.size(binvec) - 1))  # *np.nan

        for i in range(len(self.box_idx)):
            if len(self.box_idx) <= 1:
                continue
            elif i != len(self.box_idx) - 1:
                start = i
                end = i + 1
            else:
                continue

            xx = var[self.sortidx[self.box_idx[start] : self.box_idx[end]]]
            xx = xx[~np.isnan(xx)]
            # xx = xx[(~np.isnan(xx)) & (xx != -666) & (xx != -333)]
            if len(xx) > 0:
                varstat[self.srt_idx[self.box_idx[i]], :] = np.histogram(xx, binvec)[0]
            elif len(xx) == 0:
                varstat[self.srt_idx[self.box_idx[i]], :] = np.nan
            else:
                continue

        varstat[np.isnan(varstat)] = self.fillvalue
        vargrid = {}
        vargrid[varname + "/Histogram_Counts"] = np.reshape(
            varstat,
            (
                self.grid["matrixsize"][0],
                self.grid["matrixsize"][1],
                np.size(binvec) - 1,
            ),
        )
        return vargrid

    def compute_2D_histogram(self, var1, var2, binvec1, binvec2, varname, var_name_out):
        var1 = reformat_vector(var1)
        var2 = reformat_vector(var2)

        # check if the sizes of the coordinates passed to the function are consistent
        if (
            np.shape(self.lat) != np.shape(self.lon)
            or np.shape(self.lat) != np.shape(var1)
            or np.shape(self.lat) != np.shape(var2)
        ):
            raise ValueError("Input coordinates have different size")

        # initialize output variables
        var2Dstat = np.zeros(
            (self.init_size, np.size(binvec1) - 1, np.size(binvec2) - 1)
        )  # *np.nan

        # loop for the computation of the output variables
        for i in range(len(self.box_idx)):
            if len(self.box_idx) <= 1:
                continue
            elif i != len(self.box_idx) - 1:
                start = i
                end = i + 1
            else:
                continue

            xx = var1[self.sortidx[self.box_idx[start] : self.box_idx[end]]]
            yy = var2[self.sortidx[self.box_idx[start] : self.box_idx[end]]]
            nan_idx = np.isnan(xx) | np.isnan(yy)
            xx = xx[~nan_idx]
            yy = yy[~nan_idx]
            # idx_333 = xx == -333 | yy == -333
            # idx_666 = xx == -666 | yy == -666
            # xx = xx[(~nan_idx) & (~idx_333) & (~idx_666)]
            # yy = yy[(~nan_idx) & (~idx_333) & (~idx_666)]

            if (len(xx) > 0) & (len(yy) > 0):
                var2Dstat[self.srt_idx[self.box_idx[i]], :, :] = np.histogram2d(
                    xx, yy, bins=(binvec1, binvec2)
                )[0]
            elif (len(xx) == 0) | (len(yy) == 0):
                var2Dstat[self.srt_idx[self.box_idx[i]], :, :] = np.nan
            else:
                continue

        var2Dstat[np.isnan(var2Dstat)] = self.fillvalue
        vargrid = {}
        vargrid[varname + "/" + var_name_out] = np.reshape(
            var2Dstat,
            (
                self.grid["matrixsize"][0],
                self.grid["matrixsize"][1],
                np.size(binvec1) - 1,
                np.size(binvec2) - 1,
            ),
        )

        return vargrid

    def compute_minmax(self, var, varname):
        var = reformat_vector(var)

        # check if the sizes of the coordinates passed to the function are consistent
        if np.shape(self.lat) != np.shape(self.lon) or np.shape(self.lat) != np.shape(
            var
        ):
            raise ValueError("Input coordinates have different size")

        # initialize output variables
        varmax = np.zeros(self.init_size) * np.nan
        varmin = np.zeros(self.init_size) * np.nan

        # loop for the computation of the output variables
        for i in range(len(self.box_idx)):
            if len(self.box_idx) <= 1:
                continue
            elif i != len(self.box_idx) - 1:
                start = i
                end = i + 1
            else:
                continue

            # grab data from var, make sure there are no nans
            xx = var[self.sortidx[self.box_idx[start] : self.box_idx[end]]]
            xx = xx[~np.isnan(xx)]
            if len(xx) > 0:
                varmax[self.srt_idx[self.box_idx[i]]] = np.max(xx)
                varmin[self.srt_idx[self.box_idx[i]]] = np.min(xx)
            elif len(xx) == 0:
                varmax[self.srt_idx[self.box_idx[i]]] = np.nan
                varmin[self.srt_idx[self.box_idx[i]]] = np.nan
            else:
                continue

        # Set all NaN values to fill, see issue-15
        varmax[np.isnan(varmax)] = self.fillvalue
        varmin[np.isnan(varmin)] = self.fillvalue

        if varname != "":
            varname += "/"
        # write the outputs into the output dictionary
        vargrid = {}
        vargrid[varname + "Max"] = np.reshape(varmax, self.grid["matrixsize"])
        vargrid[varname + "Min"] = np.reshape(varmin, self.grid["matrixsize"])

        return vargrid


def yori_median(var, binvec, resolution):
    # bins = np.arange(0, max_value+resolution, resolution)
    bins = binvec
    hist, edges = np.histogram(var, bins)
    median_out = estimate_median(hist, edges, resolution)
    return median_out, edges


def estimate_median(hist, edges, resolution):
    msg1 = (
        "Median Error: something is wrong with i_neg or i_pos that I did not "
        "anticipate. If you see this error, please send an email to "
        "paolo.veglio@ssec.wisc.edu providing a test case able to reproduce the "
        "issue. Thanks."
    )
    msg2 = (
        "Median Error: corr_factor should never be negative. If you see this error "
        "send an email to paolo.veglio@ssec.wisc.edu providing a test case able to "
        "reproduce the issue. Thanks."
    )
    if np.sum(hist) == 0:
        return {"est_median": np.nan, "hist": hist}

    # this is to account for linear vs log bins. linear bins use np.arange while
    # log bins use np.geomspace, which requires the number of bins, not their size
    if resolution > 1:
        resolution = np.diff(edges)

    rel_area = resolution * (np.cumsum(hist) - np.cumsum(hist)[-1] / 2)

    if np.sum(hist) == 1:
        idx = np.nonzero(hist != 0)[0]
        return {"est_median": edges[idx], "hist": hist}

    i_zero = np.nonzero(rel_area == 0)[0]
    i_pos = np.nonzero(rel_area > 0)[0]
    i_neg = np.nonzero(rel_area < 0)[0]

    num_count = hist[i_pos[0]]
    corr_factor = -rel_area[i_pos[0] - 1]

    if corr_factor == 0 and len(i_neg) > 0:
        est_median = (edges[i_neg[-1] + 1] + edges[i_pos[0]]) / 2
    elif len(i_neg) == 0:
        if len(i_zero) > 0:
            est_median = edges[i_zero[0]]
        elif len(i_pos) > 0:
            est_median = edges[i_pos[0]]
        else:
            # this should never happen. I'm leaving it for now in case something weird
            # makes the code enter this condition
            raise ValueError(msg1)
    elif corr_factor > 0:
        est_median = edges[i_pos[0]] + corr_factor / num_count
    else:
        # this should never happen. I'm leaving it for now in case something weird
        # makes the code enter this condition
        raise ValueError(msg2)

    median_out = {"est_median": est_median, "hist": hist}

    return median_out


def remedian(arr: np.ndarray) -> np.ndarray:
    def prime_factors(n):
        i = 2
        factors = []
        while i * i <= n:
            if n % i:
                i += 1
            else:
                n //= i
                factors.append(i)
        if n > 1:
            factors.append(n)
        return np.array(factors)

    m = arr
    primes = prime_factors(len(m))
    for p in primes[primes > 2]:
        tmp_arr = m[(len(m) % p) :]
        newdim = int(len(tmp_arr) / p)
        tmp_arr = np.reshape(tmp_arr, (newdim, p))
        m = np.median(tmp_arr, axis=1)

    return np.median(m)


def reformat_vector(vec):
    if vec.ndim > 1:
        vec = np.squeeze(vec)
        vec = np.reshape(vec, np.shape(vec)[0] * np.shape(vec)[1])

    vec = np.array(vec, dtype="f8")
    return vec
