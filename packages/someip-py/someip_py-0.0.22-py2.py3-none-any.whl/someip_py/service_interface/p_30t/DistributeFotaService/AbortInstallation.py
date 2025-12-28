from someip_py.codec import *


class IdtAssignmentIDKls(SomeIpPayload):

    _include_struct_len = True

    InstallationOrderID: SomeIpDynamicSizeString

    EcuAddr: SomeIpDynamicSizeString

    def __init__(self):

        self.InstallationOrderID = SomeIpDynamicSizeString()

        self.EcuAddr = SomeIpDynamicSizeString()


class IdtAssignmentID(SomeIpPayload):

    IdtAssignmentID: IdtAssignmentIDKls

    def __init__(self):

        self.IdtAssignmentID = IdtAssignmentIDKls()


class IdtClearAllData(SomeIpPayload):

    IdtClearAllData: Bool

    def __init__(self):

        self.IdtClearAllData = Bool()


class IdtResultCode(SomeIpPayload):

    IdtResultCode: Uint8

    def __init__(self):

        self.IdtResultCode = Uint8()
