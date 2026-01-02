import cv2
import numpy as np


# 删除png图片的透明区域
def crop_transparent( image_path , turn_jpg: bool = False ) :
    # 读取图片，包括 alpha 通道
    img = cv2.imread( image_path , cv2.IMREAD_UNCHANGED )
    # 找到图片中的非透明部分
    coords = np.argwhere( img[ ... , 3 ] )
    # 计算非透明部分的边界
    x0 , y0 = coords.min( axis = 0 )
    x1 , y1 = coords.max( axis = 0 ) + 1
    # 裁剪图片
    cropped_img = img[ x0 :x1 , y0 :y1 ]
    if cropped_img.size != 0 :
        # 保存裁剪后的图片
        if turn_jpg is False :
            cv2.imwrite( image_path , cropped_img )
        else :
            # 将透明背景转换为白色
            alpha_channel = cropped_img[ : , : , 3 ]
            _ , mask = cv2.threshold( alpha_channel , 0 , 255 , cv2.THRESH_BINARY )  # binarize mask
            color = cropped_img[ : , : , :3 ]
            new_img = cv2.bitwise_not( cv2.bitwise_not( color , mask = mask ) )
            image_path = image_path.rsplit( '.' , 1 )[ 0 ] + '.jpg'
            cv2.imwrite( image_path , new_img )

    return image_path

