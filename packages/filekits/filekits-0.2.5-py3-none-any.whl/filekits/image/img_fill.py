# import cv2
# import numpy as np
import random
from typing import Literal
from PIL import Image
from ..base_io import load_image

def paste_image( original_image , paste_img , box , backend: Literal["PIL"] = "PIL" ) -> Image.Image:
    original_image = load_image( original_image , backend )
    paste_img = load_image( paste_img , backend )

    if backend == "PIL" :
        rounded_box = tuple( round( element ) if isinstance( element , float ) else element for element in box )
        # isinstance(element, float) 是用来判断元素是否为浮点数类型，如果是则执行四舍五入操作，否则保持原样。
        original_image.paste( paste_img , rounded_box )

    # todo 下面这段代码存在问题，无法使用：ValueError: could not broadcast input array from shape (800,800,3) into shape (371,800,3)
    # elif backend == "cv2" and len( box ) == 4 :
    #     startX , startY , endX , endY = box[ 0 ] , box[ 1 ] , box[ 2 ] , box[ 3 ]
    #     # 计算偏移量
    #     offsetX , offsetY = endX - startX , endY - startY
    #     # 创建仿射变换矩阵
    #     matrix = np.float32( [ [ 1 , 0 , offsetX ] , [ 0 , 1 , offsetY ] ] )
    #     # 应用仿射变换
    #     transformed_image = cv2.warpAffine( paste_img , matrix ,
    #                                         (original_image.shape[ 1 ] , original_image.shape[ 0 ]) )
    #     # 将变换后的图像粘贴到原图像上
    #     # original_image[ startY :endY, startX :endX ] = transformed_image
    #     original_image[ round( startY ) :round( endY ) , round( startX ) :round( endX ) ] = transformed_image

    return original_image


# 在图像的四角随机一处添加水印
def paste_logo( image_path , logo_path , output_path, choice=[ 'top_left' , 'top_right' ] ) :
    """
    Args:
        image_path (str): 原始图像路径
        logo_path (str): 水印图像路径
        output_path (str): 输出图像路径
        choice (list, optional): 选择添加水印的位置，默认为 ['top_left', 'top_right'],
            可选:['top_left', 'top_right', 'bottom_left', 'bottom_right']
    """
    image = Image.open( image_path )
    logo = Image.open( logo_path )
    width , height = image.size
    logo_width , logo_height = logo.size

    # 考虑到10px的边距
    margin = 10

    # 随机选择一个四角位置
    corner = random.choice( choice )
    if corner == 'top_left' :
        x = y = margin
    elif corner == 'top_right' :
        x = width - logo_width - margin
        y = margin
    elif corner == 'bottom_left' :
        x = margin
        y = height - logo_height - margin
    else :
        x = width - logo_width - margin
        y = height - logo_height - margin

    # 在选定的位置粘贴水印
    image = paste_image( image , logo , (x , y) , "PIL" )
    # 保存修改后的图像
    image.save( output_path )
    image.close()
    logo.close()

    return output_path

