from someip_py.codec import *


class IdtADModFieldsKls(SomeIpPayload):

    _include_struct_len = True

    Key: Uint8

    Value: Uint8

    def __init__(self):

        self.Key = Uint8()

        self.Value = Uint8()


class IdtADModFields(SomeIpPayload):

    IdtADModFields: IdtADModFieldsKls

    def __init__(self):

        self.IdtADModFields = IdtADModFieldsKls()
