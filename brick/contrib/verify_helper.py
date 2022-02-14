#!/usr/bin/env python
# coding=utf-8

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# from common import random_helper, file_helper, log_helper

# def create_verify_code(length = 4, size=(100, 40), img_type='jpg',
#                         mode='RGB', bg_color=(255, 255, 255), fg_color=(0, 0, 255),
#                         font_size=19, font_type='/data/www/simple_interface/static/arial.ttf',
#                         draw_lines=True, n_line=(2, 5),
#                         draw_points=True, point_chance=5):
#     """
#     生成验证码图片
#     :param length: 生成验证码数量
#     :param size: 生成图片的宽和高
#     :param img_type: 生成图片类型
#     :param mode: 图片模式
#     :param bg_color: 背景颜色
#     :param fg_color: 字体颜色
#     :param font_size: 字体大小
#     :param font_type: 验证码字体，linux系统里需要绝对路径
#     :param draw_lines: 是否绘制干扰线
#     :param n_line: 干扰线数量
#     :param draw_points: 是否绘制干扰点
#     :param point_chance: 干扰点数量
#     :return:
#     """
#     width, height = size
#     img = Image.new(mode, size, bg_color)
#     draw = ImageDraw.Draw(img)
#
#     def create_line():
#         line_num = random_helper.get_number_for_range(n_line[0], n_line[1])
#
#         for i in range(line_num):
#             begin = (random_helper.get_number_for_range(0, size[0]), random_helper.get_number_for_range(0, size[1]))
#             end = (random_helper.get_number_for_range(0, size[0]), random_helper.get_number_for_range(0, size[1]))
#             draw.line([begin, end], fill=(0, 0, 0))
#
#     def create_points():
#         chance = min(100, max(0, int(point_chance)))
#         for w in range(width):
#             for h in range(height):
#                 tmp = random_helper.get_number_for_range(0, 100)
#                 if tmp > 100 - chance:
#                     draw.point((w, h), fill=(0, 0, 0))
#
#     def create_strs():
#         c_chars = random_helper.get_string(length)
#         strs = ' %s ' % ' '.join(c_chars)
#         log_helper.info(font_type)
#         log_helper.info(file_helper.exists(font_type))
#         font = ImageFont.truetype(font_type, font_size)
#         font_width, font_height = font.getsize(strs)
#         draw.text(((width - font_width) / 3, (height - font_height) / 3),
#                   strs, font=font, fill=fg_color)
#         return ''.join(c_chars)
#
#     if draw_lines:
#         create_line()
#     if draw_points:
#         create_points()
#     strs = create_strs()
#
#     params = [1 - float(random_helper.get_number_for_range(1, 2)) / 100,
#               0,
#               0,
#               0,
#               1 - float(random_helper.get_number_for_range(1, 10)) / 100,
#               float(random_helper.get_number_for_range(1, 2)) / 500,
#               0.001,
#               float(random_helper.get_number_for_range(1, 2)) / 500
#               ]
#     img = img.transform(size, Image.PERSPECTIVE, params)
#     img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
#     return img, strs

# if __name__ == '__main__':
#     code_img,capacha_code= create_verify_code()
#     code_img.save('xx_' + random_helper.get_string(3) + '.jpg','JPEG')
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

_letter_cases = "abcdefghjkmnpqrstuvwxy"  # 小写字母，去除可能干扰的i，l，o，z
_upper_cases = _letter_cases.upper()  # 大写字母
_numbers = ''.join(map(str, range(3, 10)))  # 数字
init_chars = ''.join((_letter_cases, _upper_cases, _numbers))


def create_validate_code(size=(120, 30),
                         chars=init_chars,
                         img_type="GIF",
                         mode="RGB",
                         bg_color=(255, 255, 255),
                         fg_color=(0, 0, 255),
                         font_size=20,
                         font_type="arial.ttf",
                         length=4,
                         draw_lines=True,
                         n_line=(1, 3),
                         draw_points=True,
                         point_chance=2):
    """
    @todo: 生成验证码图片
    @param size: 图片的大小，格式（宽，高），默认为(120, 30)
    @param chars: 允许的字符集合，格式字符串
    @param img_type: 图片保存的格式，默认为GIF，可选的为GIF，JPEG，TIFF，PNG
    @param mode: 图片模式，默认为RGB
    @param bg_color: 背景颜色，默认为白色
    @param fg_color: 前景色，验证码字符颜色，默认为蓝色#0000FF
    @param font_size: 验证码字体大小
    @param font_type: 验证码字体，默认为 ae_AlArabiya.ttf
    @param length: 验证码字符个数
    @param draw_lines: 是否划干扰线
    @param n_lines: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
    @param draw_points: 是否画干扰点
    @param point_chance: 干扰点出现的概率，大小范围[0, 100]
    @return: [0]: PIL Image实例
    @return: [1]: 验证码图片中的字符串
    """

    width, height = size  # 宽高
    # 创建图形
    img = Image.new(mode, size, bg_color)
    draw = ImageDraw.Draw(img)  # 创建画笔

    def get_chars():
        """生成给定长度的字符串，返回列表格式"""
        return random.sample(chars, length)

    def create_lines():
        """绘制干扰线"""
        line_num = random.randint(*n_line)  # 干扰线条数

        for i in range(line_num):
            # 起始点
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            # 结束点
            end = (random.randint(0, size[0]), random.randint(0, size[1]))
            draw.line([begin, end], fill=(0, 0, 0))

    def create_points():
        """绘制干扰点"""
        chance = min(100, max(0, int(point_chance)))  # 大小限制在[0, 100]

        for w in range(width):
            for h in range(height):
                tmp = random.randint(0, 100)
                if tmp > 100 - chance:
                    draw.point((w, h), fill=(0, 0, 0))

    def create_strs():
        """绘制验证码字符"""
        c_chars = get_chars()
        strs = ' %s ' % ' '.join(c_chars)  # 每个字符前后以空格隔开

        font = ImageFont.truetype(font_type, font_size)
        font_width, font_height = font.getsize(strs)

        draw.text(((width - font_width) / 3, (height - font_height) / 3),
                  strs, font=font, fill=fg_color)

        return ''.join(c_chars)

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    strs = create_strs()

    # 图形扭曲参数
    params = [1 - float(random.randint(1, 2)) / 100,
              0,
              0,
              0,
              1 - float(random.randint(1, 10)) / 100,
              float(random.randint(1, 2)) / 500,
              0.001,
              float(random.randint(1, 2)) / 500
              ]
    img = img.transform(size, Image.PERSPECTIVE, params)  # 创建扭曲

    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)  # 滤镜，边界加强（阈值更大）

    return img, strs


# 获取拖动图形验证码
def GetPicVerify():
    backpng = './background.png'
    shapng = './shape.png'
    # 加载背景图片与形状图片
    background = Image.open(backpng)
    shape = Image.open(shapng)
    # 获取图片像素，并随机设置背景图片中哪个像素开始截取图片
    # 该位置可以你保存到后台，前台拖动图片时，传入匹配的妈化像素值到后台校验
    # 后台校验输入的像素位置，也就是校验输入的验证码
    ranglen = background.width - 2 * shape.width
    pos = shape.width + random.randint(10, ranglen)
    # 初始化获取形状[0,0]处像素
    shapebackpixel = shape.getpixel((0, 0))
    for i in range(0, shape.width):
        for j in range(0, shape.height):
            pixel = shape.getpixel((i, j))
            # 与形状像素（0，0）处相同，不用设置像素
            if pixel == shapebackpixel:
                continue
            backpixel = background.getpixel((pos + i, j))
            pixel = list(pixel)
            backpixel = list(backpixel)
            # 设置形状
            pixel[0] = backpixel[0]
            pixel[1] = backpixel[1]
            pixel[2] = backpixel[2]
            shape.putpixel((i, j), tuple(pixel))
            # 设置背景
            alpha = pixel[3] * 1.0 / 0xff
            backpixel[0] = int((1 - alpha) * backpixel[0] + alpha * 0xff)
            backpixel[1] = int((1 - alpha) * backpixel[1] + alpha * 0xef)
            backpixel[2] = int((1 - alpha) * backpixel[2] + alpha * 0xdb)
            backpixel[3] = int((0xff * 0xff - (0xff - backpixel[3]) * (0xff - pixel[3])) / 0xff)
            background.putpixel((pos * i, j), tuple(backpixel))
    # 保存生成的图片
    # background.save('./background_captcha.png', 'PNG')
    # background.close()
    # shape.save('./shape-captcha.png', 'PNG')
    # shape.colse()
    return background, shape, pos


#
# from PIL import Image,ImageDraw,ImageFont,ImageFilter
# import random,string
# #获取随机4个字符组合
# def getRandomChar():
#     chr_all = string.ascii_letters+string.digits
#     chr_4 = ''.join(random.sample(chr_all,4))
#     return chr_4
# #获取随机颜色
# def getRandomColor(low,high):
#     return (random.randint(low,high),random.randint(low,high),random.randint(low,high))
# #制作验证码图片
# def getPicture():
#     width,height = 180,60
#     #创建空白画布
#     image = Image.new('RGB',(width,height),getRandomColor(20,100))
#     #验证码的字体
#     font = ImageFont.truetype('C:/Windows/fonts/stxinwei.ttf',40)
#     #创建画笔
#     draw = ImageDraw.Draw(image)
#     #获取验证码
#     char_4 = getRandomChar()
#     #向画布上填写验证码
#     for i in range(4):
#         draw.text((40*i+10,0),char_4[i],font = font,fill=getRandomColor(100,200))
#     #绘制干扰点
#     for x in range(random.randint(200,600)):
#         x = random.randint(1,width-1)
#         y = random.randint(1,height-1)
#         draw.point((x,y),fill=getRandomColor(50,150))
#     #模糊处理
#     image = image.filter(ImageFilter.BLUR)
#     image.save('./%s.jpg' % char_4)

if __name__ == '__main__':
    # code_img,capacha_code= create_validate_code()
    # # code_img.save('xx_' + random_helper.get_string(3) + '.jpg','JPEG')
    # code_img.show()
    code_img,shape_img,pos=GetPicVerify()
    code_img.show(), shape_img.show(), print( pos)
