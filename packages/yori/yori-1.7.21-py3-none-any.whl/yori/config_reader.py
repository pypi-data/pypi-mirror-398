import numpy as np
from ruamel.yaml import YAML


########################################
#               FUNCTION               #
########################################
# function to read the configuration file
class ConfigReader(object):
    #
    def __init__(self, yaml_str):
        yaml_str = str(yaml_str[:])
        # read config
        # config = yaml.load(yaml_str, yaml.RoundTripLoader)
        yaml = YAML(typ="safe")
        config = yaml.load(yaml_str)

        self.grid_settings = config["grid_settings"]
        self.var_settings = config["variable_settings"]
        self.yaml_str = yaml_str

        # read the YAML file and check some exceptions
        var_list_in = []
        var_list_out = []

        for i in range(len(self.var_settings)):
            if any(
                names not in self.var_settings[i] for names in ["name_in", "name_out"]
            ):
                raise IOError(
                    'in YAML file "name_in" or "name_out" '
                    + "are missing somewhere in the file"
                )
            var_list_in.append(self.var_settings[i]["name_in"])
            if "masks" in self.var_settings[i]:
                try:
                    len(self.var_settings[i]["masks"])
                except TypeError:
                    raise IOError(
                        'in YAML file "masks" keyword has been '
                        + "defined without any mask names"
                    )
            if "inverse_masks" in self.var_settings[i]:
                try:
                    len(self.var_settings[i]["inverse_masks"])
                except TypeError:
                    raise IOError(
                        'in YAML file "inverse_masks" keyword has '
                        + "been defined without any mask names"
                    )
            var_list_out.append(self.var_settings[i]["name_out"])

            if "2D_histograms" in self.var_settings[i]:
                # if 'histograms' not in self.var_settings[i]:
                #     raise IOError('in YAML file, "histograms" is not ' +
                #                   'defined. In order to compute a joint' +
                #                   '(2D) histogram the "histograms" ' +
                #                   'keyword must be defined for the first ' +
                #                   'variable')
                jhisto = self.var_settings[i]["2D_histograms"]
                for j in range(len(jhisto)):
                    if "name_out" not in jhisto[j]:
                        raise IOError(
                            'in YAML file, "name_out" is missing '
                            + "from some 2D_histogram"
                        )
                    jvar = jhisto[j]["joint_var"]
                    if "name_in" not in jvar:
                        raise IOError(
                            'in YAML file, "name_in" is missing '
                            + "from some 2D_histogram"
                        )
                    if "extra_masks" in jvar:
                        try:
                            len(jvar["extra_masks"])
                        except TypeError:
                            raise IOError(
                                'in YAML file "extra_masks" '
                                + "keyword has been defined without "
                                + "any mask names"
                            )

        if any(var_list_out.count(x) > 1 for x in var_list_out):
            raise NameError(
                "in YAML file one or more output variables have " + "the same name"
            )

    def read_variable_list(self, var_block):
        var_list = {
            "in": [],
            "out": [],
            "masks": [],
            "inverse_masks": [],
            "histograms": [],
            "2D_histograms": [],
            "extra_masks": [],
            "only_histogram": [],
        }

        for v in self.var_settings:
            if any(names not in v for names in ["name_in", "name_out"]):
                raise IOError(
                    'in YAML file "name_in" or "name_out" '
                    + "are missing somewhere in the file"
                )
            var_list["in"].append(v["name_in"])
            var_list["out"].append(v["name_out"])

        return var_list

    def readHist(self, histBlock):
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
                    np.arange(
                        histBlock["start"], histBlock["stop"], histBlock["interval"]
                    )
                )
        else:
            raise IOError("in YAML file, histogram is not defined correctly")

        return varbins
