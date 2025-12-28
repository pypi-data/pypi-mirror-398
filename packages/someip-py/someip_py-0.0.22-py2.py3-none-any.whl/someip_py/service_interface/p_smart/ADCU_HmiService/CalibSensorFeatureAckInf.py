from someip_py.codec import *


class SensorFeatureStatusAck(SomeIpPayload):

    SensorFeatureStatusAck: Uint32

    def __init__(self):

        self.SensorFeatureStatusAck = Uint32()
