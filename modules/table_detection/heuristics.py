from table_det_utils import *
import pipeline_utils


def heuristics__is_graph(data, table_data, min_cell_dim):
    not_table_flag = False
    bad_message = ''

    if data['col_count'] == 0 or data['row_count'] == 0:
        bad_message = 'number of rows or columns is 0'
        not_table_flag = True
        return not_table_flag, bad_message

    cells = data['cells']
    temp_cells = [ cell_data['bbox'] for cell_id, cell_data in cells.items() ]
    cells_all_area = 0
    area_t = table_data['area']

    area_diff = area_t/table_data['page_area']*100
    min_table_area = (min_cell_dim*6) * (min_cell_dim*6)
    min_area_diff = min_table_area/table_data['page_area']*100

    if area_diff <= min_area_diff:
        bad_message = 'table box is too small in relation to page'
        not_table_flag = True
        return not_table_flag, bad_message

    if len(temp_cells) < 2:
        bad_message = 'number of cells less than 2'
        not_table_flag = True
        return not_table_flag, bad_message

    for i in range(len(temp_cells)):
        cell_i = temp_cells[i]
        x = cell_i[0]
        y = cell_i[1]
        w = abs(cell_i[2] - x)
        h = abs(cell_i[3] - y)
        cells_all_area += w*h
        for j in range(len(temp_cells)):
            if i != j:
                cell_j = temp_cells[j]
                intr_result, _ = pipeline_utils.intersection_xy(cell_i,cell_j)
                if intr_result:
                    not_table_flag = True
                    bad_message = 'cell intersection found'
                    return not_table_flag, bad_message

    if cells_all_area/area_t*100 < 40:
        not_table_flag = True
        bad_message = 'total area of cells is too small compared to area of table'
        return not_table_flag, bad_message

    return not_table_flag, bad_message


def heuristic__is_bad_table(data, table, gap=15):
    is_bad = False
    bad_message = ''

    # проверка соотношения кол-ва найденных линий с кол-вом столбцов и строк
    h_in_bbox = table['h_lines']
    v_in_bbox = table['v_lines']
    all_y = sorted([ point[0][1] for point in h_in_bbox ])
    y_groups = list(pipeline_utils.grouper(all_y)) # all vertical coords
    all_x = sorted([ point[0][0] for point in v_in_bbox ])
    x_groups = list(pipeline_utils.grouper(all_x)) # all horizontal coords

    row_edges = len(y_groups)
    column_edges = len(x_groups)

    rows = row_edges-1
    columns = column_edges-1

    if data['col_count'] != columns or data['row_count'] != rows:
        is_bad = True
        bad_message = "number of rows/columns not match of number of internal lines in table"
        return is_bad, bad_message

    # расчет отступов от краев найденной таблицы
    extreme_cells = get_extreme_cells_ids(data['full_structure'])
    left_cells_id = extreme_cells['left']
    right_cells_id = extreme_cells['right']
    if None in left_cells_id or None in right_cells_id:
        is_bad = True
        bad_message = "missing cells in one of columns"
        return is_bad, bad_message

    tl_cell_bbox = data['cells'][left_cells_id[0]]['bbox']
    tr_cell_bbox = data['cells'][right_cells_id[0]]['bbox']
    bl_cell_bbox = data['cells'][left_cells_id[-1]]['bbox']
    br_cell_bbox = data['cells'][right_cells_id[-1]]['bbox']

    cell_grid_tl = [tl_cell_bbox[0],tl_cell_bbox[1]]
    cell_grid_tr = [tr_cell_bbox[2],tr_cell_bbox[1]]
    cell_grid_bl = [bl_cell_bbox[0],bl_cell_bbox[3]]
    cell_grid_br = [br_cell_bbox[2],br_cell_bbox[3]]
    cell_grid_edges_points = [cell_grid_tl, cell_grid_tr, cell_grid_bl, cell_grid_br]

    table_tl = [data['bbox'][0], data['bbox'][1]]
    table_tr = [data['bbox'][2], data['bbox'][1]]
    table_bl = [data['bbox'][0], data['bbox'][3]]
    table_br = [data['bbox'][2], data['bbox'][3]]
    table_edges_points = [table_tl, table_tr, table_bl, table_br]

    for grid_point, table_point in zip(cell_grid_edges_points, table_edges_points):
        x_diff = abs(grid_point[0]-table_point[0])
        y_diff = abs(grid_point[1]-table_point[1])

        if x_diff >= gap or y_diff >= gap:
            is_bad = True
            bad_message = "strange indentation from edge of table bbox"
            return is_bad, bad_message

    # поиск пропусков в структуре
    gap_in_structure_status, _, _ = find_gap_in_structure(np.array(data['full_structure']))
    if gap_in_structure_status:
        is_bad = True
        bad_message = "gap_in_structure"
        return is_bad, bad_message

    return is_bad, bad_message