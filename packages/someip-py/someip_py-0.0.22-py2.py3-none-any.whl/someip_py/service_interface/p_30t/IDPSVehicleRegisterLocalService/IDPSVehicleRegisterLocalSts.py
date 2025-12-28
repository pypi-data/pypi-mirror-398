from someip_py.codec import *


class IdtIDPSRegisterLocalSts(SomeIpPayload):

    IdtIDPSRegisterLocalSts: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtIDPSRegisterLocalSts = SomeIpDynamicSizeString()
