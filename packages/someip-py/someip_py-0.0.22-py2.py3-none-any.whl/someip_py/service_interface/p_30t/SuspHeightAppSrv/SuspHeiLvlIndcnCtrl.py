from someip_py.codec import *


class IdtSuspHeiLvlIndcnKls(SomeIpPayload):

    _include_struct_len = True

    SuspHeiLvlIndcnVal: Uint8

    HeiCtrlTriSource: Uint8

    def __init__(self):

        self.SuspHeiLvlIndcnVal = Uint8()

        self.HeiCtrlTriSource = Uint8()


class IdtSuspHeiLvlIndcn(SomeIpPayload):

    IdtSuspHeiLvlIndcn: IdtSuspHeiLvlIndcnKls

    def __init__(self):

        self.IdtSuspHeiLvlIndcn = IdtSuspHeiLvlIndcnKls()
