from ipamd.public.utils.plugin_manager import PluginBase
def func(frame, type1, threshold=4, type2=''):
    cm = PluginBase.call('contact_map', frame, type1, threshold=4, type2='')
    cm.print()
    pass