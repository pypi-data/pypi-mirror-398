from someip_py.codec import *


class IdtSteplsLvlgGroupKls(SomeIpPayload):

    _include_struct_len = True

    SteplsLvlgFL: Uint8

    SteplsLvlgFR: Uint8

    SteplsLvlgRL: Uint8

    SteplsLvlRR: Uint8

    def __init__(self):

        self.SteplsLvlgFL = Uint8()

        self.SteplsLvlgFR = Uint8()

        self.SteplsLvlgRL = Uint8()

        self.SteplsLvlRR = Uint8()


class IdtSteplsLvlgGroup(SomeIpPayload):

    IdtSteplsLvlgGroup: IdtSteplsLvlgGroupKls

    def __init__(self):

        self.IdtSteplsLvlgGroup = IdtSteplsLvlgGroupKls()
