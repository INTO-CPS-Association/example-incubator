import numpy as np
from oomodelling import ModelSolver
import matplotlib.pyplot as plt

from calibration.calibrator import Calibrator
from interfaces.parametric_controller import IParametricController
from interfaces.database import IDatabase
from config.config import load_config
from digital_twin.simulator.plant_simulator import PlantSimulator4Params
from models.controller_models.controller_open_loop import ControllerOpenLoop
from models.physical_twin_models.system_model4_open_loop import SystemModel4ParametersOpenLoopSimulator
from models.plant_models.four_parameters_model.four_parameter_model import FourParameterIncubatorPlant
from models.self_adaptation.self_adaptation_scenario import SelfAdaptationScenario
from self_adaptation.self_adaptation_manager import SelfAdaptationManager
from monitoring.kalman_filter_4p import KalmanFilter4P
from self_adaptation.controller_optimizer import ControllerOptimizer
from self_adaptation.supervisor import SupervisorSM
from tests.cli_mode_test import CLIModeTest


class SelfAdaptationTests(CLIModeTest):

    def test_run_self_adaptation(self):
        config = load_config("startup.conf")

        n_samples_period = config["physical_twin"]["controller_open_loop"]["n_samples_period"]
        n_samples_heating = 5
        C_air = config["digital_twin"]["models"]["plant"]["param4"]["C_air"]
        G_box = config["digital_twin"]["models"]["plant"]["param4"]["G_box"]
        G_box_kf = G_box
        C_heater = config["digital_twin"]["models"]["plant"]["param4"]["C_heater"]
        G_heater = config["digital_twin"]["models"]["plant"]["param4"]["G_heater"]
        initial_box_temperature = 41
        initial_heat_temperature = 47
        initial_room_temperature = 21
        std_dev = 0.001
        step_size = 3.0
        anomaly_threshold = 2.0
        # Time spent before declaring that there is an self_adaptation_manager, after the first time the self_adaptation_manager occurred.
        ensure_anomaly_timer = 1
        # Time spent, after the self_adaptation_manager was declared as detected, just so enough data about the system is gathered.
        # The data used for recalibration will be in interval [time_first_occurrence, time_data_gathered]
        gather_data_timer = 10
        conv_xatol = 0.1
        conv_fatol = 0.1
        max_iterations = 200
        desired_temperature = 41
        max_t_heater = 60
        restrict_T_heater = True
        trigger_optimization_threshold = 1000.0
        wait_til_supervising_timer = 1000  # N steps supervisor should wait before kicking in.
        optimize_controller = False

        tf = 6000 if self.ide_mode() else 3000

        kalman = KalmanFilter4P(step_size, std_dev,
                                C_air, G_box_kf, C_heater, G_heater,
                                initial_room_temperature, initial_heat_temperature, initial_box_temperature)

        database = MockDatabase(step_size)
        plant_simulator = PlantSimulator4Params()
        calibrator = Calibrator(database, plant_simulator, conv_xatol, conv_fatol, max_iterations)
        pt_simulator = SystemModel4ParametersOpenLoopSimulator()
        ctrl = MockController()

        if optimize_controller:
            ctrl_optimizer = ControllerOptimizer(database, pt_simulator, ctrl, conv_xatol, conv_fatol, max_iterations, restrict_T_heater, desired_temperature, max_t_heater)
        else:
            ctrl_optimizer = NoOPControllerOptimizer()

        anomaly_detector = SelfAdaptationManager(anomaly_threshold, ensure_anomaly_timer, gather_data_timer, calibrator, kalman, ctrl_optimizer)
        supervisor = SupervisorSM(ctrl_optimizer, desired_temperature, max_t_heater, trigger_optimization_threshold, wait_til_supervising_timer)

        m = SelfAdaptationScenario(n_samples_period, n_samples_heating,
                                   C_air, G_box, C_heater, G_heater,
                                   initial_box_temperature,
                                   initial_heat_temperature,
                                   initial_room_temperature,
                                   kalman, anomaly_detector, supervisor,
                                   std_dev)

        # Inform mock db of plant _plant.
        database.set_models(m.physical_twin.plant, m.physical_twin.ctrl)
        # Inform mock of controller
        ctrl.set_model(m.physical_twin.ctrl)

        # Wire in a custom function for the G_box input, so we can change it.
        m.physical_twin.plant.G_box = lambda: G_box if m.time() < 1000 else (G_box * 10 if m.time() < 2000 else G_box)

        # Wire in a custom function for the C_air parameter,
        # so we mimick a different object being placed in the incubator.
        # Commented out because it does not seem to work very well.
        # m.physical_twin.plant.C_air = lambda: C_air if m.time() < 1000 else (C_air * 7 if m.time() < 2000 else C_air)

        ModelSolver().simulate(m, 0.0, tf, 3.0)

        fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, sharex='all')

        ax1.plot(m.signals['time'], m.physical_twin.plant.signals['T'], label=f"- T")
        ax1.plot(m.signals['time'], m.kalman.signals['out_T'], linestyle="dashed", label=f"~ T")
        ax1.plot(m.signals['time'], m.kalman.signals['out_T_prior'], linestyle="dashed", label=f"~ T_prior")

        for (times, trajectory) in database.plant_calibration_trajectory_history:
            ax1.plot(times, trajectory[0, :], label=f"cal T", linestyle='dotted')

        for (times, T, T_heater, heater_on) in database.ctrl_optimal_policy_history:
            ax1.plot(times, T, label=f"opt T", linestyle='dotted')

        ax1.legend()

        ax2.plot(m.signals['time'], [(1 if b else 0) for b in m.physical_twin.ctrl.signals['heater_on']], label=f"heater_on")
        ax2.plot(m.signals['time'], [(1 if b else 0) for b in m.kalman.signals['in_heater_on']], linestyle="dashed", label=f"~ heater_on")

        ax2.legend()

        ax3.plot(m.signals['time'], m.physical_twin.plant.signals['T_heater'], label=f"T_heater")
        ax3.plot(m.signals['time'], m.kalman.signals['out_T_heater'], linestyle="dashed", label=f"~ T")

        ax3.legend()

        # The following plot is incorrect, since it does not match with the actual residual computed by the self_adaptation_manager
        # ax4.scatter(m.signals['time'],
        #             np.absolute(np.array(m.physical_twin.plant.signals['T']) - np.array(m.kalman.signals['out_T'])),
        #             label=f"Error")

        ax4.scatter(m.signals['time'],
                    m.self_adaptation_manager.signals["temperature_residual_abs"],
                    label=f"Error")
        ax4.legend()

        ax5.plot(m.signals['time'], m.kalman.signals['out_P_00'], linestyle="dashed", label=f"P_00")
        ax5.plot(m.signals['time'], m.kalman.signals['out_P_11'], linestyle="dashed", label=f"P_11")

        ax5.legend()

        if self.ide_mode():
            print("Parameters:")
            print("C_air: ", database.C_air)
            print("G_box: ", database.G_box)
            print("C_heater: ", database.C_heater)
            print("G_heater: ", database.G_heater)
            plt.show()


class NoOPControllerOptimizer:
    def optimize_controller(self):
        pass


class MockController(IParametricController):

    controller: ControllerOpenLoop = None

    def set_new_parameters(self, n_samples_heating_new, n_samples_period_new):
        assert self.controller is not None
        assert isinstance(n_samples_heating_new, int)
        assert isinstance(n_samples_period_new, int)
        self.controller.reset_params(n_samples_heating_new, n_samples_period_new)

    def set_model(self, ctrl):
        assert self.controller is None
        self.controller = ctrl


class MockDatabase(IDatabase):

    _plant: FourParameterIncubatorPlant = None
    _ctrl: ControllerOpenLoop = None

    C_air: list[float] = []
    G_box: list[float] = []
    C_heater: list[float] = []
    G_heater: list[float] = []
    plant_calibration_trajectory_history: list = []
    ctrl_optimal_policy_history: list = []

    n_samples_heating: list[float] = []
    n_samples_period: list[float] = []

    def __init__(self, ctrl_step_size):
        self.ctrl_step_size = ctrl_step_size

    def set_models(self, plant: FourParameterIncubatorPlant, ctrl: ControllerOpenLoop):
        assert len(self.C_air) == len(self.G_box) == len(self.C_heater) == len(self.G_heater) == \
               len(self.plant_calibration_trajectory_history) == len(self.n_samples_heating) == \
               len(self.n_samples_period) == 0
        self._plant = plant
        self._ctrl = ctrl
        self.C_air.append(plant.C_air())
        self.G_box.append(plant.G_box())
        self.C_heater.append(plant.C_heater)
        self.G_heater.append(plant.G_heater)
        self.n_samples_heating.append(ctrl.param_n_samples_heating)
        self.n_samples_period.append(ctrl.param_n_samples_period)

    def get_plant_signals_between(self, t_start_s, t_end_s):
        signals = self._plant.signals
        # Find indexes for t_start_s and t_end_s
        t_start_idx = next(i for i, t in enumerate(signals["time"]) if t >= t_start_s)
        t_end_idx = next(i for i, t in enumerate(signals["time"]) if t >= t_end_s)
        return signals, t_start_idx, t_end_idx

    def store_calibrated_trajectory(self, times, calibrated_sol):
        self.plant_calibration_trajectory_history.append((times, calibrated_sol))

    def store_new_plant_parameters(self, start_time_s, C_air_new, G_box_new, C_heater, G_heater):
        self.C_air.append(C_air_new)
        self.G_box.append(G_box_new)
        self.C_heater.append(C_heater)
        self.G_heater.append(G_heater)

    def get_plant4_parameters(self):
        return self.C_air[-1], self.G_box[-1], self.C_heater[-1], self.G_heater[-1]

    def get_plant_snapshot(self):
        return self._plant.time(), self._plant.T(), self._plant.T_heater(), self._plant.in_room_temperature()

    def get_ctrl_parameters(self):
        return self.n_samples_heating[-1], self.n_samples_period[-1], self.ctrl_step_size

    def store_new_ctrl_parameters(self, start_time_s, n_samples_heating_new, n_samples_period_new, controller_step_size):
        self.n_samples_heating.append(n_samples_heating_new)
        self.n_samples_period.append(n_samples_period_new)

    def store_controller_optimal_policy(self, time, T, T_heater, heater_on):
        self.ctrl_optimal_policy_history.append((time, T, T_heater, heater_on))