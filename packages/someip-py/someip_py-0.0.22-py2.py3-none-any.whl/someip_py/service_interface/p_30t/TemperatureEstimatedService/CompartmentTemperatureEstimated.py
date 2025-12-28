from someip_py.codec import *


class IdtCmptmtTEstimdKls(SomeIpPayload):

    _include_struct_len = True

    CmptmtFirstLeTEstimd: Float32

    CmptmtFirstRiTEstimd: Float32

    CmptmtSecLeTEstimd: Float32

    CmptmtSecRiTEstimd: Float32

    CmptmtThrdLeTEstimd: Float32

    CmptmtThrdRiTEstimd: Float32

    CmptmtExtrMtrlTEstimd: Float32

    CmptmtIntrMtrlTEstimd: Float32

    CmptmtSunMtrlTEstimd: Float32

    def __init__(self):

        self.CmptmtFirstLeTEstimd = Float32()

        self.CmptmtFirstRiTEstimd = Float32()

        self.CmptmtSecLeTEstimd = Float32()

        self.CmptmtSecRiTEstimd = Float32()

        self.CmptmtThrdLeTEstimd = Float32()

        self.CmptmtThrdRiTEstimd = Float32()

        self.CmptmtExtrMtrlTEstimd = Float32()

        self.CmptmtIntrMtrlTEstimd = Float32()

        self.CmptmtSunMtrlTEstimd = Float32()


class IdtCmptmtTEstimd(SomeIpPayload):

    IdtCmptmtTEstimd: IdtCmptmtTEstimdKls

    def __init__(self):

        self.IdtCmptmtTEstimd = IdtCmptmtTEstimdKls()
