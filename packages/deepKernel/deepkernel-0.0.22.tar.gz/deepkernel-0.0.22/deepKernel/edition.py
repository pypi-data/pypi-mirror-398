import json, re
from deepKernel import base,information

def create_job(job:str)->bool:
    try:
        openedjob = information.get_opened_jobs()
        if job in openedjob:
            return False
        for ch in job:
            if u'\u4e00' <= ch <= u'\u9fff':
                return False
        if re.search('((?=[\x20-\x7e]+)[^A-Za-z0-9\_\+\-])',job)!=None or job=='eplib':
            return False
        else:
            ret = json.loads(base.job_create(job))['status']
            return bool(ret)
    except Exception as e:
        print(e)
        return False
    
#判断指定料号是否打开       
def is_job_open(job:str)->bool:
    try:
        _ret= base.is_job_open(job)
        ret =json.loads(_ret)['paras']['status']
        return ret
    except Exception as e:
        print(e)
        return False 
    
# 创建step
def create_step(job:str, step:str, col_index:int=-1):
    try:
        base.create_step(job, step, col_index)
    except Exception as e:
        print(e)

def layer_compare(job1:str, step1:str, layer1:str, job2:str, step2:str, layer2:str, tol:int, isGlobal:bool, consider_SR:bool, comparison_map_layername:str, map_layer_resolution:int)->None:
    try:
        base.layer_compare(job1, step1, layer1, job2, step2, layer2, tol, isGlobal, consider_SR, comparison_map_layername, map_layer_resolution)
    except Exception as e:
        print(e)
    return None

def layer_compare_point(job1:str, step1:str, layer1:str, job2:str, step2:str, layer2:str, tol:int = 22860,isGlobal:bool = True,consider_SR:bool = True, map_layer_resolution:int = 5080000)->list:
    try:
        tolerance = tol
        mode = isGlobal
        point = base.layer_compare_point(job1, step1, layer1, job2, step2, layer2, tolerance, mode, consider_SR, map_layer_resolution)
        points = json.loads(point)['result']
        return points
    except Exception as e:
        print(e)
    return [] 