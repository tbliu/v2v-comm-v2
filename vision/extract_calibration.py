'''
Grab the existing calibration data from the yaml file
to run before tracking any aruco markers or boards
'''

import cv2

# FILE_STORAGE_READ
cv_file = cv2.FileStorage("calibration/calibration.yaml", cv2.FILE_STORAGE_READ)

# Note : we also have to specify the type to retrieve otherwise we only get a
# FileNode object back instead of a matrix
camera_matrix = cv_file.getNode("camera_matrix").mat()
dist_matrix = cv_file.getNode("dist_coeff").mat()

# print("camera_matrix : ", camera_matrix.tolist())
# print("dist_matrix : ", dist_matrix.tolist())

cv_file.release()
