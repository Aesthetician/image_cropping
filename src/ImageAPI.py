import cv2
from PIL import Image

class ImageAPI:

    @staticmethod
    def read_image(file_path):
        image = cv2.imread(file_path)
        height, width, _ = image.shape
        image_size = [width, height]
        return image_size, image

    @staticmethod
    def crop_image(x1, y1, x2, y2, image):
        cropped_image = image[y1:y2, x1:x2].copy()
        return cropped_image

    @staticmethod
    def gen_a_cropped_image(img, roi, output_file):
        cropped_image = ImageAPI.crop_image(roi[0], roi[1], roi[2], roi[3], img)
        cv2.imwrite(output_file, cropped_image)
    
    @staticmethod
    def gen_a_cropped_image_by_PIL(img_path, roi, output_file):
        img = Image.open(img_path)
        cropped_img = img.crop(roi)
        cropped_img.save(output_file)
        img.close()



