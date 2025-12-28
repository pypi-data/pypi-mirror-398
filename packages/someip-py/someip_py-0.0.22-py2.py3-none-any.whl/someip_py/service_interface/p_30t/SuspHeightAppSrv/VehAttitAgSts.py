from someip_py.codec import *


class IdtVehAttitAgStsKls(SomeIpPayload):

    _include_struct_len = True

    PitchA: Float32

    RollA: Float32

    def __init__(self):

        self.PitchA = Float32()

        self.RollA = Float32()


class IdtVehAttitAgSts(SomeIpPayload):

    IdtVehAttitAgSts: IdtVehAttitAgStsKls

    def __init__(self):

        self.IdtVehAttitAgSts = IdtVehAttitAgStsKls()
