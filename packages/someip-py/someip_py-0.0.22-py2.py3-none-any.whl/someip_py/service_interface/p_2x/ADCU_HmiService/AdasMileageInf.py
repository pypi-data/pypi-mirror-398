from someip_py.codec import *


class Uni32baseType(SomeIpPayload):

    Uni32baseType: Uint32

    def __init__(self):

        self.Uni32baseType = Uint32()
