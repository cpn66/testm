import cv2
import os
import sys


root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_path)
sys.path.append(os.getcwd())

import table_structure_recognition as tsr
import lines_detections as ld


class TableDetector:
    def __init__(self, table_type = "borderd", use_heuristics = True):
        self.use_heuristics = use_heuristics

    def prepare_image(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, img_bin = cv2.threshold(img, 100,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        img_bin = 255 - img_bin
        return img_bin


    def prepare_image_adaptive(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_bin = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 11)
        img_bin = 255 - img_bin
        return img_bin

    def find_table(self, img, num_page = 0):
        img_orig = img.copy()
        img_h, img_w, _= img_orig.shape

        img_bin_adptv = self.prepare_image_adaptive(img)
        img_bin = self.prepare_image(img)

        pix_10_font = img_h * 0.712589 / 100

        merged_lines, lines_h, lines_v, intersection_coords = ld.lines_detection(img_bin_adptv, img_bin, pix_10_font)

        tables_bboxes = tsr.get_tables_bboxes(img_bin, merged_lines)
        tables = tsr.lines_to_tables(img_bin, tables_bboxes, lines_v, lines_h, pix_10_font, merged_lines, intersection_coords, line_ext_intrv=pix_10_font)

        page_tables = tsr.get_structure(img_w, img_h, tables, pix_10_font, self.use_heuristics)

        return page_tables

    def remove_tables_from_page(self, img, page_table_data):
        page_img = img.copy()
        for table_data in page_table_data:
            table_bbox = table_data['bbox']
            table_img = page_img[table_bbox[1]:table_bbox[3], table_bbox[0]:table_bbox[2]]
            table_data['img'] = table_img.copy()
            page_img[table_bbox[1]:table_bbox[3], table_bbox[0]:table_bbox[2]] = (255, 255, 255)
        return page_img, page_table_data

    def draw_lines(self, img, coords, color=(0, 180, 0)):
        for line in coords:
            thickness = 3
            img = cv2.line(img, line[0], line[1], color, thickness)
        return img

    def draw_structure(self, img, page_structure):
        for table_data in page_structure:
            table_bbox = table_data['bbox']
            start_point = (table_bbox[0], table_bbox[1])
            end_point = (table_bbox[2], table_bbox[3])

            table_color = (0, 0, 255)
            if table_data['type'] == 'graph':
                table_color = (112, 0, 112)
            elif table_data['is_bad']:
                table_color = (117, 103, 58)

            cv2.rectangle(img, start_point, end_point, table_color, 2)
            if table_data['type'] == 'table':
                for cell_id, cell_data in table_data['cells'].items():
                    cell_bbox = table_data['cells'][cell_id]['bbox']
                    start_point = (cell_bbox[0], cell_bbox[1])
                    end_point = (cell_bbox[2], cell_bbox[3])
                    cv2.rectangle(img, start_point, end_point, (255, 0, 0), 2)

        return img
