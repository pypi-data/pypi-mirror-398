from someip_py.codec import *


class IdtDriveModeStateKls(SomeIpPayload):

    _include_struct_len = True

    EcoMode: bool

    ComfortMode: bool

    SportMode: bool

    PersonalMode: bool

    OffroadMode: bool

    AdaptiveMode: bool

    RaceMode: bool

    SnowMode: bool

    SandMode: bool

    MudMode: bool

    RockMode: bool

    GrassOrGravelMode: bool

    DeepSnowMode: bool

    MountainMode: bool

    WaterWadingMode: bool

    Anti_CarsicknessMode: bool

    SlipperyMode: bool

    SportPlusMode: bool

    def __init__(self):

        self.EcoMode = bool()

        self.ComfortMode = bool()

        self.SportMode = bool()

        self.PersonalMode = bool()

        self.OffroadMode = bool()

        self.AdaptiveMode = bool()

        self.RaceMode = bool()

        self.SnowMode = bool()

        self.SandMode = bool()

        self.MudMode = bool()

        self.RockMode = bool()

        self.GrassOrGravelMode = bool()

        self.DeepSnowMode = bool()

        self.MountainMode = bool()

        self.WaterWadingMode = bool()

        self.Anti_CarsicknessMode = bool()

        self.SlipperyMode = bool()

        self.SportPlusMode = bool()


class IdtDriveModeState(SomeIpPayload):

    IdtDriveModeState: IdtDriveModeStateKls

    def __init__(self):

        self.IdtDriveModeState = IdtDriveModeStateKls()
