from someip_py.codec import *


class FIVEGModeStructKls(SomeIpPayload):

    _include_struct_len = True

    FIVEGMode: Uint8

    RetVal: Uint8

    def __init__(self):

        self.FIVEGMode = Uint8()

        self.RetVal = Uint8()


class FIVEGModeStruct(SomeIpPayload):

    FIVEGModeStruct: FIVEGModeStructKls

    def __init__(self):

        self.FIVEGModeStruct = FIVEGModeStructKls()
