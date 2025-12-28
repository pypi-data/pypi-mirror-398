from someip_py.codec import *


class IdtEyeGazeRegionKls(SomeIpPayload):

    _include_struct_len = True

    EyeGazeZone: Uint8

    EyeGazeZoneTime: Uint16

    def __init__(self):

        self.EyeGazeZone = Uint8()

        self.EyeGazeZoneTime = Uint16()


class IdtEyeGazeRegion(SomeIpPayload):

    IdtEyeGazeRegion: IdtEyeGazeRegionKls

    def __init__(self):

        self.IdtEyeGazeRegion = IdtEyeGazeRegionKls()
