from someip_py.codec import *


class DriverLearningState(SomeIpPayload):

    DriverLearningState: Uint8

    def __init__(self):

        self.DriverLearningState = Uint8()
