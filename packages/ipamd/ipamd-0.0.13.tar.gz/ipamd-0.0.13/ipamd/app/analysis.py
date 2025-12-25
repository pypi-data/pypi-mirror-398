from ipamd.public.utils.plugin_manager import PluginBase
from ipamd.public import shared_data

class Analysis(PluginBase):
    def __init__(self, app):
        extra_plugin_dir = shared_data.config.get('analyse_plugin_dir')
        plugin_dir = ([shared_data.module_installation_dir + '/plugins/analysis/operator'] + extra_plugin_dir)
        super().__init__(plugin_dir)
        self.__app = app
        self.def_schema('io', {
            'working_dir': lambda: self.__app.working_dir
        })
        self.add_resource('cuda', self.__app.cuda)
        if shared_data.config.get('auto_load'):
            self.load_all()