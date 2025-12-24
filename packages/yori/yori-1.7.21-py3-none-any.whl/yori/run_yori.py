import os.path
import sys
import warnings
from importlib.metadata import distribution

import netCDF4 as nc
import numpy as np

import yori.config_reader as cfg
import yori.gridtools as grid
import yori.IOtools as IO

VERSION = distribution("yori").version
_NC_FILL_DOUBLE = -9999.0
# temp workaround, not sure if there are better ways to make yori packages
# work from shell probably I need to add the entire path to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class SetupYori:
    def __init__(self, config_file, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.outpath, self.outfn = os.path.split(output_file)
        warnings.simplefilter("module")

        if os.path.isfile(output_file):
            raise IOError(
                f"The file {self.outfn} already exists in " + "the destination folder"
            )

        if config_file.lower().endswith(".csv"):
            cfg.write_config(config_file)
            config_file = config_file[:-3] + "yml"

        cf = open(config_file)
        config_str = cf.read()
        cf.close()
        self.ymlSet = cfg.ConfigReader(config_str)
        self.grid_proj = self.ymlSet.grid_settings["projection"]
        self.grid_size = np.array(self.ymlSet.grid_settings["gridsize"], dtype="f8")
        if self.grid_proj == "equal_area":
            self.grid_size = 1000 * self.grid_size

        if (
            "lat_in" not in self.ymlSet.grid_settings
            or "lon_in" not in self.ymlSet.grid_settings
        ):
            warnings.warn(
                "Coordinate names are not defined in the configuration file. "
                "This format will be discontinued in future versions",
                DeprecationWarning,
            )

            self.lat_key = "latitude"
            self.lon_key = "longitude"

        else:
            self.lat_key = self.ymlSet.grid_settings["lat_in"]
            self.lon_key = self.ymlSet.grid_settings["lon_in"]

        if "fill_value" in self.ymlSet.grid_settings:
            self.fv = self.ymlSet.grid_settings["fill_value"]
        else:
            self.fv = _NC_FILL_DOUBLE

        if (self.fv - np.trunc(self.fv)) != 0:
            warnings.warn(
                "Yori does not support the definition of non-integer fill values. "
                + f"For now the code will use the truncated value {np.trunc(self.fv)} "
                + "instead, but using a non-integer fill value will cause an error in "
                + "future versions",
                DeprecationWarning,
            )
            self.fv = np.trunc(self.fv)
            # raise IOError('The fill value must be an integer')

    def setCoordinates(self):
        tmplat = np.zeros((1,))
        tmplon = np.zeros((1,))
        # NOTE:
        # this part works as long as the projection is equal angle.
        # Once we introduce different projections this part needs to be changed
        myCoords = grid.Grid(tmplat, tmplon, self.grid_size, self.grid_proj, self.fv)
        gridvar = {}
        coord_grid = myCoords.create_index()
        gridvar["latitude"] = coord_grid["latgrid"]
        gridvar["longitude"] = coord_grid["longrid"]
        #        gridvar['latitude'] = np.arange(-90.+self.grid_size/2.,
        #                                        90.+self.grid_size-self.grid_size/2.,
        #                                        self.grid_size)
        #        gridvar['longitude'] = np.arange(-180.+self.grid_size/2.,
        #                                         180.+self.grid_size-self.grid_size/2.,
        #                                         self.grid_size)

        return gridvar

    def setVariable(self, var_settings, lat, data_in, joint=False):
        if joint is False:
            var_name_in = var_settings["name_in"]
        else:
            var_name_in = var_settings["joint_var"]["name_in"]

        var_name_out = var_settings["name_out"]

        mask_list, inv_mask_list, extra_mask_list = [], [], []
        if "masks" in var_settings:
            mask_list = var_settings["masks"]
        if "inverse_masks" in var_settings:
            inv_mask_list = var_settings["inverse_masks"]
        if "extra_masks" in var_settings:
            extra_mask_list = var_settings["extra_masks"]

        current_mask = create_mask(
            data_in, np.shape(lat), mask_list=mask_list, inv_mask_list=inv_mask_list
        )
        current_mask = create_mask(
            data_in,
            np.shape(lat),
            mask_list=extra_mask_list,
            existing_mask=current_mask,
        )

        mask_idx = np.nonzero(current_mask == 0)
        tmp_data_in = data_in[var_name_in][:]
        if hasattr(tmp_data_in, "filled"):
            tmp_data_in = tmp_data_in.filled(np.nan)
        masked_data_in = tmp_data_in
        masked_data_in[mask_idx] = np.nan
        return masked_data_in, var_name_out

    def runYori(self, debug=False, compression=0):
        data_in = nc.Dataset(self.input_file)
        gridvar = self.setCoordinates()

        lat = data_in[self.lat_key][:]
        lon = data_in[self.lon_key][:]
        myGrid = grid.ComputeVariables(
            lat, lon, self.grid_size, self.grid_proj, self.fv
        )

        data_out = nc.Dataset(self.output_file, "w")

        data_out.setncattr("YAML_config", self.ymlSet.yaml_str)
        data_out.setncattr("Yori_version", str(VERSION))

        for i in range(len(self.ymlSet.var_settings)):
            var_settings = self.ymlSet.var_settings[i]

            if "only_histograms" not in var_settings:
                only_hist = False
            else:
                only_hist = True

            # 'only_weights' is temporary, when defined in cfg, change accordingly
            if "only_weights" not in var_settings:
                only_wgt = False
            else:
                only_wgt = True

            masked_data_in, var_name_out = self.setVariable(var_settings, lat, data_in)

            if only_hist is False and only_wgt is False:
                tmp_gridvar = myGrid.compute_stats(masked_data_in, var_name_out)
                gridvar.update(tmp_gridvar)

            if "median" in var_settings:
                varbins = self.ymlSet.readHist(var_settings["median"])
                tmp_gridvar = myGrid.compute_median(
                    masked_data_in,
                    var_name_out,
                    varbins,
                    var_settings["median"]["interval"],
                )
                gridvar.update(tmp_gridvar)

            if "minmax" in var_settings:
                tmp_gridvar = myGrid.compute_minmax(masked_data_in, var_name_out)
                gridvar.update(tmp_gridvar)

            if "weights" in var_settings:
                wgt = data_in[var_settings["weights"]]
                tmp_gridvar = myGrid.compute_wgt_stats(
                    masked_data_in, var_name_out, weight=wgt
                )
                gridvar.update(tmp_gridvar)

            if "histograms" in var_settings:
                varbins = self.ymlSet.readHist(var_settings["histograms"])
                tmp_gridvar = myGrid.compute_histogram(
                    masked_data_in, varbins, var_name_out
                )
                gridvar.update(tmp_gridvar)

            if "2D_histograms" in var_settings:
                for k in range(len(var_settings["2D_histograms"])):
                    hist_2D_settings = var_settings["2D_histograms"][k]
                    varbins = self.ymlSet.readHist(hist_2D_settings["primary_var"])
                    joint_varbins = self.ymlSet.readHist(hist_2D_settings["joint_var"])

                    joint_masked_data_in, vno = self.setVariable(
                        hist_2D_settings, lat, data_in, joint=True
                    )

                    joint_var_name_out = hist_2D_settings["name_out"]
                    tmp_gridvar = myGrid.compute_2D_histogram(
                        masked_data_in,
                        joint_masked_data_in,
                        varbins,
                        joint_varbins,
                        var_name_out,
                        joint_var_name_out,
                    )
                    gridvar.update(tmp_gridvar)

            IO.write_output(
                data_out,
                gridvar,
                compression,
                self.grid_size,
                self.ymlSet,
                self.fv,
                edges=myGrid.edges,
                write_edges=True,
            )
            IO.append_attributes(data_out, var_settings)
            gridvar = {}

        data_in.close()
        data_out.close()


def callYori(config_file, input_file, output_file, debug=False, compression=0):
    Yori = SetupYori(config_file, input_file, output_file)
    Yori.runYori(debug, compression)


def create_mask(in_data, init_size, mask_list=[], inv_mask_list=[], existing_mask=None):
    if existing_mask is None:
        out_mask = np.array(np.ones(init_size), dtype="i8")
    else:
        out_mask = existing_mask

    for mask in mask_list:
        update_mask = np.array(in_data[mask][:], dtype="i8")
        out_mask &= update_mask

    # Note: this doesn't have to be used for inverse masks. Another possible
    # use is to update existing masks, like the case of 2D histograms with
    # extra masks that are being applied on top of any existing mask
    for inverse_mask in inv_mask_list:
        tmp_inv_mask = np.array(in_data[inverse_mask][:], dtype="i8")
        update_mask = np.abs(tmp_inv_mask - 1)
        out_mask &= update_mask

    return out_mask


# main
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("usage: rungrid.py <config_file> <input_file> <output_file>")
        sys.exit(1)

    config_file = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    comp = sys.argv[4] if len(sys.argv) == 5 else 0

    callYori(config_file, input_file, output_file, compression=comp)
