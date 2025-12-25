from deepKernel import base
import json

#打开料号
def open_job(job:str, path:str)->bool:
    try:
       ret= json.loads(base.open_job(path, job))['paras']['status']
       return ret   
    except Exception as e:
        print(e)
        return False
    
def open_dxf(job,path,step,layer,scale,polylineEnds,units,proportionText,convertCircleToApertures,convertDonutsToApertures,fillClosedZeroWidthPolylines,layerApart)->bool:
    try:
        ret = json.loads(base.read_dxf(path,job,step,layer,scale,polylineEnds,units,proportionText,convertCircleToApertures,convertDonutsToApertures,fillClosedZeroWidthPolylines,layerApart))['paras']['status']
        return ret
    except Exception as e:
        print(e)
        return False
    
def file_identify(path:str)->dict:
    try:
        ret = base.file_identify(path)
        data = json.loads(ret)
        if 'paras' in data:
            return data['paras']
        return None
    except Exception as e:
        return None
    
def file_translate(path:str, job:str, step:str, layer:str, param:dict)->bool:
    try:
        file_format = param['format']
        pa = param['parameters']
        if file_format == 'Gerber274x' or file_format == 'Excellon2' or file_format == 'DXF' or file_format == 'Excellon1':
            ret = base.file_translate(path, job, step, layer, pa, '', '', '', [])    
            data = json.loads(ret)
            if 'paras' in data:
                if 'result' in data['paras']:
                    return data['paras']['result']
    except Exception as e:
        return False
    return False