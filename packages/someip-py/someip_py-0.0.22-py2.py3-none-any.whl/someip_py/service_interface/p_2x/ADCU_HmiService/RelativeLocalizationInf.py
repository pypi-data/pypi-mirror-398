from someip_py.codec import *


class RelativeLocalizationKls(SomeIpPayload):

    PositionXSeN: Int32

    PositionYSeN: Int32

    YawSeN: Int32

    PitchSeN: Int32

    DisplayPitchSeN: Int32

    TargetPoistionXSeN: Int32

    TargetPoistionYSeN: Int32

    TargetPoistionAngleSeN: Int32

    ParkProgressSeN: Int8

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()

        self.YawSeN = Int32()

        self.PitchSeN = Int32()

        self.DisplayPitchSeN = Int32()

        self.TargetPoistionXSeN = Int32()

        self.TargetPoistionYSeN = Int32()

        self.TargetPoistionAngleSeN = Int32()

        self.ParkProgressSeN = Int8()


class RelativeLocalization(SomeIpPayload):

    RelativeLocalization: RelativeLocalizationKls

    def __init__(self):

        self.RelativeLocalization = RelativeLocalizationKls()
