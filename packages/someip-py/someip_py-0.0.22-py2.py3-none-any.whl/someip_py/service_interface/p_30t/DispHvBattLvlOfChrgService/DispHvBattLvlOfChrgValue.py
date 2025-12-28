from someip_py.codec import *


class IdtDispHvBattLvlOfChrgKls(SomeIpPayload):

    _include_struct_len = True

    DispHvBattLvlOfChrgValue: Float32

    HvBattSOCVld: Uint8

    def __init__(self):

        self.DispHvBattLvlOfChrgValue = Float32()

        self.HvBattSOCVld = Uint8()


class IdtDispHvBattLvlOfChrg(SomeIpPayload):

    IdtDispHvBattLvlOfChrg: IdtDispHvBattLvlOfChrgKls

    def __init__(self):

        self.IdtDispHvBattLvlOfChrg = IdtDispHvBattLvlOfChrgKls()
