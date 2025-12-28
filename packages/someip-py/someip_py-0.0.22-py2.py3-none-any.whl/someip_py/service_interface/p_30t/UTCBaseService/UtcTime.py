from someip_py.codec import *


class IdtTime(SomeIpPayload):

    _include_struct_len = True

    Year: Int32

    Month: Int32

    Day: Int32

    Hour: Int32

    Minute: Int32

    Second: Int32

    Milliseconds: Int32

    def __init__(self):

        self.Year = Int32()

        self.Month = Int32()

        self.Day = Int32()

        self.Hour = Int32()

        self.Minute = Int32()

        self.Second = Int32()

        self.Milliseconds = Int32()


class IdtVehicleTime(SomeIpPayload):

    _include_struct_len = True

    Second: Int64

    Nanosecond: Int64

    def __init__(self):

        self.Second = Int64()

        self.Nanosecond = Int64()


class IdtUtcDateTimeKls(SomeIpPayload):

    _include_struct_len = True

    TimeSource: Uint8

    Time: IdtTime

    VehicleTime: IdtVehicleTime

    def __init__(self):

        self.TimeSource = Uint8()

        self.Time = IdtTime()

        self.VehicleTime = IdtVehicleTime()


class IdtUtcDateTime(SomeIpPayload):

    IdtUtcDateTime: IdtUtcDateTimeKls

    def __init__(self):

        self.IdtUtcDateTime = IdtUtcDateTimeKls()
