from control import ss
from filterpy.common import Q_discrete_white_noise
from filterpy.kalman import KalmanFilter
from oomodelling import Model
import sympy as sp
import numpy as np

from models.plant_models.globals import HEATER_VOLTAGE, HEATER_CURRENT
from monitoring.updateable_kalman_filter import UpdateableKalmanFilter


def construct_filter(step_size, std_dev,
                     C_air_num,
                     G_box_num,
                     C_heater_num,
                     G_heater_num,
                     initial_heat_temperature,
                     initial_box_temperature):
    # Parameters
    C_air = sp.symbols("C_air")  # Specific heat capacity
    G_box = sp.symbols("G_box")  # Specific heat capacity
    C_heater = sp.symbols("C_heater")  # Specific heat capacity
    G_heater = sp.symbols("G_heater")  # Specific heat capacity

    # Constants
    V_heater = sp.symbols("V_heater")
    i_heater = sp.symbols("i_heater")

    # Inputs
    in_room_temperature = sp.symbols("T_room")
    on_heater = sp.symbols("on_heater")

    # States
    T = sp.symbols("T")
    T_heater = sp.symbols("T_h")

    power_in = on_heater * V_heater * i_heater

    power_transfer_heat = G_heater * (T_heater - T)

    total_power_heater = power_in - power_transfer_heat

    power_out_box = G_box * (T - in_room_temperature)

    total_power_box = power_transfer_heat - power_out_box

    der_T = (1.0 / C_air) * (total_power_box)
    der_T_heater = (1.0 / C_heater) * (total_power_heater)

    # Turn above into a CT linear system
    """
    States are:
    [[ T_heater ]
     [ T        ]]

    Inputs are: 
    [ [ on_heater ], 
      [ in_room_ptemperature ]]
    """
    A = sp.Matrix([
        [der_T_heater.diff(T_heater), der_T_heater.diff(T)],
        [der_T.diff(T_heater), der_T.diff(T)]
    ])

    B = sp.Matrix([
        [der_T_heater.diff(on_heater), der_T_heater.diff(in_room_temperature)],
        [der_T.diff(on_heater), der_T.diff(in_room_temperature)]
    ])

    # Observation matrix: only T can be measured
    C = sp.Matrix([[0.0, 1.0]])

    # Replace constants and get numerical matrices
    def replace_constants(m):
        return np.array(m.subs({
            V_heater: HEATER_VOLTAGE,
            i_heater: HEATER_CURRENT,
            C_air: C_air_num,
            G_box: G_box_num,
            C_heater: C_heater_num,
            G_heater: G_heater_num
        })).astype(np.float64)

    A_num, B_num, C_num = map(replace_constants, [A, B, C])

    ct_system = ss(A_num, B_num, C_num, np.array([[0.0, 0.0]]))
    dt_system = ct_system.sample(step_size, method="backward_diff")

    f = KalmanFilter(dim_x=2, dim_z=1, dim_u=2)
    f.x = np.array([[initial_heat_temperature],  # T_heater at t=0
                    [initial_box_temperature]])  # T at t=0
    f.F = dt_system.A
    f.B = dt_system.B
    f.H = dt_system.C
    f.P = np.array([[100., 0.],
                    [0., 100.]])
    f.R = np.array([[std_dev]])
    f.Q = Q_discrete_white_noise(dim=2, dt=step_size, var=std_dev ** 2)

    return f


class KalmanFilter4P(Model, UpdateableKalmanFilter):
    def __init__(self, step_size, std_dev,
                 C_air,
                 G_box,
                 C_heater,
                 G_heater,
                 initial_room_temperature=25.0, initial_heat_temperature=25.0, initial_box_temperature=25.0):
        super().__init__()

        self.in_heater_on = self.input(lambda: False)
        self.in_room_T = self.input(lambda: initial_room_temperature)
        self.in_T = self.input(lambda: initial_box_temperature)

        self.cached_T = initial_box_temperature
        self.cached_T_heater = initial_box_temperature
        self.filter = construct_filter(step_size, std_dev,
                                       C_air, G_box, C_heater, G_heater,
                                       initial_heat_temperature, initial_box_temperature)

        self.out_T = self.var(lambda: self.cached_T)
        self.out_T_heater = self.var(lambda: self.cached_T_heater)

        self.save()

    def kalman_step(self, in_heater, in_room_T, in_T):
        self.filter.predict(u=np.array([
            [in_heater],
            [in_room_T]
        ]))
        self.filter.update(np.array([[in_T]]))
        return self.filter.x

    def discrete_step(self):
        next_x = self.kalman_step(1.0 if self.in_heater_on() else 0.0, self.in_room_T(), self.in_T())
        self.cached_T_heater = next_x[0, 0]
        self.cached_T = next_x[1, 0]
        return super().discrete_step()

    # Overrides
    def update_parameters(self, C_air, G_box, C_heater, G_heater):
        print("Updating parameters of Kalman filter...")
        pass
