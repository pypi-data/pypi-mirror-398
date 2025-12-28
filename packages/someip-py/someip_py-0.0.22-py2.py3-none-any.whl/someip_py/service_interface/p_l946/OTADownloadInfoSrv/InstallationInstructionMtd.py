from someip_py.codec import *


class SoftwarepartinstallationinstructionStruct(SomeIpPayload):

    _include_struct_len = True

    FileName: SomeIpDynamicSizeString

    Downloadtype: SomeIpDynamicSizeString

    Installationtype: SomeIpDynamicSizeString

    Fileencryptiontype: SomeIpDynamicSizeString

    Validtime: SomeIpDynamicSizeString

    Estimatedinstallationtime: Uint32

    Validdate: SomeIpDynamicSizeString

    def __init__(self):

        self.FileName = SomeIpDynamicSizeString()

        self.Downloadtype = SomeIpDynamicSizeString()

        self.Installationtype = SomeIpDynamicSizeString()

        self.Fileencryptiontype = SomeIpDynamicSizeString()

        self.Validtime = SomeIpDynamicSizeString()

        self.Estimatedinstallationtime = Uint32()

        self.Validdate = SomeIpDynamicSizeString()


class EcuinstructionsdataStruct(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    Queuedrequest: Uint16

    SecurityCode: SomeIpDynamicSizeString

    Sblnotpresent: Uint8

    EcuAddress: SomeIpDynamicSizeString

    IsSilentInstall: Uint8

    Flashgroupid: Uint32

    SilentInstallTimeout: Uint32

    SoftwarePartInstallationinStructionArray: SomeIpDynamicSizeArray[
        SoftwarepartinstallationinstructionStruct
    ]

    def __init__(self):

        self.Queuedrequest = Uint16()

        self.SecurityCode = SomeIpDynamicSizeString()

        self.Sblnotpresent = Uint8()

        self.EcuAddress = SomeIpDynamicSizeString()

        self.IsSilentInstall = Uint8()

        self.Flashgroupid = Uint32()

        self.SilentInstallTimeout = Uint32()

        self.SoftwarePartInstallationinStructionArray = SomeIpDynamicSizeArray(
            SoftwarepartinstallationinstructionStruct
        )


class EcudataStruct(SomeIpPayload):

    _include_struct_len = True

    ValidationKey: SomeIpDynamicSizeString

    Keyvalue: SomeIpDynamicSizeString

    def __init__(self):

        self.ValidationKey = SomeIpDynamicSizeString()

        self.Keyvalue = SomeIpDynamicSizeString()


class POSTvalidationStruct(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    EcuAddress: SomeIpDynamicSizeString

    EcudataArray: SomeIpDynamicSizeArray[EcudataStruct]

    def __init__(self):

        self.EcuAddress = SomeIpDynamicSizeString()

        self.EcudataArray = SomeIpDynamicSizeArray(EcudataStruct)


class InstallationInstructionsStruct(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    Installationinstructionsversion: SomeIpDynamicSizeString

    Bssid: SomeIpDynamicSizeString

    Displayedversion: SomeIpDynamicSizeString

    TargetECUNum: Uint8

    MaximumParallelECUNum: Uint8

    Requiredpreparationtime: Uint32

    Area1112securitycode: SomeIpDynamicSizeString

    Operationsequence: Uint32

    EcuinstructionsdataStruct: EcuinstructionsdataStruct

    Assignmentvalidationpre: SomeIpDynamicSizeString

    Assignmentvalidationpost: POSTvalidationStruct

    Expectedinstallationtime: Uint32

    def __init__(self):

        self.Installationinstructionsversion = SomeIpDynamicSizeString()

        self.Bssid = SomeIpDynamicSizeString()

        self.Displayedversion = SomeIpDynamicSizeString()

        self.TargetECUNum = Uint8()

        self.MaximumParallelECUNum = Uint8()

        self.Requiredpreparationtime = Uint32()

        self.Area1112securitycode = SomeIpDynamicSizeString()

        self.Operationsequence = Uint32()

        self.EcuinstructionsdataStruct = EcuinstructionsdataStruct()

        self.Assignmentvalidationpre = SomeIpDynamicSizeString()

        self.Assignmentvalidationpost = POSTvalidationStruct()

        self.Expectedinstallationtime = Uint32()


class OTAWriteInstallationInstructionStructKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    InstallationorderUUID: SomeIpDynamicSizeString

    Ecuremaining: Uint8

    InstallationInstructionsStruct: InstallationInstructionsStruct

    def __init__(self):

        self.InstallationorderUUID = SomeIpDynamicSizeString()

        self.Ecuremaining = Uint8()

        self.InstallationInstructionsStruct = InstallationInstructionsStruct()


class OTAWriteInstallationInstructionStruct(SomeIpPayload):

    OTAWriteInstallationInstructionStruct: OTAWriteInstallationInstructionStructKls

    def __init__(self):

        self.OTAWriteInstallationInstructionStruct = (
            OTAWriteInstallationInstructionStructKls()
        )


class OTASignatureCertificateRespStructKls(SomeIpPayload):

    _include_struct_len = True

    Status: SomeIpDynamicSizeString

    RetVal: Uint8

    def __init__(self):

        self.Status = SomeIpDynamicSizeString()

        self.RetVal = Uint8()


class OTASignatureCertificateRespStruct(SomeIpPayload):

    OTASignatureCertificateRespStruct: OTASignatureCertificateRespStructKls

    def __init__(self):

        self.OTASignatureCertificateRespStruct = OTASignatureCertificateRespStructKls()
