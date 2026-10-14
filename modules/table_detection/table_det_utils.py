import cv2
import numpy as np
import pipeline_utils


def find_gap_in_structure(full_structure):
    result = False
    row_gap, col_gap = np.where(full_structure == -1)
    if len(row_gap.tolist()) != 0 or len(col_gap.tolist()) != 0:
        result = True
    return result, row_gap, col_gap

def get_extreme_cells_ids(structure):
    left_cells_id = []
    right_cells_id = []

    for row in structure:
        temp_indx_left = None
        temp_indx_right = None

        for col_cell_id in row:
            if col_cell_id != -1:
                temp_indx_left = col_cell_id
                break
        for col_cell_id in row[::-1]:
            if col_cell_id != -1:
                temp_indx_right = col_cell_id
                break
        left_cells_id.append(temp_indx_left)
        right_cells_id.append(temp_indx_right)

    extreme_cells = {
        'left': left_cells_id,
        'right': right_cells_id,
    }
    return extreme_cells


def expand_bbox(bbox, gap_x = 5, gap_y = 5):
    point_1 = [ bbox[0], bbox[1] ]
    point_2 = [ bbox[2], bbox[3] ]

    return [
            point_1[0]-gap_x, point_1[1]-gap_y,
            point_2[0]+gap_x, point_2[1]+gap_y
        ]


def check_connection_between_points_with_gap(point_1, point_2, lines, gap_x = 5, gap_y = 5):
    for line in lines:
        line_rect = line_to_rectangle(line)
        line_rect = expand_bbox(line_rect, gap_x, gap_y)
        if is_point_in_bbox(line_rect, point_1):
            if  is_point_in_bbox(line_rect, point_2):
                return True
    return False

def find_cell_bbox(tl_pos, column_connection, row_connection, structure_points, min_font_size):
    tl_row, tl_col = tl_pos

    # find all connection
    # find tr
    tr_connections = []
    for connections in column_connection[tl_row]:
        if tl_col in connections:
            tl_col_index = connections.index(tl_col)
            if tl_col_index != len(connections)-1:
                tr_connections = connections[tl_col_index+1:]

    # find bl
    bl_connections = []
    for connections in row_connection[tl_col]:
        if tl_row in connections:
            tl_row_index = connections.index(tl_row)
            if tl_row_index != len(connections)-1:
                bl_connections = connections[tl_row_index+1:]

    if len(tr_connections) == 0:
        return None, None
    if len(bl_connections) == 0:
        return None, None

    # find br
    tr_pos = None
    bl_pos = None
    br_pos = None

    cell_found = False
    for row_indx in bl_connections:
        if not cell_found:
            for cl_indx in tr_connections:
                if not cell_found:
                    temp_col_connections = column_connection[row_indx]
                    temp_row_connections = row_connection[cl_indx]
                    for col_connections in temp_col_connections:
                        if tl_col in col_connections and cl_indx in col_connections:
                            for row_connections in temp_row_connections:
                                if tl_row in row_connections and row_indx in row_connections:
                                    tr_pos = [tl_row, cl_indx]
                                    bl_pos = [row_indx, tl_col]
                                    br_pos = [row_indx, cl_indx]
                                    cell_found = True
                                    break
                        if cell_found:
                            break

    if None in [ tr_pos, bl_pos, br_pos ]:
        return None, None

    tl = structure_points[tl_pos[0]][tl_pos[1]]
    tr = structure_points[tr_pos[0]][tr_pos[1]]
    bl = structure_points[bl_pos[0]][bl_pos[1]]
    br = structure_points[br_pos[0]][br_pos[1]]

    row_start = min(tl_pos[1], bl_pos[1])
    row_end = max(tr_pos[1], br_pos[1])
    col_start = min(tl_pos[0], tr_pos[0])
    col_end = max(bl_pos[0], br_pos[0])

    if None in [ tl, tr, bl, br ]:
        return None, None
    
    left_x = min(tl[0], bl[0])
    top_y = min(tl[1], tr[1])

    right_x = max(tr[0], br[0])
    bot_y = max(bl[1], br[1])

    if (bot_y-top_y) < min_font_size or (right_x-left_x) < min_font_size:
        return None, None

    cell_bbox = [
                    [left_x, top_y],
                    [right_x, bot_y]
                ]
    return cell_bbox, [[row_start, row_end], [col_start, col_end]]


def is_point_in_bbox(bbox, point):
    x, y = point
    xtl, ytl, xbr, ybr = bbox
    return xtl <= x <= xbr and ytl <= y <= ybr

def get_center_line(line_points):
    return [
                int(abs(line_points[0][0]+line_points[1][0]) / 2),
                int(abs(line_points[0][1]+line_points[1][1]) / 2)
           ]

def draw_lines(img, coords, color = (0, 180, 0) ):
    for line in coords:
        thickness = 3
        img = cv2.line(img, line[0], line[1], color, thickness)
    return img

def draw_white_line(img, coords):
    color = (255)
    thickness = 1
    img = cv2.line(img, coords[0], coords[1], color, thickness)
    return img

def draw_black_line(img, coords):
    color = (0)
    thickness = 1
    img = cv2.line(img, coords[0], coords[1], color, thickness)
    return img



def create_line(p1, p2):
    """ Get cartesian line equation through 2 points.
        Ax + By + C = 0
        Args:
            p1 (list): Point '1' x,y coordinates
            p2 (list): Point '2' x,y coordinates
        Returns:
            A, B, C (tuple): Coefficients of line equation.
    """
    A = p1[1] - p2[1]
    B = p2[0] - p1[0]
    C = p1[0] * p2[1] - p2[0] * p1[1]
    return A, B, -C

def check_point_on_line(point, line):
    """ Determines which side of the line the point is on.
        Args:
                point (tuple): Point x, y coordinates.
                line (tuple): Line in format coefficients of line equation.
        Returns:
            res (int): If 'res' is greater than zero, then point placed in
                    upper half-plane, if equal to zero, then point is on line,
                    and if less than zero, then point placed in lower half-plane.
    """
    res = line[0] * point[0] + line[1] * point[1] - line[2]
    return res == 0

def line_to_rectangle(line):
    min_x = min(line[0][0], line[1][0])
    min_y = min(line[0][1], line[1][1])

    max_x = max(line[0][0], line[1][0])
    max_y = max(line[0][1], line[1][1])

    return [min_x, min_y, max_x, max_y]


def get_bin_imgs_lines_intersections(img_1, img_2):
    # for 1px lines
    intersection_img = img_1 + img_2 - 255

    intersection_places = np.where(intersection_img == 255)
    intersection_places_y = intersection_places[0].tolist()
    intersection_places_x = intersection_places[1].tolist()

    intersection_coords = []
    for x, y in zip(intersection_places_x, intersection_places_y):
        intersection_coords.append([x, y])
    return intersection_img, intersection_coords


def bbox_to_lines(bbox):
    p1 = [bbox[0],bbox[1]]
    p2 = [bbox[2],bbox[3]]
    l1_v = [ p1,              [ p1[0], p2[1] ] ]
    l2_v = [ [ p2[0], p1[1] ], p2              ]

    l1_h = [ p1, [p2[0], p1[1]] ]
    l2_h = [ [ p1[0], p2[1] ], p2 ]
    return [l1_v, l2_v], [l1_h, l2_h]

def translate_line(line, t_x, t_y):
    line[0][0] = int(line[0][0] + t_x)
    line[1][0] = int(line[1][0] + t_x)

    line[0][1] = int(line[0][1] + t_y)
    line[1][1] = int(line[1][1] + t_y)

    return line


def check_edges_cells(img_bin, intersection_coords, table_data, gap=3, ):

    def edge_check(img_bin, lines, edge_indx, coord_indx, points_for_del, gap, table_edge_line, lines_for_del):
        not_empty = False
        if (len(lines[0]) and len(lines[1])) and len(lines[0]) == len(lines[1]):
            if lines[0][0][coord_indx] == lines[1][0][coord_indx] and lines[0][-1][coord_indx] == lines[1][-1][coord_indx]:
                for i in range(len(lines[0])-1):
                    rect = [lines[0][i], lines[1][i+1]]
                    img_part = img_bin[ rect[0][1]+gap:rect[1][1]-gap, rect[0][0]+gap:rect[1][0]-gap]
                    white_pos = np.where(img_part == 255)
                    if len(white_pos[0]) > 1:
                        x_coord = list(pipeline_utils.grouper(list(set(white_pos[0]))))
                        y_coord = list(pipeline_utils.grouper(list(set(white_pos[1]))))
                        x_lens = [True for group in x_coord if len(group)>2 ]
                        y_lens = [True for group in y_coord if len(group)>2 ]
                        if len(x_lens)>0 or len(y_lens)>0:
                            not_empty = True
                if not_empty == False:
                    lines_for_del.append(table_edge_line)
                    for point in lines[edge_indx]:
                        points_for_del.append(point)
        return points_for_del, lines_for_del

    all_y = sorted(list(set([ point[1] for point in intersection_coords ])))
    all_x = sorted(list(set([ point[0] for point in intersection_coords ])))

    points_for_del = []
    if len(table_data['h_lines']) > 3 and len(all_y)>2:
        y_min_pair = [all_y[0], all_y[1]]
        y_max_pair = [all_y[-2], all_y[-1]]

        lines_h = [[], [], [], []]
        lines_for_del = []
        if table_data['add_lines_flags'][0] or table_data['add_lines_flags'][1]:
            for point in table_data['intersections']:
                if point[1]==y_min_pair[0] and table_data['add_lines_flags'][0]:
                    lines_h[0].append(point)
                if point[1]==y_min_pair[1] and table_data['add_lines_flags'][0]:
                    lines_h[1].append(point)

                if point[1]==y_max_pair[0] and table_data['add_lines_flags'][1]:
                    lines_h[2].append(point)
                if point[1]==y_max_pair[1] and table_data['add_lines_flags'][1]:
                    lines_h[3].append(point)
            
            for i in range(len(lines_h)):
                lines_h[i] = sorted(lines_h[i], key=lambda p: p[0])

            points_for_del, lines_for_del = edge_check(img_bin, [lines_h[0], lines_h[1]], 0, 0, points_for_del, gap, table_data['structure_table_lines'][0], lines_for_del)
            points_for_del, lines_for_del = edge_check(img_bin, [lines_h[2], lines_h[3]], 1, 0, points_for_del, gap, table_data['structure_table_lines'][1], lines_for_del)
        for del_line in lines_for_del:
            if del_line is not None:
                indx = table_data['h_lines'].index(del_line)
                table_data['h_lines'].pop(indx)

    if len(table_data['v_lines']) > 3 and len(all_x)>2:
        x_min_pair = [all_x[0], all_x[1]]
        x_max_pair = [all_x[-2], all_x[-1]]

        lines_v = [[], [], [], []]
        lines_for_del = []
        if table_data['add_lines_flags'][2] or table_data['add_lines_flags'][3]:
            for point in table_data['intersections']:
                if point[0]==x_min_pair[0] and table_data['add_lines_flags'][2]:
                    lines_v[0].append(point)
                if point[0]==x_min_pair[1] and table_data['add_lines_flags'][2]:
                    lines_v[1].append(point)

                if point[0]==x_max_pair[0] and table_data['add_lines_flags'][3]:
                    lines_v[2].append(point)
                if point[0]==x_max_pair[1] and table_data['add_lines_flags'][3]:
                    lines_v[3].append(point)
            
            for i in range(len(lines_v)):
                lines_v[i] = sorted(lines_v[i], key=lambda p: p[1])

            points_for_del, lines_for_del = edge_check(img_bin, [lines_v[0], lines_v[1]], 0, 1, points_for_del, gap, table_data['structure_table_lines'][2], lines_for_del)
            points_for_del, lines_for_del = edge_check(img_bin, [lines_v[2], lines_v[3]], 1, 1, points_for_del, gap, table_data['structure_table_lines'][3], lines_for_del)
        for del_line in lines_for_del:
            indx = table_data['v_lines'].index(del_line)
            table_data['v_lines'].pop(indx)

    points_for_del = [list(t) for t in set(map(tuple, points_for_del))]
    for point in points_for_del:
        indx = table_data['intersections'].index(point)
        table_data['intersections'].pop(indx)

    return table_data

def get_lines_with_intersections(lines, intersection_points, gap_x=5, gap_y=5, intersection_th=1):
    lines_with_intersections = {i: 0 for i in range(len(lines))}
    for indx, line in enumerate(lines):
        line_rect = line_to_rectangle(line)
        line_rect = expand_bbox(line_rect, gap_x, gap_y)
        for point in intersection_points:
            if is_point_in_bbox(line_rect, point):
                lines_with_intersections[indx] += 1
    lines_th_intersection = [lines[indx] for indx, val in lines_with_intersections.items() if val >= intersection_th]
    bad_lines = [lines[indx] for indx, val in lines_with_intersections.items() if val < intersection_th]
    return lines_th_intersection, bad_lines