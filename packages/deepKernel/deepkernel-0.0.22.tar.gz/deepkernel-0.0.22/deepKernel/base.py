from deepKernel import deepline
import json

def _init():
    global _global_dict
    _global_dict={}

def set_config_path(path):
    data = {
        'func': 'SET_CONFIG_PATH',
        'paras': {
                      'path': path
                      }   
    }
    #print(json.dumps(data))
    return deepline.process(json.dumps(data))

#获取当前层feature数
def get_layer_feature_count(jobName, stepName, layerName):
    data = {
        'func': 'GET_LAYER_FEATURE_COUNT',
        'paras': {'jobName': jobName, 
                  'stepName': stepName, 
                  'layerName': layerName}
    }
    return deepline.process(json.dumps(data))

def get_opened_jobs():
    data = {
        'func': 'GET_OPENED_JOBS'
    }
    #print(json.dumps(data))
    return deepline.process(json.dumps(data))

def open_job(path, job):
    data = {
        'func': 'OPEN_JOB',
        'paras': [{'path': path},
                  {'job': job}]
    }
    # print(json.dumps(data))
    ret = deepline.process(json.dumps(data))
    return ret

def get_matrix(job):
    data = {
        'func': 'GET_MATRIX',
        'paras': {'job': job}
    }
    # print(json.dumps(data))
    return deepline.process(json.dumps(data))

def has_profile(job, step):
    data = {
        'func': 'HAS_PROFILE',
        'paras': {
                    'job': job,
                    'step': step
                      }   
    }
    #print(json.dumps(data))
    return deepline.process(json.dumps(data))

def get_profile_box(job, step):
    data = {
            'func': 'PROFILE_BOX',
            'paras': {'job': job, 
                      'step': step}
    }
    js = json.dumps(data)
    #print(js)
    ret = deepline.process(json.dumps(data))
    return ret

#导出
def layer_export(job, step, layer, _type, filename, gdsdbu, resize, angle, scalingX, scalingY, isReverse,
                    mirror, rotate, scale, profiletop, cw, cutprofile, mirrorpointX, mirrorpointY, rotatepointX,
                    rotatepointY, scalepointX, scalepointY, mirrordirection, cut_polygon,numberFormatL=2,numberFormatR=6,
                    zeros=2,unit=0):
    data = {
            'func': 'LAYER_EXPORT',
            'paras': {
                        'job': job,
                        'step': step,
                        'layer': layer,
                        'type': _type,
                        'filename': filename,
                        'gdsdbu': gdsdbu,
                        'resize': resize,
                        'angle': angle,
                        'scalingX': scalingX,
                        'scalingY': scalingY,
                        'isReverse': isReverse,
                        'mirror': mirror,
                        'rotate': rotate,
                        'scale': scale,
                        'profiletop': profiletop,
                        'cw': cw,
                        'cutprofile': cutprofile,
                        'mirrorpointX': mirrorpointX,
                        'mirrorpointY': mirrorpointY,
                        'rotatepointX': rotatepointX,
                        'rotatepointY': rotatepointY,
                        'scalepointX': scalepointX,
                        'scalepointY': scalepointY,
                        'mirrordirection': mirrordirection,
                        'cut_polygon': cut_polygon,
                        'numberFormatL': numberFormatL,
                        'numberFormatR': numberFormatR,
                        'zeros': zeros,
                        'unit': unit
                      }                    
            }   
    js = json.dumps(data)
    print(js)
    return deepline.process(json.dumps(data))

#load layer
def load_layer(jobname, stepname, layername):
    data = {
            'func': 'LOAD_LAYER',
            'paras': {'jobname': jobname,
                      'stepname': stepname,
                      'layername': layername}                   
        }
    js = json.dumps(data)
    #print(js)
    deepline.process(json.dumps(data))

#料号另存为
def save_job_as(job, path):
    data = {
            'func': 'SAVE_JOB_AS',
            'paras': {
                      'job': job,
                      'path': path
                      }             
        }
    js = json.dumps(data)
    #print(js)
    ret = deepline.process(json.dumps(data))
    return ret

def save_png(job,step,layers,xmin,ymin,xmax,ymax,picpath,picname,backcolor,layercolors):
    data = {
        "func": "OUTPUT_FIXED_PICTURE",
        "paras": {
            "job": job,
            "step":step,
            "layers":layers,
            "xmin":xmin,
            "ymin":ymin,
            "xmax": xmax,
            "ymax":ymax,
            "picpath":picpath,
            "picname":picname,
            "backcolor": backcolor,
            "layercolors":layercolors
        }
    }
    return deepline.process(json.dumps(data))

def save_true_png(job,step,layers,xmin,ymin,xmax,ymax,picpath,picname,backcolor,layercolors,drawSR,size):
    data = {
        "func": "OUTPUT_PICTURE",
        "paras": {
            "job": job,
            "step":step,
            "layers":layers,
            "xmin":xmin,
            "ymin":ymin,
            "xmax": xmax,
            "ymax":ymax,
            "picpath":picpath,
            "picname":picname,
            "backcolor": backcolor,
            "layercolors":layercolors,
            "drawSR":drawSR,
            "size":size,
        }
    }
    return deepline.process(json.dumps(data))    

def get_all_feature_info(job, step, layer,featuretype=127):
    data = {
        'func': 'GET_ALL_FEATURE_INFO',
        'paras': {'job': job, 
                  'step': step, 
                  'layer': layer,
                  'featureType':featuretype
        }
    }
    return deepline.process(json.dumps(data))

def read_dxf(path,job,step,layer,scale,polylineEnds,units,propertionText,convertCircleToApertures,convertDpnutsToApertures,fillClosedZeroWidthPolylines,layerApart):
    data = {
        "func":"READ_DXF",
        "paras":{
            "path":path,
            "job":job,
            "step":step,
            "layer":layer,
            "scale":scale,
            "polylineEnds":polylineEnds,
            "units":units,
            "propertionText":propertionText,
            "convertCircleToApertures":convertCircleToApertures,
            "convertDpnutsToApertures":convertDpnutsToApertures,
            "fillClosedZeroWidthPolylines":fillClosedZeroWidthPolylines,
            "layerApart":layerApart
        }
    }
    return deepline.process(json.dumps(data))

def dxf2file(job,step,layers,savePath):
    '''
    job料是eps时为带后缀全名
    savePath为全路径
    '''
    data = {
        "func":"DXF2FILE",
        "paras":{
            "job":job,
            "step":step,
            "layers":layers,
            "savePath":savePath
        }
    }
    return deepline.process(json.dumps(data))

#层别比对放入目标层
def layer_compare(jobname1, stepname1, layername1, jobname2, stepname2, layername2, tolerance, mode, consider_SR, 
                    comparison_map_layername, map_layer_resolution):
    data = {
            'func': 'LAYER_COMPARE',
            'paras': {
                        'jobname1': jobname1,
                        'stepname1': stepname1,
                        'layername1': layername1,
                        'jobname2': jobname2,
                        'stepname2': stepname2,
                        'layername2': layername2,
                        'tolerance': tolerance,
                        'global': mode,
                        'consider_SR': consider_SR,
                        'comparison_map_layername': comparison_map_layername,
                        'map_layer_resolution': map_layer_resolution,
                      }                    
            }   
    js = json.dumps(data)
    #print(js)
    return deepline.process(json.dumps(data))

#层别比对返回问题点
def layer_compare_point(jobname1, stepname1, layername1, jobname2, stepname2, layername2, 
                            tolerance = 22860, mode = True, consider_SR = True, map_layer_resolution = 5080000):
    data = {
            'func': 'LAYER_COMPARE_POINT',
            'paras': {
                        'jobname1': jobname1,
                        'stepname1': stepname1,
                        'layername1': layername1,
                        'jobname2': jobname2,
                        'stepname2': stepname2,
                        'layername2': layername2,
                        'tolerance': tolerance,
                        'global': mode,
                        'consider_SR': consider_SR,
                        'map_layer_resolution': map_layer_resolution, 
                      }                    
            }   
    js = json.dumps(data)
    #print(js)
    return deepline.process(json.dumps(data))

#layer_compare_bmp 
def layer_compare_bmp(jobname1, stepname1, layername1, jobname2, stepname2,layername2, tolerance, grid_size, savepath, suffix, bmp_width, bmp_height):
    data = {
                'func': 'LAYER_COMPARE_BMP',
                'paras': {  'jobname1': jobname1, 
                            'stepname1': stepname1,
                            'layername1': layername1,
                            'jobname2': jobname2,
                            'stepname2': stepname2,
                            'layername2': layername2,
                            'tolerance': tolerance,
                            'grid_size': grid_size,
                            'savepath': savepath,
                            'suffix': suffix,
                            'bmp_width': bmp_width,
                            'bmp_height': bmp_height}
           }      
    ret = deepline.process(json.dumps(data))
    return ret

#identify
def file_identify(path):
    data = {
            'func': 'FILE_IDENTIFY',
            'paras': {'pathname': path}                   
        }
    js = json.dumps(data)
    #print(js)
    ret = deepline.process(json.dumps(data))
    return ret

#translate
def file_translate(path, job, step, layer, parameters, start_time, end_time, assigned_dcodes, defect_reports):
    data = {
        'func': 'FILE_TRANSLATE',
        'paras': {
                    'path': path,
                    'job': job,
                    'step': step,
                    'layer': layer,
                    'parameters': parameters,
                    'start_time': start_time,
                    'end_time': end_time,
                    'assigned_dcodes': assigned_dcodes,
                    'defect_reports': defect_reports
                      }   
    }
    #print(json.dumps(data))
    return deepline.process(json.dumps(data))

#创建料号（无路径）
def job_create(job):
    data = {
        'func': 'JOB_CREATE',
        'paras': {
                    'job': job
                      }   
    }
    #print(json.dumps(data))
    return deepline.process(json.dumps(data))

#创建料号（有路径）
def create_job(path, job):
    data = {
        'func': 'CREATE_JOB',
        'paras': {
                    'path': path,
                    'job': job
                      }   
    }
    #print(json.dumps(data))
    return deepline.process(json.dumps(data))

#创建新层
def create_new_layer(job, step, layer, index):
    data = {
        'func': 'CREATE_NEW_LAYER',
        'paras': {'job': job,
                  'step': step, 
                  'layer': layer,
                  'index': index}
    }
    deepline.process(json.dumps(data))

#创建新step
def create_step(jobname, stepname, index):
    data = {
        'func': 'CREATE_STEP',
        'paras': {'jobname': jobname,
                  'stepname': stepname, 
                  'index': index}
    }
    deepline.process(json.dumps(data))

def is_job_open(job):
    data = {
        'func': 'IS_JOB_OPENED',
        'paras': {'jobname': job }
    }
    js = json.dumps(data)
    # print(js)
    return deepline.process(js)

def draw_panel_picture(job,step,layer,path):
    data = {
            'func': 'DRAW_PANEL_PICTURE',
            'paras': {
                        'job': job,
                        'step': step,
                        'layer': layer,
                        'path': path
                        }                    
            } 
    js = json.dumps(data)
    print(js)
    return deepline.process(json.dumps(data))

#加载layer
def open_layer(job, step, layer):
    data = {
        'func': 'OPEN_LAYER',
        'paras': {'jobname': job,
                  'step': step,
                  'layer': layer}
    }
    return deepline.process(json.dumps(data))

def layer_box(job,step,layers):
    data = {
        'func': 'LAYER_BOX',
        'paras': {
            'job': job, 
            'step': step, 
            'layers': layers
        }
    }
    return deepline.process(json.dumps(data))

