from someip_py.codec import *


class IdtCmptmtTEstimdFacKls(SomeIpPayload):

    _include_struct_len = True

    CmptmtTCmpForFlowDistbnAtRowFirst: Float64

    CmptmtTCmpForFlowForRowFirst: Float64

    CmptmtTCmpForFlowForRowSec: Float64

    CmptmtTCmpForFlowForRowThrd: Float64

    FbForCmptmtT: Float64

    def __init__(self):

        self.CmptmtTCmpForFlowDistbnAtRowFirst = Float64()

        self.CmptmtTCmpForFlowForRowFirst = Float64()

        self.CmptmtTCmpForFlowForRowSec = Float64()

        self.CmptmtTCmpForFlowForRowThrd = Float64()

        self.FbForCmptmtT = Float64()


class IdtCmptmtTEstimdFac(SomeIpPayload):

    IdtCmptmtTEstimdFac: IdtCmptmtTEstimdFacKls

    def __init__(self):

        self.IdtCmptmtTEstimdFac = IdtCmptmtTEstimdFacKls()
