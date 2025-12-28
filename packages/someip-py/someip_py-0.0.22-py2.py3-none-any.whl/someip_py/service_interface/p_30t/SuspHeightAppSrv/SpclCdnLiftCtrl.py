from someip_py.codec import *


class IdtSpclCdnLiftCtrl(SomeIpPayload):

    IdtSpclCdnLiftCtrl: Uint8

    def __init__(self):

        self.IdtSpclCdnLiftCtrl = Uint8()
