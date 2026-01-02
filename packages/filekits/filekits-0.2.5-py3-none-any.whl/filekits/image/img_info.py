# 判断颜色是否为深色
def is_dark_color( rgb ) :
    # 简单亮度判断公式，可根据需要调整
    brightness = sum( rgb ) / 3
    return brightness < 128