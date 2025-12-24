from dconvexhull import convxHull

ptc = [
    [2.0, 3.0],
    [5.0, 1.0],
    [4.0, 3.0],
    [2.0, 8.0],
    [1.0, 6.0],
    [6.0, 5.0],
    [3.0, 4.0],
    [1.0, 1.0],
    [4.0, 9.0]
    ]

# xx = ConvHull()
# for i in xx.draw_convHull(ptc):
#     # print(i)
#     ...
# convxHull.draw_convxHull_from_arr(ptc)
convxHull.draw_convxHull_from_csv("data.csv")


