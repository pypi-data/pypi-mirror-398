import json,os
from deepKernel import base,information
from PIL import Image,ImageEnhance
import numpy as np
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

def enhance_image(input_image, brightness=1.0, contrast=1.0, color=1.0, sharpness=1.0):
    img = input_image
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if color != 1.0:
        img = ImageEnhance.Color(img).enhance(color)
    if sharpness != 1.0:
        img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img

def process_row(args: Tuple[np.ndarray, int, int]) -> Tuple[int, np.ndarray]:
    img_array, start_row, end_row = args
    for row in range(start_row, end_row):
        white_pixels = np.all(img_array[row, :, :3] == 255, axis=1)
        img_array[row, white_pixels, 3] = 0
    return start_row, img_array[start_row:end_row]

def png_process_multithread(pngpath: str, thread_num: int = 4) -> None:
    img = Image.open(pngpath).convert('RGBA')
    imgx, imgy = img.size
    img_array = np.array(img)
    thread_num = min(thread_num, imgy)
    rows_per_thread = imgy // thread_num
    remaining_rows = imgy % thread_num
    tasks = []
    current_row = 0
    for i in range(thread_num):
        end_row = current_row + rows_per_thread + (1 if i == thread_num - 1 else 0)
        end_row = min(end_row, imgy)
        tasks.append((img_array, current_row, end_row))
        current_row = end_row
    results = []
    with ThreadPoolExecutor(max_workers=thread_num) as executor:
        future_to_task = {executor.submit(process_row, task): task for task in tasks}
        for future in as_completed(future_to_task):
            results.append(future.result())
    results.sort(key=lambda x: x[0])
    processed_array = np.vstack([result[1] for result in results])
    img_processed = Image.fromarray(processed_array)
    img_enhanced = enhance_image(img_processed, 0.9, 0.9, 1.2, 1.5)
    img_enhanced.save(pngpath)

def png_process(pngpath: str) -> None:
    png_process_multithread(pngpath, thread_num=8)

def save_gerber( job:str, step:str, layer:str, filename:str,  resize:int=0, angle:float=0, 
                scalingX:float=1, scalingY:float=1, mirror:bool=False, rotate:bool=False, 
                scale:bool=False, cw:bool=False,  mirrorpointX:int=0, mirrorpointY:int=0, 
                rotatepointX:int=0, rotatepointY:int=0, scalepointX:int=0, scalepointY:int=0, 
                mirrorX:bool = False, mirrorY:bool = False, numberFormatL:int=2, 
                numberFormatR:int=6, zeros:int=0, unit:int=0)->bool:
    try:
        _type = 0
        gdsdbu = 0.01
        profiletop = False
        cutprofile = True
        isReverse = False
        cut_polygon = []
        if scalingX == 0:
            scalingX == 1
        if scalingY == 0:
            scalingY == 1
        if mirrorX == True and mirrorY ==True:
            mirrordirection = 'XY'
        elif mirrorX==True and mirrorY ==False:
            mirrordirection = 'Y'
        elif mirrorX==False and mirrorY ==True:
            mirrordirection = 'X'
        else:
            mirrordirection = 'NO'
        _ret = base.layer_export(job, step, layer, _type, filename, gdsdbu, resize, angle, scalingX, scalingY, isReverse,
                    mirror, rotate, scale, profiletop, cw, cutprofile, mirrorpointX, mirrorpointY, rotatepointX,
                    rotatepointY, scalepointX, scalepointY, mirrordirection, cut_polygon,numberFormatL,numberFormatR,
                    zeros,unit)
        ret = json.loads(_ret)['status']
        if ret == 'true':
            ret = True
        else:
            ret = False
        return ret
    except Exception as e:
        print(e)
    return False

def save_job(job:str,path:str)->bool:
    try:
        layers = information.get_layers(job)
        steps = information.get_steps(job)
        for step in steps:
            for layer in layers:
                base.load_layer(job,step,layer)
        base.save_job_as(job,path)
        return True
    except Exception as e:
        print(e)
    return False

def save_png(job:str, step:str, layers:list,picpath:str, layercolors:list,size,drawSR=False)->bool:
    try:
        (picfolder,picname) = os.path.split(picpath)
        backcolor=[255,255,255,255]
        layer_box = json.loads(base.layer_box(job,step,layers))['paras']
        xmin = layer_box['xmin']
        ymin = layer_box['ymin']
        xmax = layer_box['xmax']
        ymax = layer_box['ymax']
        _ret = base.save_true_png(job,step,layers,xmin,ymin,xmax,ymax,picfolder,picname,backcolor,layercolors,drawSR,size)
        png_process(picpath)
        ret = json.loads(_ret)['status']
        return ret
    except Exception as e:
        print(e)
    return False

def save_dxf(job:str,step:str,layers:list,savePath:str)->bool:
    try:
        _ret = base.dxf2file(job,step,layers,savePath)
        ret = json.loads(_ret)['paras']['result']
        return ret
    except Exception as e:
        print(e)
    return False