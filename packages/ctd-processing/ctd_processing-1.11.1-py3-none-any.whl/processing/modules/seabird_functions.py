import logging
import warnings
from pathlib import Path
from typing import Tuple

import numpy as np
from scipy.signal import butter, correlate, filtfilt, find_peaks
from seabirdfilehandler import CnvFile
from seabirdfilehandler.ctddata import CTDData
from seabirdfilehandler.parameter import Parameter
from seabirdscientific import processing as sbs_proc

from processing.module import ArrayModule, MissingParameterError

logger = logging.getLogger(__name__)


class LoopRemoval(ArrayModule):
    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self,
        input: Path | str | CnvFile | CTDData,
        arguments: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        default_values: dict = {
            "precut_period": 5,
            "cut_period": 10,
            "mean_speed_percent": 30,
            "delay": 2,
            "filter_order": 4,
        },
        **kwargs,
    ) -> None | CnvFile | CTDData:
        return super().__call__(
            input, arguments, output, output_name, default_values
        )

    def transformation(self) -> bool:
        """
        Calls the loop removal function and handles the resulting flag values
        for array truncation.
        """
        if not self._check_parameter_existence("prDM"):
            logger.error("Failed, not finding pressure")
            return False

        pressure = self.ctd_data["prDM"].data

        new_flag_array = self.jens_loop_removal(
            pressure=pressure,
            sample_interval=1 / self.sample_rate,
            **self.arguments,
        )

        self.handle_new_flags(new_flag_array)
        return True

    def jens_loop_removal(
        self,
        pressure: np.ndarray,
        sample_interval: float,
        precut_period: int = 5,
        cut_period: int = 10,
        mean_speed_percent: int = 20,
        delay: int = 2,
        filter_order: int = 4,
    ):
        """
        Flag loops in CTD data caused by ship heave.
        Credit: Dr. Jens Faber, IOW.

        Parameters:
        - pressure: Array of vertical axis values (e.g., pressure).
        - time: Array of time values.
        - precut_period: Cutoff period for the pre-filter (seconds).
        - cut_period: Cutoff period for the main filter (seconds).
        - mean_speed_percent: Percentage of filtered velocity to use as a threshold.
        - delay: Delay (in seconds) to shift the flag array.
        - filter_order: Order of the Butterworth filter.

        Returns:
        - flag_bool: Boolean array where `True` indicates a flagged (bad) data point.
        """
        warnings.warn(
            "LoopRemoval is still in an experimental state. Be cautious with the results."
        )
        # Compute vertical velocityocity
        velocity = np.gradient(pressure) / sample_interval

        # Pre-filtering: Low-pass Butterworth filter
        b, a = butter(
            filter_order, 2 * sample_interval / precut_period, btype="low"
        )
        # Pad the signal
        velocity_padded = np.pad(velocity, (3, 3), mode="edge")
        velocity_filt_pre = filtfilt(b, a, velocity_padded)
        # Remove padding
        velocity_filt_pre = velocity_filt_pre[3:-3]

        # Main filtering: Low-pass Butterworth filter
        b, a = butter(
            filter_order, 2 * sample_interval / cut_period, btype="low"
        )
        # Pad the signal
        velocity_padded = np.pad(velocity_filt_pre, (3, 3), mode="edge")
        velocity_filt = filtfilt(b, a, velocity_padded)
        # Remove padding
        velocity_filt = velocity_filt[3:-3]

        # Flag data where velocityocity is below the threshold
        flag_bool = velocity < (velocity_filt * mean_speed_percent / 100)

        # Shift the flag array to account for delay
        sample_shift = int(round(delay / sample_interval))
        flag_bool = np.roll(flag_bool, sample_shift)
        # Ensure no flags are set before the delay
        flag_bool[:sample_shift] = False

        return flag_bool


class AlignCTD(ArrayModule):
    """
    Align the given parameter columns.

    Given a measurement parameter in parameters, the column will be shifted
    by either, a float amount that is given as value, or, by a calculated
    amount, using cross-correlation between the high-frequency components of
    the temperature and the target parameters.
    The returned numpy array will thus feature the complete CnvFile data,
    with the columns shifted to their correct positions.
    """

    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self,
        input: Path | str | CnvFile | CTDData,
        arguments: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        default_values: dict = {
            "Oxygen": 3,
            "minimum_correlation": 0.1,
        },
        **kwargs,
    ) -> None | CnvFile | CTDData:
        return super().__call__(
            input, arguments, output, output_name, default_values
        )

    def transformation(self) -> bool:
        """
        Performs the base logic of distinguishing whether to use given values
        or compute a delay.

        Returns
        -------
        A numpy array, representing the cnv data after the alignment.

        """
        self.check_whether_working_on_binned_data()
        return_value = False
        new_parameter_metadata = {}
        for key, value in self.handle_parameter_input(self.arguments).items():
            # key is something like oxygen1 or oxygen2
            # value is either None or a numerical value in string or other form
            target_parameters = [
                param
                for param in self.ctd_data.get_parameter_list()
                if (param.param.lower().startswith(key[:-1]))
                and (str(int(key[-1]) - 1) in param.name)
            ]
            # if there are no measurement parameters of the given key inside
            # the cnv file, remove the key from the input, to avoid printing
            # that key to the output files header
            if len(target_parameters) == 0:
                continue
            # if no shift value given, estimate it
            if not value:
                value, correlation_value = self.estimate_sensor_delay(
                    delayed_parameter=target_parameters[0],
                    margin=len(self.ctd_data.get_full_data_array()) // 4,
                )
                correlation_string = f", with PCC: {correlation_value}"
                if not self.check_correlation_result(
                    value,
                    correlation_value,
                    self.arguments["minimum_correlation"],
                ):
                    correlation_string = f", default value. Calculated delay: {str(float('{:.2f}'.format(value / self.sample_rate)))} PCC: {correlation_value}"
                    # set to a default value
                    value = 3 * self.sample_rate
            else:
                # the input is in seconds, so we calculate a shift in rows
                value = float(value) * self.sample_rate
                correlation_string = ""
            # apply shift for all columns of the given parameter
            for parameter in target_parameters:
                # get the number of decimals to format the output in the same
                # way
                number_of_decimals = len(str(parameter.data[0]).split(".")[1])
                # do the shifting/alignment
                parameter.data = np.append(
                    parameter.data[int(value) :,].round(
                        decimals=number_of_decimals
                    ),
                    np.full((int(value),), self.bad_flag),
                )
                # format the output back to seconds
                new_parameter_metadata[parameter.name] = (
                    str(float("{:.2f}".format(value / self.sample_rate)))
                    + "s"
                    + correlation_string
                )
                try:
                    self.array = self.ctd_data.get_full_data_array()
                except IndexError as error:
                    logger.error(
                        f"AlignCTD failed for {self.ctd_data.path_to_file} while aligning {parameter}: {error}"
                    )
                    return_value = False
                    break
                # at least one column has been altered so we can give positive
                # feedback
                return_value = True
        self.arguments = new_parameter_metadata
        return return_value

    def estimate_sensor_delay(
        self,
        delayed_parameter: Parameter,
        margin: int = 240,
        shift_seconds: int = 10,
    ) -> Tuple[float, float]:
        """
        Estimate delay between a delayed parameter and temperature signals via
        cross-correlation of high-frequency components.

        Parameters
        ----------
        delayed_parameter: Parameter :
            The parameter whose delay shall be computed.

        margin: int :
            A number of data points that are cutoff from both ends.
             (Default value = 240)

        shift_seconds: int :
             Maximum time window to search for lag (default: 10 seconds).

        Returns
        -------
        A float value, representing the parameter delay in seconds.

        """
        temperature = self.find_corresponding_temperature(
            delayed_parameter
        ).data
        delayed_values = delayed_parameter.data
        assert len(temperature) == len(delayed_values)
        # remove edge effects (copying Gerds MATLAB software)
        while len(temperature) <= 2 * margin:
            margin = margin // 2

        t_shortened = np.array(temperature[margin:-margin])
        v_shortened = np.array(delayed_values[margin:-margin])

        if np.all(np.isnan(v_shortened)):
            return np.nan, np.nan

        # design Butterworth filter
        b, a = butter(3, 0.005)

        # smooth signals
        t_smoothed = filtfilt(b, a, t_shortened)
        v_smoothed = filtfilt(b, a, v_shortened)

        # high-frequency components
        t_high_freq = t_shortened - t_smoothed
        v_high_freq = v_shortened - v_smoothed

        # cross-correlation
        max_lag = int(shift_seconds * self.sample_rate)
        sign = self.get_correlation(delayed_parameter)
        corr = correlate(v_high_freq, t_high_freq * sign, mode="full")
        lags = np.arange(-len(t_high_freq) + 1, len(t_high_freq))
        lag_indices = np.where(np.abs(lags) <= max_lag)[0]

        # normalize correlation values
        norm_factor = np.sqrt(np.sum(v_high_freq**2) * np.sum(t_high_freq**2))
        corr_normalized = corr / norm_factor

        corr_segment = corr_normalized[lag_indices]
        lags_segment = lags[lag_indices]

        # restrict to only positive delays
        positive_indices = np.where(lags_segment > 0)[0]
        corr_segment_positive = corr_segment[positive_indices]

        peaks, props = find_peaks(
            corr_segment_positive, height=0.01, distance=5
        )

        # handle case, when no correlation can be found
        if len(peaks) == 0:
            return np.nan, np.nan

        # find lag with highest correlation
        best_index = int(np.argmax(props["peak_heights"]))

        return float(peaks[best_index]), float(
            "{:.2f}".format(props["peak_heights"][best_index])
        )

    def check_correlation_result(
        self,
        value: float,
        correlation_value: float,
        minimum_correlation: float = 0.1,
    ) -> bool:
        """
        Performs several checks on the delay outputed by
        self.estimate_sensor_delay and returns True, if the result is
        considered feasible.
        """
        if (value is np.nan) or (correlation_value is np.nan):
            return False
        value = value / self.sample_rate
        if correlation_value < minimum_correlation:
            return False
        if value < 1 or value > 6:
            return False
        return True

    def find_corresponding_temperature(
        self, parameter: Parameter
    ) -> Parameter:
        """
        Find the temperature values of the sensor that shared the same water
        mass as the input parameter.

        Parameters
        ----------
        parameter: Parameter :
            The parameter of interest.


        Returns
        -------
        The temperature parameter object.

        """
        if "0" in parameter.name:
            return self.ctd_data["t090C"]
        elif "1" in parameter.name:
            return self.ctd_data["t190C"]
        else:
            raise MissingParameterError("AlignCTD", "Temperature")

    def get_correlation(self, parameter: Parameter) -> float:
        """
        Gives a number indicating the cross correlation type regarding the
        input parameter and the temperature.

        Basically distinguishes between positive correlation, 1, and anti-
        correlation, -1. This value is then used to alter the temperature
        values accordingly.

        Parameters
        ----------
        parameter: Parameter :
            The parameter to cross correlate with temperature.

        Returns
        -------
        A float value representing positive or negative correlation.

        """
        if parameter.metadata["name"].lower().startswith("oxygen"):
            return -1
        else:
            return 1

    def handle_parameter_input(self, input_dict: dict) -> dict:
        new_dict = {}
        all_parameter_names = [
            value["name"].lower()
            for value in self.ctd_data.get_metadata().values()
        ]
        for parameter_input, value in input_dict.items():
            # remove all non-alphanumeric characters
            parameter = (
                "".join(filter(str.isalnum, parameter_input)).lower().strip()
            )
            if parameter_input[-1] in ["1", "2"]:
                parameter = parameter[:-1]
                number = parameter_input[-1]
            else:
                number = None
            parameter_names = [
                name
                for name in all_parameter_names
                if name.startswith(parameter)
            ]
            # check, whether we are working with multiple sensors
            if "2" in [name[-1] for name in parameter_names]:
                # differentiate the different cases for 2 sensors
                # only parameter without sensor number information given
                if parameter.lower() in parameter_names and not number:
                    new_dict[f"{parameter}1"] = value
                    new_dict[f"{parameter}2"] = value
                # explicitly given sensor 1
                if parameter.lower() in parameter_names and number == "1":
                    new_dict[f"{parameter}1"] = value
                # explicitly given sensor 2
                if parameter.lower() in parameter_names and number == "2":
                    new_dict[f"{parameter}2"] = value
            else:
                # single sensor is easy, just use the value for sensor 1
                if not parameter[-1] == "2":
                    new_dict[f"{parameter}1"] = value
        return new_dict


class WFilter(ArrayModule):
    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self,
        input: Path | str | CnvFile | CTDData,
        arguments: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        default_values: dict = {
            "Pressure": {
                "window_type": sbs_proc.WindowFilterType.GAUSSIAN,
                "window_width": 20,
                "half_width": 0.415,
                "offset": 0,
            },
            "Temperature": {
                "window_type": sbs_proc.WindowFilterType.GAUSSIAN,
                "window_width": 24,
                "half_width": 0.5,
                "offset": 0,
            },
            "Conductivity": {
                "window_type": sbs_proc.WindowFilterType.GAUSSIAN,
                "window_width": 24,
                "half_width": 0.5,
                "offset": 0,
            },
            "Salinity": {
                "window_type": sbs_proc.WindowFilterType.GAUSSIAN,
                "window_width": 24,
                "half_width": 0.5,
                "offset": 0,
            },
            "Oxygen": {
                "window_type": sbs_proc.WindowFilterType.GAUSSIAN,
                "window_width": 48,
                "half_width": 1,
                "offset": 0,
            },
            "Fluorometer": {
                "window_type": sbs_proc.WindowFilterType.MEDIAN,
                "window_width": 5,
                "half_width": 1,
                "offset": 0,
            },
            "Turbidity Meter": {
                "window_type": sbs_proc.WindowFilterType.MEDIAN,
                "window_width": 5,
                "half_width": 1,
                "offset": 0,
            },
            "PAR": {
                "window_type": sbs_proc.WindowFilterType.MEDIAN,
                "window_width": 5,
                "half_width": 1,
                "offset": 0,
            },
            "SPAR": {
                "window_type": sbs_proc.WindowFilterType.MEDIAN,
                "window_width": 5,
                "half_width": 1,
                "offset": 0,
            },
        },
        **kwargs,
    ) -> None | CnvFile | CTDData:
        self.default_values = default_values
        return super().__call__(input, arguments, output, output_name)

    def transformation(self) -> bool:
        """
        Performs the base logic of distinguishing whether to use given values
        or compute a delay.

        Returns
        -------
        A numpy array, representing the cnv data after the alignment.

        """
        general_kwargs = {
            "flags": self.flags,
            "sample_interval": 1 / self.sample_rate,
            "exclude_flags": False,
            "flag_value": self.bad_flag,
        }
        new_arguments = {}
        for param in self.ctd_data.parameters.get_parameter_list():
            try:
                specific_kwargs = self.default_values[param.param]
            except KeyError:
                specific_kwargs = {}
            if param.param in self.arguments:
                logger.error(param.param)
                for key, value in self.arguments[param.param].items():
                    if key == "window_type":
                        value = sbs_proc.WindowFilterType(value.lower())
                    specific_kwargs[key] = value
            if specific_kwargs:
                with warnings.catch_warnings(action="ignore"):
                    param.data = sbs_proc.window_filter(
                        data_in=param.data,
                        **general_kwargs,
                        **specific_kwargs,
                    )
                new_arguments[param.param] = ", ".join(
                    [
                        (
                            str(value)
                            if type(value) is not sbs_proc.WindowFilterType
                            else value.value.capitalize()
                        )
                        for value in specific_kwargs.values()
                    ]
                )

        self.arguments = new_arguments

        return True


class CellTM(ArrayModule):
    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self,
        input: Path | str | CnvFile | CTDData,
        arguments: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        default_mapping: dict = {
            "sbe9": (0.03, 7.0),
            "sbe19": (0.04, 8.0),
        },
        **kwargs,
    ) -> None | CnvFile | CTDData:
        self.cell_tm_param_mapping = default_mapping
        return super().__call__(input, arguments, output, output_name)

    def transformation(self) -> bool:
        if "alpha" in self.arguments and "beta" in self.arguments:
            self.alpha = self.arguments["alpha"]
            self.beta = self.arguments["beta"]
        else:
            try:
                for key in self.cell_tm_param_mapping:
                    if key in self.ctd_data.header[0].lower().replace(" ", ""):
                        self.alpha, self.beta = self.cell_tm_param_mapping[key]

            except KeyError:
                logger.error(
                    f"No cell_tm parameters for instrument {self.ctd_data.header[0][:-10]}. No cell thermal mass correction applied."
                )
            else:
                self.arguments["alpha"] = self.alpha
                self.arguments["beta"] = self.beta
        for param in [p for p in self.ctd_data if p.param == "Conductivity"]:
            # check availability of temperature in this sensor strand
            if param.sensor_number == 1:
                temperature = "t090C"
            else:
                temperature = "t190C"
            if not self._check_parameter_existence(temperature):
                logger.error(
                    f"Missing temperature for sensor strand {param.sensor_number}"
                )
                return False

            # enforce correct conductivity unit
            if param.unit == "mS/cm":
                conductivity = param.data / 10.0
            elif param.unit == "S/m":
                conductivity = param.data
            else:
                logger.error(
                    f"Unknown conductivity unit {param.unit}. Aborting."
                )
                return False
            corrected_conductivity = sbs_proc.cell_thermal_mass(
                temperature_C=self.ctd_data[temperature].data,
                conductivity_Sm=conductivity,
                amplitude=self.alpha,
                time_constant=1 / self.beta,
                sample_interval=1 / self.sample_rate,
            )

            if param.unit == "mS/cm":
                param.data = corrected_conductivity * 10
            elif param.unit == "S/m":
                param.data = corrected_conductivity

        return True


class BinAvg(ArrayModule):
    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self,
        input: Path | str | CnvFile | CTDData,
        arguments: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        default_values: dict = {
            "bin_variable": "prDM",
            "bin_size": 1,
            "interpolate": True,
            "cast_type": "downcast",
        },
        **kwargs,
    ) -> None | CnvFile | CTDData:
        self.name = "binning"
        return super().__call__(
            input, arguments, output, output_name, default_values
        )

    def transformation(self) -> bool:
        """
        Calls the loop removal function and handles the resulting flag values
        for array truncation.
        """
        self.arguments["cast_type"] = sbs_proc.CastType[
            self.arguments["cast_type"].upper()
        ]
        # drop all flagged data first
        self.ctd_data.drop_flagged_rows()

        dataset = self.ctd_data.get_pandas_dataframe()
        try:
            df = sbs_proc.bin_average(
                dataset=dataset,
                **self.arguments,
            )
        except Exception as error:
            logger.error(
                f"Could not bin {self.ctd_data.path_to_file}: {error}"
            )
            return False
        for column, param in zip(df.columns, self.ctd_data):
            param.data = df[column].to_numpy()

        self.ctd_data[self.arguments["bin_variable"]].data = np.round(
            self.ctd_data[self.arguments["bin_variable"]].data, 0
        )
        # set new sample rate
        if self.arguments["bin_variable"] == "prDM":
            bin_unit = "decibars"
        elif self.arguments["bin_variable"] == "timeS":
            bin_unit = "seconds"
        else:
            bin_unit = self.arguments["bin_variable"]

        self.ctd_data.set_sample_rate(
            float(self.arguments["bin_size"]), bin_unit
        )

        return True
