from someip_py.codec import *


class IdtMemoryRouteStatusKls(SomeIpPayload):

    Status: Uint8

    Cause: Uint8

    Advice: Uint8

    RouteUuid: Uint64

    RecordingLength: Uint32

    RecordingStartPosition: Uint32

    NaviId: SomeIpDynamicSizeString

    def __init__(self):

        self.Status = Uint8()

        self.Cause = Uint8()

        self.Advice = Uint8()

        self.RouteUuid = Uint64()

        self.RecordingLength = Uint32()

        self.RecordingStartPosition = Uint32()

        self.NaviId = SomeIpDynamicSizeString()


class IdtMemoryRouteStatus(SomeIpPayload):

    IdtMemoryRouteStatus: IdtMemoryRouteStatusKls

    def __init__(self):

        self.IdtMemoryRouteStatus = IdtMemoryRouteStatusKls()
