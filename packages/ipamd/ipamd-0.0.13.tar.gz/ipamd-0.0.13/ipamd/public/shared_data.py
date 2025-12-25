import ipamd
import os
from ipamd.public.utils.hardware import available_gpus
from ipamd.public.utils.config import Config
available_ff = []
config = Config()
gpu_list = available_gpus()
module_installation_dir = os.path.dirname(ipamd.__file__)