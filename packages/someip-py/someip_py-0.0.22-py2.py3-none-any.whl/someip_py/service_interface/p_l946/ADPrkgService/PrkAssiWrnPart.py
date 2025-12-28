from someip_py.codec import *


class IdtPrkAssiWrnPartKls(SomeIpPayload):

    _include_struct_len = True

    RearLftSide1Regn: Uint8

    RearLftCorRegn: Uint8

    RearLftMidRegn: Uint8

    RearRiMidRegn: Uint8

    RearRiCorRegn: Uint8

    RearRiSide1Regn: Uint8

    FrntLftSide1Regn: Uint8

    FrntLftCorRegn: Uint8

    FrntLftMidRegn: Uint8

    FrntRiMidRegn: Uint8

    FrntRiCorRegn: Uint8

    FrntRiSide1Regn: Uint8

    RearLftSide1Dist: Uint16

    RearLftCorDist: Uint16

    RearLftMidDist: Uint16

    RearRiMidDist: Uint16

    RearRiCorDist: Uint16

    RearRiSide1Dist: Uint16

    FrntLftSide1Dist: Uint16

    FrntLftCorDist: Uint16

    FrntLftMidDist: Uint16

    FrntRiMidDist: Uint16

    FrntRiCorDist: Uint16

    FrntRiSide1Dist: Uint16

    def __init__(self):

        self.RearLftSide1Regn = Uint8()

        self.RearLftCorRegn = Uint8()

        self.RearLftMidRegn = Uint8()

        self.RearRiMidRegn = Uint8()

        self.RearRiCorRegn = Uint8()

        self.RearRiSide1Regn = Uint8()

        self.FrntLftSide1Regn = Uint8()

        self.FrntLftCorRegn = Uint8()

        self.FrntLftMidRegn = Uint8()

        self.FrntRiMidRegn = Uint8()

        self.FrntRiCorRegn = Uint8()

        self.FrntRiSide1Regn = Uint8()

        self.RearLftSide1Dist = Uint16()

        self.RearLftCorDist = Uint16()

        self.RearLftMidDist = Uint16()

        self.RearRiMidDist = Uint16()

        self.RearRiCorDist = Uint16()

        self.RearRiSide1Dist = Uint16()

        self.FrntLftSide1Dist = Uint16()

        self.FrntLftCorDist = Uint16()

        self.FrntLftMidDist = Uint16()

        self.FrntRiMidDist = Uint16()

        self.FrntRiCorDist = Uint16()

        self.FrntRiSide1Dist = Uint16()


class IdtPrkAssiWrnPart(SomeIpPayload):

    IdtPrkAssiWrnPart: IdtPrkAssiWrnPartKls

    def __init__(self):

        self.IdtPrkAssiWrnPart = IdtPrkAssiWrnPartKls()
