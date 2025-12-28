from someip_py.codec import *


class IdtDoorStsWithFacQlyKls(SomeIpPayload):

    _include_struct_len = True

    DoorSts: Uint8

    FacQly: Uint8

    def __init__(self):

        self.DoorSts = Uint8()

        self.FacQly = Uint8()


class IdtDoorStsWithFacQly(SomeIpPayload):

    IdtDoorStsWithFacQly: IdtDoorStsWithFacQlyKls

    def __init__(self):

        self.IdtDoorStsWithFacQly = IdtDoorStsWithFacQlyKls()
