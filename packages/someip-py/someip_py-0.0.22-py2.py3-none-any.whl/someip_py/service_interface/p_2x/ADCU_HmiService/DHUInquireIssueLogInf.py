from someip_py.codec import *


class IdtDHUInquireIssueLogKls(SomeIpPayload):

    InquireFlag: Uint8

    InquireIssueLogTime: Uint64

    def __init__(self):

        self.InquireFlag = Uint8()

        self.InquireIssueLogTime = Uint64()


class IdtDHUInquireIssueLog(SomeIpPayload):

    IdtDHUInquireIssueLog: IdtDHUInquireIssueLogKls

    def __init__(self):

        self.IdtDHUInquireIssueLog = IdtDHUInquireIssueLogKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
