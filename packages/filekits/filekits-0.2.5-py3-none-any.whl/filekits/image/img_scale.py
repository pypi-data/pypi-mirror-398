from PIL import Image


# 将第2张图片 强制缩放到和第一张图片一样大小
def scale_image( path_1 , path_2 ) :
    with Image.open( path_1 ) as img1 :
        width1 , height1 = img1.size

    with Image.open( path_2 ) as img2 :
        width2 , height2 = img2.size
        if width1 == width2 or height1 == height2 :
            return
        print( f"图片对比尺寸不一致：\n{path_1} 尺寸: {width1}x{height1} \n{path_2} 尺寸: {width2}x{height2}" )
        # 强制缩放到第一个图片的尺寸
        img2_resized = img2.resize( (width1 , height1) , resample = Image.BICUBIC )
        # 保存缩放后的图片
        img2_resized.save( path_2 )
        return