import unittest

from oomodelling import ModelSolver

import matplotlib.pyplot as plt

from virtual.models.physical_twin_models.system_model4 import SystemModel4Parameters
from virtual.models.plant_models.four_parameters_model import four_param_model_params
from software.src.visualization.data_plotting import plotly_incubator_data, show_plotly
from software.tests.cli_mode_test import CLIModeTest
import pandas as pd


class CosimulationTests(CLIModeTest):

    def test_run_cosim_4param_model(self):
        C_air_num = four_param_model_params[0]
        G_box_num = four_param_model_params[1]
        C_heater_num = four_param_model_params[2]
        G_heater_num = four_param_model_params[3]

        plt.figure()

        def show_trace(heating_time):
            m = SystemModel4Parameters(C_air=C_air_num,
                                       G_box=G_box_num,
                                       C_heater=C_heater_num,
                                       G_heater=G_heater_num, heating_time=heating_time, heating_gap=2.0,
                                       temperature_desired=35, initial_box_temperature=22)
            ModelSolver().simulate(m, 0.0, 3000, 3.0)

            plt.plot(m.signals['time'], m.plant.signals['T'], label=f"Trial_{heating_time}")

        # show_trace(0.1)
        # show_trace(1.0)
        show_trace(3.0)
        # show_trace(100.0)

        plt.legend()

        if self.ide_mode():
            plt.show()

    def test_fine_tune_controller(self):
        C_air_num = four_param_model_params[0]
        G_box_num = four_param_model_params[1]
        C_heater_num = four_param_model_params[2]
        G_heater_num = four_param_model_params[3]

        m = SystemModel4Parameters(C_air=C_air_num,
                                   G_box=G_box_num,
                                   C_heater=C_heater_num,
                                   G_heater=G_heater_num, heating_time=20.0, heating_gap=30.0,
                                   temperature_desired=35, initial_box_temperature=22)
        ModelSolver().simulate(m, 0.0, 3000, 3.0)

        # Convert cosim data into a dataframe
        data_cosim = pd.DataFrame()
        data_cosim["time"] = m.signals['time']
        data_cosim["average_temperature"] = m.plant.signals['T']
        data_cosim["t1"] = m.plant.signals['in_room_temperature']
        data_cosim["heater_on"] = m.plant.signals['in_heater_on']

        fig = plotly_incubator_data(data_cosim, overlay_heater=True)

        if self.ide_mode():
            show_plotly(fig)



if __name__ == '__main__':
    unittest.main()
