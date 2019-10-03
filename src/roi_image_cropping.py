import os
from pymongo import MongoClient 
from collections import defaultdict

import my_file_api as fapi
from AvoDef import FieldDef
import VisualizeAnnotation as visanno
import CroppingRegionProplsal as crp
import ImageAPI as iapi
import Rectangle as rect
from PIL import Image


def run(mongoDB_server, output_dir, collection_name, no_boat, stop_num = 10, is_visualized = True, is_test = False, is_stopped = False):
    '''
    prepare output folder 
    '''
    output_folder = os.path.join(output_dir, 'output-' + collection_name)
    fapi.create_folder(output_folder)
    vis_output_folder = os.path.join(output_folder, 'visualization')      
    if is_visualized:
        fapi.create_folder(os.path.join(output_folder, 'visualization'))      
    fapi.create_folder(os.path.join(output_folder, 'images'))
    fapi.create_folder(os.path.join(output_folder, 'annotations')) 

    '''
    mongoDB initialization 
    '''    
    client = MongoClient(mongoDB_server)
    db_raw_roi = client['VALObjectDetectionRawROI'] 
    db_raw_annotation = client['VALObjectDetectionRawAnnotation']
    roi_collection = db_raw_roi[collection_name]
    annotation_collection = db_raw_annotation[collection_name]
    
    '''
    prepare info of image & annotation

    '''
    img_dict = defaultdict(dict)
    i = 0
    #query = {'folder_name':"April15-16_bike1"}
    query = {}
    for doc in annotation_collection.find(query): 
    #for doc in annotation_collection.find({'folder_name':"April15-16_bike1"}): 
        local_path = doc[FieldDef.local_path_str]
        a_dict = {}
        subclass_annotation = get_subclass_annotation(annotation_collection, local_path, no_boat)
        sorted_gt_annotation = get_sorted_gt_annotation(annotation_collection, local_path, no_boat)
        i += 1        
        if is_test and is_stopped and i > stop_num:
            break           
        if len(sorted_gt_annotation) < 3 or not subclass_annotation:
            print('[img-skip] ', local_path)            
            continue
        folder_name = doc[FieldDef.folder_name_str]
        for roi in roi_collection.find({FieldDef.folder_name_str:folder_name}):
            if is_test:
                print('[roi] ', roi)
            rois = roi[FieldDef.annotation_str]
        a_dict['folder_name'] = folder_name
        a_dict['roi'] = rois
        a_dict['sub_anno'] = subclass_annotation
        a_dict['gt_anno'] = sorted_gt_annotation
        img_dict[local_path] = a_dict
    i = 0
    for local_path, img_info in img_dict.items():
        print('[img] ', local_path)            
        subclass_cropping(local_path, img_info, output_folder, vis_output_folder, is_test, is_visualized)
        i += 1
        if is_stopped and is_test and (i > stop_num):
            break

def convert_path_root(a_path):
    converted_path = a_path.replace('/mnt/liquid_nas','/mnt/data-pcie1/zf.working')
    print('[lcl] ', converted_path)
    return converted_path

def subclass_cropping(local_path, img_info, output_folder, vis_output_folder, is_test = True, is_visualized = True):
    image_cmt = ''
    each_img = convert_path_root(local_path)
    img_output_path = os.path.join(output_folder, 'images', image_cmt + visanno.VisualizeAnnotation.get_file_body_name(each_img) + '-0.jpg')
    if os.path.exists(img_output_path):
        print('[existed]')
        return
    
    subclass_annotation = img_info['sub_anno']
    sorted_gt_annotation = img_info['gt_anno']
    rois = img_info['roi']
    region_proposal = crp.CroppingRegionProposal(each_img, subclass_annotation, sorted_gt_annotation, rois)
    
    '''
    bbox_and_anno has resized annotations according to each roi
    bbox_and_visualized_anno has annotations based on the whole image
    '''
    bbox_and_anno = region_proposal.get_region_proposal() 
    bbox_and_visualized_anno = region_proposal.get_visualized_region_proposal()
    if is_test:
        print('[bbox_and_anno] ', bbox_and_anno)
        unfold_list(bbox_and_anno, 0)
        print('[bbox_and_vis_anno] ', bbox_and_visualized_anno)
        unfold_list(bbox_and_visualized_anno, 0)
    if is_visualized:
        '''
        visualize all of roi in a image
        '''
        shown_annotations = test_visualize_all_result(bbox_and_visualized_anno, rois, sorted_gt_annotation)
        visanno.VisualizeAnnotation(each_img, shown_annotations, vis_output_folder, image_cmt)
    export_cropped_images_and_anno(bbox_and_anno, bbox_and_visualized_anno, each_img, output_folder, vis_output_folder, rois, image_cmt, is_test, is_visualized)

def export_cropped_images_and_anno(bbox_and_anno, bbox_and_visualized_anno, image_path, output_folder, vis_output_folder, rois, image_cmt = '', is_test = True, is_visualized = True):
    #image_size, a_image = iapi.ImageAPI.read_image(image_path)  
    for i in range(len(bbox_and_anno)):
        crop_bbox = bbox_and_anno[i][0]
        crop_bbox_2point = rect.Rectangle.convert_bbox_to_2points(crop_bbox)
        img_output_path = os.path.join(output_folder, 'images', image_cmt + visanno.VisualizeAnnotation.get_file_body_name(image_path) + '-' + str(i) + '.jpg')
        #iapi.ImageAPI.gen_a_cropped_image(a_image, crop_bbox_2point, img_output_path)
        iapi.ImageAPI.gen_a_cropped_image_by_PIL(image_path, crop_bbox_2point, img_output_path)
        resized_annotations = bbox_and_anno[i][1]
        if is_test:
            print('[resized_annotations] ', resized_annotations)
            unfold_list(resized_annotations, 0)
            print('[crop bbox] ', crop_bbox)
        img_check(img_output_path, crop_bbox)    
        anno_output_path = os.path.join(output_folder, 'annotations', image_cmt + visanno.VisualizeAnnotation.get_file_body_name(image_path) + '-' + str(i) + '.txt')
        #visanno.VisualizeAnnotation.export_annotation(anno_output_path, resized_annotations, crop_bbox, is_normalized = True)
        visanno.VisualizeAnnotation.export_annotation_wi_2point_bbox(anno_output_path, resized_annotations, crop_bbox, is_normalized = True)
        if not is_visualized:
            return
        shown_annotations = test_visualize_a_result(bbox_and_visualized_anno[i], rois)
        if shown_annotations: 
            visanno.VisualizeAnnotation(image_path, shown_annotations, vis_output_folder, '', '-' + str(i) + '-ori')
        visanno.VisualizeAnnotation(img_output_path, resized_annotations, vis_output_folder, '', '-rsz')
        normalized_vis_path = os.path.join(vis_output_folder, visanno.VisualizeAnnotation.get_file_body_name(image_path) + '-' + str(i) + '-nor')
        visanno.VisualizeAnnotation.draw_normalized_annotation(anno_output_path, img_output_path, normalized_vis_path)

def img_check(img_path, crop_bbox):
    with Image.open(img_path) as img:
        img_width, img_height = img.size  
        if img_width != crop_bbox[2] or img_height != crop_bbox[3]:
            print('[crop bbox] ', crop_bbox)            
            print('[img sz] ', img_width, 'x', img_height)
            print('[not equal]')

def unfold_list(alsit, layer):
    print('[layer] ', layer)
    for each in alsit:
        if isinstance(each, list):
            unfold_list(each, layer + 1)
        else:
            print(each)

def test_visualize_a_result(a_bbox_and_anno, rois):
    ''' visualize the annotation on the image 
    '''
    shown_annotations = a_bbox_and_anno[1]
    crop_bbox = a_bbox_and_anno[0]
    bbox_dict = {'confidence': 1.0, 'y': crop_bbox[1], 'x': crop_bbox[0], 'label': 9, 'height': crop_bbox[3], 'width': crop_bbox[2], 'class': 'test'}
    shown_annotations.append(bbox_dict)
    for roi in rois:
        roi_dict = {'confidence': 1.0, 'y': roi['top'], 'x': roi['left'], 'label': 10, 'height': roi['height'], 'width': roi['width'], 'class': 'roi'}
        shown_annotations.append(roi_dict)
    return shown_annotations

def test_visualize_all_result(bbox_and_anno, rois, shown_annotations):
    ''' visualize all the annotation on the image 
    '''
    for each in bbox_and_anno:
        crop_bbox = each[0]
        bbox_dict = {'confidence': 1.0, 'y': crop_bbox[1], 'x': crop_bbox[0], 'label': 9, 'height': crop_bbox[3], 'width': crop_bbox[2], 'class': 'test'}
        shown_annotations.append(bbox_dict)
    for roi in rois:
        roi_dict = {'confidence': 1.0, 'y': roi['top'], 'x': roi['left'], 'label': 10, 'height': roi['height'], 'width': roi['width'], 'class': 'roi'}
        shown_annotations.append(roi_dict)
    return shown_annotations

def get_subclass_annotation(annotation_collection, local_path_name, no_boat = False):
    aggregation_option = [
        { '$match' : {FieldDef.local_path_str: local_path_name} },
        { '$unwind' : "$annotation" },
        { '$sort' : { 'annotation.confidence' : -1} },
        #{ '$match' : {'annotation.class': 'person'} },
        { '$match' : { '$or' : [{'annotation.class': 'bus'}, {'annotation.class': 'truck'}, {'annotation.class': 'bicycle'}, {'annotation.class': 'motorcycle'}, {'annotation.class': 'boat'}] } },
        #{ '$match' : { '$or' : [{'annotation.class': 'person'}] } },        
        { 
            '$group' : 
                {
                    '_id': '$' + FieldDef.local_path_str, 
                    FieldDef.annotation_str: { '$push' : "$annotation" }
                }
        }   
    ]
    aggregation_no_boat_option = [
        { '$match' : {FieldDef.local_path_str: local_path_name} },
        { '$unwind' : "$annotation" },
        { '$sort' : { 'annotation.confidence' : -1} },
        #{ '$match' : {'annotation.class': 'person'} },
        { '$match' : { '$or' : [{'annotation.class': 'bus'}, {'annotation.class': 'truck'}, {'annotation.class': 'bicycle'}, {'annotation.class': 'motorcycle'}] } },
        { 
            '$group' : 
                {
                    '_id': '$' + FieldDef.local_path_str, 
                    FieldDef.annotation_str: { '$push' : "$annotation" }
                }
        }   
    ]
    if no_boat:
        aggregation_option = aggregation_no_boat_option
    doc = annotation_collection.aggregate(aggregation_option)
    anno = []
    for item in doc:
        anno = item[FieldDef.annotation_str]
    return anno

def get_sorted_gt_annotation(annotation_collection, local_path_name, no_boat = False):
    aggregation_option = [
        { '$match' : {FieldDef.local_path_str: local_path_name} },
        { '$unwind' : "$annotation" },
        { '$sort' : { 'annotation.confidence' : -1} },
        { 
            '$group' : 
                {
                    '_id': '$' + FieldDef.local_path_str, 
                    FieldDef.annotation_str: { '$push' : "$annotation" }
                }
        }   
    ]
    aggregation_no_boat_option = [
        { '$match' : {FieldDef.local_path_str: local_path_name} },
        { '$unwind' : "$annotation" },
        { '$sort' : { 'annotation.confidence' : -1} },
        { '$match' : { '$or' : [{'annotation.class': 'person'}, {'annotation.class': 'face'}, {'annotation.class': 'car'}, {'annotation.class': 'bus'}, {'annotation.class': 'truck'}, {'annotation.class': 'bicycle'}, {'annotation.class': 'motorcycle'}] } },
        { 
            '$group' : 
                {
                    '_id': '$' + FieldDef.local_path_str, 
                    FieldDef.annotation_str: { '$push' : "$annotation" }
                }
        }   
    ]
    if no_boat:
        aggregation_option = aggregation_no_boat_option
    doc = annotation_collection.aggregate(aggregation_option)
    doc = annotation_collection.aggregate(aggregation_option)
    anno = []
    for item in doc:
        anno = item[FieldDef.annotation_str]
    return anno

def get_annotation(annotation_collection, local_path_name):
    doc = annotation_collection.find({FieldDef.local_path_str:local_path_name})
    anno = []
    for item in doc:
        anno = item[FieldDef.annotation_str]
    return anno

@fapi.ioframe
def run_all(out_dir):
    mongoDB_server = 'mongodb://apps01:27017'
    #collection_list = ['detrac_train_raw', 'youtube_batch1_raw']
    #collection_list = ['youtube_batch1_raw']
    #collection_list = ['detrac_train_raw']
    #collection_list = ['night_annotations_with_faces_raw', 'subclass_batch1_with_faces_raw', 'subclass_batch2_part1_with_faces_raw', \
    #    'subclass_batch2_part2_with_faces_raw', 'subclass_batch3_with_faces_raw']
    #collection_list = ['subclass_batch1_with_faces_raw', 'subclass_batch2_part1_with_faces_raw', 'subclass_batch2_part2_with_faces_raw', 'subclass_batch3_with_faces_raw', 'night_annotations_with_faces_raw']
    #collection_list = ['subclass_batch2_part1_with_faces_raw', 'subclass_batch2_part2_with_faces_raw', 'subclass_batch3_with_faces_raw', 'night_annotations_with_faces_raw']
    collection_list = ['subclass_batch1_with_faces_raw', 'subclass_batch2_part1_with_faces_raw', 'subclass_batch2_part2_with_faces_raw', \
            'subclass_batch3_with_faces_raw', 'night_annotations_with_faces_raw', \
            'detrac_train_raw', 'youtube_batch1_raw']
    #collection_list = ['subclass_batch3_with_faces_raw']
    for collection_name in collection_list:
        if 'detrac' in collection_name:
            no_boat = True
        else:
            no_boat = False
        print('[skip boat] ', no_boat)
        run(mongoDB_server, out_dir, collection_name, no_boat, is_visualized = True, is_test = False)


if __name__ == '__main__':
    run_all()
