from someip_py.codec import *


class IdtEyePosnValidSigKls(SomeIpPayload):

    _include_struct_len = True

    EyePosnValidSig_X: Int16

    EyePosnValidSig_Y: Int16

    EyePosnValidSig_Z: Int16

    def __init__(self):

        self.EyePosnValidSig_X = Int16()

        self.EyePosnValidSig_Y = Int16()

        self.EyePosnValidSig_Z = Int16()


class IdtEyePosnValidSig(SomeIpPayload):

    IdtEyePosnValidSig: IdtEyePosnValidSigKls

    def __init__(self):

        self.IdtEyePosnValidSig = IdtEyePosnValidSigKls()
