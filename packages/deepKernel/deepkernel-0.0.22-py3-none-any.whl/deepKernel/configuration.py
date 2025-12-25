from deepKernel import deepline,base

def init(path:str): 
    deepline.init(path)
    base.set_config_path(path)