from someip_py.codec import *


class IdtNtrlIlluminanceValKls(SomeIpPayload):

    _include_struct_len = True

    IlluminanceValue: Uint16

    IlluminanceReliability: Uint8

    def __init__(self):

        self.IlluminanceValue = Uint16()

        self.IlluminanceReliability = Uint8()


class IdtNtrlIlluminanceVal(SomeIpPayload):

    IdtNtrlIlluminanceVal: IdtNtrlIlluminanceValKls

    def __init__(self):

        self.IdtNtrlIlluminanceVal = IdtNtrlIlluminanceValKls()
