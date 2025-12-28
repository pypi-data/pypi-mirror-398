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


class IdtAssignmentStatus(SomeIpPayload):

    _include_struct_len = True

    InstallationOrderID: SomeIpDynamicSizeString

    FotaState: Uint8

    ReasonCode: Uint8

    SumSize: Uint64

    InstallProgress: Uint8

    DetailReason: SomeIpDynamicSizeString

    def __init__(self):

        self.InstallationOrderID = SomeIpDynamicSizeString()

        self.FotaState = Uint8()

        self.ReasonCode = Uint8()

        self.SumSize = Uint64()

        self.InstallProgress = Uint8()

        self.DetailReason = SomeIpDynamicSizeString()


class IdtAssignmentStatusReplyKls(SomeIpPayload):

    _include_struct_len = True

    ResultCode: Uint8

    AssignmentStatus: IdtAssignmentStatus

    def __init__(self):

        self.ResultCode = Uint8()

        self.AssignmentStatus = IdtAssignmentStatus()


class IdtAssignmentStatusReply(SomeIpPayload):

    IdtAssignmentStatusReply: IdtAssignmentStatusReplyKls

    def __init__(self):

        self.IdtAssignmentStatusReply = IdtAssignmentStatusReplyKls()
