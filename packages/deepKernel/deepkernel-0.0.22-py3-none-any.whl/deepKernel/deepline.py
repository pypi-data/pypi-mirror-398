import ctypes
import os
import json

dll = None
bin_path = None
isInit = False

def init(path):
    global dll
    global bin_path
    bin_path = path
    os.environ['path'] += (r";" + bin_path)

    dll = ctypes.CDLL(bin_path + r"\LIB_DL.dll")
    dll.process.restype =  ctypes.c_char_p
    dll.init_func_map.restype =  ctypes.c_char_p
    dll.init_orig_func_map.restype =  ctypes.c_char_p
    dll.getVersion.restype =  ctypes.c_char_p
    # dll.getVersion.restype =  ctypes.c_char_p
    dll.process.argtypes = [ctypes.c_char_p]
    ret = dll.init_func_map()
    ret = dll.init_orig_func_map()
    global isInit
    isInit = True
    return ret.decode('utf-8')

def set_use_times(times):
    times.encode('utf-8')
    #print(type(json))
    times_str = bytes(times, encoding='utf-8')
    dll.setUseTimes(times_str)

def process(json):
    if isInit == False:
        print('Please init first')
        return

    json.encode('utf-8')
    #print(type(json))
    string_buff = bytes(json, encoding='utf-8')
    #print(type(string_buff), string_buff)
    ret = dll.process(string_buff)
    #print(ret)
    return ret.decode('utf-8')

# def view_cmd(vjson):
#     string_vjson = bytes(vjson, encoding='utf-8')
#     vdll.view_cmd(string_vjson)

def getVersion():
    ret = dll.getVersion()
    ret = ret.decode('utf-8')
    return json.loads(ret)

# def uiprocess(json):
#     json.encode('utf-8')
#     #print(type(json))
#     string_buff = bytes(json, encoding='utf-8')
#     #print(type(string_buff), string_buff)
#     ret = uidll.process(string_buff)
#     #print(ret)
#     return ret.decode('utf-8')

# def readPathFactoryJson(vjson):
#     string_vjson = bytes(vjson, encoding='utf-8')
#     ret = matrixdll.readPathFactoryJson(string_vjson)
#     return ret.decode('gbk')

# def readPathTemplateConfigJson(vjson):
#     string_vjson = bytes(vjson, encoding='utf-8')
#     ret = matrixdll.readPathTemplateConfigJson(string_vjson)
#     return ret.decode('gbk')

# def getMatchedLayers(vjson):
#     string_vjson = bytes(vjson, encoding='utf-8')
#     ret = matrixdll.getMatchedLayers(string_vjson)
#     return ret.decode('gbk')

# def saveNewMatchRule(vjson):
#     string_vjson = bytes(vjson, encoding='utf-8')
#     ret = matrixdll.saveNewMatchRule(string_vjson)
#     return ret.decode('gbk')

def get_config_path():
    return bin_path