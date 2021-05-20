import math
import unittest

import numpy as np
import pandas

from config.config import resource_file_path
from data_processing.data_processing import load_data, derive_data
from monitoring.kalman_filter_4p import KalmanFilter4P
from models.plant_models.model_functions import run_experiment_four_parameter_model
from visualization.data_plotting import plotly_incubator_data, show_plotly
from tests.cli_mode_test import CLIModeTest
from models.plant_models.four_parameters_model.best_parameters import four_param_model_params


class TestKalmanFilter(CLIModeTest):

    def test_kalman_4_param_model(self):
        data_sample_size = 3.0

        # Load the data
        time_unit = 'ns'
        data, _ = load_data("./datasets/lid_opening_experiment_jan_2021/lid_opening_experiment_jan_2021.csv",
                                     desired_timeframe=(- math.inf, math.inf),
                                     time_unit=time_unit,
                                     normalize_time=False,
                                     convert_to_seconds=True)
        events = pandas.read_csv(resource_file_path("./datasets/lid_opening_experiment_jan_2021/events.csv"))
        events["timestamp"] = pandas.to_datetime(events["time"], unit=time_unit)

        # Inputs to model
        measurements_heater = np.array([1.0 if b else 0.0 for b in data["heater_on"]])
        measurements_Troom = data["t1"].to_numpy()

        # System state
        measurements_T = data["average_temperature"].to_numpy()

        std_dev = 0.001

        params = four_param_model_params
        C_air_num = params[0]
        G_box_num = params[1]
        C_heater_num = params[2]
        G_heater_num = params[3]

        f = KalmanFilter4P(data_sample_size, std_dev,
                           C_air=C_air_num,
                           G_box=G_box_num,
                           C_heater=C_heater_num,
                           G_heater=G_heater_num,
                           initial_room_temperature=25.0,
                           initial_box_temperature=25.0)

        kalman_prediction = []
        for i in range(len(measurements_heater)):
            x = f.kalman_step(measurements_heater[i], measurements_Troom[i], measurements_T[i])
            kalman_prediction.append(x)

        kalman_prediction = np.array(kalman_prediction).squeeze(2)

        # Run experiment with model, without any filtering, just for comparison.
        results_4p, sol = run_experiment_four_parameter_model(data, params)

        fig = plotly_incubator_data(data,
                                    compare_to={
                                        "4pModel": {
                                            "timestamp": data["timestamp"],
                                            "T": results_4p.signals["T"],
                                        },
                                        "Kalman": {
                                            "timestamp": data["timestamp"],
                                            "T": kalman_prediction[:, 1]
                                        },
                                    },
                                    heater_T_data={
                                        "4pModel": {
                                            "timestamp": data["timestamp"],
                                            "T_heater": results_4p.signals["T_heater"],
                                        },
                                        "Kalman": {
                                            "timestamp": data["timestamp"],
                                            "T_heater": kalman_prediction[:, 0]
                                        },
                                    },
                                    events=events,
                                    overlay_heater=True,
                                    show_hr_time=True)

        if self.ide_mode():
            show_plotly(fig)


if __name__ == '__main__':
    unittest.main()
