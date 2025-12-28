import sys
import time
import cv2
import numpy as np
import cairocffi as cairo
from aabd.image import conv_img


class ImageDrawer:
    def __init__(self, data: np.ndarray, processor='audo', family_name=None):
        self.height, self.width, c = data.shape
        self.processor = processor
        self._ctx = None
        self._surface = None
        if processor == 'cairo':
            self.image_bgr = data
            self.ctx
        else:
            self.image_bgr = np.ascontiguousarray(data)

        if family_name is None:
            if sys.platform == "win32":
                # family_name = "Alibaba PuHuiTi 3.0"
                family_name = "Microsoft YaHei"
            else:
                # apt install fonts-noto-cjk
                family_name = "Noto Sans CJK SC"
        self.family_name = family_name

    @property
    def ctx(self):
        if self._ctx is None:
            self.image_bgra = np.concatenate(
                [self.image_bgr, np.full((self.height, self.width, 1), 255, dtype=np.uint8)],
                axis=2)
            stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, self.width)
            self._surface = cairo.ImageSurface.create_for_data(self.image_bgra, cairo.FORMAT_ARGB32,
                                                               self.width, self.height, stride)
            self._ctx = cairo.Context(self._surface)
            self.processor = 'cairo'
        return self._ctx

    @property
    def surface(self):
        if self._surface is None:
            self.ctx
        return self._surface

    @staticmethod
    def cairo_start(image):
        if not isinstance(image, np.ndarray):
            image = conv_img.to_numpy(image, target_normalized=False, target_color_order="BGR", target_dim_order="HWC")
        return ImageDrawer(image, processor='cairo')

    @staticmethod
    def cv_start(image):
        if not isinstance(image, np.ndarray):
            image = conv_img.to_numpy(image, target_normalized=False, target_color_order="BGR", target_dim_order="HWC")
        return ImageDrawer(image, processor='cv2')

    @staticmethod
    def start(image):
        if not isinstance(image, np.ndarray):
            image = conv_img.to_numpy(image, target_normalized=False, target_color_order="BGR", target_dim_order="HWC")
        return ImageDrawer(image)

    def set_font_family(self, family_name):
        self.family_name = family_name
        return self

    def test_text(self):
        pass

    def text(self, text, position, font_size=None, font_color=None, anchor=None, padding=None,
             border_color=None, border_width=None, background_color=None):
        if self.processor == "cv2":
            return self._cv_text(text, position, font_size, font_color, anchor, padding,
                                 border_color, border_width, background_color)
        else:
            return self._cairo_text(text, position, font_size, font_color, anchor, padding,
                                    border_color, border_width, background_color)

    def _cairo_text(self, text, position, font_size=None, font_color=None, anchor=None, padding=None,
                    border_color=None, border_width=None, background_color=None):
        """
        写一行字
        :param text: 文字
        :param position 位置 x,y
        :param font_size: 字体大小
                            >1: 字号
                            <=1: 根据图片的高度定义字体的大小
        :param font_color: 字体的颜色,颜色格式rgb或rgba数据格式list或tuple 默认是红色
        :param anchor: 对齐方式,lt:左上 lm:左中 lb:左下 mt:中上 mm:中中 mb:中下 rt:右上 rm:右中 rb:右下
        :param border_color: 边框颜色, None时无边框, 颜色格式rgb或rgba数据格式list或tuple
        :param border_width: 边框宽度
        :param padding: 字周围间隙
        :param background_color: 背景颜色, None时无背景, 颜色格式rgb或rgba数据格式list或tuple
        :return:
        """
        real_anchor_pos_x, real_anchor_pos_y = position
        if font_size is None:
            font_size = 20
        elif font_size > 1:
            font_size = int(font_size)
        else:
            font_size = min(5, int(font_size * self.height))

        if font_color is None:
            font_color = (255, 255, 255)
        if len(font_color) == 4 and font_color[3] > 1:
            font_color = (*font_color[:3], font_color[3] / 255)
        if anchor is None:
            anchor = "lb"

        if border_color is None and border_width is not None:
            border_color = (255, 0, 0)
        if border_width is None and border_color is not None:
            border_width = 1
        if border_color is not None and len(border_color) == 4 and border_color[3] > 1:
            border_color = (*border_color[:3], border_color[3] / 255)

        if background_color is not None and len(background_color) == 4 and background_color[3] > 1:
            background_color = (*background_color[:3], background_color[3] / 255)
        if padding is None:
            padding_t, padding_b, padding_l, padding_r = 0, 0, 0, 0
        elif isinstance(padding, (list, tuple)) and len(padding) == 4:
            padding_t, padding_b, padding_l, padding_r = padding
        elif isinstance(padding, (list, tuple)) and len(padding) == 2:
            padding_t, padding_b = padding
            padding_l, padding_r = padding
        elif isinstance(padding, int):
            padding_t, padding_b, padding_l, padding_r = padding, padding, padding, padding
        else:
            raise ValueError("Invalid padding")
        self.ctx.select_font_face(self.family_name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.ctx.set_font_size(font_size)

        # 计算文本尺寸
        x_bearing, y_bearing, width, height, x_advance, y_advance = self.ctx.text_extents(text)
        # 真实文本左下角与书写锚定点(0,0)的偏差
        move_lb_offset_x = -x_bearing
        move_lb_offset_y = -(height + y_bearing)
        # 计算书写锚定点的位置 = 真实位置 + 偏移量
        match anchor[0]:
            case "l":
                write_anchor_pos_x = real_anchor_pos_x + move_lb_offset_x + padding_l
                text_box_lt_x = real_anchor_pos_x
            case "m":
                write_anchor_pos_x = real_anchor_pos_x + move_lb_offset_x + (padding_l - width - padding_r) / 2
                text_box_lt_x = real_anchor_pos_x - (width + padding_r + padding_l) / 2
            case "r":
                write_anchor_pos_x = real_anchor_pos_x + move_lb_offset_x - width - padding_r
                text_box_lt_x = real_anchor_pos_x - width - padding_l - padding_r
            case _:
                raise ValueError("Invalid anchor")
        match anchor[1]:
            case "t":
                write_anchor_pos_y = real_anchor_pos_y + move_lb_offset_y + height + padding_t
                text_box_lt_y = real_anchor_pos_y
            case "m":
                write_anchor_pos_y = real_anchor_pos_y + move_lb_offset_y + (height + padding_t - padding_b) / 2
                text_box_lt_y = real_anchor_pos_y - (height + padding_t + padding_b) / 2
            case "b":
                write_anchor_pos_y = real_anchor_pos_y + move_lb_offset_y - padding_b
                text_box_lt_y = real_anchor_pos_y - padding_b - padding_t - height
            case _:
                raise ValueError("Invalid anchor")
        if background_color is not None:
            self.ctx.rectangle(text_box_lt_x, text_box_lt_y,
                               width + padding_l + padding_r, height + padding_t + padding_b)
            self.ctx.set_source_rgba(*list(map(lambda x: x / 255 if x > 1 else x, background_color)))
            self.ctx.fill()
        if border_color is not None and border_width is not None:
            self.ctx.rectangle(text_box_lt_x, text_box_lt_y,
                               width + padding_l + padding_r, height + padding_t + padding_b)
            self.ctx.set_line_width(border_width)
            self.ctx.set_source_rgb(*list(map(lambda x: x / 255 if x > 1 else x, border_color)))
            self.ctx.stroke()
        self.ctx.set_source_rgba(*list(map(lambda x: x / 255 if x > 1 else x, font_color)))
        self.ctx.move_to(write_anchor_pos_x, write_anchor_pos_y)
        self.ctx.show_text(text)
        return text_box_lt_x, text_box_lt_y, width + padding_l + padding_r, height + padding_t + padding_b

    def _cv_text(self, text, position, font_size=None, font_color=None, anchor=None, padding=None,
                 border_color=None, border_width=None, background_color=None):
        """
        写一行字
        :param text: 文字
        :param position 位置 x,y
        :param font_size: 字体大小
                            >1: 字号
                            <=1: 根据图片的高度定义字体的大小
        :param font_color: 字体的颜色,颜色格式rgb或rgba数据格式list或tuple 默认是红色
        :param anchor: 对齐方式,lt:左上 lm:左中 lb:左下 mt:中上 mm:中中 mb:中下 rt:右上 rm:右中 rb:右下
        :param border_color: 边框颜色, None时无边框, 颜色格式rgb或rgba数据格式list或tuple
        :param border_width: 边框宽度
        :param padding: 字周围间隙
        :param background_color: 背景颜色, None时无背景, 颜色格式rgb或rgba数据格式list或tuple
        :return:
        """
        real_anchor_pos_x, real_anchor_pos_y = position
        if font_size is None:
            font_size = 20
        elif font_size > 1:
            font_size = int(font_size)
        else:
            font_size = min(5, int(font_size * self.height))
        font_scale = font_size / 30
        if font_color is None:
            font_color = (255, 255, 255)
        if len(font_color) == 4 and font_color[3] > 1:
            font_color = (*font_color[:3], font_color[3] / 255)
        if anchor is None:
            anchor = "lb"

        if border_color is None and border_width is not None:
            border_color = (255, 0, 0)
        if border_width is None and border_color is not None:
            border_width = 1
        if border_color is not None and len(border_color) == 4 and border_color[3] > 1:
            border_color = (*border_color[:3], border_color[3] / 255)

        if background_color is not None and len(background_color) == 4 and background_color[3] > 1:
            background_color = (*background_color[:3], background_color[3] / 255)
        if padding is None:
            padding_t, padding_b, padding_l, padding_r = 0, 0, 0, 0
        elif isinstance(padding, (list, tuple)) and len(padding) == 4:
            padding_t, padding_b, padding_l, padding_r = padding
        elif isinstance(padding, (list, tuple)) and len(padding) == 2:
            padding_t, padding_b = padding
            padding_l, padding_r = padding
        elif isinstance(padding, int):
            padding_t, padding_b, padding_l, padding_r = padding, padding, padding, padding
        else:
            raise ValueError("Invalid padding")
        # self.ctx.select_font_face(self.family_name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        # self.ctx.set_font_size(font_size)
        # 计算文本尺寸
        (width, height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        x_advance = width
        y_advance = 0
        # 真实文本左下角与书写锚定点(0,0)的偏差
        move_lb_offset_x = 0
        move_lb_offset_y = 0
        # 计算书写锚定点的位置 = 真实位置 + 偏移量
        match anchor[0]:
            case "l":
                write_anchor_pos_x = real_anchor_pos_x + move_lb_offset_x + padding_l
                text_box_lt_x = real_anchor_pos_x
            case "m":
                write_anchor_pos_x = real_anchor_pos_x + move_lb_offset_x + (padding_l - width - padding_r) / 2
                text_box_lt_x = real_anchor_pos_x - (width + padding_r + padding_l) / 2
            case "r":
                write_anchor_pos_x = real_anchor_pos_x + move_lb_offset_x - width - padding_r
                text_box_lt_x = real_anchor_pos_x - width - padding_l - padding_r
            case _:
                raise ValueError("Invalid anchor")
        match anchor[1]:
            case "t":
                write_anchor_pos_y = real_anchor_pos_y + move_lb_offset_y + height + padding_t
                text_box_lt_y = real_anchor_pos_y
            case "m":
                write_anchor_pos_y = real_anchor_pos_y + move_lb_offset_y + (height + padding_t - padding_b) / 2
                text_box_lt_y = real_anchor_pos_y - (height + padding_t + padding_b) / 2
            case "b":
                write_anchor_pos_y = real_anchor_pos_y + move_lb_offset_y - padding_b
                text_box_lt_y = real_anchor_pos_y - padding_b - padding_t - height
            case _:
                raise ValueError("Invalid anchor")
        text_box_lt_x, text_box_lt_y = int(text_box_lt_x), int(text_box_lt_y)
        if background_color is not None:
            if len(background_color) == 4 and background_color[3] < 1:
                alpha = background_color[3]
                overlay = self.image_bgr.copy()
                cv2.rectangle(overlay, (text_box_lt_x, text_box_lt_y),
                              (text_box_lt_x + width + padding_l + padding_r,
                               text_box_lt_y + height + padding_t + padding_b),
                              background_color[:3][::-1], -1)
                self.image_bgr = cv2.addWeighted(overlay, alpha, self.image_bgr, 1 - alpha, 0)
            else:
                cv2.rectangle(self.image_bgr, (text_box_lt_x, text_box_lt_y),
                              (text_box_lt_x + width + padding_l + padding_r,
                               text_box_lt_y + height + padding_t + padding_b),
                              background_color[:3][::-1], -1)
        if border_color is not None and border_width is not None:
            if len(border_color) == 4 and border_color[3] < 1:
                alpha = border_color[3]
                overlay = self.image_bgr.copy()
                cv2.rectangle(overlay, (text_box_lt_x, text_box_lt_y),
                              (text_box_lt_x + width + padding_l + padding_r,
                               text_box_lt_y + height + padding_t + padding_b),
                              border_color[:3][::-1], border_width)
                self.image_bgr = cv2.addWeighted(overlay, alpha, self.image_bgr, 1 - alpha, 0)
            else:
                cv2.rectangle(self.image_bgr, (text_box_lt_x, text_box_lt_y),
                              (text_box_lt_x + width + padding_l + padding_r,
                               text_box_lt_y + height + padding_t + padding_b),
                              border_color[:3][::-1], border_width)
        if len(font_color) == 4 and font_color[3] < 1:
            alpha = font_color[3]
            overlay = self.image_bgr.copy()
            cv2.putText(overlay, text, (int(write_anchor_pos_x), int(write_anchor_pos_y)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_color[:3][::-1], 1)
            self.image_bgr = cv2.addWeighted(overlay, alpha, self.image_bgr, 1 - alpha, 0)
        else:
            cv2.putText(self.image_bgr, text, (int(write_anchor_pos_x), int(write_anchor_pos_y)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_color[:3][::-1], 1)
        return text_box_lt_x, text_box_lt_y, width + padding_l + padding_r, height + padding_t + padding_b

    def multiline_text(self, text, pos):
        pass

    def _box_config(self, line_color=None, line_width=None, fill_color=None,
                    label_color=None, label_size=None, label_bg_color=None, label_anchor=None):
        if fill_color is None:
            if line_color is None:
                line_color = (255, 0, 0)
            if line_width is None:
                line_width = 1
            if label_bg_color is None:
                label_bg_color = line_color
        else:
            if line_color is not None and line_width is None:
                line_width = 1
            if line_width is not None and line_color is None:
                line_color = (255, 0, 0)
            if label_bg_color is None:
                if line_color is None:
                    label_bg_color = fill_color
                else:
                    label_bg_color = line_color
        if label_size is None:
            label_size = 20

        if label_color is None:
            color = line_color or fill_color
            label_color = tuple(map(lambda x: 255 - x, color[:3]))
            if len(color) == 4:
                label_color = (*label_color, color[3])
        if label_anchor is None:
            label_anchor = "lb"
        return {

            "line_color": line_color,
            "line_width": line_width,
            "fill_color": fill_color,
            "label_color": label_color,
            "label_size": label_size,
            "label_bg_color": label_bg_color,
            "label_anchor": label_anchor
        }

    def _cv_box(self, box, line_color=None, line_width=None, fill_color=None):
        if fill_color is None:
            if line_color is None:
                line_color = (255, 0, 0)
            if line_width is None:
                line_width = 1
        else:
            if len(fill_color) == 4 and fill_color[3] < 1:
                alpha = fill_color[3]
                overlay = self.image_bgr.copy()
                cv2.rectangle(overlay, (box[0], box[1]), (box[2], box[3]), fill_color[:3][::-1], -1)
                self.image_bgr = cv2.addWeighted(overlay, alpha, self.image_bgr, 1 - alpha, 0)
            else:
                cv2.rectangle(self.image_bgr, (box[0], box[1]), (box[2], box[3]), fill_color[:3][::-1], -1)
        if line_color is not None and line_width is not None:
            if len(line_color) == 4 and line_color[3] < 1:
                alpha = line_color[3]
                overlay = self.image_bgr.copy()
                cv2.rectangle(overlay, (box[0], box[1]), (box[2], box[3]), line_color[:3][::-1], line_width)
                self.image_bgr = cv2.addWeighted(overlay, alpha, self.image_bgr, 1 - alpha, 0)
            else:
                cv2.rectangle(self.image_bgr, (box[0], box[1]), (box[2], box[3]), line_color[:3][::-1], line_width)

    def _cairo_box(self, box, line_color=None, line_width=None, fill_color=None):
        if fill_color is None:
            if line_color is None:
                line_color = (255, 0, 0)
            if line_width is None:
                line_width = 1
        else:
            self.ctx.rectangle(box[0], box[1], box[2] - box[0], box[3] - box[1])
            self.ctx.set_source_rgba(*list(map(lambda x: x / 255 if x > 1 else x, fill_color)))
            self.ctx.fill()
        if line_color is not None and line_width is not None:
            self.ctx.rectangle(box[0], box[1], box[2] - box[0], box[3] - box[1])
            self.ctx.set_line_width(line_width)
            self.ctx.set_source_rgba(*list(map(lambda x: x / 255 if x > 1 else x, line_color)))
            self.ctx.stroke()

    def _box(self, box, line_color=None, line_width=None, fill_color=None, **kwargs):
        if self.processor == "cv2":
            return self._cv_box(box, line_color=line_color, line_width=line_width, fill_color=fill_color)
        elif self.processor == "cairo":
            return self._cairo_box(box, line_color=line_color, line_width=line_width, fill_color=fill_color)
        else:
            if len(line_color or []) > 3 or len(fill_color or []) > 3:
                return self._cairo_box(box, line_color=line_color, line_width=line_width, fill_color=fill_color)
            else:
                return self._cv_box(box, line_color=line_color, line_width=line_width, fill_color=fill_color)

    def _box_label(self, label, x1, y2, label_color=None, label_size=None, label_bg_color=None, label_anchor=None,
                   **kwargs):
        self.text(label, position=(x1, y2), font_size=label_size, font_color=label_color, anchor=label_anchor,
                  padding=1, background_color=label_bg_color)

    def _label_config(self, config, label, label_config):
        if label_config is None:
            return config
        cf = label_config.get(label, {})
        if isinstance(cf, dict):
            return {**config, **cf}
        else:
            return {**config, "line_color": cf}

    def boxes(self, boxes, line_color=None, line_width=None, fill_color=None,
              label_color=None, label_size=None, label_bg_color=None, label_anchor=None, label_config=None):
        """
        根据参数画一个框, 如果带有标签, 将标签放在框的左上角
        :param boxes: 框数据, 支持的格式 list, 也可以是tuple
                        纯框
                            [x1, y1, x2, y2].
                            [[x1, y1, x2, y2]].
                            {"box":[x1, y1, x2, y2]}
                            [{"box":[x1, y1, x2, y2]}].

                        带标签的框
                            [x1, y1, x2, y2, label].
                            [[x1, y1, x2, y2, label]].
                            {"box":[x1, y1, x2, y2], "label":"abc"}
                            [{"box":[x1, y1, x2, y2], "label":"abc"}].
        :param line_color: 线条的颜色, None时不画线, 颜色格式rgb或rgba数据格式list或tuple
        :param line_width: 线条的宽度, None, 0时不画线
        :param fill_color: 填充的颜色, None时不填充, 颜色格式rgb或rgba数据格式list或tuple
        :param label_color: 标签的颜色, None时忽略标签, 颜色格式rgb或rgba数据格式list或tuple
        :param label_size: 标签字体的大小, None,0时忽略标签
        :param label_bg_color: 标签的背景颜色, None时不填充, 颜色格式rgb或rgba数据格式list或tuple
        :param label_config: 标签配置
        :return:
        """
        params = {
            "line_color": line_color,
            "line_width": line_width,
            "fill_color": fill_color,
            "label_color": label_color,
            "label_size": label_size,
            "label_bg_color": label_bg_color,
            "label_anchor": label_anchor
        }

        def draw_box(box, label):
            kwargs = self._box_config(**self._label_config(params, label, label_config))
            self._box(box, **kwargs)
            if label is not None:
                self._box_label(label, box[0], box[1], **kwargs)

        if isinstance(boxes, list):
            if len(boxes) == 0:
                return
            box0 = boxes[0]
            if isinstance(box0, dict):
                if 'label' in box0:
                    # [{"box":[x1, y1, x2, y2], "label":"abc"}]
                    for box_info in boxes:
                        draw_box(box_info['box'], box_info['label'])
                else:
                    # [{"box":[x1, y1, x2, y2]}]
                    for box_info in boxes:
                        draw_box(box_info['box'], None)
            elif isinstance(box0, list):
                if len(box0) == 5:
                    # [[x1, y1, x2, y2, label]]
                    for box_info in boxes:
                        draw_box(box_info[:4], box_info[4])
                else:
                    # [[x1, y1, x2, y2]]
                    for box_info in boxes:
                        draw_box(box_info, None)
            else:
                if len(boxes) == 4:
                    # [x1, y1, x2, y2]
                    draw_box(boxes, None)
                elif len(boxes) == 5:
                    # [x1, y1, x2, y2, label]
                    draw_box(boxes[:4], boxes[4])
        elif isinstance(boxes, dict):
            if 'label' in boxes:
                # {"box":[x1, y1, x2, y2], "label":"abc"}
                draw_box(boxes['box'], boxes['label'])
            else:
                # {"box":[x1, y1, x2, y2]}
                draw_box(boxes['box'], None)

    def _cairo_boxes(self, boxes, line_color, line_width, fill_color, label_color, label_size, label_bg_color):

        pass

    def lines(self, points):
        pass

    def polyline(self, points):
        pass

    def polygon(self, points):
        pass

    def to_file(self, path):
        if self._ctx is None:
            cv2.imwrite(path, self.image_bgr)
        else:
            self.surface.write_to_png(path)

    def image(self):
        pass


if __name__ == '__main__':
    image = conv_img.to_numpy(r"D:\Code\aigc-stream-ai\files\wtt\img.png", target_normalized=False,
                              target_color_order="BGR", target_dim_order="HWC")
    time1 = time.time()
    drawer = ImageDrawer.start(image)
    time2 = time.time()
    print(f"{time2 - time1}")
    for i, t in enumerate(["aabc王想让"]):
        st = time.time()
        # drawer.text(f"hello world {t}", (1000, 500), font_size=8 + i, font_color=(255, i, 255, 0.5),
        #             border_color=(255, i, 0), border_width=1,
        #             # background_color=(0, 0, 255, 0.5),
        #             padding=(0, 0, 0, 0), anchor='mm')
        drawer.boxes([[100, 100, 200, 200, t]], label_color=(0, 255, 255, 0.5), label_bg_color=(255, 0, 0, 0.5),
                     line_color=(255, 0, 255), fill_color=(255, 255, 0, 0.5))
        print(f"{time.time() - st}")
    drawer.to_file('ou.png')
