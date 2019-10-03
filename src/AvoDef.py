class FieldDef:
    annotation_str = 'annotation'
    folder_name_str = 'folder_name'
    local_path_str = 'local_path'
    threshold_str = 'threshold'

class ObjectDef:
    person_str = 'person'
    face_str = 'face'
    bicycle_str = 'bicycle'
    car_str = 'car'
    motorcycle_str = 'motorcycle'
    bus_str = 'bus'
    truck_str = 'truck'
    boat_str = 'boat'
    test_str = 'test'
    person_id = 1
    face_id = 2
    bicycle_id = 3
    car_id = 4
    motorcycle_id = 5
    bus_id = 6
    truck_id = 7
    boat_id = 8
    test_id = 9

    avo_labelmap = {
        person_id: person_str,
        face_id: face_str,
        bicycle_id: bicycle_str,
        car_id: car_str,
        motorcycle_id: motorcycle_str,
        bus_id: bus_str,
        truck_id: truck_str,
        boat_id: bus_str,
        test_id: test_str
        }

    avo_idmap = {
        person_str: person_id,
        face_str: face_id,
        bicycle_str: bicycle_id,
        car_str: car_id,
        motorcycle_str: motorcycle_id,
        bus_str: bus_id,
        truck_str: truck_id,
        boat_str: bus_id,
        test_str: test_id
        }

class AnnotationDef:
    height_str = 'height'
    width_str = 'width'
    confidence_str = 'confidence'
    class_str = 'class'
    label_str = 'label'
    x_str = 'x'
    y_str = 'y'
   
