from someip_py.codec import *


class IdtDriveModeForbid(SomeIpPayload):

    IdtDriveModeForbid: Bool

    def __init__(self):

        self.IdtDriveModeForbid = Bool()
