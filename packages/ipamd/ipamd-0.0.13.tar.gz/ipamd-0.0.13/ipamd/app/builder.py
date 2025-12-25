from ipamd.public.utils.plugin_manager import PluginBase
from ipamd.public.shared_data import *

class Builder(PluginBase):
    def __init__(self, app):
        extra_plugin_dir = config.get('builder_plugin_dir')
        plugin_dir = [module_installation_dir + '/plugins/builder/generator'] + extra_plugin_dir
        super().__init__(plugin_dir)
        self.__app = app
        self.def_schema('io', {
            'working_dir': lambda: self.__app.working_dir
        })
        self.add_resource('cuda', self.__app.cuda)
        self.add_resource('ff', lambda: self.__app.force_field)
        if config.get('auto_load'):
            self.load_all()