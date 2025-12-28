from someip_py.codec import *


class SensorConfigInfoKls(SomeIpPayload):

    AdpuConfigInfSeN: Uint32

    ArchConfigInfSeN: Uint32

    def __init__(self):

        self.AdpuConfigInfSeN = Uint32()

        self.ArchConfigInfSeN = Uint32()


class SensorConfigInfo(SomeIpPayload):

    SensorConfigInfo: SensorConfigInfoKls

    def __init__(self):

        self.SensorConfigInfo = SensorConfigInfoKls()
