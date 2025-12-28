from someip_py.codec import *


class RelativeLocalizationKls(SomeIpPayload):

    PositionXSeN: Int32

    PositionYSeN: Int32

    YawSeN: Float32

    PitchSeN: Int32

    DisplayPitchSeN: Int32

    TargetPoistionXSeN: Int16

    TargetPoistionYSeN: Int16

    TargetPoistionAngleSeN: Int32

    ParkProgressSeN: Int8

    PositionZSeN: Int32

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()

        self.YawSeN = Float32()

        self.PitchSeN = Int32()

        self.DisplayPitchSeN = Int32()

        self.TargetPoistionXSeN = Int16()

        self.TargetPoistionYSeN = Int16()

        self.TargetPoistionAngleSeN = Int32()

        self.ParkProgressSeN = Int8()

        self.PositionZSeN = Int32()


class RelativeLocalization(SomeIpPayload):

    RelativeLocalization: RelativeLocalizationKls

    def __init__(self):

        self.RelativeLocalization = RelativeLocalizationKls()
