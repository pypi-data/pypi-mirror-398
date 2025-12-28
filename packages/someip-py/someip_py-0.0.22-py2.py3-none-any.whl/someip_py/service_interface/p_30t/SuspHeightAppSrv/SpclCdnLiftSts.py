from someip_py.codec import *


class IdtSpclCdnLiftSts(SomeIpPayload):

    IdtSpclCdnLiftSts: Uint8

    def __init__(self):

        self.IdtSpclCdnLiftSts = Uint8()
