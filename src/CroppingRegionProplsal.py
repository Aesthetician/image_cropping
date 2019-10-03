import os
import random
import VisualizeAnnotation as visanno
import ImageAPI as iapi
import Rectangle as rect
import AvoDef as avodef

class CroppingRegionProposal:
    def __init__(self, image_path, sorted_anno, sorted_gt_anno, roi):
        '''
        Returns:
            self._pairs_of_cropping_bbox_and_anno : cropping bbox and non-resized annotations for visualization 
            self._pairs_of_cropping_bbox_and_resized_anno : cropping bbox and resized annotations for final result 
                format:[bbox, anno]
                    bbox: [x, y, width, height]
        '''
        self._subclass = ['bus', 'truck', 'bicycle', 'motorcycle','boat']
        self._pairs_of_cropping_bbox_and_anno = []
        self._pairs_of_cropping_bbox_and_resized_anno = self.run(image_path, sorted_anno, sorted_gt_anno, roi)
        self._aspect_ratio = 1.5
        self._aspect_ratio_threshold = 2

    def run(self, image_path, sorted_anno, sorted_gt_anno, roi, topk = 5, cnt_of_selection = 3, is_visualized = True):
        image_size, a_image = iapi.ImageAPI.read_image(image_path)        
        selected_bboxes = self.select_bboxes(sorted_anno, sorted_gt_anno)
        if not selected_bboxes:
            return []
        best_bboxes = []
        for each_bbox in selected_bboxes:
            best_bbox = self.get_best_expaned_bbox(image_size, each_bbox, sorted_gt_anno, roi)
            best_bboxes.append(best_bbox)
        pairs_of_cropping_bbox_and_resized_anno = []
        pairs_of_cropping_bbox_and_anno = []        
        discard_cnt = 0
        for each_best_bbox in best_bboxes:
            is_discarded, refined_anno = self.refine_annotation(each_best_bbox, sorted_gt_anno)
            if is_discarded:
                discard_cnt += 1
                continue
            resized_anno = CroppingRegionProposal.resize_annotation(each_best_bbox, refined_anno)    
            a_pair = [each_best_bbox, resized_anno]
            pairs_of_cropping_bbox_and_resized_anno.append(a_pair)
            if is_visualized:
                pairs_of_cropping_bbox_and_anno.append([each_best_bbox, refined_anno])
        
        '''
        retreat if the bboxes are all discarded
        '''
        while discard_cnt == cnt_of_selection:
            discard_cnt -= 1
            selected_bboxes = self.select_bboxes(sorted_anno, sorted_gt_anno)
            a_best_bbox = self.get_best_expaned_bbox(image_size, selected_bboxes[0], sorted_gt_anno, roi)
            is_discarded, refined_anno = self.refine_annotation(a_best_bbox, sorted_gt_anno)
            if is_discarded:
                discard_cnt += 1
                continue
            resized_anno = CroppingRegionProposal.resize_annotation(a_best_bbox, refined_anno)    
            a_pair = [a_best_bbox, resized_anno]
            pairs_of_cropping_bbox_and_resized_anno.append(a_pair)
            if is_visualized:            
                pairs_of_cropping_bbox_and_anno.append([a_best_bbox, refined_anno])
        self._pairs_of_cropping_bbox_and_anno = pairs_of_cropping_bbox_and_anno
        return pairs_of_cropping_bbox_and_resized_anno
    
    def get_best_expaned_bbox(self, image_size, bbox, gt_anno, roi):
        expanded_bboxes = self.expand_bbox(image_size, bbox)
        max_score = 0
        max_idx = 0
        for i in range(len(expanded_bboxes)):
            score = self.score_a_bbox(expanded_bboxes[i], roi, gt_anno)
            if max_score < score:
                max_idx = i
                max_score = score
        return expanded_bboxes[max_idx]
    
    @staticmethod
    def resize_annotation(bbox, annotations, is_test = False):
        resized_annotations = []
        for each_anno in annotations:
            resized_anno = CroppingRegionProposal.resize_an_annotation(bbox, each_anno, is_test)
            resized_annotations.append(resized_anno)            
            if is_test:
                print('[bbox] ', bbox)
                print('[anno] ', each_anno)            
                print('[resized_anno] ', resized_anno)            
        return resized_annotations

    @staticmethod
    def resize_an_annotation(bbox, anno, is_test = False):
        res = anno.copy()
        res[avodef.AnnotationDef.x_str] = res[avodef.AnnotationDef.x_str] - bbox[0] 
        res[avodef.AnnotationDef.y_str] = res[avodef.AnnotationDef.y_str] - bbox[1]
        if res[avodef.AnnotationDef.x_str] < 0:
            if is_test:
                print('[anno bf adj neg]', res)
            res[avodef.AnnotationDef.width_str] += res[avodef.AnnotationDef.x_str]
            res[avodef.AnnotationDef.x_str] = 0
        if res[avodef.AnnotationDef.y_str] < 0:
            if is_test:
                print('[anno bf adj neg]', res)
            res[avodef.AnnotationDef.height_str] += res[avodef.AnnotationDef.y_str]
            res[avodef.AnnotationDef.y_str] = 0
        if res[avodef.AnnotationDef.x_str] + res[avodef.AnnotationDef.width_str] > bbox[0] + bbox[2]:
            if is_test:
                print('[anno bf adj boundary]', res)
            res[avodef.AnnotationDef.width_str] = bbox[0] + bbox[2] - res[avodef.AnnotationDef.x_str]
        if res[avodef.AnnotationDef.y_str] + res[avodef.AnnotationDef.height_str] > bbox[1] + bbox[3]:
            if is_test:
                print('[anno bf adj boundary]', res)
            res[avodef.AnnotationDef.height_str] = bbox[1] + bbox[3] - res[avodef.AnnotationDef.y_str]
        return res

    @staticmethod
    def get_averaged_bbox_area(anno, sacle = 100):
        avg_bbox_area = [0] * 8
        max_bbox_area = [0] * 8
        cnt_bbox = [0] * 8
        for each in anno:
            obj_bbox, text, conf, label = visanno.VisualizeAnnotation.read_annotation_in_dict(each)
            obj_bbox = CroppingRegionProposal.convert_to_int(obj_bbox)
            idx = avodef.ObjectDef.avo_idmap[text]
            bbox_area = obj_bbox[2] / sacle * obj_bbox[3] / sacle
            avg_bbox_area[idx] += bbox_area
            max_bbox_area[idx] = max(max_bbox_area[idx], bbox_area)
            cnt_bbox[idx] += 1
        for i in range(len(avg_bbox_area)):
            if cnt_bbox[i] > 1:
                avg_bbox_area[i] = (avg_bbox_area[i] - max_bbox_area[i]) / (cnt_bbox[i] - 1)    
        return avg_bbox_area

    def refine_annotation(self, bbox, anno, high_threshold = 0.6, low_threshold = 0.4, obj_ratio_in_bbox = 0.4):
        refined_anno = []
        is_discarded = False
        bbox_by_2point = rect.Rectangle.convert_bbox_to_2points(bbox)
        rect_bbox = rect.Rectangle(*bbox_by_2point)
        bbox_area = rect_bbox.get_area()
        scale = 100
        averaged_obj_bbox_area = self.get_averaged_bbox_area(anno, scale)
        for each in anno:
            if self.is_included_in_bbox(bbox, each):
                if not self.is_abnormal_anno(averaged_obj_bbox_area, bbox, each, scale):
                    refined_anno.append(each)
            else:
                bbox_anno = CroppingRegionProposal.get_bbox(each)
                bbox_anno_by_2point = rect.Rectangle.convert_bbox_to_2points(bbox_anno)
                rect_bbox_anno = rect.Rectangle(*bbox_anno_by_2point)
                if not rect_bbox.is_intersected(rect_bbox_anno):
                    continue
                else:
                    intersection = rect_bbox & rect_bbox_anno
                    intersection_area = intersection.get_area()
                    IoA = intersection_area / rect_bbox_anno.get_area()
                    if IoA > high_threshold:
                        if not self.is_abnormal_anno(averaged_obj_bbox_area, bbox, each, scale):
                            refined_anno.append(each)
                    elif IoA < low_threshold:
                        continue
                    else:
                        #is_discarded = True                        
                        if intersection_area / bbox_area > obj_ratio_in_bbox:
                            is_discarded = True
        return is_discarded, refined_anno

    def select_bboxes(self, sorted_anno, sorted_gt_anno, topk = 5, cnt_of_selection = 3):
        '''Select 3 bboxes from topk bbox with highest confidnce. If # of anno < 3, gt_anno is included to be chosen   

        Args:
            sorted_anno: annotation list of interested categories
            sorted_gt_anno: annotation list of ground truth 
            format of anno
                [{'height': y1, ...}, {'height': y2, ...}]
        Returns:
            3 or cnt_of_selection bboxes 
            bbox: [x, y, width, height]

        '''
        #sorted_anno = [{'width': 23.0, 'x': 742.0, 'confidence': 0.58, 'height': 26.0, 'class': 'person', 'y': 127.0, 'label': 1}]
        #sorted_gt_anno = [{'width': 23.0, 'x': 742.0, 'confidence': 0.58, 'height': 26.0, 'class': 'person', 'y': 127.0, 'label': 1}, {'width': 23.0, 'x': 742.0, 'confidence': 0.58, 'height': 26.0, 'class': 'person', 'y': 127.0, 'label': 1}]        
        selected_list = [i for i in range(len(sorted_anno))]
        selected_gt_list = []
        if len(sorted_anno) >= topk:
            selected_list = random.sample(range(topk), cnt_of_selection)
        elif len(sorted_anno) > cnt_of_selection:
            selected_list = random.sample(range(len(sorted_anno)), cnt_of_selection)
        else:
            sample_range = min(topk, len(sorted_gt_anno))
            if sample_range > cnt_of_selection - len(sorted_anno):
                selected_gt_list = random.sample(range(sample_range), cnt_of_selection - len(sorted_anno))
            else:
                selected_gt_list = [random.randint(0, len(sorted_gt_anno) - 1) for i in range(cnt_of_selection - len(sorted_anno))]    
        bboxes = []
        #print('[sa]', len(sorted_anno))
        for i in selected_list:
            bboxes.append(CroppingRegionProposal.get_bbox(sorted_anno[i]))
        '''skipped
        for i in selected_gt_list:
            #print(i)
            bboxes.append(CroppingRegionProposal.get_bbox(sorted_gt_anno[i]))
        '''
        return bboxes
    
    @staticmethod
    def get_bbox(annotation):
        bbox, text, conf, label = visanno.VisualizeAnnotation.read_annotation_in_dict(annotation)
        bbox = CroppingRegionProposal.convert_to_int(bbox)
        return bbox

    @staticmethod
    def convert_to_int(lst):
        for i in range(len(lst)):
            lst[i] = int(lst[i])
        return lst

    def expand_bbox(self, image_size, bbox, number_of_expanding = 10):
        expanded_bboxes = []
        for i in range(number_of_expanding):
            expanded_bbox = CroppingRegionProposal.get_expanded_bbox(bbox, image_size)
            expanded_bboxes.append(expanded_bbox)
        return expanded_bboxes

    @staticmethod
    def get_expanded_bbox(bbox, boundary):
        '''generate new bbox by expanding the given bbox 
        
        Args:
            boundary: [height, width]
            bbox: [x, y, width, height]

        Returns:
            expanded bbox: [x_new, y_new, width_new, height_new]
        
        '''
        x, y, width, height = bbox
        x_new = random.randint(0, x)
        y_new = random.randint(0, y)
        width_tmp = random.randint(x + width, boundary[0]) - x_new
        height_tmp = random.randint(y + height, boundary[1]) - y_new
        width_new, height_new = CroppingRegionProposal.adjust_aspect_ratio(width_tmp, height_tmp, 1.5, 1.8)
        bbox_new = [x_new, y_new, width_new, height_new]
        return bbox_new 

    @staticmethod
    def adjust_aspect_ratio(width, height, aspect_ratio = 3, threshold = 4):
        if width > height and width / height > threshold:
            return width, int(width // aspect_ratio)
        if height > width and height / width > threshold:
            return int(height // aspect_ratio), height
        return width, height

    def score_a_bbox(self, bbox, rois, annotations, subclass_ratio = 10, subclass_area_ratio = 1.3, nonroi_ratio = 1, is_test = False):
        '''assign a score to bbox 
        Returns:
            score: # of objects - area of not(roi) 

        '''
        total_annotation = len(annotations)
        area_of_subclass, cnt_of_included_subclass_obj, cnt_of_included_obj = self.calculate_included_object(bbox, annotations)
        overlapped_area_with_non_roi = self.calculate_overlapped_non_roi(bbox, rois)
        if is_test:
            print('[overlap] ', overlapped_area_with_non_roi)
        obj_score = (cnt_of_included_subclass_obj * subclass_ratio + cnt_of_included_obj) / total_annotation 
        total_roi_area = CroppingRegionProposal.calculate_roi_area(rois)
        if total_roi_area == 0:
            nonroi_score = 0
        else:
            nonroi_score = overlapped_area_with_non_roi / total_roi_area
        subclass_area_score = area_of_subclass / CroppingRegionProposal.get_bbox_area(bbox)
        return obj_score + subclass_area_ratio * subclass_area_score - nonroi_ratio * nonroi_score
    
    @staticmethod
    def get_bbox_area(bbox):
        return bbox[2] * bbox[3]

    def calculate_included_object(self, bbox, annotations):
        cnt = 0
        cnt_of_subclass = 0
        area_of_subclass = 0
        for anno in annotations:
            if self.is_included_in_bbox(bbox, anno):
                cnt += 1
                if anno[avodef.AnnotationDef.class_str] in self._subclass:
                    cnt_of_subclass += 1
                    area_of_subclass += CroppingRegionProposal.calculate_bbox_area_of_an_annotation(anno)
        #print('[cnt]', cnt)
        return area_of_subclass, cnt_of_subclass, cnt

    @staticmethod
    def is_abnormal_anno(averaged_obj_bbox_area, bbox, anno, scale = 100):
        obj_bbox, text, conf, label = visanno.VisualizeAnnotation.read_annotation_in_dict(anno)
        obj_bbox = CroppingRegionProposal.convert_to_int(obj_bbox)
        if text == avodef.ObjectDef.person_str and obj_bbox[2] / obj_bbox[3] > 3:
            return True
        if obj_bbox[2] / scale * obj_bbox[3] / scale >= 0.25 * int(bbox[2]) / scale * int(bbox[3]) / scale \
            and obj_bbox[2] / scale * obj_bbox[3] / scale >= 4 * averaged_obj_bbox_area[avodef.ObjectDef.avo_idmap[text]]:
            print('[skip abnormal obj] ',text, ':', obj_bbox, '@', bbox)
            return True
        return False

    def is_included_in_bbox(self, bbox, anno):
        obj_bbox = CroppingRegionProposal.get_bbox(anno)
        if self.is_within_a_segment(obj_bbox[0], obj_bbox[0] + obj_bbox[2], bbox[0], bbox[0] + bbox[2]) and \
           self.is_within_a_segment(obj_bbox[1], obj_bbox[1] + obj_bbox[3], bbox[1], bbox[1] + bbox[3]):
            return True
        return False

    def is_within_a_segment(self, x1, x2, s1, s2):
        return True if s1 < x1 and x2 < s2 else False
    
    @staticmethod
    def calculate_bbox_area_of_an_annotation(anno):
        bbox = CroppingRegionProposal.get_bbox(anno)
        bbox_by_2point = rect.Rectangle.convert_bbox_to_2points(bbox)
        rect_bbox = rect.Rectangle(*bbox_by_2point)
        return rect_bbox.get_area()

    @staticmethod
    def read_roi_as_bbox(roi):
        return [roi['left'], roi['top'], roi['width'], roi['height']]

    def calculate_overlapped_non_roi(self, bbox, rois):
        sum_of_non_roi = 0
        for roi in rois:
            bbox_of_roi = CroppingRegionProposal.read_roi_as_bbox(roi)
            roi_by_2point = rect.Rectangle.convert_bbox_to_2points(bbox_of_roi)
            bbox_by_2point = rect.Rectangle.convert_bbox_to_2points(bbox)
            rect_roi = rect.Rectangle(*roi_by_2point)
            rect_bbox = rect.Rectangle(*bbox_by_2point)
            intersection = rect_bbox & rect_roi
            sum_of_non_roi += rect_bbox.get_area() - intersection.get_area()
        return sum_of_non_roi

    @staticmethod
    def calculate_roi_area(rois):
        sum_of_roi_area = 0
        for roi in rois:
            bbox_of_roi = CroppingRegionProposal.read_roi_as_bbox(roi)
            roi_by_2point = rect.Rectangle.convert_bbox_to_2points(bbox_of_roi)
            rect_roi = rect.Rectangle(*roi_by_2point)
            sum_of_roi_area += rect_roi.get_area()
        return sum_of_roi_area

    def get_region_proposal(self):
        return self._pairs_of_cropping_bbox_and_resized_anno
    
    def get_visualized_region_proposal(self):
        return self._pairs_of_cropping_bbox_and_anno
