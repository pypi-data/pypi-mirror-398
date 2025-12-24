from . import convhull
from . import graphConv

class ConvHull:
    '''The Convex Class: to construct the convex line of 2D list'''
    def __init__(self):
        self._cov_vertics = []
    
    def draw_convHull(self, vertices):
        '''The main function to build, construct and draw the convex'''
        if (len(vertices) >= 3):
            try:
                convObj = convhull.ConvexHull(vertices)
                for i in convObj.convArr():
                    self._cov_vertics.append([i.x, i.y]) 
                graphConv.graph2d_(vertices, self._cov_vertics)
                return self._cov_vertics
            
            except Exception as e:
                print(f" ERROR: {e}")
        
        else: print(f"The list of vertices Must be at least three verticeses of TWO DIMENSIONS!")

def draw_convxHull_from_arr(vertics):
    if (isinstance(vertics, list) and
        len(vertics) > 3 and
        all(isinstance(row, list) for row in vertics)):
        obj = ConvHull()
        obj.draw_convHull(vertics)
    else:
        print(f"The list of vertices Must be at least three verticeses of TWO DIMENSIONS!")

def draw_convxHull_from_csv(path_to_vertics):
    import csv

    extract_vertics = []
    try:
        with open(path_to_vertics, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    x1 = float(row[0])
                    y1 = float(row[1])
                    extract_vertics.append([x1, y1])
                    # print(float(row))
                except:
                    print ("Your CSV file must have contained a non-numerical values or empty cell. make sure all are numerical and no missing values")
                    extract_vertics = []
                    break
            if extract_vertics:
                draw_convxHull_from_arr(extract_vertics)
            else:
                print("Process of extracting the vertics from the CSV is not successful")
    except:
        print("No such CSV file in the path")




