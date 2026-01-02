# 图像处理模块
# 提供图片格式转换、绘制、裁剪、缩放等图像处理功能

# 图片格式转换
from .convert import to_jpg

# 图片绘制相关
from .draw import draw_mask, add_text

# 图片裁剪相关
from .img_crop import crop_transparent

# 图片填充/合成相关
from .img_fill import paste_image, paste_logo

# 图片信息获取
from .img_info import is_dark_color

# 图片缩放相关
from .img_scale import scale_image

# 定义 __all__ 列表，明确指定哪些符号会被导出
__all__ = [
    # 图片格式转换
    'to_jpg',
    
    # 图片绘制相关
    'draw_mask',
    'add_text',
    
    # 图片裁剪相关
    'crop_transparent',
    
    # 图片填充/合成相关
    'paste_image',
    'paste_logo',
    
    # 图片信息获取
    'is_dark_color',
    
    # 图片缩放相关
    'scale_image'
]