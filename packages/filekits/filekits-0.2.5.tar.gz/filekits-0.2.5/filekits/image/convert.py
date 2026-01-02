import os
from PIL import Image

# 转换图片为jpg
def to_jpg( image_path , output_folder = "" , image_name = "" , delete_origin = True ) :
    """
    将各种格式的图片转换为 JPG 格式（增强版，支持 GIF、PNG、WebP 等）

    参数:
    image_path (str): 输入图片文件的完整路径
    output_folder (str): 输出文件夹路径，默认为空（使用原文件所在文件夹）
    image_name (str): 图片文件名，默认为空（使用原文件名的base_name）
    delete_origin (bool): 是否删除原始文件，默认为 True

    返回:
    str: 转换后的 JPG 文件路径
    """
    try :
        # 处理默认参数：如果output_folder或image_name为空，使用原文件信息
        if not output_folder or not image_name :
            original_dir = os.path.dirname( image_path )
            original_filename = os.path.basename( image_path )

            if not output_folder :
                output_folder = original_dir
            if not image_name :
                image_name = original_filename

        # 先检查文件扩展名
        file_ext = image_name.lower()
        has_jpg_extension = file_ext.endswith( '.jpg' ) or file_ext.endswith( '.jpeg' )

        # 打开图片
        with Image.open( image_path ) as img :
            # 如果扩展名不是jpg/jpeg，直接转换，不需要检测格式
            if not has_jpg_extension :
                # print( f"{image_path} 扩展名不是JPG格式，需要转换" )
                pass
            else :
                # 扩展名是jpg/jpeg时，检测实际格式
                actual_format = img.format
                if actual_format == 'JPEG' :
                    # print( f"{image_path} 已经是 JPG 格式，无需转换" )
                    return image_path
                else :
                    print( f"{image_path} 扩展名为JPG但实际格式为{actual_format}，需要转换" )

            # 确保输出文件夹存在
            if output_folder :  # 只有当output_folder不为空时才创建
                os.makedirs( output_folder , exist_ok = True )
            # 获取图片的文件名（不包含扩展名）
            base_name = os.path.splitext( image_name )[ 0 ]
            # 新的图片路径，扩展名为.jpg
            new_image_path = os.path.join( output_folder , base_name + '.jpg' )

            # 根据不同的图片模式进行处理
            if img.mode in [ 'RGBA' , 'LA' ] :
                # 处理带透明通道的图片（PNG、GIF等）
                # 创建一个白色背景的图片
                background = Image.new( 'RGB' , img.size , (255 , 255 , 255) )

                if img.mode == 'RGBA' :
                    # RGBA模式：使用alpha通道作为mask
                    background.paste( img , mask = img.split()[ 3 ] )
                elif img.mode == 'LA' :
                    # LA模式：使用alpha通道作为mask
                    background.paste( img , mask = img.split()[ 1 ] )

                processed_img = background

            elif img.mode == 'P' :
                # 处理调色板模式的图片（部分GIF）
                if 'transparency' in img.info :
                    # 如果有透明色，先转换为RGBA再处理透明背景
                    rgba_img = img.convert( 'RGBA' )
                    background = Image.new( 'RGB' , rgba_img.size , (255 , 255 , 255) )
                    background.paste( rgba_img , mask = rgba_img.split()[ 3 ] )
                    processed_img = background
                else :
                    # 没有透明色，直接转换为RGB
                    processed_img = img.convert( 'RGB' )

            elif img.mode in [ 'L' , 'CMYK' ] :
                # 处理灰度图像和CMYK图像
                processed_img = img.convert( 'RGB' )

            elif img.mode == 'RGB' :
                # 已经是RGB模式，直接使用
                processed_img = img

            else :
                # 其他模式统一转换为RGB
                processed_img = img.convert( 'RGB' )

            # 如果需要删除原始文件
            if delete_origin :
                try :
                    os.remove( image_path )
                    # print(f"{image_path} 已删除。")
                except Exception as e :
                    print( f"{image_path} 删除失败: {str( e )}" )

            # 保存为JPG格式，使用最高质量设置
            processed_img.save( new_image_path , 'JPEG' , quality = 100 , optimize = True )
            print( f"{image_path} 已被转换为 {new_image_path}" )

            return new_image_path

    except Exception as e :
        print( f"转换失败: {image_path} -> {str( e )}" )
        return image_path  # 转换失败时返回原路径
