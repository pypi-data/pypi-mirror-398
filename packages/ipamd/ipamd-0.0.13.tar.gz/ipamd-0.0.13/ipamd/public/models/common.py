from enum import Enum
from ipamd.public.utils.output import *
from ipamd.public import shared_data
from ipamd.public.utils.plugin_manager import PluginBase

class AnalysisResult(PluginBase):
    class Type(Enum):
        UNKNOWN = 0
        SCALAR = 1
        VECTOR = 2
        MATRIX = 3
        DISTRIBUTION = 4
        RATIO = 5

    def __init__(self, title, data, type_):
        super().__init__(
            [shared_data.module_installation_dir + '/plugins/analysis/data_process']
        )
        self.title = title
        self.data = data
        self.type = type_
        self.weight = 1
        if config.get('auto_load'):
            self.load_all()

    def name_as(self, name):
        self.title = name
        return self

    def parse(self, data):
        match data:
            case int() | float():
                self.type = AnalysisResult.Type.SCALAR
                self.data = data
            case dict():
                self.data = data
                for d in data.values():
                    if type(d) == dict:
                        self.type = AnalysisResult.Type.MATRIX
                    else:
                        self.type = AnalysisResult.Type.VECTOR
                    break
