from someip_py.codec import *


class IdtHostVehInLitArea(SomeIpPayload):

    IdtHostVehInLitArea: Bool

    def __init__(self):

        self.IdtHostVehInLitArea = Bool()
