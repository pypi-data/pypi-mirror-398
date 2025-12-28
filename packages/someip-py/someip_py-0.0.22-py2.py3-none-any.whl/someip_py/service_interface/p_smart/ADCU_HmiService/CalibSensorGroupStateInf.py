from someip_py.codec import *


class CalibSensorGroupStateKls(SomeIpPayload):

    AllSensorCalibStateSeN: Uint32

    CalibSensorGroupSeN: Uint32

    CalibSensorProgressSeN: Uint32

    CalibSensorDurationSeN: Float64

    CalibSensorPromptSeN: Uint32

    def __init__(self):

        self.AllSensorCalibStateSeN = Uint32()

        self.CalibSensorGroupSeN = Uint32()

        self.CalibSensorProgressSeN = Uint32()

        self.CalibSensorDurationSeN = Float64()

        self.CalibSensorPromptSeN = Uint32()


class CalibSensorGroupState(SomeIpPayload):

    CalibSensorGroupState: CalibSensorGroupStateKls

    def __init__(self):

        self.CalibSensorGroupState = CalibSensorGroupStateKls()
