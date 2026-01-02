import os
from PIL import Image , ImageDraw , ImageFont , ImageStat
from .img_info import is_dark_color


# 画出mask图像
def draw_mask( image_path , modify_info , output_folder , output_path , expansion_area = 200 ) :
    startX = modify_info[ 'startX' ]
    startY = modify_info[ 'startY' ]
    endX = modify_info[ 'endX' ]
    endY = modify_info[ 'endY' ]

    # 这里不能使用with
    img = Image.open( image_path )
    width , height = img.size

    if expansion_area == 0 :
        # 创建一个全黑的图片，与原始图片大小相同
        black_image = Image.new( 'RGB' , (width , height) , color = (0 , 0 , 0) )
        cropped_img_path = new_area = ""
    else :
        # 扩展mask指定像素的区域
        new_startX = max( 0 , startX - expansion_area )
        new_startY = max( 0 , startY - expansion_area )
        new_endX = min( width , endX + expansion_area )
        new_endY = min( height , endY + expansion_area )

        new_area = {
            'startX' : new_startX ,
            'startY' : new_startY ,
            'endX'   : new_endX ,
            'endY'   : new_endY
        }
        # 裁剪出这部分区域，注意 在PIL库中，.crop() 裁剪操作会保留原有图像的数据和模式
        cropped_img = img.crop( (new_startX , new_startY , new_endX , new_endY) )
        # 确保转换为 RGB 模式
        cropped_img = cropped_img.convert( 'RGB' )
        # 创建一个全黑的图片，与裁剪后的图片大小相同
        black_image = Image.new( 'RGB' , cropped_img.size , color = (0 , 0 , 0) )

        startX = startX - new_startX
        startY = startY - new_startY
        endX = endX - new_startX
        endY = endY - new_startY

        # 保存裁剪后的图片
        cropped_img_path = os.path.join( output_folder , "cropped_image.jpg" )
        cropped_img.save( cropped_img_path )

    # 创建一个可以在图片上绘制的对象
    draw = ImageDraw.Draw( black_image )

    # 确保矩形有效：即右下角的坐标应该大于或等于左上角的坐标。
    startX , endX = min( startX , endX ) , max( startX , endX )
    startY , endY = min( startY , endY ) , max( startY , endY )

    # 在指定区域绘制一个白色的矩形
    draw.rectangle( [ (startX , startY) , (endX , endY) ] , fill = (255 , 255 , 255) )

    black_image.save( output_path )

    # 关闭原始图像文件
    img.close()

    return cropped_img_path , new_area


def add_text( img_path , box_infos , font_path , output_path = 'add_text.jpg' ) :
    """
    将文字添加到图片的指定区域，自动选择横向或纵向排列。
    """
    if isinstance( img_path , str ) :
        image = Image.open( img_path )
    else :
        image = img_path

    draw = ImageDraw.Draw( image )

    for box_info in box_infos :
        text = box_info[ "text_translated" ]
        box = box_info[ "box" ]

        # 计算边界框
        left_x = min( [ point[ 0 ] for point in box ] )
        right_x = max( [ point[ 0 ] for point in box ] )
        top_y = min( [ point[ 1 ] for point in box ] )
        bottom_y = max( [ point[ 1 ] for point in box ] )

        box_width = box_info[ "width" ]
        box_height = box_info[ "height" ]
        wh_ratio = box_width / box_height

        # 选择字体
        short_side = box_info[ "short_side" ]
        font_file = font_path[ "Bold" ] if short_side >= 30 else font_path[ "Medium" ]

        # 获取背景颜色并决定文字颜色
        box_crop = image.crop( (left_x , top_y , right_x , bottom_y) )
        stat = ImageStat.Stat( box_crop )
        avg_color = stat.mean[ :3 ]
        font_color = (255 , 255 , 255) if is_dark_color( avg_color ) else (0 , 0 , 0)

        # 判断是横向还是纵向,准备文本
        if wh_ratio < 0.5 :
            # 纵向排列时将文本转为竖排
            display_text = '\n'.join( text )
        else :
            display_text = text

        # 寻找合适的字体大小
        found_fit = False

        # 二分查找适合的字体大小
        min_size = 2
        max_size = 50
        current_font_size = 20

        while min_size <= max_size :
            mid_size = (min_size + max_size) // 2
            font = ImageFont.truetype( font_file , mid_size )

            # 计算文本尺寸
            left , top , right , bottom = draw.textbbox( (0 , 0) , display_text , font = font )
            text_width = right - left
            text_height = bottom - top

            # 检查是否适合
            if text_width <= box_width and text_height <= box_height :
                # 找到一个合适的大小，尝试更大的
                found_fit = True
                min_size = mid_size + 1
                current_font_size = mid_size
            else :
                # 太大了，尝试更小的
                max_size = mid_size - 1

        # 如果找到合适的大小，绘制文本
        if found_fit :
            font = ImageFont.truetype( font_file , current_font_size )

            # 计算最终文本尺寸
            left , top , right , bottom = draw.textbbox( (0 , 0) , display_text , font = font )
            # text_width = right - left
            text_height = bottom - top

            # 文字位置：靠左对齐、垂直居中
            # center_x = (left_x + right_x) / 2
            # x = int( center_x - text_width / 2 )
            center_y = (top_y + bottom_y) / 2
            x = int( left_x )
            y = int( center_y - text_height / 2 )

            # 绘制文本
            draw.text( (x , y) , display_text , font = font , fill = font_color )

    image.save( output_path )
    return output_path


def draw_mask_by_box( img_path , boxes , output_path , expansion_box = 20 ) :
    """
    绘制mask：将整张图片填充为黑色，指定形状区域填充为白色。

    :param img_path: 输入图片路径
    :param boxes: 指定形状的点列表，格式为 [[(x1, y1), (x2, y2), ..., (xn, yn)], ...]
    :param output_path: 输出图片路径
    :param expansion_box: 要扩展的像素数，默认为20
    """
    # 打开图像
    image = Image.open( img_path )
    width , height = image.size

    # 创建一个全黑的图片，与原始图片大小相同
    mask_image = Image.new( 'RGB' , (width , height) , color = (0 , 0 , 0) )
    draw = ImageDraw.Draw( mask_image )

    # 绘制每个框
    for i , box in enumerate( boxes ) :
        # 找到多边形的中心点
        x_coords = [ p[ 0 ] for p in box ]
        y_coords = [ p[ 1 ] for p in box ]

        # 计算各个方向的扩展量
        # 向四周扩展指定的像素
        expanded_points = [ ]
        for point in box :
            x , y = point
            # 计算点到中心的向量
            center_x = sum( x_coords ) / len( x_coords )
            center_y = sum( y_coords ) / len( y_coords )

            # 计算方向向量
            dir_x = x - center_x
            dir_y = y - center_y

            # 如果点在中心，则不需要扩展方向
            if abs( dir_x ) < 1e-6 and abs( dir_y ) < 1e-6 :
                expanded_x , expanded_y = x , y
            else :
                # 计算单位向量
                dist = (dir_x ** 2 + dir_y ** 2) ** 0.5
                norm_x , norm_y = dir_x / dist , dir_y / dist

                # 扩展点
                expanded_x = x + norm_x * expansion_box
                expanded_y = y + norm_y * expansion_box

            # 确保不超出图片范围
            expanded_x = max( 0 , min( width - 1 , expanded_x ) )
            expanded_y = max( 0 , min( height - 1 , expanded_y ) )

            expanded_points.append( (expanded_x , expanded_y) )

        # 在指定区域绘制一个白色的形状
        draw.polygon( expanded_points , fill = (255 , 255 , 255) )

    # 保存图像到新的文件
    if output_path != "" :
        mask_image.save( output_path )
        return output_path
    else :
        return mask_image