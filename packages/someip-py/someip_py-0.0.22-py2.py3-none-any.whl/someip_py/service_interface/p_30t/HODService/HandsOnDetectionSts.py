from someip_py.codec import *


class IdtHandsOnDetectionKls(SomeIpPayload):

    _include_struct_len = True

    HandsOnStatus: Uint8

    ErrorStatus: Uint8

    def __init__(self):

        self.HandsOnStatus = Uint8()

        self.ErrorStatus = Uint8()


class IdtHandsOnDetection(SomeIpPayload):

    IdtHandsOnDetection: IdtHandsOnDetectionKls

    def __init__(self):

        self.IdtHandsOnDetection = IdtHandsOnDetectionKls()
