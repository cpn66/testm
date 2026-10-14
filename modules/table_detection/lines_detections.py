import cv2
import numpy as np
import itertools

import pipeline_utils
from table_det_utils import *



def lines_to_rectangles_imgs(lines):
    contours, hierarchy = cv2.findContours(lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rect_coordinates = []

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        rect_coordinates.append([x,y,w,h])
        lines = cv2.rectangle(lines,(x,y),(x+w,y+h),(255),-1)
    return lines, rect_coordinates


def find_lines(img_bin, kernel, erode_iter=1, dilate_iter=2):
    temp_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel)
    image_1 = cv2.erode(img_bin, temp_kernel, iterations=erode_iter)
    temp_lines = cv2.dilate(image_1, temp_kernel, iterations=dilate_iter)
    return temp_lines


def rects_to_lines_coord(lines_rects, reverse = False):
    coords = []
    for rect in lines_rects:
        if reverse:
            # vertical
            x1 = int(rect[0] + rect[2]/2)
            x2 = int(x1)
            y1 = int(rect[1])
            y2 = int(rect[1]+rect[3])
        else:
            # horizontal
            x1 = int(rect[0])
            x2 = int(rect[0]+rect[2])
            y1 = int(rect[1]+rect[3]/2)
            y2 = int(y1)

        temp_line = [[x1,y1],[x2,y2]]
        coords.append(temp_line)
    return coords


def merging_close_lines(lines, gap_size, sort_key = 0):
    half_gap_size = int(gap_size/2)
    new_lines = []
    all_grouped_ids = []

    lines_sorted = sorted(lines, key=lambda x: x[sort_key])
    centers = [ get_center_line(points) for points in lines_sorted ]

    coords = sorted([ point[sort_key] for point in centers ])
    group_coords = list(pipeline_utils.grouper(coords, half_gap_size))
    group_coords = [ group for group in group_coords if len(group)>1 ]

    lines_by_groups = []
    lines_idx_by_groups = []
    for group in group_coords:
        group_lines = []
        group_lines_ids = []
        for i_c, c_point in enumerate(centers):
            if c_point[sort_key] in group:
                temp_line = lines_sorted[i_c]
                group_lines.append(temp_line)
                group_lines_ids.append(i_c)
        lines_by_groups.append(group_lines)
        lines_idx_by_groups.append(group_lines_ids)

    for group_ids, group_lines in zip(lines_idx_by_groups, lines_by_groups):
        all_grouped_ids += group_ids
        for i in range(len(group_lines)):
            for j in range(len(group_lines)):
                if i != j :
                    line_1 = group_lines[i]
                    line_2 = group_lines[j]

                    if sort_key == 1:
                        set_include_points_1 = set(range(line_1[0][0], line_1[1][0]+1))
                        set_include_points_2 = set(range(line_2[0][0], line_2[1][0]+1))
                        if len(set_include_points_1.intersection(set_include_points_2)):
                            y_all = [line_1[0][1], line_1[1][1], line_2[1][1], line_2[1][1]]
                            new_y = min(y_all) + int((max(y_all) - min(y_all))/2)

                            new_line = [
                                [min([line_1[0][0], line_2[0][0]]), new_y],
                                [max([line_1[1][0], line_2[1][0]]), new_y]
                            ]
                            group_lines[i] = new_line
                            group_lines[j] = new_line
                    
                    if sort_key == 0:
                        set_include_points_1 = set(range(line_1[0][1], line_1[1][1]+1))
                        set_include_points_2 = set(range(line_2[0][1], line_2[1][1]+1))
                        if len(set_include_points_1.intersection(set_include_points_2)):
                            x_all = [line_1[0][0], line_1[1][0], line_2[0][0], line_2[1][0]]
                            new_x = min(x_all) + int((max(x_all) - min(x_all))/2)

                            new_line = [
                                [new_x, min([line_1[0][1], line_2[0][1]])],
                                [new_x, max([line_1[1][1], line_2[1][1]])]
                            ]
                            group_lines[i] = new_line
                            group_lines[j] = new_line
        group_lines = sorted(group_lines)
        new_lines += list(k for k,_ in itertools.groupby(group_lines))

    for line_idx, line in enumerate(lines_sorted):
        if line_idx not in all_grouped_ids:
            new_lines.append(line)

    return new_lines


def get_verticals_and_horizontals(img_bin, erode_iter=1, dilate_iter=2, val=50):
    img_height, img_width = img_bin.shape

    kernel_len_ver = max(5, img_height // val)
    kernel_len_hor = max(5, img_width // val)
    vertical_lines = find_lines(img_bin, (1, kernel_len_ver), erode_iter=erode_iter, dilate_iter=dilate_iter)
    horizontal_lines = find_lines(img_bin, (kernel_len_hor, 1), erode_iter=erode_iter, dilate_iter=dilate_iter)

    return vertical_lines, horizontal_lines


def lines_detection(img_bin_adptv, img_bin, pix_10_font):
    img_height, img_width = img_bin.shape

    # нет FP, но не находятся бледные, не ровыные линии
    # могут обрезаться части таблиц
    # erode_iter = 3
    # dilate_iter = 4

    # линии находятся лучше, но могут быть FP
    erode_iter = 1
    dilate_iter = 2

    val = 50 # больше FN по ячейкам, меньше FP по таблицам.
    # val = 70 # точность по ячейкам лучше, беда с 3им типом таблиц.

    vertical_lines_1, horizontal_lines_1 =  get_verticals_and_horizontals(img_bin_adptv, erode_iter, dilate_iter, val)
    vertical_lines_2, horizontal_lines_2 =  get_verticals_and_horizontals(img_bin, erode_iter, dilate_iter, val)
    vertical_lines = cv2.bitwise_or(vertical_lines_1, vertical_lines_2)
    horizontal_lines = cv2.bitwise_or(horizontal_lines_1, horizontal_lines_2)

    # выравнивание кривых линий
    vertical_lines, rects_v = lines_to_rectangles_imgs(vertical_lines)
    horizontal_lines, rects_h = lines_to_rectangles_imgs(horizontal_lines)

    # move to coordinates
    lines_coords_h = rects_to_lines_coord(rects_h)
    lines_coords_v = rects_to_lines_coord(rects_v, reverse = True)

    lines_coords_v = merging_close_lines(lines_coords_v, pix_10_font, sort_key = 0)
    lines_coords_h = merging_close_lines(lines_coords_h, pix_10_font, sort_key = 1)

    # перерисовка линий
    empty_v = np.zeros( (img_height,img_width), dtype=np.uint8)
    empty_h = np.zeros( (img_height,img_width), dtype=np.uint8)

    for line in lines_coords_v:
        empty_v = draw_white_line(empty_v, line)
    for line in lines_coords_h:
        empty_h = draw_white_line(empty_h, line)

    _, intersections_coords = get_bin_imgs_lines_intersections(empty_v, empty_h)
    lines_coords_v, bad_lines_v = get_lines_with_intersections(lines_coords_v, intersections_coords, 1, 1)
    lines_coords_h, bad_lines_h = get_lines_with_intersections(lines_coords_h, intersections_coords, 1, 1)

    # закрашиваем линии не имеющие пересечений
    for line in bad_lines_v:
        empty_v = draw_black_line(empty_v, line)
    for line in bad_lines_h:
        empty_h = draw_black_line(empty_h, line)
    merged_lines = cv2.bitwise_or(empty_v, empty_h)

    return merged_lines, lines_coords_h, lines_coords_v, intersections_coords
