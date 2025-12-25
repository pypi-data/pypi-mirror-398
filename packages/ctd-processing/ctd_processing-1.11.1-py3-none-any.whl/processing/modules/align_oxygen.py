from pathlib import Path

import matplotlib.pyplot as plt

# from abc import ABC, abstractmethod
import pandas as pd
from scipy import signal

# from code_tools.logging import get_logger
from seabirdfilehandler.datatablefiles import CnvFile

from processing.module import MissingParameterError, Module


# TODO testin:
# TODO ftir filter
# TODO Some kind of Correlation
# TODO bandstop filter 10 seconds to about 0.5 seconds?
# TODO zeit in datenpunkte umrechnen? bandpass = 240, 12?
class align_oxygen(Module):
    def __call__(
        self,
        input: Path | str | CnvFile | pd.DataFrame,
        parameters: dict = {"type": "ocean"},  # ???
        name: str = "test",
        output: str = "cnvobject",
        output_name: str | None = None,
    ) -> None | CnvFile | pd.DataFrame:
        return Module.__call__(
            self, input, parameters, name, output, output_name
        )

    def transformation(self) -> pd.DataFrame:
        rv = ["Temp", "Pressure", "Oxygen"]
        self.get_relevant_values(rv)
        # temp = self.detect_temp_spikes(relevant_values["Temp"])
        # ox = self.detect_ox_spikes(relevant_values["Oxygen"])

        # plt.plot(signal.correlate(temp, ox))

        plt.show()

        return self.df

    def butter_bandpass(self, lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = signal.butter(order, [low, high], btype="band")
        return b, a

    def butter_bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        y = signal.filtfilt(b, a, data)
        return y

    def detect_temp_spikes(self, temp: list):
        filtered = self.butter_bandpass_filter(temp, 12, 240, len(temp))

        # plt.plot(filtered, label="Filtered Temp")
        plt.plot(temp, label="temp")
        plt.legend(loc="upper right")

        return filtered

    def detect_ox_spikes(self, ox: list):
        b, a = signal.butter(3, 0.003, btype="high")
        filtered = signal.filtfilt(b, a, ox)

        # plt.plot(ox, label="ox")
        # plt.plot(filtered, label="filtered ox")
        # plt.plot(diff_arr, label="ox_diff")
        return filtered

    def get_relevant_values(
        self, values: list
    ) -> dict:  # in need of better name prolly
        rel_dict = {}

        for i in range(len(values)):
            rel_dict[values[i]] = (
                self.df[self.get_identifier(values[i])]
                .to_numpy()
                .astype(float)
            )

        return rel_dict

    def get_identifier(self, unit_name: str) -> str:
        list = []
        for i in range(len(self.cnv.data_table_names_and_spans)):
            name = self.cnv.data_table_names_and_spans[i][0]
            if unit_name in name:
                list.append(name)
        if not list:
            raise MissingParameterError("get_identifier()", unit_name)
        return list[0].split(":")[0]


instance = align_oxygen()(
    input="E:\Arbeit\Processing\processing\seabird_example_data\cnv\multiple_soaking.cnv"
)


# # sampling frequency
# f_sample = 48

# # pass band frequency
# f_pass = 1050

# # stop band frequency
# f_stop = 600

# # pass band ripple
# fs = 0.5

# # pass band freq in radian
# wp = f_pass/(f_sample/2)

# # stop band freq in radian
# ws = f_stop/(f_sample/2)

# # Sampling Time
# Td = 1

# # pass band ripple
# g_pass = 1

# # stop band attenuation
# g_stop = 50


# x = np.linspace(0.0, N*T, N)
#         y = np.sin(50.0 * 2.0*np.pi*x) + 0.5*np.sin(80.0 * 2.0*np.pi*x)
#         xf = np.linspace(0.0, 1.0/(2.0*T), N//2)
#         yf = fft(filtered)
#         fig, ax = plt.subplots()
#         ax.plot(xf, 2.0/N * np.abs(yf[:N//2]))
