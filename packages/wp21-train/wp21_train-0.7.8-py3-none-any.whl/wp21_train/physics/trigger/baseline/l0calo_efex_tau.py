from .. import RoITrigger
from ....bookkeeping.keys import TauEFEXKeys

class EFEXTau(RoITrigger):
    def __init__(self):
        super().__init__("eTAU")

    @classmethod
    def get_discriminants(cls, **kwargs):
        return TauEFEXKeys().values()
