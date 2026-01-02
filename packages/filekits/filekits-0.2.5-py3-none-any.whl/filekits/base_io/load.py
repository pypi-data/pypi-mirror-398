import json
import yaml
import base64
import openpyxl
import pandas as pd
import numpy as np

import cv2
from PIL import Image
from typing import Union, overload, Literal


# 读取txt文档，返回列表
def load_txt(file_path, lower_list=0, return_type="list"):
    f = open(file_path, "r", encoding='utf-8')
    text = f.read()
    f.close()
    if return_type == "str":
        return text
    else:
        my_list = text.split("\n")
        if lower_list == 1:  # 转换为小写
            new_list = [word.lower() for word in my_list]
            return new_list
        else:
            return my_list


# 读取yaml文件
def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data


# 读取Excel文件，返回pandas.DataFrame 或者 sheet
def load_excel(file_path, return_type, sheet_name=None, skiprows=0, header=0):
    '''
    for i in range (2 , num+1) :  # 第1行是 标题，所以从第2行开始
        sku = sheet.cell (i , 2).value
    '''
    if return_type == "sheet":
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        if sheet is not None:
            num = sheet.max_row
        else:
            num = 0
        print("共有行：{}".format(num))
        return wb, sheet, num
    elif return_type == "df":
        if sheet_name is None:
            sheet_name = 0
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header,
                            skiprows=skiprows if skiprows != 0 else None)
        return df
    else:
        raise ValueError("return_type参数错误！")


# 读取json文件，返回字典
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


# 读取任意文件转为 base64 编码
def load_base64(file_path):
    with open(file_path, "rb") as file:
        file_data = file.read()
    base64_data = base64.b64encode(file_data).decode('utf-8')
    return base64_data


# 读取图像
# 使用 @overload 装饰器进行类型重载，以便静态类型检查器（如 Pyright）
# 能够根据 backend 参数的值精确推断返回类型，避免类型检查错误
@overload
def load_image( image_path , backend: Literal["PIL"] = "PIL" ) -> Image.Image : ...

@overload
def load_image( image_path , backend: Literal["cv2"] ) -> np.ndarray : ...

def load_image( image_path , backend="PIL" ) -> Union[Image.Image, np.ndarray] :
    """
    读取图像文件或处理图像对象
    
    Args:
        image_path: 图像文件路径(str)或图像对象(PIL.Image/np.ndarray)
        backend: 读取后端，可选 "PIL" 或 "cv2"，默认 "PIL"
    
    Returns:
        图像对象
        - PIL图像对象有 mode 属性
        - OpenCV图像(numpy数组)有 shape 属性
    """
    if isinstance( image_path , str ) :
        if backend == "PIL" :
            image = Image.open( image_path )
        elif backend == "cv2" :
            image = cv2.imread( image_path )
        else:
            raise ValueError(f"不支持的读取方法: {backend}. 请使用 'PIL' 或 'cv2'")
    elif hasattr(image_path, 'mode') or hasattr(image_path, 'shape') :
        # 如果 image_path 是图像对象(PIL.Image或np.ndarray)，直接使用
        image = image_path
    else:
        raise TypeError(f"不支持的图像类型: {type(image_path)}. 请提供文件路径或图像对象")
    return image
