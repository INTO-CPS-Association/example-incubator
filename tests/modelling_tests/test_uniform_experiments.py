import math
import unittest

import numpy

import matplotlib.pyplot as plt

from scipy import integrate

from data_processing.data_processing import load_data, derive_data
from tests.cli_mode_test import CLIModeTest


class UniformExperimentTests(CLIModeTest):

    def test_plot_data_uniform_experiment(self):
        # CWD: Example_Digital-Twin_Incubator\software\
        data, _ = load_data("./datasets/uniform_temperature/unitform_temperature.csv", desired_timeframe=(-math.inf, math.inf))

        data["power_in"] = data.apply(lambda row: 11.8 * 10.45 if row.heater_on else 0.0, axis=1)

        data["energy_in"] = data.apply(
            lambda row: integrate.trapz(data[0:row.name + 1]["power_in"], x=data[0:row.name + 1]["time"]), axis=1)
        data["average_temperature"] = data.apply(lambda row: numpy.mean([row.t1, row.t2, row.t3]), axis=1)
        data["std_dev_temperature"] = data.apply(lambda row: numpy.std([row.t1, row.t2, row.t3]), axis=1)
        data["max_dev_temperature"] = data.apply(
            lambda row: max([row.t1, row.t2, row.t3]) - min([row.t1, row.t2, row.t3]), axis=1)
        zero_kelvin = 273.15
        data["avg_temp_kelvin"] = data["average_temperature"] + zero_kelvin
        air_mass = 0.04  # Kg
        air_heat_capacity = 700  # (j kg^-1 °K^-1)

        data["potential_energy"] = data["avg_temp_kelvin"] * air_mass * air_heat_capacity
        data["potential_energy"] = data["potential_energy"] - data.iloc[0]["potential_energy"]

        fig, (ax1, ax2, ax3, ax5) = plt.subplots(4, 1)

        ax1.plot(data["time"], data["t1"], label="t1")
        ax1.plot(data["time"], data["t2"], label="t2")
        ax1.plot(data["time"], data["t3"], label="t3")
        ax1.plot(data["time"], data["average_temperature"], label="average_temperature")
        ax1.legend()

        ax2.plot(data["time"], data["heater_on"], label="heater_on")
        ax2.plot(data["time"], data["fan_on"], label="fan_on")
        ax2.legend()

        ax3.plot(data["time"], data["execution_interval"], label="execution_interval")
        ax3.plot(data["time"], data["elapsed"], label="elapsed")
        ax3.legend()

        ax5.plot(data["time"], data["std_dev_temperature"], label="std_dev_temperature")
        ax5.plot(data["time"], data["max_dev_temperature"], label="max_dev_temperature")
        ax5.legend()

        if self.ide_mode():
            plt.show()

    def test_show_temperature_sensor_redundant(self):
        # CWD: Example_Digital-Twin_Incubator\software\
        data, _ = load_data("./datasets/uniform_temperature/unitform_temperature_better_fan.csv", desired_timeframe=(-math.inf, math.inf))

        data["power_in"] = data.apply(lambda row: 11.8 * 10.45 if row.heater_on else 0.0, axis=1)

        data["energy_in"] = data.apply(
            lambda row: integrate.trapz(data[0:row.name + 1]["power_in"], x=data[0:row.name + 1]["time"]), axis=1)
        data["average_temperature"] = data.apply(lambda row: numpy.mean([row.t2, row.t3]), axis=1)
        data["std_dev_temperature"] = data.apply(lambda row: numpy.std([row.t2, row.t3]), axis=1)
        data["max_dev_temperature"] = data.apply(lambda row: max([row.t2, row.t3]) - min([row.t1, row.t2, row.t3]),
                                                 axis=1)
        zero_kelvin = 273.15
        data["avg_temp_kelvin"] = data["average_temperature"] + zero_kelvin
        air_mass = 0.04  # Kg
        air_heat_capacity = 700  # (j kg^-1 °K^-1)

        data["potential_energy"] = data["avg_temp_kelvin"] * air_mass * air_heat_capacity
        data["potential_energy"] = data["potential_energy"] - data.iloc[0]["potential_energy"]

        fig, (ax1, ax2, ax3, ax5) = plt.subplots(4, 1, sharex=True)

        ax1.plot(data["time"], data["t1"], label="t1")
        ax1.plot(data["time"], data["t2"], label="t2")
        ax1.plot(data["time"], data["t3"], label="t3")
        ax1.plot(data["time"], data["average_temperature"], label="average_temperature")
        ax1.label_outer()
        ax1.legend()

        ax2.plot(data["time"], data["heater_on"], label="heater_on")
        ax2.plot(data["time"], data["fan_on"], label="fan_on")

        ax2.label_outer()
        ax2.legend()

        ax3.plot(data["time"], data["execution_interval"], label="execution_interval")
        ax3.plot(data["time"], data["elapsed"], label="elapsed")
        ax3.label_outer()
        ax3.legend()

        ax5.plot(data["time"], data["std_dev_temperature"], label="std_dev_temperature")
        ax5.plot(data["time"], data["max_dev_temperature"], label="max_dev_temperature")
        ax5.set(xlabel='time (s)')
        ax5.label_outer()

        ax5.legend()

        if self.ide_mode():
            # plt.savefig("uniform_experiments.svg")
            plt.show()


if __name__ == '__main__':
    unittest.main()
