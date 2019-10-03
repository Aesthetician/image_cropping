import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
import os
import re
import sys
import cv2
import numpy as np
import AvoDef as avodef


class VisualizeAnnotation:
    color_def1 = {
        'person': 'b',
        'face': 'g',
        'bicycle': 'r',
        'car': 'c',
        'motorcycle': 'm',
        'bus': 'y',
        'truck': 'lawngreen',
        'boat': 'orange',
        'test': 'white',
        'roi': 'gold'
    }
    color_def2 = {
        'person': 'purple',
        'face': 'lime',
        'bicycle': 'darkred',
        'car': 'salmon',
        'motorcycle': 'deepskyblue',
        'bus': 'gold',
        'truck': 'deeppink',
        'boat': 'brown',
        'test': 'white',
        'roi': 'b'
    }

    def __init__(self, image_path, annotations_group, output_folder, image_pre_cmt='', image_post_cmt=''):
        '''
        Args:
            annotations_group: a list of annotation group
                format 1: annotation formatted in dictionary  
                    ex: [[{anno1-1}, {anno1-2}, ...], [{anno2-1}, {anno2-2}, ...], ...]
                format 2: annotation foramtted in list
                    ex: [[[anno1-1], [anno1-2], ...], [[anno2-1], [anno2-2], ...], ...]
            if annotations_group is a list of annotation, it will be nested in a list.
                    ex: [[anno1-1],[anno1-2]] will become [ [[anno1-1], [anno1-1]] ] 

        '''
        if self.get_depth_of_list(annotations_group) == 2:
            annotations_group = [annotations_group]
        self._bboxes_group, self._texts_group, self._confs_group = self.read_annotations_group(
            annotations_group)
        self._img_with_anno = self.draw_annotation(
            image_path, self._bboxes_group, self._texts_group, self._confs_group)
        self._output_path = os.path.join(
            output_folder, image_pre_cmt + self.get_file_body_name(image_path) + image_post_cmt)
        self.save_image(self._img_with_anno, self._output_path)

    @staticmethod
    def get_file_body_name(full_path, is_refined=True):
        base = os.path.basename(full_path)
        if len(base) < 20 and is_refined:
            match = re.match(r'(.*)\/images\/(.*)', full_path, re.I)
            if not match:
                print('Error to get file', full_path)
                sys.exit('Error Message')
            prefix = os.path.basename(match.groups()[0])
            body = os.path.splitext(match.groups()[1])[0]
            refined_name = prefix + '-' + body
        else:
            refined_name = os.path.splitext(os.path.basename(full_path))[0]
        if '.' in refined_name:
            refined_name = refined_name.replace('.', '--')
        return refined_name

    def get_image(self, image_path):
        img = Image.open(image_path)
        return img

    def save_image(self, fig, output_path):
        fig.savefig(output_path, dpi=90, bbox_inches='tight')
        plt.close(fig)

    @staticmethod
    def get_depth_of_list(nested_list):
        if isinstance(nested_list, list):
            return 1 + VisualizeAnnotation.get_depth_of_list(nested_list[0])
        elif isinstance(nested_list, dict):
            return 1
        else:
            return 0

    def read_annotations_group(self, annotations_group):
        bboxes_group = []
        texts_group = []
        confs_group = []
        for i in range(len(annotations_group)):
            bboxes, texts, confs = self.read_annotation(annotations_group[i])
            bboxes_group.append(bboxes)
            texts_group.append(texts)
            confs_group.append(confs)
        return bboxes_group, texts_group, confs_group

    @staticmethod
    def read_annotation(annotations):
        '''
        bbox = [xmin, ymin, width, height]
        '''
        bboxes = []
        texts = []
        confs = []
        for i in range(len(annotations)):
            if isinstance(annotations[i], dict):
                bbox, text, conf, label = VisualizeAnnotation.read_annotation_in_dict(
                    annotations[i])
            else:
                bbox, text, conf = VisualizeAnnotation.read_annotation_in_list(
                    annotations[i])
            bboxes.append(bbox)
            texts.append(text)
            confs.append(conf)
        return bboxes, texts, confs

    @staticmethod
    def read_annotation_in_dict(annotation):
        bbox = [
            annotation[avodef.AnnotationDef.x_str],
            annotation[avodef.AnnotationDef.y_str],
            annotation[avodef.AnnotationDef.width_str],
            annotation[avodef.AnnotationDef.height_str]
        ]
        text = annotation[avodef.AnnotationDef.class_str]
        conf = annotation[avodef.AnnotationDef.confidence_str]
        label = annotation[avodef.AnnotationDef.label_str]
        return bbox, text, conf, label

    @staticmethod
    def read_annotation_in_list(annotation):
        pass

    @staticmethod
    def export_annotation(output_path, annotations, roi=[], is_normalized=False):
        annos = []
        for i in range(len(annotations)):
            bbox, text, conf, label = VisualizeAnnotation.read_annotation_in_dict(
                annotations[i])
            if is_normalized:
                #print('[roi] ', roi)
                #print('[bbox bf norm] ', bbox)
                bbox = VisualizeAnnotation.normalize_anno_bbox(bbox, roi)
                #print('[bbox norm] ', bbox)
            annos.append([label, bbox[0], bbox[1], bbox[2], bbox[3]])
        #print('[anno] ', annos)
        np.savetxt(output_path, annos, delimiter=',',
                   fmt='%d,%1.6f,%1.6f,%1.6f,%1.6f')

    @staticmethod
    def export_annotation_wi_2point_bbox(output_path, annotations, roi=[], is_normalized=False, is_test = False):
        annos = []
        for i in range(len(annotations)):
            bbox, text, conf, label = VisualizeAnnotation.read_annotation_in_dict(
                annotations[i])
            if is_normalized:
                if is_test:
                    print('[bbox]', bbox)
                bbox = VisualizeAnnotation.normalize_anno_bbox(bbox, roi)
                if is_test:
                    print('[norl bbox]', bbox)
            xmin = bbox[0]
            ymin = bbox[1]
            if is_normalized:          
                xmax = xmin + bbox[2] if xmin + bbox[2] < 1.0 else 1.0
                ymax = ymin + bbox[3] if ymin + bbox[3] < 1.0 else 1.0
            else:
                xmax = xmin + bbox[2] 
                ymax = ymin + bbox[3]
            annos.append([label, xmin, ymin, xmax, ymax])
        #print('[anno] ', annos)        
        np.savetxt(output_path, annos, delimiter=',',
                   fmt='%d,%1.6f,%1.6f,%1.6f,%1.6f')

    @staticmethod
    def normalize_anno_bbox(bbox, roi):
        '''
        Args:
            bbox, roi: [x, y, width, height]
        '''
        x = bbox[0] / roi[2]
        y = bbox[1] / roi[3]
        width = bbox[2] / roi[2]
        height = bbox[3] / roi[3]
        return [x, y, width, height]

    @staticmethod
    def draw_normalized_annotation(anno_path, image_path, output_path, is_test = False):
        '''
        Args:
            bboxes: [bbox1, bbox2, ...]
                bbox1: [x, y, width, height]
        '''
        bboxes = []
        texts = []
        confs = []
        colors = {
            'person': 'b',
            'face': 'g',
            'bicycle': 'r',
            'car': 'c',
            'motorcycle': 'm',
            'bus': 'y',
            'truck': 'lawngreen',
            'boat': 'orange',
            'test': 'white',
            'roi': 'gold'
        }   
        img = Image.open(image_path)
        img_width, img_height = img.size  
        #print('[img sz] ', img_width, 'x', img_height)
        with open(anno_path, 'r') as f:
            for line in f:
                dlimiter = ','
                if ' ' in line:
                    dlimiter = ' '
                tmp = line.rstrip().split(dlimiter)
                texts.append(avodef.ObjectDef.avo_labelmap[int(tmp[0])])
                bbox_2point = [float(tmp[1]), float(tmp[2]), float(tmp[3]), float(tmp[4])]
                #print('[bbox 2p]', bbox_2point)                
                if bbox_2point[2] - bbox_2point[0] <= 1: 
                    a_bbox = [bbox_2point[0] * img_width, \
                        bbox_2point[1] * img_height, \
                        (bbox_2point[2] - bbox_2point[0]) * img_width, \
                        (bbox_2point[3] - bbox_2point[1]) * img_height]
                else:
                    a_bbox = [bbox_2point[0], \
                        bbox_2point[1], \
                        (bbox_2point[2] - bbox_2point[0]), \
                        (bbox_2point[3] - bbox_2point[1])]
                #print('[a_bbox]', a_bbox)                
                bboxes.append(a_bbox)
        fig = plt.figure()
        plt.imshow(img)
        ax = plt.gca()

        for i in range(len(bboxes)):
            bbox = bboxes[i]
            text = texts[i]
            color = colors[text]
            x, y, width, height = bbox
            coords = (x, y), width, height
            rect = Rectangle(*coords, linewidth=1,
                             edgecolor=color, facecolor='none')
            ax.add_patch(rect)
            if text:
                if confs:
                    text += ':' + str(round(confs[i], 2))
                ax.text(x, y, text, bbox={'facecolor': color, 'alpha': 0.3})
        fig.savefig(output_path, dpi=90, bbox_inches='tight')
        plt.close(fig)

    def draw_annotation(self, image_path, bboxes_group, texts_group, confs_group):
        '''
        Args:
            bboxes_group: a list of bbox group
                ex: [[bbox1-1, bbox1-2, ...], [bbox2-1, bbox2-2, ...], ...]
            texts_group: a list of text group
            colors_group: a list of color group
            confs_group: a list of confidence group
        '''
        colors_group = self.get_colors_def(bboxes_group)
        if not confs_group:
            confs_group = self.init_confs(bboxes_group)

        with Image.open(image_path) as img:
            fig = plt.figure()
            plt.imshow(img)
            ax = plt.gca()
            for i in range(len(bboxes_group)):
                if bboxes_group[i]:
                    self.draw_rects(fig, ax, bboxes_group[i], colors_group[i], texts_group[i], confs_group[i], str(i)) 
        # if not os.path.isfile(image_path):
        #     print('[err-not exist] ', image_path)
        # img = cv2.imread(image_path)
        # fig = plt.figure()
        # plt.imshow(img)
        # ax = plt.gca()
        # for i in range(len(bboxes_group)):
        #     if bboxes_group[i]:
        #         self.draw_rects(fig, ax, bboxes_group[i], colors_group[i], texts_group[i], confs_group[i], str(i))
        return fig

    def draw_rects(self, fig, ax, bboxes, colors, texts, confs, idx=''):
        for i in range(len(bboxes)):
            bbox = bboxes[i]
            text = texts[i]
            color = colors[text]
            x, y, width, height = bbox
            coords = (x, y), width, height
            rect = Rectangle(*coords, linewidth=1,
                             edgecolor=color, facecolor='none')
            ax.add_patch(rect)
            if text:
                if idx:
                    text = idx + '-' + text
                text += ':' + str(round(confs[i], 2))
                ax.text(x, y, text, bbox={'facecolor': color, 'alpha': 0.3})

    def get_colors_def(self, bboxes_group):
        colors_def = []
        colors_def.append(self.color_def1)
        if len(bboxes_group) == 2:
            colors_def.append(self.color_def2)
        if len(bboxes_group) > 2:
            for i in range(2, len(bboxes_group)):
                colors_def.append(self.color_def1)
        return colors_def

    def init_confs(self, bboxes_group):
        confs = []
        for i in range(bboxes_group):
            conf = [''] * len(bboxes_group[i])
            confs.append(conf)
        return confs
