from someip_py.codec import *


class IdtMaxWaterWadingDeepLine(SomeIpPayload):

    IdtMaxWaterWadingDeepLine: Uint8

    def __init__(self):

        self.IdtMaxWaterWadingDeepLine = Uint8()
