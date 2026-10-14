import cv2
from lxml import etree


def grouper(iterable, diff_val=1):
    prev = None
    group = []
    for item in iterable:
        if prev is None or item - prev <= diff_val:
            group.append(item)
        else:
            yield group
            group = [item]
        prev = item
    if group:
        yield group

def draw_bboxes(img, bboxes):
    for bbox in bboxes:
        start = (bbox[0], bbox[1])
        end = (bbox[2], bbox[3])
        cv2.rectangle(img, start, end, (0, 255, 0), 1)
    return img


def include_xy(a, b):
    x_include = a[0] <= b[0] <= a[2] and a[0] <= b[2] <= a[2]
    y_include = a[1] <= b[1] <= a[3] and a[1] <= b[3] <= a[3]
    if x_include and y_include:
        return True
    else: 
        return False

def intersection_xy(a, b):
    x1 = max(min(a[0], a[2]), min(b[0], b[2]))
    y1 = max(min(a[1], a[3]), min(b[1], b[3]))
    x2 = min(max(a[0], a[2]), max(b[0], b[2]))
    y2 = min(max(a[1], a[3]), max(b[1], b[3]))
    if x1<x2 and y1<y2:
        return True, [[x1,y1], [x2,y2]]
    else: 
        return False, None

def intersection_wh(a, b):
    a_xy = [a[0], a[1], a[0]+a[2], a[1]+a[3]]
    b_xy = [b[0], b[1], b[0]+b[2], b[1]+b[3]]
    return intersection_xy(a_xy, b_xy)


def intersection_wh(a, b):
    a_xy = [a[0], a[1], a[0]+a[2], a[1]+a[3]]
    b_xy = [b[0], b[1], b[0]+b[2], b[1]+b[3]]
    return intersection_xy(a_xy, b_xy)

def remove_table_lines(img):
    result = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255,
                        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Remove horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    remove_horizontal = cv2.morphologyEx(thresh,
                                        cv2.MORPH_OPEN,
                                        horizontal_kernel,
                                        iterations=2)
    cnts = cv2.findContours(remove_horizontal, cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, (255, 255, 255), 5)

    # Remove vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    remove_vertical = cv2.morphologyEx(thresh,
                                    cv2.MORPH_OPEN,
                                    vertical_kernel,
                                    iterations=2)
    cnts = cv2.findContours(remove_vertical, cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, (255, 255, 255), 5)
    return result

def bbox_xy_to_wh(bbox):
    new_bbox = [
        bbox[0],
        bbox[1],
        bbox[2] - bbox[0],
        bbox[3] - bbox[1],
    ]
    return new_bbox