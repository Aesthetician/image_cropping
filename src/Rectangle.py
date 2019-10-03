class Rectangle:
    def __init__(self, x1, y1, x2, y2):
        '''
        x1, y1: min x and y of the rectangle, left bottom point
        x2, y2: max x and y of the rectangle, right top point 
        '''
        if x1 > x2 or y1 > y2:
            raise ValueError('[Error] it violates, x1 < x2 and y1 < y2')
        else:
            self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

    def is_intersected(self, other):
        if self.x1 > other.x2 or self.x2 < other.x1 or self.y1 > other.y2 or self.y2 < other.y1:
            return False
        else:
            return True

    @staticmethod
    def convert_bbox_to_2points(bbox):
        '''
        return
            rectangle: [x_min, y_min, x_max, y_max]
        '''
        return [bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]]

    def __and__(self, other):
        if self.is_intersected(other):
            x1 = max(self.x1, other.x1)
            y1 = max(self.y1, other.y1)
            x2 = min(self.x2, other.x2)
            y2 = min(self.y2, other.y2)
            return Rectangle(x1, y1, x2, y2)
        else:
            return Rectangle(0, 0, 0, 0)

    def get_bbox(self):
        '''
        return 
            bbox: [x, y, width, height]
        '''
        return [self.x1, self.y1, self.x2 - self.x1, self.y2 - self.y1]

    def get_area(self):
        return (self.x2 - self.x1) * (self.y2 - self.y1)
