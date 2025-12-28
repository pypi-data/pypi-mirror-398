from someip_py.codec import *


class IdtRuleLocalCmd(SomeIpPayload):

    IdtRuleLocalCmd: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtRuleLocalCmd = SomeIpDynamicSizeString()


class IdtRuleLocalResp(SomeIpPayload):

    IdtRuleLocalResp: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtRuleLocalResp = SomeIpDynamicSizeString()
