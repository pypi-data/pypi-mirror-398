import json
from deepKernel import base

#打开料号
def open_job(job:str, path:str)->bool:
    try:
       ret= json.loads(base.open_job(path, job))['paras']['status']
       return ret   
    except Exception as e:
        print(e)
        return False
    
def get_profile_box(job:str, step:str)->dict:  
    try:
        #转成小写
        job= job.lower()
        step= step.lower()
        info= check_matrix_info(job, step)
        if info:
            ret_= base.has_profile(job,step)
            data_= json.loads(ret_)['result']
            if data_:
                ret = base.get_profile_box(job, step)
                data = json.loads(ret)
                box = data['paras']
                profile_box = {}
                profile_box['xmax'] = box['Xmax']
                profile_box['xmin'] = box['Xmin']
                profile_box['ymax'] = box['Ymax']
                profile_box['ymin'] = box['Ymin']
                return profile_box
            print('没有profile!')
            return {}
        return None
    except Exception as e:
        print(e)
    return None

def check_matrix_info(job:str, step:str='', layers:list=[])->bool:
    try:
        if isinstance(job, str) and isinstance(step, str) and isinstance(layers, list):
            open_jobs = get_opened_jobs()
            if job in open_jobs: 
                if step == '' and layers == []:
                    return False
                step_lst= get_steps(job)
                layer_lst = get_layers(job)
                if step!='':
                    if step not in step_lst:
                        print('step不存在')
                        return False
                if layers!=[]:
                    for layer in layers:
                        if layer not in layer_lst:
                            print(layer + ' 不存在')
                            return False
            else:
                print(f'{job}:未打开,请查找原因!')
                return False
        else:
            print("请检查填写的参数类型!")
            return False
    except Exception as e:
        return False
        print(e)
    return True

def get_opened_jobs()->list:
    try:
        ret= base.get_opened_jobs()
        data= json.loads(ret)
        if 'paras' in data:
            return data['paras']
        else:
            return []
    except Exception as e:
        print(repr(e))
        return None
    
def get_steps(job:str)->list:
    try:
        ret = base.get_matrix(job)
        data = json.loads(ret)
        steps = data['paras']['steps']
        return steps
    except Exception as e:
        print(e)
    return []

def get_layers(job:str)->list:
    try:
        ret = base.get_matrix(job)
        data = json.loads(ret)
        layer_infos = data['paras']['info']
        layer_list = []
        for i in range(0, len(layer_infos)):
            layer_list.append(layer_infos[i]['name'])
        return layer_list
    except Exception as e:
        print(e)
    return []

def get_layer_feature_count(job:str, step:str, layer:str)->int:
    try:
        ret = base.get_layer_feature_count(job, step, layer)
        ret = json.loads(ret)
        if 'featureNum' in ret:
            return int(ret['featureNum'])
        return -1
    except Exception as e:
        print(e)
    return -1

def get_all_features_info(job:str ,step:str, layer:str)->list:
    try:
        ret = base.get_all_feature_info(job,step,layer,127)
        ret = json.loads(ret)['paras']
        return ret
    except Exception as e:
        print(e)
    return []