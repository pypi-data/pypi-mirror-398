from someip_py.codec import *


class SensorFeatureSts(SomeIpPayload):

    SensorFeatureSts: Uint32

    def __init__(self):

        self.SensorFeatureSts = Uint32()
