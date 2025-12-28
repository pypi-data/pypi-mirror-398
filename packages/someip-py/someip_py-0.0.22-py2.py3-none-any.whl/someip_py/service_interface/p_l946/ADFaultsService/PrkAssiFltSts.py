from someip_py.codec import *


class IdtPrkAssiFltStsKls(SomeIpPayload):

    _include_struct_len = True

    RearLftSideSnsFlt: Uint8

    RearLftCorSnsFlt: Uint8

    RearLftMidSnsFlt: Uint8

    RearRiMidSnsFlt: Uint8

    RearRiCorSnsFlt: Uint8

    RearRiSideSnsFlt: Uint8

    FrntLftSideSnsFlt: Uint8

    FrntLftCorSnsFlt: Uint8

    FrntLftMidSnsFlt: Uint8

    FrntRiMidSnsFlt: Uint8

    FrntRiCorSnsFlt: Uint8

    FrntRiSideSnsFlt: Uint8

    Reserve1: Uint8

    Reserve2: Uint8

    def __init__(self):

        self.RearLftSideSnsFlt = Uint8()

        self.RearLftCorSnsFlt = Uint8()

        self.RearLftMidSnsFlt = Uint8()

        self.RearRiMidSnsFlt = Uint8()

        self.RearRiCorSnsFlt = Uint8()

        self.RearRiSideSnsFlt = Uint8()

        self.FrntLftSideSnsFlt = Uint8()

        self.FrntLftCorSnsFlt = Uint8()

        self.FrntLftMidSnsFlt = Uint8()

        self.FrntRiMidSnsFlt = Uint8()

        self.FrntRiCorSnsFlt = Uint8()

        self.FrntRiSideSnsFlt = Uint8()

        self.Reserve1 = Uint8()

        self.Reserve2 = Uint8()


class IdtPrkAssiFltSts(SomeIpPayload):

    IdtPrkAssiFltSts: IdtPrkAssiFltStsKls

    def __init__(self):

        self.IdtPrkAssiFltSts = IdtPrkAssiFltStsKls()
