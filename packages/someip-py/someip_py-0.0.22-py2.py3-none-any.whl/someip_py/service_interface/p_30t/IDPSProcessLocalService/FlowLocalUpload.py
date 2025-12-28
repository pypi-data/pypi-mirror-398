from someip_py.codec import *


class IdtFlowLocalUploadCmd(SomeIpPayload):

    IdtFlowLocalUploadCmd: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtFlowLocalUploadCmd = SomeIpDynamicSizeString()


class IdtFlowLocalUploadResult(SomeIpPayload):

    IdtFlowLocalUploadResult: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtFlowLocalUploadResult = SomeIpDynamicSizeString()
