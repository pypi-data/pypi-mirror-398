from someip_py.codec import *


class IdtWarningWaterWadingDeepLine(SomeIpPayload):

    IdtWarningWaterWadingDeepLine: Uint8

    def __init__(self):

        self.IdtWarningWaterWadingDeepLine = Uint8()
