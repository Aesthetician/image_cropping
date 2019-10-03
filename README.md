## Generate Cropped Images and Annotations based on Given ROI 

Overview: within a given ROI, cropping images with emphasizing the subclass of interest. 

### Introduction

1. Cropping Method
    - Please refer to the [confluence page](https://confluence.york.lan/display/BOSTONENG/Image+Cropping+within+ROIs)

2. Format Assumption 

### Installation 

- installation manually 
    1. Python 3.5.2

    2. PyMongo

```bash
python -m pip install pymongo
```

- Or you can use the virtual environment on the cental by running the following script. 

```bash
cd <path_to_object_detection_training_tools>/env_setup
source set_env.sh
```


### Usage

0. copy image sources from liquid_nas to local disk
    - liquid_nas: /mnt/liquid_nas/VALObjectDetectionDataCenter/<image_raw> 
    - local disk : /mnt/data-pcie1/<your_dir_name>/VALObjectDetectonDataCenter/<image_raw>
    - the images are cloned from liquid_nas to local machine before starting cropping.


```python
# in roi_image_cropping.py
def convert_path_root(a_path):
# line 87
    converted_path = a_path.replace('/mnt/liquid_nas','/mnt/data-pcie1/<dir_name>')
```

1. Define Input/output info in the script 
    - input : list of the image source in mongoDB
    - output : images and annotations  

```python
# in ./src/roi_image_cropping_mp.py
# line 273
def run_all(out_dir):
# line 274: define mongodb server address
    mongoDB_server = 'mongodb://apps01:27017'
# line 275: define the collection list on mongodb
    collection_list = ['subclass_batch1_with_faces_raw', 'subclass_batch2_part1_with_faces_raw', 'subclass_batch2_part2_with_faces_raw', 'subclass_batch3_with_faces_raw', 'night_annotations_with_faces_raw']

```

```bash
# define output path in gen_cropped_images_and_annotaions.sh
OUT=<path_of_output>
# Example
OUT="/mnt/data-pcie1/zf.working/working/roi_cropping/subclass"
```

2. Run the script 

```bash
bash gen_cropped_images_and_annotations.sh
```

### Advanced Notice 

1. How to modify the subclass of interest
    - add or delete the class name in "roi_image_cropping_mp.py"
        - {'annotation.class': 'bus'}
    - modify line 198 as the following

```python
# in file, roi_image_cropping_mp.py.
def get_subclass_annotation(annotation_collection, local_path_name, no_boat = False):
    aggregation_option = [
        { '$match' : {FieldDef.local_path_str: local_path_name} },
        { '$unwind' : "$annotation" },
        { '$sort' : { 'annotation.confidence' : -1} },
        #line 198
        { '$match' : { '$or' : [{'annotation.class': 'bus'}, {'annotation.class': 'truck'}, {'annotation.class': 'bicycle'}, {'annotation.class': 'motorcycle'}, {'annotation.class': 'boat'}] } },
    # skip...
    ]
```

2. How to adjust the aspec ratio
    - aspect_ratio : aspect ratio 
    - aspect_ratio_threshold : aspect ratio threshold to skip objects  

```python
# ./src/CroppingRegionProplsal.py
# line 238
        width_new, height_new = CroppingRegionProposal.adjust_aspect_ratio(width_tmp, height_tmp, <aspect_ratio>, <aspect_ratio_threshold>)
```



