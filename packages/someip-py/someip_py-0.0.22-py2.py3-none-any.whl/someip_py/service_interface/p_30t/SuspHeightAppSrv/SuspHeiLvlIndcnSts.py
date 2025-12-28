from someip_py.codec import *


class IdtSuspHeiLvlIndcnVal(SomeIpPayload):

    IdtSuspHeiLvlIndcnVal: Uint8

    def __init__(self):

        self.IdtSuspHeiLvlIndcnVal = Uint8()
