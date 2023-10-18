#!/usr/bin/env python3
# Copyright (C) 2022 Sophgo Technologies Inc.  All rights reserved.
#
# TPU-MLIR is licensed under the 2-Clause BSD License except for the
# third-party components.
#
# ==============================================================================
try:
    from tpu_mlir.python import *
except ImportError:
    pass

import numpy as np
import os
import sys
import argparse
import cv2
from tools.model_runner import mlir_inference, model_inference, onnx_inference, torch_inference
from utils.preprocess import supported_customization_format

COCO_CLASSES = ("person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
                "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
                "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
                "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis",
                "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
                "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife",
                "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
                "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed",
                "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard",
                "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
                "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush")

_COLORS = np.array([
    0.000, 0.447, 0.741, 0.850, 0.325, 0.098, 0.929, 0.694, 0.125, 0.494, 0.184, 0.556, 0.466,
    0.674, 0.188, 0.301, 0.745, 0.933, 0.635, 0.078, 0.184, 0.300, 0.300, 0.300, 0.600, 0.600,
    0.600, 1.000, 0.000, 0.000, 1.000, 0.500, 0.000, 0.749, 0.749, 0.000, 0.000, 1.000, 0.000,
    0.000, 0.000, 1.000, 0.667, 0.000, 1.000, 0.333, 0.333, 0.000, 0.333, 0.667, 0.000, 0.333,
    1.000, 0.000, 0.667, 0.333, 0.000, 0.667, 0.667, 0.000, 0.667, 1.000, 0.000, 1.000, 0.333,
    0.000, 1.000, 0.667, 0.000, 1.000, 1.000, 0.000, 0.000, 0.333, 0.500, 0.000, 0.667, 0.500,
    0.000, 1.000, 0.500, 0.333, 0.000, 0.500, 0.333, 0.333, 0.500, 0.333, 0.667, 0.500, 0.333,
    1.000, 0.500, 0.667, 0.000, 0.500, 0.667, 0.333, 0.500, 0.667, 0.667, 0.500, 0.667, 1.000,
    0.500, 1.000, 0.000, 0.500, 1.000, 0.333, 0.500, 1.000, 0.667, 0.500, 1.000, 1.000, 0.500,
    0.000, 0.333, 1.000, 0.000, 0.667, 1.000, 0.000, 1.000, 1.000, 0.333, 0.000, 1.000, 0.333,
    0.333, 1.000, 0.333, 0.667, 1.000, 0.333, 1.000, 1.000, 0.667, 0.000, 1.000, 0.667, 0.333,
    1.000, 0.667, 0.667, 1.000, 0.667, 1.000, 1.000, 1.000, 0.000, 1.000, 1.000, 0.333, 1.000,
    1.000, 0.667, 1.000, 0.333, 0.000, 0.000, 0.500, 0.000, 0.000, 0.667, 0.000, 0.000, 0.833,
    0.000, 0.000, 1.000, 0.000, 0.000, 0.000, 0.167, 0.000, 0.000, 0.333, 0.000, 0.000, 0.500,
    0.000, 0.000, 0.667, 0.000, 0.000, 0.833, 0.000, 0.000, 1.000, 0.000, 0.000, 0.000, 0.167,
    0.000, 0.000, 0.333, 0.000, 0.000, 0.500, 0.000, 0.000, 0.667, 0.000, 0.000, 0.833, 0.000,
    0.000, 1.000, 0.000, 0.000, 0.000, 0.143, 0.143, 0.143, 0.286, 0.286, 0.286, 0.429, 0.429,
    0.429, 0.571, 0.571, 0.571, 0.714, 0.714, 0.714, 0.857, 0.857, 0.857, 0.000, 0.447, 0.741,
    0.314, 0.717, 0.741, 0.50, 0.5, 0
]).astype(np.float32).reshape(-1, 3)

COCO_IDX = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 27, 28,
    31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
    56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 67, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 84,
    85, 86, 87, 88, 89, 90
]

ANCHORS = {  # stride: anchor
    8: [[1.25000, 1.62500], [2.00000, 3.75000], [4.12500, 2.87500]],
    16: [[1.87500, 3.81250], [3.87500, 2.81250], [3.68750, 7.43750]],
    32: [[3.62500, 2.81250], [4.87500, 6.18750], [11.65625, 10.18750]]
}

customization_format_attributes = {
    'RGB_PLANAR': ('rgb', 'nchw'),
    'RGB_PACKED': ('rgb', 'nhwc'),
    'BGR_PLANAR': ('bgr', 'nchw'),
    'BGR_PACKED': ('bgr', 'nhwc'),
    'GRAYSCALE': ('gray', 'nchw'),
    'YUV420_PLANAR': ('bgr', 'nchw'),
    'YUV_NV12': ('bgr', 'nchw'),
    'YUV_NV21': ('bgr', 'nchw'),
    'RGBA_PLANAR': ('rgba', 'nchw')
}


def vis(img, boxes, scores, cls_ids, conf=0.5, class_names=None):

    for i in range(len(boxes)):
        box = boxes[i]
        cls_id = int(cls_ids[i])
        score = scores[i]
        if score < conf:
            continue
        x0 = int(box[0])
        y0 = int(box[1])
        x1 = int(box[2])
        y1 = int(box[3])
        color = (_COLORS[cls_id] * 255).astype(np.uint8).tolist()
        text = '{}:{:.1f}%'.format(class_names[cls_id], score * 100)
        txt_color = (0, 0, 0) if np.mean(_COLORS[cls_id]) > 0.5 else (255, 255, 255)
        font = cv2.FONT_HERSHEY_SIMPLEX

        txt_size = cv2.getTextSize(text, font, 0.4, 1)[0]
        cv2.rectangle(img, (x0, y0), (x1, y1), color, 1)

        txt_bk_color = (_COLORS[cls_id] * 255 * 0.7).astype(np.uint8).tolist()
        cv2.rectangle(img, (x0, y0 + 1), (x0 + txt_size[0] + 1, y0 + int(1.5 * txt_size[1])),
                      txt_bk_color, -1)
        cv2.putText(img, text, (x0, y0 + txt_size[1]), font, 0.4, txt_color, thickness=1)

    return img


def vis2(img, dets, input_shape, class_names=None):
    shape = dets.shape
    num = shape[-2]
    img_h, img_w = img.shape[0:2]
    for i in range(num):
        d = dets[0][0][i]
        cls_id = int(d[1])
        score = d[2]
        x, y, w, h = d[3], d[4], d[5], d[6]
        r = min(input_shape[0] / img.shape[0], input_shape[1] / img.shape[1])
        new_img_h = img_h * r
        new_img_w = img_w * r
        x -= ((input_shape[1] - new_img_w) / 2)
        y -= ((input_shape[0] - new_img_h) / 2)
        x /= r
        y /= r
        w /= r
        h /= r
        x0 = int(x - w / 2)
        y0 = int(y - h / 2)
        x1 = int(x + w / 2)
        y1 = int(y + h / 2)
        color = (_COLORS[cls_id] * 255).astype(np.uint8).tolist()
        text = '{}:{:.1f}%'.format(class_names[cls_id], score * 100)
        txt_color = (0, 0, 0) if np.mean(_COLORS[cls_id]) > 0.5 else (255, 255, 255)
        font = cv2.FONT_HERSHEY_SIMPLEX

        txt_size = cv2.getTextSize(text, font, 0.4, 1)[0]
        cv2.rectangle(img, (x0, y0), (x1, y1), color, 1)

        txt_bk_color = (_COLORS[cls_id] * 255 * 0.7).astype(np.uint8).tolist()
        cv2.rectangle(img, (x0, y0 + 1), (x0 + txt_size[0] + 1, y0 + int(1.5 * txt_size[1])),
                      txt_bk_color, -1)
        cv2.putText(img, text, (x0, y0 + txt_size[1]), font, 0.4, txt_color, thickness=1)

    return img


def nms(boxes, scores, iou_thres):
    """Single class NMS implemented in Numpy."""
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(ovr <= iou_thres)[0]
        order = order[inds + 1]

    return keep


def multiclass_nms_class_aware(boxes, scores, iou_thres, score_thres):
    """Multiclass NMS implemented in Numpy. Class-aware version."""
    final_dets = []
    num_classes = scores.shape[1]
    for cls_ind in range(num_classes):
        cls_scores = scores[:, cls_ind]
        valid_score_mask = cls_scores > score_thres
        if valid_score_mask.sum() == 0:
            continue
        else:
            valid_scores = cls_scores[valid_score_mask]
            valid_boxes = boxes[valid_score_mask]
            keep = nms(valid_boxes, valid_scores, iou_thres)
            if len(keep) > 0:
                cls_inds = np.ones((len(keep), 1)) * cls_ind
                dets = np.concatenate([valid_boxes[keep], valid_scores[keep, None], cls_inds], 1)
                final_dets.append(dets)
    if len(final_dets) == 0:
        return None
    return np.concatenate(final_dets, 0)


def multiclass_nms_class_agnostic(boxes, scores, iou_thres, score_thres):
    """Multiclass NMS implemented in Numpy. Class-agnostic version."""
    cls_inds = scores.argmax(1)
    cls_scores = scores[np.arange(len(cls_inds)), cls_inds]

    valid_score_mask = cls_scores > score_thres
    if valid_score_mask.sum() == 0:
        return None
    valid_scores = cls_scores[valid_score_mask]
    valid_boxes = boxes[valid_score_mask]
    valid_cls_inds = cls_inds[valid_score_mask]
    keep = nms(valid_boxes, valid_scores, iou_thres)
    if keep:
        dets = np.concatenate(
            [valid_boxes[keep], valid_scores[keep, None], valid_cls_inds[keep, None]], 1)
    return dets


def multiclass_nms(boxes, scores, iou_thres, score_thres, class_agnostic=False):
    """Multiclass NMS implemented in Numpy"""
    if class_agnostic:
        nms_method = multiclass_nms_class_agnostic
    else:
        nms_method = multiclass_nms_class_aware
    return nms_method(boxes, scores, iou_thres, score_thres)


def preproc(img, input_size, pixel_format, channel_format, fuse_pre, swap=(2, 0, 1)):
    if len(img.shape) == 3:
        padded_img = np.ones((input_size[0], input_size[1], 3), dtype=np.uint8) * 114  # 114
    else:
        padded_img = np.ones(input_size, dtype=np.uint8) * 114  # 114

    r = min(input_size[0] / img.shape[0], input_size[1] / img.shape[1])
    resized_img = cv2.resize(
        img,
        (int(img.shape[1] * r), int(img.shape[0] * r)),
        interpolation=cv2.INTER_LINEAR,
    ).astype(np.uint8)
    top = int((input_size[0] - int(img.shape[0] * r)) / 2)
    left = int((input_size[1] - int(img.shape[1] * r)) / 2)
    padded_img[top:int(img.shape[0] * r) + top, left:int(img.shape[1] * r) + left] = resized_img

    if (channel_format == 'nchw'):
        padded_img = padded_img.transpose(swap)  # HWC to CHW
    if (pixel_format == 'rgb'):
        padded_img = padded_img[::-1]  # BGR to RGB

    padded_img = np.ascontiguousarray(padded_img, dtype=np.float32 if not fuse_pre else np.uint8)

    return padded_img, r, top, left


def make_grid(nx, ny, stride, anchor):
    stride = np.array(stride)
    anchor = np.array(anchor)
    xv, yv = np.meshgrid(np.arange(nx), np.arange(ny))
    grid = np.stack((xv, yv), -1)
    anchor_grid = (anchor * stride).reshape(1, len(anchor), 1, 1, 2)
    return grid, anchor_grid


def _sigmoid(x):
    return 1. / (1. + np.exp(-x))


def postproc(outputs, imsize, top, left, anchors=ANCHORS):
    z = []
    for out in outputs.values():
        if out.ndim != 5 or (out.shape[0], out.shape[1], out.shape[4]) != (1, 3, 85):
            if out.ndim == 4 and (out.shape[0], out.shape[1]) == (1, 255):
                out = out.reshape(1, 3, 85, out.shape[2], out.shape[3])
                out = out.transpose(0, 1, 3, 4, 2)
            elif out.ndim == 4 and (out.shape[0], out.shape[3]) == (1, 255):
                out = out.reshape(1, out.shape[1], out.shape[2], 3, 85)
                out = out.transpose(0, 3, 1, 2, 4)
            elif out.ndim == 4 and (out.shape[0], out.shape[1], out.shape[3] % 85) == (1, 3, 0):
                out = out.reshape(1, 3, out.shape[2], -1, 85)
            else:
                print("Warning: Output node with shape {} is not vaild, please check.".format(out.shape))
                continue
        # 1, 3, y, x, 85
        _, _, ny, nx, _ = out.shape
        stride = imsize[0] / ny
        assert (stride == imsize[1] / nx)
        anchor = anchors[stride]
        grid, anchor_grid = make_grid(nx, ny, stride, anchor)
        y = _sigmoid(out)
        y[..., 0:2] = (y[..., 0:2] * 2 - 0.5 + grid) * stride  # xy
        y[..., 0:1] = y[..., 0:1] - left  # x
        y[..., 1:2] = y[..., 1:2] - top  # y
        y[..., 2:4] = (y[..., 2:4] * 2)**2 * anchor_grid  # wh
        z.append(y.reshape(-1, 85))
    pred = np.concatenate(z, axis=0)
    boxes = pred[:, :4]
    scores = pred[:, 4:5] * pred[:, 5:]

    boxes_xyxy = np.ones_like(boxes)
    boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.
    boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.
    boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2.
    boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2.
    return scores, boxes_xyxy



def parse_args():
    # yapf: disable
    parser = argparse.ArgumentParser(description='Inference Yolo v5 network.')
    parser.add_argument("--model", type=str, required=True, help="Model definition file")
    parser.add_argument("--net_input_dims", type=str, default="640,640", help="(h,w) of net input")
    parser.add_argument("--input", type=str, required=True, help="Input image for testing")
    parser.add_argument("--output", type=str, required=True, help="Output image after detection")
    parser.add_argument("--conf_thres", type=float, default=0.001, help="Confidence threshold")
    parser.add_argument("--iou_thres", type=float, default=0.6, help="NMS IOU threshold")
    parser.add_argument("--score_thres", type=float, default=0.5, help="Score of the result")
    parser.add_argument("--fuse_preprocess", action='store_true', help="if the model fused preprocess")
    parser.add_argument("--fuse_postprocess", action='store_true', help="if the model fused postprocess")
    # yapf: enable
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    input_shape = tuple(map(int, args.net_input_dims.split(',')))
    pixel_format = 'rgb'
    channel_format = 'nchw'
    origin_img = cv2.imread(args.input)
    img, ratio, top, left = preproc(origin_img, input_shape, pixel_format, channel_format,
                                    args.fuse_preprocess)
    img = np.expand_dims(img, axis=0)
    if (not args.fuse_preprocess):
        img /= 255.  # 0 - 255 to 0.0 - 1.0
    data = {"data": img}  # input name from model
    output = dict()
    if args.model.endswith('.onnx'):
        output = onnx_inference(data, args.model, False)
    elif args.model.endswith('.pt') or args.model.endswith('.pth'):
        output = torch_inference(data, args.model, False)
    elif args.model.endswith('.mlir'):
        output = mlir_inference(data, args.model, False)
    elif args.model.endswith(".bmodel"):
        output = model_inference(data, args.model)
    elif args.model.endswith(".cvimodel"):
        output = model_inference(data, args.model, False)
    else:
        raise RuntimeError("not support modle file:{}".format(args.model))
    if not args.fuse_postprocess:
        scores, boxes_xyxy = postproc(output, input_shape, top, left)
        dets = multiclass_nms(boxes_xyxy,
                              scores,
                              iou_thres=args.iou_thres,
                              score_thres=args.conf_thres,
                              class_agnostic=True)
        if dets is None:
            raise RuntimeError("model:[{}] nothing detect out:{}".format(args.model, args.input))
        final_boxes, final_scores, final_cls_inds = dets[:, :4], dets[:, 4], dets[:, 5]
        final_boxes /= ratio
        fix_img = vis(origin_img,
                      final_boxes,
                      final_scores,
                      final_cls_inds,
                      conf=args.score_thres,
                      class_names=COCO_CLASSES)
        cv2.imwrite(args.output, fix_img)
    else:
        dets = output['yolo_post']
        fix_img = vis2(origin_img, dets, input_shape, class_names=COCO_CLASSES)
        cv2.imwrite(args.output, fix_img)


if __name__ == '__main__':
    main()
