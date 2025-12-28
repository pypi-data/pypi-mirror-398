from someip_py.codec import *


class IdtAssignmentID(SomeIpPayload):

    _include_struct_len = True

    InstallationOrderID: SomeIpDynamicSizeString

    EcuAddr: SomeIpDynamicSizeString

    def __init__(self):

        self.InstallationOrderID = SomeIpDynamicSizeString()

        self.EcuAddr = SomeIpDynamicSizeString()


class IdtFotaFileInfo(SomeIpPayload):

    _include_struct_len = True

    VBFName: SomeIpDynamicSizeString

    FileSize: Uint64

    URL: SomeIpDynamicSizeString

    Signature: SomeIpDynamicSizeString

    def __init__(self):

        self.VBFName = SomeIpDynamicSizeString()

        self.FileSize = Uint64()

        self.URL = SomeIpDynamicSizeString()

        self.Signature = SomeIpDynamicSizeString()


class IdtTransferQoS(SomeIpPayload):

    _include_struct_len = True

    LimitSpeed: Uint32

    def __init__(self):

        self.LimitSpeed = Uint32()


class IdtAssignmentInfoKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    AssignmentID: IdtAssignmentID

    FileInfoList: SomeIpDynamicSizeArray[IdtFotaFileInfo]

    TransferQoS: IdtTransferQoS

    FileEncryptionType: Uint8

    DigitalEnvelope: SomeIpDynamicSizeString

    SignatureCertificate: SomeIpDynamicSizeString

    VBFDuplicateCheck: Bool

    def __init__(self):

        self.AssignmentID = IdtAssignmentID()

        self.FileInfoList = SomeIpDynamicSizeArray(IdtFotaFileInfo)

        self.TransferQoS = IdtTransferQoS()

        self.FileEncryptionType = Uint8()

        self.DigitalEnvelope = SomeIpDynamicSizeString()

        self.SignatureCertificate = SomeIpDynamicSizeString()

        self.VBFDuplicateCheck = Bool()


class IdtAssignmentInfo(SomeIpPayload):

    IdtAssignmentInfo: IdtAssignmentInfoKls

    def __init__(self):

        self.IdtAssignmentInfo = IdtAssignmentInfoKls()


class IdtForceClearAssignment(SomeIpPayload):

    IdtForceClearAssignment: Bool

    def __init__(self):

        self.IdtForceClearAssignment = Bool()


class IdtResultCode(SomeIpPayload):

    IdtResultCode: Uint8

    def __init__(self):

        self.IdtResultCode = Uint8()
