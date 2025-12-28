from someip_py.codec import *


class CalibSensorStatus(SomeIpPayload):

    CalibSensorIDSeN: Int32

    CalibPerSensorStatusSeN: Int32

    CalibPerSensorReasonSeN: Int32

    CalibResultRollSeN: Int32

    CalibResultPitchSeN: Int32

    CalibResultYawSeN: Int32

    def __init__(self):

        self.CalibSensorIDSeN = Int32()

        self.CalibPerSensorStatusSeN = Int32()

        self.CalibPerSensorReasonSeN = Int32()

        self.CalibResultRollSeN = Int32()

        self.CalibResultPitchSeN = Int32()

        self.CalibResultYawSeN = Int32()


class CalibSensorStatusAckInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    CalibAllSensorStatusSeN: Uint32

    CalibSensorStatusSeN: SomeIpDynamicSizeArray[CalibSensorStatus]

    def __init__(self):

        self.CalibAllSensorStatusSeN = Uint32()

        self.CalibSensorStatusSeN = SomeIpDynamicSizeArray(CalibSensorStatus)


class CalibSensorStatusAckInfo(SomeIpPayload):

    CalibSensorStatusAckInfo: CalibSensorStatusAckInfoKls

    def __init__(self):

        self.CalibSensorStatusAckInfo = CalibSensorStatusAckInfoKls()
