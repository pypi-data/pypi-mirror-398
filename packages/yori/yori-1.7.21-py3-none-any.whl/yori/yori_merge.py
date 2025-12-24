import sys

# import warnings
from importlib.metadata import distribution

import netCDF4 as nc

import yori.aggrtools as tools
import yori.config_reader as cfg
import yori.IOtools as IO

VERSION = distribution("yori").version
_attr_list = ["Yori_version", "input_files", "daily_defn_of_day_adjustment"]


def merge(file_list, fname_out, compression=5, fill_value=None):
    f_in = nc.Dataset(file_list[0])
    f_out = nc.Dataset(fname_out, "w")
    f_out.setncattr("Yori_version", VERSION)
    f_out.setncattr(
        "daily_defn_of_day_adjustment", f_in.getncattr("daily_defn_of_day_adjustment")
    )
    f_out.setncattr("YAML_config", f_in.getncattr("YAML_config"))
    f_out.setncattr("input_files", "")
    cfg_data = f_out.getncattr("YAML_config")
    ymlSet = cfg.ConfigReader(cfg_data)
    if fill_value is None:
        fv = ymlSet.grid_settings["fill_value"]
    else:
        fv = fill_value

    lat = f_in["latitude"][:].data
    f_out.createDimension("latitude", len(lat))
    f_out.createVariable("latitude", "f8", ("latitude",), fill_value=fv)
    f_out["latitude"][:] = lat
    lon = f_in["longitude"][:].data
    f_out.createDimension("longitude", len(lon))
    f_out.createVariable("longitude", "f8", ("longitude",), fill_value=fv)
    f_out["longitude"][:] = lon

    f_in.close()
    f_out.close()

    for input_file in file_list:
        merge_files(input_file, fname_out, compression, fill_value)


def merge_files(input_file, output_file, compression, fill_value):
    f_out = nc.Dataset(output_file, "a")
    f_in = nc.Dataset(input_file)
    ymlSet = cfg.ConfigReader(f_in.getncattr("YAML_config"))
    grid_size = ymlSet.grid_settings["gridsize"]

    merge_vars = {}
    for grp in list(f_in.groups):
        merge_vars[grp] = {}
        for var in list(f_in[grp].variables):
            merge_vars[grp][var] = f_in[grp][var][:]
        merge_vars = tools.restructDict(merge_vars)
        IO.write_output(f_out, merge_vars, compression, grid_size, ymlSet, fill_value)
        merge_vars = {}

    for i in range(len(ymlSet.var_settings)):
        var_settings = ymlSet.var_settings[i]
        IO.append_attributes(f_out, var_settings)

    update_global_attributes(f_in, f_out)

    f_out.close()
    f_in.close()


def update_global_attributes(f_in, f_out):
    str_config_in = f_in.getncattr("YAML_config").split("variable_settings:")[1]
    flist = f_out.getncattr("input_files") + f_in.getncattr("input_files")

    str_config = f_out.getncattr("YAML_config") + str_config_in

    f_out.setncattr("input_files", flist)
    f_out.setncattr("YAML_config", str_config)


"""
def merge(in_file_1, in_file_2, out_fname, replace=False, compression=5, fill_value=None):

    if replace is True:
        # f_merged = nc.Dataset(in_file_1, 'a')
        # f1 = f_merged
        warnings.warn('This feature is still in development, the code will ignore '
                      'user input and run with "--replace False".')
    else:
        f1 = nc.Dataset(in_file_1)
        f_merged = nc.Dataset(out_fname, 'w')
    f2 = nc.Dataset(in_file_2)

#    for attr in _attr_list:
#        try:
#            attr1 = f1.getncattr(attr)
#            attr2 = f2.getncattr(attr)
#        except AttributeError:
#            pass

    # Attribute checks
    if 'Yori_version' not in f1.ncattrs() or 'Yori_version' not in f2.ncattrs():
        warnings.warn('yori-merge could not find "Yori_version" in the input files.')
    if f1.getncattr('Yori_version') != f2.getncattr('Yori_version'):
        warnings.warn('Yori_version warning #1')
    if (f1.getncattr('Yori_version') != str(VERSION) or
       f2.getncattr('Yori_version') != str(VERSION)):
        warnings.warn('Yori_version warning #2')
    f_merged.setncattr('Yori_version', str(VERSION))

    fl1, fl2 = '', ''
    if 'input_files' in f1.ncattrs():
        fl1 = f1.getncattr('input_files')
    if 'input_files' in f2.ncattrs():
        fl2 = f2.getncattr('input_files')
    f_merged.setncattr('input_files', fl1 + ',' + fl2)

    if ('daily_defn_of_day_adjustment' in f1.ncattrs() and
       'daily_defn_of_day_adjustment' in f2.ncattrs()):
        if (f1.getncattr('daily_defn_of_day_adjustment') !=
           f2.getncattr('daily_defn_of_day_adjustment')):
            warnings.warn('"daily_defn_of_day_adjustment" warning #1')
    elif ('daily_defn_of_day_adjustment' in f1.ncattrs() or
          'daily_defn_of_day_adjustment' in f2.ncattrs()):
        warnings.warn('"daily_defn_of_day_adjustment" warning #2')
    else:
        pass
    f_merged.setncattr('daily_defn_of_day_adjustment', '')

    config_str_1 = f1.getncattr('YAML_config')[:]
    config_str_2 = f2.getncattr('YAML_config')[:]

    yml_cfg1 = cfg.ConfigReader(config_str_1)
    yml_cfg2 = cfg.ConfigReader(config_str_2)

    if yml_cfg1.grid_settings['gridsize'] != yml_cfg2.grid_settings['gridsize']:
        raise ValueError('Value of "gridsize" in file 1 does not match '
                         'the value in file 2')
    if yml_cfg1.grid_settings['projection'] != yml_cfg2.grid_settings['projection']:
        raise ValueError('"projection" setting in file 1 is different from '
                         'the one in file 2')
    if (yml_cfg1.grid_settings['fill_value'] != yml_cfg2.grid_settings['fill_value']
       and fill_value is not None):
        warnings.warn('"fill_value" is set to different in the two input files, '
                      'in this situation Yori chooses the value for the first file '
                      'passed. If this is not the desired choice, you can define a '
                      'new fill_value by using the option --fill-value provided '
                      'with the merge tool ("merge --help" for more info)')

"""


if __name__ == "__main__":
    merge(sys.argv[1], sys.argv[2], replace=False)
