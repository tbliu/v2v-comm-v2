#!usr/bin/env python

'''
The difference between this python script and `talker.py` is that 
`talker.py` extracts pose from individual markers, while this file
extracts the pose from an aruco board

Reference: https://github.com/treyfortmuller/rosflight_aruco/blob/master/aruco_tracker/aruco_tracker.py
'''

import numpy as np
import cv2
import cv2.aruco as aruco
import glob
import extract_calibration
#import rospy
from consts import *

# TODO add display stuff

DEBUG = 1
DISPLAY = 1 # this displays camera output to a screen on the machine
board = aruco.GridBoard_create(ROWS, COLS, markerLength, markerSeparation, aruco_dict)

# generate the aruco board
# note this function is deterministic so it will match the board
# generated by `create_board.py` as long as the parameters from
# `consts.py` don't change.

# init video capture
cap = cv2.VideoCapture(0)

# get existing calibration data for pose estimation
mtx = extract_calibration.camera_matrix
dist = extract_calibration.dist_matrix

while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
    parameters = aruco.DetectorParameters_create()

    # we need to detect the markers before trying to detect the board
    corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    aruco.refineDetectedMarkers(gray, board, corners, ids, rejected)
    font = cv2.FONT_HERSHEY_SIMPLEX

    if np.all(ids != None):
        # estimate pose
        retval, rvec, tvec = aruco.estimatePoseBoard(corners, ids, board, mtx, dist)
        aruco.drawAxis(frame, mtx, dist, rvec, tvec, 0.1)
        print(tvec)
        aruco.drawDetectedMarkers(frame, corners, ids)

        cv2.putText(frame, "ID: " + str(ids), (0,64), font, 1, (0,255,0), 2, cv2.LINE_AA)
        

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release the capture
cap.release()
cv2.destroyAllWindows()

