import argparse
import os
import cv2
import time
import statistics
from PIL import Image
from pix2text import Pix2Text


class ImageDetector:
    def __init__(self, th=0.5):
        self.layout_det = Pix2Text(analyzer_config=dict(model_name='layout'))
        self.th = th
        self.out_classes = ['Figure']

    def find_images(self, image):
        page_layout = self.layout_det.analyzer(image)
        images_bboxes = [[data['box'][0].astype(int).tolist(), data['box'][2].astype(int).tolist()] for data in page_layout if data['type'] in self.out_classes and data['score'] >= self.th]
        return images_bboxes
    
    def draw_bboxes(self, img, bboxes, color=(0,0,255)):
        for bbox in bboxes:
            # print(bbox)
            start_point = bbox[0]
            end_point = bbox[1]
            cv2.rectangle(img, start_point, end_point, color, 2)
        return img
    
    def remove_images_from_page(self, img, images_bboxes):
        page_img = img.copy()
        images = []
        for img_bbox in images_bboxes:
            start_point = img_bbox[0]
            end_point = img_bbox[1]
            temp_img = page_img[start_point[1]:end_point[1], start_point[0]:end_point[0]]
            images.append(temp_img.copy())
            page_img[start_point[1]:end_point[1], start_point[0]:end_point[0]] = (255, 255, 255)
        return page_img, images





def run_detector_pipeline(
                            input_folder,
                            save_imgs_path=None,
                        ):

    times = []
    if save_imgs_path is not None:
        if not os.path.exists(save_imgs_path):
            os.makedirs(save_imgs_path)

    files = os.listdir(input_folder)
    detector = ImageDetector()
    for k, file in enumerate(files):
        print(file)

        file_label = os.path.splitext(os.path.split(file)[-1])[0]
        img = cv2.imread(input_folder + "/" + file)
        img_h, img_w, _ = img.shape

        t0 = time.time()
        im_pil = Image.fromarray(img)
        images_bboxes = detector.find_images(im_pil)
        t1 = time.time()
        times.append(t1 -t0)

        if save_imgs_path is not None:
            save_path = os.path.join(save_imgs_path, file_label+"_out.jpeg")
            img = detector.draw_bboxes(img, images_bboxes, (255,0,255))
            cv2.imwrite(save_path, img)

    if len(times):
        print("Table detection time (ms): ")
        print("min:", min(times))
        print("avg:", statistics.mean(times))
        print("max:", max(times))


if __name__ == "__main__":
    # pip install pix2text
    # python3 table_detection.py --folder ./test_data/2_broken_lines/imgs/
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", help="input images folder path", default= "./test_data/3_with_pic/")
    parser.add_argument("--img_output", help="image output folder path", default= "./boris/")

    args = parser.parse_args()
    run_detector_pipeline(args.folder, args.img_output)
