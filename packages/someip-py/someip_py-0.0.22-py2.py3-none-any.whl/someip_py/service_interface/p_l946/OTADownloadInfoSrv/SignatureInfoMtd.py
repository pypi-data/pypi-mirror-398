from someip_py.codec import *


class AssignmentFileInfoStruct(SomeIpPayload):

    _include_struct_len = True

    FileName: SomeIpDynamicSizeString

    Flashgroupid: Uint32

    Downloadtype: SomeIpDynamicSizeString

    Installationtype: SomeIpDynamicSizeString

    Fileencryptiontype: SomeIpDynamicSizeString

    Validtime: SomeIpDynamicSizeString

    Validdate: SomeIpDynamicSizeString

    Softwarepartsignaturedata: SomeIpDynamicSizeString

    Filechecksum: SomeIpDynamicSizeString

    def __init__(self):

        self.FileName = SomeIpDynamicSizeString()

        self.Flashgroupid = Uint32()

        self.Downloadtype = SomeIpDynamicSizeString()

        self.Installationtype = SomeIpDynamicSizeString()

        self.Fileencryptiontype = SomeIpDynamicSizeString()

        self.Validtime = SomeIpDynamicSizeString()

        self.Validdate = SomeIpDynamicSizeString()

        self.Softwarepartsignaturedata = SomeIpDynamicSizeString()

        self.Filechecksum = SomeIpDynamicSizeString()


class OTASetAssignmentFileInfoStructKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    InstallationorderUUID: SomeIpDynamicSizeString

    Ecuremaining: Uint8

    Iastsegment: Uint8

    EcuAddress: SomeIpDynamicSizeString

    AssignfileinfoArray: SomeIpDynamicSizeArray[AssignmentFileInfoStruct]

    def __init__(self):

        self.InstallationorderUUID = SomeIpDynamicSizeString()

        self.Ecuremaining = Uint8()

        self.Iastsegment = Uint8()

        self.EcuAddress = SomeIpDynamicSizeString()

        self.AssignfileinfoArray = SomeIpDynamicSizeArray(AssignmentFileInfoStruct)


class OTASetAssignmentFileInfoStruct(SomeIpPayload):

    OTASetAssignmentFileInfoStruct: OTASetAssignmentFileInfoStructKls

    def __init__(self):

        self.OTASetAssignmentFileInfoStruct = OTASetAssignmentFileInfoStructKls()


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
