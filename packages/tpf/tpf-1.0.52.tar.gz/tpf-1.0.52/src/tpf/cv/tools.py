import numpy as np

from PIL import Image
import cv2 as cv
import os

def PNG2JPG(PngPath):
    """默认将同目录下保存jpg图片
    """
    img = cv.imread(PngPath, 0)
    w, h = img.shape[::-1]
    infile = PngPath
    outfile = os.path.splitext(infile)[0] + ".jpg"
    img = Image.open(infile)
    img = img.resize((int(w / 2), int(h / 2)), Image.ANTIALIAS)
    try:
        if len(img.split()) == 4:
            # prevent IOError: cannot write mode RGBA as BMP
            r, g, b, a = img.split()
            img = Image.merge("RGB", (r, g, b))
            img.convert('RGB').save(outfile, quality=70)
            os.remove(PngPath)
        else:
            img.convert('RGB').save(outfile, quality=70)
            os.remove(PngPath)
        return outfile
    except Exception as e:
        print("PNG转换JPG 错误", e)




def iou(box, boxes, isMin=False):
    """
    box格式(x1,y1,x2,y2),两个点的坐标
    计算iou，两个框形成的长方形，
    交集的面积除以并集的面积；
    用两个框的交集除以 并集或最小集；
    """
    area = (box[2] - box[0]) * (box[3] - box[1])
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    # 交集的左上角取两个框大的值，右下角取两个款小的值
    x1 = np.maximum(box[0], boxes[:, 0])
    y1 = np.maximum(box[1], boxes[:, 1])
    x2 = np.minimum(box[2], boxes[:, 2])
    y2 = np.minimum(box[3], boxes[:, 3])
    # 求交集的边长，最短为0
    w = np.maximum(0, x2 - x1)
    h = np.maximum(0, y2 - y1)
    inter = w * h

    if isMin:
        return np.divide(inter, np.minimum(area, areas))
    else:
        return np.divide(inter, area + areas - inter)



def nms(boxes, thresh=0.3, isMin=False):
    """
    非极大值抑制，iou大于阈值的框看作重复框去除，留下iou小的框，可能是另一个人脸;
    0.3:重合的部分占并集的三分之一，意味着原始的两张图片，重合了一半；
    """
    if boxes.shape[0] == 0:
        return np.array([])
    # 将框根据置信度从大到小排序
    _boxes = boxes[(-boxes[:, 4]).argsort()]
    r_box = []
    # 计算iou，留下iou值小的框
    while _boxes.shape[0] > 1:
        a_box = _boxes[0]
        b_boxes = _boxes[1:]
        r_box.append(a_box)
        index = np.where(iou(a_box, b_boxes, isMin) < thresh)
        _boxes = b_boxes[index]

    if _boxes.shape[0] > 0:
        r_box.append(_boxes[0])

    return np.stack(r_box)


def convert_to_square(boxes):
    """
    扩充成正方形
    """
    if boxes.shape[0] == 0:
        return np.array([])
    square_boxes = boxes.copy()
    w = boxes[:, 2] - boxes[:, 0]
    h = boxes[:, 3] - boxes[:, 1]
    max_side = np.maximum(w, h)
    square_boxes[:, 0] = boxes[:, 0] + w / 2 - max_side / 2
    square_boxes[:, 1] = boxes[:, 1] + h / 2 - max_side / 2
    square_boxes[:, 2] = square_boxes[:, 0] + max_side
    square_boxes[:, 3] = square_boxes[:, 1] + max_side

    return square_boxes


def soft_nms(boxes, thresh=0.3, isMin=False):
    if boxes.shape[0] == 0:
        return np.array([])
    # 将框根据置信度从大到小排序
    _boxes = boxes[(-boxes[:, 4]).argsort()]
    r_box = []
    # 计算iou，留下iou值小的框
    while _boxes.shape[0] > 1:
        a_box = _boxes[0]
        b_boxes = _boxes[1:]
        r_box.append(a_box)
        iou_score = iou(a_box, b_boxes, isMin)
        index = np.where(iou_score < thresh)
        # iou值大的框，降低他们的置信度
        index_score_max = np.where(iou_score >= thresh)
        b_boxes[index_score_max, 4] *= np.array((1 - iou_score[iou_score >= thresh]), dtype=np.float32)
        r_box.extend(b_boxes[index_score_max])

        _boxes = b_boxes[index]

    if _boxes.shape[0] > 0:
        r_box.append(_boxes[0])

    return np.stack(r_box)


if __name__ == '__main__':
    a = np.array([1, 1, 10, 10, 0.98])
    bs = np.array([[1, 1, 9, 9, 0.8], [9, 8, 13, 20, 0.7], [6, 11, 18, 17, 0.85]])
    print(iou(a, bs))

    bs = np.array([[1, 1, 10, 10, 0.98], [1, 1, 9, 9, 0.8], [9, 8, 13, 20, 0.7], [6, 11, 18, 17, 0.85]])
    # print((-bs[:, 4]).argsort())
    print(nms(bs))
    print("*************")
    print(soft_nms(bs))
    # c = np.array([[1, 1, 9, 3]])
    # print(convert_to_square(c))
