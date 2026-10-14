import cv2
import numpy as np
import pipeline_utils
from copy import deepcopy

from heuristics import *
from table_det_utils import *



def get_tables_bboxes(img_bin, merged_lines, border_size = 30, perm_inter_val = 2):
    img_height, img_width = img_bin.shape
    page_area = img_height * img_width

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    img_vh = cv2.erode(~merged_lines, kernel, iterations=2)
    _, img_vh = cv2.threshold(img_vh, 128, 255, cv2.THRESH_BINARY )

    # добавляем рамки к изображению
    img_vh = cv2.copyMakeBorder(
        img_vh,
        top=border_size,
        bottom=border_size,
        left=border_size,
        right=border_size,
        borderType=cv2.BORDER_CONSTANT,
        value=(255)
    )

    # Detect contours for following box detection
    contours, hierarchy = cv2.findContours(img_vh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # remove page contour
    table_bboxes = []
    contours_new = []
    areas = []
    hierarchy_levels = []
    for c, hrch in zip(contours, hierarchy[0]):
        _, _, w, h = cv2.boundingRect(c)
        if (w < 0.95*img_width and h < 0.95*img_height):
            contours_new.append(c)
            hierarchy_levels.append(hrch[-1])

    if len(hierarchy_levels):
        min_hierarchy_level = min(hierarchy_levels)
        positions = [i for i, x in enumerate(hierarchy_levels) if x == min_hierarchy_level]
        for pos in positions:
            c = contours_new[pos]
            x, y, w, h = cv2.boundingRect(c)
            areas.append(w*h)
            bbox = [x-border_size, y-border_size, x+w-border_size, y+h-border_size]
            table_bboxes.append(bbox)

    # убираем меньшие пересекающиеся контуры
    indx_for_del = []
    for i in range(len(table_bboxes)):
        t_i = table_bboxes[i]
        area_i = areas[i]
        if area_i/page_area*100 < 1:
            indx_for_del.append(i)
        for j in range(len(table_bboxes)):
            if i != j:
                t_j = table_bboxes[j]
                area_j = areas[j]

                inter_check, inter_rect =  pipeline_utils.intersection_xy(t_i,t_j)
                if inter_check:
                    x_inter_diff = abs(inter_rect[1][0]-inter_rect[0][0])
                    y_inter_diff = abs(inter_rect[1][1]-inter_rect[0][1])
                    # inter_area = x_inter_diff*y_inter_diff
                    if area_i < area_j and (x_inter_diff > perm_inter_val and y_inter_diff > perm_inter_val):
                        indx_for_del.append(i)
                    if area_j < area_i and (x_inter_diff > perm_inter_val and y_inter_diff > perm_inter_val):
                        indx_for_del.append(j)
    indx_for_del = sorted(list(set(indx_for_del)), reverse=True)
    for indx in indx_for_del:
        table_bboxes.pop(indx)

    return table_bboxes


def lines_to_tables(img_bin, tables_bboxes, lines_v, lines_h, min_font_size, merged_lines, intersection_coords, line_ext_intrv = 5):
    img_height, img_width = merged_lines.shape

    tables_lines = np.zeros( (img_height,img_width), dtype=np.uint8)

    centers_v = [ get_center_line(points) for points in lines_v ]
    centers_h = [ get_center_line(points) for points in lines_h ]

    tables = []
    tr = min_font_size/2
    min_cell_dim = min_font_size*2.5

    intersection_table_bbox = []
    for t_bbox in tables_bboxes:
        w = abs(t_bbox[2]-t_bbox[0])
        h = abs(t_bbox[3]-t_bbox[1])
        area = w*h

        temp_table = {
            'bbox': t_bbox,
            'area': area,
            'page_area': img_height*img_width,
            'h_lines': [],
            'v_lines': [],
            'intersections': [],
            'add_lines_flags': [],
            'structure_table_lines': []
        }

        # TODO: reduced bbox points
        p1_x = int(t_bbox[0] + tr)
        p1_y = int(t_bbox[1] + tr)
        p2_x = int(p1_x + (w-tr*2))
        p2_y = int(p1_y + (h-tr*2))

        v_lines_in_bbox = []
        h_lines_in_bbox = []

        v_centres_in_bbox = []
        h_centres_in_bbox = []

        v_table_line_1 = [[p1_x, p1_y], [p1_x, p2_y]]
        v_table_line_2 = [[p2_x, p1_y], [p2_x, p2_y]]
        h_table_line_1 = [[p1_x, p1_y], [p2_x, p1_y]]
        h_table_line_2 = [[p1_x, p2_y], [p2_x, p2_y]]

        # get lines in table bbox
        for i, c_v in enumerate(centers_v):
            if is_point_in_bbox(t_bbox, c_v):
                v_centres_in_bbox.append(c_v[0])
                v_lines_in_bbox.append(lines_v[i])

        for j, c_h in enumerate(centers_h):
            if is_point_in_bbox(t_bbox, c_h):
                h_centres_in_bbox.append(c_h[1])
                h_lines_in_bbox.append(lines_h[j])

        if len(v_centres_in_bbox) == 0 or len(h_centres_in_bbox) == 0:
            continue

        min_line_x = min(v_centres_in_bbox)
        max_line_x = max(v_centres_in_bbox)

        min_line_y = min(h_centres_in_bbox)
        max_line_y = max(h_centres_in_bbox)


        p1_x = int(t_bbox[0] + tr)
        p1_y = int(t_bbox[1] + tr)
        p2_x = int(p1_x + (w-tr*2))
        p2_y = int(p1_y + (h-tr*2))

        h_x_left_in_table = sorted([p1_x] + [t_line[0][0] for t_line in h_lines_in_bbox if t_line[0][0]>=p1_x ])
        h_x_left_groups = list(pipeline_utils.grouper(h_x_left_in_table, line_ext_intrv))
        h_x_left_min = min(h_x_left_groups[0])

        h_x_right_in_table = sorted([p2_x] + [t_line[1][0] for t_line in h_lines_in_bbox if t_line[1][0]<=p2_x ])
        h_x_right_groups = list(pipeline_utils.grouper(h_x_right_in_table, line_ext_intrv))
        h_x_right_max = max(h_x_right_groups[-1])

        v_y_top_in_table = sorted([p1_y] + [t_line[0][1] for t_line in v_lines_in_bbox if t_line[0][1]>=p1_y ])
        v_y_top_groups = list(pipeline_utils.grouper(v_y_top_in_table, line_ext_intrv))
        v_y_top_min = min(v_y_top_groups[0])

        v_y_bot_in_table = sorted([p2_y] + [t_line[1][1] for t_line in v_lines_in_bbox if t_line[1][1]<=p2_y ])
        v_y_bot_groups = list(pipeline_utils.grouper(v_y_bot_in_table, line_ext_intrv))
        v_y_bot_max = max(v_y_bot_groups[-1])


        for h_line in h_lines_in_bbox:
            if h_line[0][0] in h_x_left_groups[0]:
                h_line[0][0] = h_x_left_min - 2
                draw_white_line(merged_lines, h_line)
            if h_line[1][0] in h_x_right_groups[-1]:
                h_line[1][0] = h_x_right_max +2
                draw_white_line(merged_lines, h_line)

        for v_line in v_lines_in_bbox:
            if v_line[0][1] in v_y_top_groups[0]:
                v_line[0][1] = v_y_top_min-2
                draw_white_line(merged_lines, v_line)
            if v_line[1][1] in v_y_bot_groups[-1]:
                v_line[1][1] = v_y_bot_max+2
                draw_white_line(merged_lines, v_line)

        # находим расстояние от крайних линий до границ ббокса
        left_diff = min_line_x-t_bbox[0]
        right_diff = t_bbox[2]-max_line_x

        top_diff = min_line_y-t_bbox[1]
        bot_diff = t_bbox[3]-max_line_y

        # draw table bbox lines
        add_table_lines_flag = [False]*4 # topt, bot, left, right
        structure_table_lines = [None]*4
        if min_cell_dim < top_diff:
            add_table_lines_flag[0] = True
            h_lines_in_bbox.append(h_table_line_1)
            structure_table_lines[0]= h_table_line_1
            draw_white_line(tables_lines, h_table_line_1)

        if min_cell_dim < bot_diff:
            add_table_lines_flag[1] = True
            h_lines_in_bbox.append(h_table_line_2)
            structure_table_lines[1] = h_table_line_2
            draw_white_line(tables_lines, h_table_line_2)

        if min_cell_dim < left_diff:
            add_table_lines_flag[2] = True
            v_lines_in_bbox.append(v_table_line_1)
            structure_table_lines[2] = v_table_line_1
            draw_white_line(tables_lines, v_table_line_1)

        if min_cell_dim < right_diff:
            add_table_lines_flag[3] = True
            v_lines_in_bbox.append(v_table_line_2)
            structure_table_lines[3] = v_table_line_2
            draw_white_line(tables_lines, v_table_line_2)

        if add_table_lines_flag[0] and add_table_lines_flag[2]:
            intersection_table_bbox.append([p1_x, p1_y])
        if add_table_lines_flag[0] and add_table_lines_flag[3]:
            intersection_table_bbox.append([p2_x, p1_y])
        if add_table_lines_flag[1] and add_table_lines_flag[2]:
            intersection_table_bbox.append([p1_x, p2_y])
        if add_table_lines_flag[1] and add_table_lines_flag[3]:
            intersection_table_bbox.append([p2_x, p2_y])

        if len(v_lines_in_bbox)+len(h_lines_in_bbox) < 4:
            continue

        temp_table['h_lines'] = h_lines_in_bbox
        temp_table['v_lines'] = v_lines_in_bbox
        temp_table['intersections'] = []
        temp_table['add_lines_flags'] = add_table_lines_flag
        temp_table['structure_table_lines'] = structure_table_lines

        tables.append(temp_table)

    # find intesection with table
    intersection_coords += intersection_table_bbox
    _, intersection_with_table_bbox = get_bin_imgs_lines_intersections(tables_lines, merged_lines)
    intersection_coords += intersection_with_table_bbox

    for i_point in intersection_coords:
        for table_data in tables:
            if table_data['h_lines'] and table_data['v_lines']:
                if is_point_in_bbox(table_data['bbox'], i_point):
                    table_data['intersections'].append(i_point)

    for table_data in tables:
        table_intersections = sorted(table_data['intersections'], key=lambda p: p[1])
        if len(table_intersections):
            table_data = check_edges_cells(img_bin, table_intersections, table_data, gap = int(tr))

        all_lines = table_data['v_lines'] + table_data['h_lines']

        if len(all_lines) <= 4:
            table_data['bad'] = True

        # TODO: del this table
        if len(all_lines) >= 4 and len(table_data['intersections']) < 4:
            table_data['bad'] = True

    return tables


def get_structure(img_w, img_h, tables, min_font_size, use_heuristics):
    page_table_data = []

    for table in tables:
        if 'bad' in table.keys():
            continue
        temp_dict = {'bbox': table['bbox'], "type": "table", "structure": [], "is_bad": False, 'bad_message': ''}
        temp_dict['cells'] = {}

        gaps_y = [ abs(line[0][1]-line[1][1]) for line in table['h_lines'] ]
        max_gap_y = max(gaps_y) if len(gaps_y) else 2
        max_gap_y = 2 if max_gap_y < 2 else max_gap_y
        gaps_x = [ abs(line[0][0]-line[1][0]) for line in table['v_lines'] ]
        max_gap_x = max(gaps_x) if len(gaps_x) else 2
        max_gap_x = 2 if max_gap_x < 2 else max_gap_x

        all_intersections = table['intersections']

        all_y = sorted([ point[1] for point in all_intersections ])
        y_groups = list(pipeline_utils.grouper(all_y, max_gap_y)) # all vertical coords

        all_x = sorted([ point[0] for point in all_intersections ])
        x_groups = list(pipeline_utils.grouper(all_x, max_gap_x)) # all horizontal coords

        row_count = len(y_groups)-1
        col_count = len(x_groups)-1
        temp_dict['row_count'] = row_count
        temp_dict['col_count'] = col_count

        structure = [[]]*row_count
        for i in range(row_count):
            for j in range(col_count):
                structure[i] = [-1]*col_count
        full_structure = deepcopy(structure)

        structure_points = [ [None]*len(x_groups) for _ in range(len(y_groups))]
        row_connection = [[]]*len(x_groups) # соединение строк по столбцам (по линиям)
        column_connection = [[]]*len(y_groups) # соединение столбцов по строкам (по линиям)

        # create structure of intersect coords
        for i, y_coords in enumerate(y_groups):
            temp_line_intr_points = [ point for point in all_intersections if point[1] in y_coords]
            for j, x_coords in enumerate(x_groups):
                temp_point = None
                for intr_point in temp_line_intr_points:
                    if intr_point[0] in x_coords:
                        temp_point = intr_point
                        break
                structure_points[i][j] = temp_point

            # find connection in line
            for px_indx in range(len(x_groups)-1):
                point = structure_points[i][px_indx]
                if point is not None:
                    next_points = structure_points[i][px_indx+1:]
                    connection_status = None
                    for px_indx_next, point_next in enumerate(next_points):
                        if point_next is not None:
                            connection_status = check_connection_between_points_with_gap(
                                                                                            point,
                                                                                            point_next,
                                                                                            table['h_lines'],
                                                                                            max_gap_x,
                                                                                            max_gap_y
                                                                                        )
                            break
                    if connection_status is not None:
                        if len(column_connection[i]) == 0:
                            column_connection[i] = [] # mheh
                            column_connection[i].append([px_indx])
                        if connection_status:
                            column_connection[i][-1].append(px_indx+1+px_indx_next)
                        else:
                            column_connection[i].append([px_indx+1+px_indx_next])

        # по строкам
        for j, x_coords in enumerate(x_groups):
            temp_intr_points = [ structure_points[i][j] for i in range(len(y_groups)) ]
            for py_indx in range(len(y_groups)-1):
                point = temp_intr_points[py_indx]
                if point is not None:
                    next_points = temp_intr_points[py_indx+1:]

                    connection_status = None
                    for py_indx_next, point_next in enumerate(next_points):
                        if point_next is not None:
                            connection_status = check_connection_between_points_with_gap(
                                                                                            point,
                                                                                            point_next,
                                                                                            table['v_lines'],
                                                                                            max_gap_x,
                                                                                            max_gap_y
                                                                                        )
                            break

                    if connection_status is not None:
                        if len(row_connection[j]) == 0:
                            row_connection[j] = [] # mheh
                            row_connection[j].append([py_indx])
                        if connection_status:
                            row_connection[j][-1].append(py_indx+1+py_indx_next)
                        else:
                            row_connection[j].append([py_indx+1+py_indx_next])

        # find cells
        temp_cell_id = 0
        for i in range(len(structure_points)):
            for j in range(len(structure_points[i])):

                if i != len(structure_points)-1 and j != len(structure_points[i])-1:
                    cell_bbox, edges = find_cell_bbox([i,j], column_connection, row_connection, structure_points, min_font_size)
                    if cell_bbox is not None and edges  is not None:
                        structure[i][j] = temp_cell_id
                        row_edges = edges[0]
                        col_edges = edges[1]

                        temp_dict['cells'][temp_cell_id] = {
                            "bbox": cell_bbox,
                            "columns": col_edges,
                            "rows": row_edges,
                        }
                        for c_ind in range(col_edges[0], col_edges[1]):
                            for r_ind in range(row_edges[0], row_edges[1]):
                                full_structure[c_ind][r_ind] = temp_cell_id

                        temp_cell_id += 1
                    else:
                        continue


        cells_img = np.zeros( (img_h,img_w, 1), dtype=np.uint8)
        for cell_id, cell_bbox in temp_dict['cells'].items():
            temp_bbox = temp_dict['cells'][cell_id]["bbox"]
            cells_img = cv2.rectangle(cells_img, cell_bbox["bbox"][0], cell_bbox["bbox"][1], (255), 3)
            temp_dict['cells'][cell_id]["bbox"] = [temp_bbox[0][0], temp_bbox[0][1], temp_bbox[1][0], temp_bbox[1][1]]

        temp_dict['structure'] = structure
        temp_dict['full_structure'] = full_structure

        # TODO: add heuristics
        if use_heuristics:
            not_table_flag, bad_message = heuristics__is_graph(temp_dict, table, min_font_size)
            if not_table_flag:
                temp_dict = {'bbox':  table['bbox'], "type": "graph", "is_bad": True, 'bad_message': bad_message}
            else:
                bad_status, bad_message = heuristic__is_bad_table(temp_dict, table, gap=min_font_size*3)
                temp_dict['is_bad'] = bad_status
                temp_dict['bad_message'] = bad_message

        page_table_data.append(temp_dict)


    return page_table_data