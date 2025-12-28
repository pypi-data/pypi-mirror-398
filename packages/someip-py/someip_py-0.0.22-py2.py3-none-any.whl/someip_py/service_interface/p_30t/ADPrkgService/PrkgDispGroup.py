from someip_py.codec import *


class IdtPrkgDispGroupKls(SomeIpPayload):

    _include_struct_len = True

    PrkgDispGroupLeCornrCoornx: Int16

    PrkgDispGroupLeCornrCoorny: Int16

    PrkgDispGroupLeCornrLocn: Uint8

    PrkgDispGroupPrkgTyp: Uint8

    PrkgDispGroupRiCornrCoornx: Int16

    PrkgDispGroupRiCornrCoorny: Int16

    def __init__(self):

        self.PrkgDispGroupLeCornrCoornx = Int16()

        self.PrkgDispGroupLeCornrCoorny = Int16()

        self.PrkgDispGroupLeCornrLocn = Uint8()

        self.PrkgDispGroupPrkgTyp = Uint8()

        self.PrkgDispGroupRiCornrCoornx = Int16()

        self.PrkgDispGroupRiCornrCoorny = Int16()


class IdtPrkgDispGroup(SomeIpPayload):

    IdtPrkgDispGroup: IdtPrkgDispGroupKls

    def __init__(self):

        self.IdtPrkgDispGroup = IdtPrkgDispGroupKls()
