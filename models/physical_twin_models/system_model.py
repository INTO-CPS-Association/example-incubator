from oomodelling import Model

from models.controller_models.controller_model4 import ControllerModel4
from models.plant_models.two_parameters_model.two_parameter_model import TwoParameterIncubatorPlant


class SystemModel(Model):
    def __init__(self):
        super().__init__()

        self.ctrl = ControllerModel4()
        self.plant = TwoParameterIncubatorPlant()

        self.ctrl.in_temperature = self.plant.T
        self.plant.in_heater_on = self.ctrl.heater_on

        self.save()
