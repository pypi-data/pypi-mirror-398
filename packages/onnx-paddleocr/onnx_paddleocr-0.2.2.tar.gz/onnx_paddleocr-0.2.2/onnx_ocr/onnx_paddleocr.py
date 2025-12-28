import argparse
import datetime
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from onnx_ocr.model_loader import download_models, get_default_model_paths
from onnx_ocr.predict_system import TextSystem
from onnx_ocr.utils import draw_ocr, project_root
from onnx_ocr.utils import infer_args as init_args


class ONNXPaddleOcr(TextSystem):
    def __init__(self, **kwargs):
        # 默认参数
        parser = init_args()
        inference_args_dict = {}
        for action in parser._actions:
            inference_args_dict[action.dest] = action.default
        params = argparse.Namespace(**inference_args_dict)

        # params.rec_image_shape = "3, 32, 320"
        params.rec_image_shape = "3, 48, 320"

        # 根据传入的参数覆盖更新默认参数
        params.__dict__.update(**kwargs)

        # 设置默认模型路径
        default_paths = get_default_model_paths()
        for key, value in default_paths.items():
            if getattr(params, key) == "":  # 如果参数为空字符串，则使用默认路径
                setattr(params, key, value)

        download_models(
            getattr(params, "det_model_dir"), getattr(params, "rec_model_dir")
        )

        # 初始化模型
        super().__init__(params)

    def ocr(self, img, det=True, rec=True, cls=True):
        if cls and not self.use_angle_cls:
            pass
            # print(
            #     "Since the angle classifier is not initialized, the angle classifier will not be used during the forward process"
            # )

        if det and rec:
            ocr_res = []
            dt_boxes, rec_res = self.__call__(img, cls)
            tmp_res = [[box.tolist(), res] for box, res in zip(dt_boxes, rec_res)]
            ocr_res.append(tmp_res)
            return ocr_res
        elif det and not rec:
            ocr_res = []
            dt_boxes = self.text_detector(img)
            tmp_res = [box.tolist() for box in dt_boxes]
            ocr_res.append(tmp_res)
            return ocr_res
        else:
            ocr_res = []
            cls_res = []

            if not isinstance(img, list):
                img = [img]
            if self.use_angle_cls and cls:
                img, cls_res_tmp = self.text_classifier(img)
                if not rec:
                    cls_res.append(cls_res_tmp)
            rec_res = self.text_recognizer(img)
            ocr_res.append(rec_res)

            if not rec:
                return cls_res
            return ocr_res


def sav2Img(org_img, result, name="draw_ocr.jpg"):
    # 显示结果

    result = result[0]
    # image = Image.open(img_path).convert('RGB')
    # 图像转BGR2RGB
    image = org_img[:, :, ::-1]
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    im_show = draw_ocr(image, boxes, txts, scores)
    im_show = Image.fromarray(im_show)
    im_show.save(name)


def save_to_img(image, result, save_path):
    """
    将OCR识别结果绘制到图像上并保存

    Args:
        image: 原始图像
        result: OCR识别结果
        save_path: 保存路径，如果是目录则使用时间戳命名文件，如果是文件路径则直接保存
    """

    save_path_obj = Path(save_path)

    # 判断save_path是文件还是目录
    if save_path_obj.suffix:  # 如果有文件扩展名，则视为文件路径
        output_file = save_path_obj
        # 确保文件所在目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
    else:  # 否则视为目录路径，使用时间戳命名文件
        # 创建保存目录
        save_path_obj.mkdir(parents=True, exist_ok=True)
        # 生成带时间戳的文件名（包含毫秒）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        output_file = save_path_obj / f"output_{timestamp}.jpg"

    # 绘制识别结果
    output_img = image.copy()

    # 先在OpenCV图像上绘制所有边界框
    for line in result[0]:
        points = np.array(line[0], dtype=np.int32)
        # 绘制边界框 (使用OpenCV)
        cv2.polylines(
            output_img, [points], isClosed=True, color=(0, 255, 0), thickness=2
        )

    # 转换为PIL图像用于文本绘制（同时支持中英文）
    img_pil = Image.fromarray(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    font_path = project_root / "fonts/simfang.ttf"
    font = (
        ImageFont.truetype(str(font_path), 36)
        if font_path.exists()
        else ImageFont.load_default()
    )

    # 在PIL图像上绘制文本
    for line in result[0]:
        points = np.array(line[0], dtype=np.int32)
        text = line[1][0]
        position = tuple(points[0])
        draw.text(position, text, font=font, fill=(0, 0, 255, 255))

    # 最后转换回OpenCV格式
    output_img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    # 保存图像
    cv2.imwrite(str(output_file), output_img)


def save_to_json(ocr_results, save_path):
    """
    将OCR识别结果保存为JSON文件

    Args:
        ocr_results: OCR识别结果列表
        save_path: 保存路径
    """
    # 创建保存目录
    save_path_obj = Path(save_path)

    # 判断save_path是文件还是目录
    if save_path_obj.suffix:  # 如果有文件扩展名，则视为文件路径
        output_file = save_path_obj
        # 确保文件所在目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
    else:  # 否则视为目录路径，使用时间戳命名文件
        # 创建保存目录
        save_path_obj.mkdir(parents=True, exist_ok=True)
        # 生成带时间戳的文件名（包含毫秒）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        output_file = save_path_obj / f"output_{timestamp}.json"

    # 保存JSON文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(ocr_results, f, ensure_ascii=False, indent=2)


def process_bounding_box(box_data):
    """处理边界框数据的辅助函数"""
    try:
        return np.asarray(box_data).reshape(4, 2).tolist()
    except (ValueError, AttributeError):
        return []


def result_to_json_data(results):
    return [
        {
            "text": line[1][0],
            "confidence": float(line[1][1]),
            "bounding_box": process_bounding_box(line[0]),
        }
        for line in results[0]
    ]
