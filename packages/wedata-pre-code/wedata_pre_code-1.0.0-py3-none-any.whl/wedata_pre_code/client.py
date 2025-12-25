

class PreCodeClient:

    def init_wedata2_pre_code(self, **kwargs):
        from wedata_pre_code.wedata2.client import Wedata2PreCodeClient
        return Wedata2PreCodeClient(**kwargs)

    def init_wedata3_pre_code(self, **kwargs):
        from wedata_pre_code.wedata3.client import Wedata3PreCodeClient
        return Wedata3PreCodeClient(**kwargs)