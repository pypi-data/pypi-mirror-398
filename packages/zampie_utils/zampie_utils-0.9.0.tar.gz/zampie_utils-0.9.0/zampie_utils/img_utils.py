# from PIL import Image, ImageDraw, ImageColor, ImageFont
# import pandas as pd

# from rich import print
# from rich.progress import track
# from pathlib import Path
# import json5

# font_path = "方正黑体简体.ttf"  # 需要中文字体
# # https://github.com/wordshub/free-font?tab=readme-ov-file 有很多免费字体
# font_size = 20
# font = ImageFont.truetype(font_path, font_size)

# def denormalize_box(bbox, img_height, img_width, std_height=1000, std_width=1000):
#     xmin, ymin, xmax, ymax = bbox
#     height_ratio = img_height / std_height
#     width_ratio = img_width / std_width
#     xmin = int(xmin * width_ratio)
#     xmax = int(xmax * width_ratio)
#     ymin = int(ymin * height_ratio)
#     ymax = int(ymax * height_ratio)
#     return [xmin, ymin, xmax, ymax]


# def calculate_iou(bbox1, bbox2):
#     """
#     计算两个矩形的IoU
#     box: [x1, y1, x2, y2] (左上角坐标和右下角坐标)
#     """
#     # 确定交集矩形的坐标
#     x_left = max(bbox1[0], bbox2[0])
#     y_top = max(bbox1[1], bbox2[1])
#     x_right = min(bbox1[2], bbox2[2])
#     y_bottom = min(bbox1[3], bbox2[3])

#     # 检查是否有交集
#     if x_right < x_left or y_bottom < y_top:
#         return 0.0

#     # 计算交集和并集面积
#     intersection_area = (x_right - x_left) * (y_bottom - y_top)
#     area_box1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
#     area_box2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
#     union_area = area_box1 + area_box2 - intersection_area

#     # 计算IoU
#     iou = intersection_area / union_area
#     return iou


# def draw_text_with_stroke(img, position, text, font, text_color=ImageColor.getrgb("white"), stroke_color=ImageColor.getrgb("black"), stroke_width=2):
#     """
#     绘制带描边效果的文本
    
#     Args:
#         draw: ImageDraw对象
#         position: 文本位置，格式为(x, y)
#         text: 要绘制的文本内容
#         font: 字体对象
#         text_color: 文本颜色
#         stroke_color: 描边颜色
#         stroke_width: 描边宽度
#     """
#     draw = ImageDraw.Draw(img)

#     x, y = position
#     # 先绘制描边（在原始位置的四周多次绘制文本）
#     for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
#         draw.text((x + dx * stroke_width, y + dy * stroke_width), 
#                 text, fill=stroke_color, font=font)
    
#     # 然后绘制主文本
#     draw.text((x, y), text, fill=text_color, font=font)


# def draw_bbox(img, bbox, label="", color=ImageColor.getrgb("white"), stroke_width=2):
#     xmin, ymin, xmax, ymax = bbox

#     draw = ImageDraw.Draw(img)
#     draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=2)

#     if label:
#         draw_text_with_stroke(
#             img=img,
#             position=(xmin, ymin),
#             text=label,
#             font=font,
#             text_color=color,
#             stroke_color=ImageColor.getrgb("black"),
#             stroke_width=stroke_width
#         )

#     return img
