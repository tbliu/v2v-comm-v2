#!usr/bin/env python

'''
Track the pose of a pre-generated aruco grid board and publish the pose of the camera
to a ros topic, also publishes camera images to the /cam_stream topic

Note: a priori grid geometry is imported from consts.py
'''

import numpy as np
import cv2
import cv2.aruco as aruco
import glob
import sys

import rospy
import tf.transformations as tfs # for rotation matrix <> quaternions
import std_msgs.msg # for Header in the stamped point
from geometry_msgs.msg import Point, Quaternion, Pose, PoseStamped, PointStamped # stamped msgs include a header
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

# import files from various directories by modifying the python path
# depending on their location
import extract_calibration

sys.path.append('./create_markers/')
from consts import *

DEBUG = False # outputs pose information to the terminal
DISPLAY = True # this displays camera output to a screen on the machine

# setup ros node and publisher
rospy.init_node('quad_cam', anonymous=True)
pose_pub = rospy.Publisher('cam_pose', PoseStamped, queue_size = 10)
cam_stream_pub = rospy.Publisher('cam_stream', Image, queue_size=10)

loop_rate = 30 # 30 frames per second
rate = rospy.Rate(loop_rate)

# import the grid board geometry to track
board = aruco.GridBoard_create(ROWS, COLS, realMarkerLength, realMarkerSeparation, aruco_dict)
# note this function is deterministic so it will match the board
# generated by `create_board.py` as long as the parameters from
# `consts.py` don't change.

# init video capture
cap = cv2.VideoCapture(0)

# get existing calibration data for pose estimation
mtx = extract_calibration.camera_matrix
dist = extract_calibration.dist_matrix

def print_debug(point, rot_mtx, quats):
    # print the debug pose info to the terminal
    print("translation: ") 
    print(point)
    print("\n")
    print("rotation matrix: ")
    print(rot_mtx)
    print("\n")
    print("quaternions: ")
    print(quats)
    print("--------")

def get_rot_mtx(axis_angle):
    # rvec returned by estimatePoseBoard is an axis-angle repesentation of the rotation
    # the direction of that vector indicates the axis of rotation
    # the length (norm) of the vector gives the angle of rotation about the prescribed axis
    sum_of_squares = 0
    for elem in axis_angle:
        sum_of_squares += elem**2
    angle = np.sqrt(sum_of_squares)

    # returns a rotation matrix in homogeneous transformation form, i.e. a 4x4
    rot_mtx = tfs.rotation_matrix(angle, axis_angle)
    
    return rot_mtx

def board_tracker():
    # initialize the pose
    translation = [0, 0, 0]
    quats = [0, 0, 0, 0]
    bridge = CvBridge()

    while not rospy.is_shutdown():
        ret, frame = cap.read()

        # convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        parameters = aruco.DetectorParameters_create()

        # we need to detect the markers before trying to detect the board
        corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        # refind not detected markers based on the already detected and the board layout
        aruco.refineDetectedMarkers(gray, board, corners, ids, rejected)
        
        font = cv2.FONT_HERSHEY_SIMPLEX

        if np.all(ids is not None): # if there is at least one detected marker
            # estimate pose
            # The returned transformation is the one that transforms points from the board
            # coordinate system to the camera coordinate system.
            retval, rvec, tvec = aruco.estimatePoseBoard(corners, ids, board, mtx, dist)
            
            # obtain the pose as a 3D point and quaternion orientation
            translation = tvec
            rot_mtx = get_rot_mtx(rvec)

            quats = tfs.quaternion_from_matrix(rot_mtx) # takes a 4x4 transformation

            if DEBUG:
                print_debug(translation, rot_mtx, quats)

            # draw on the frame for each marker and the board's origin
            axisLength = 0.1 # the length in meters of the axis drawn on the board
            aruco.drawAxis(frame, mtx, dist, rvec, tvec, axisLength)
            aruco.drawDetectedMarkers(frame, corners, ids)

        # publish the stamped point
        p = Point(translation[0], translation[1], translation[2])
        q = Quaternion(quats[0], quats[1], quats[2], quats[3])
        pose = Pose(p, q)

        h = std_msgs.msg.Header()
        h.stamp = rospy.Time.now()
        h.frame_id = 'map'

        pose_pub.publish(h, pose)

        # publish the streamed images
        try:
            cam_stream_pub.publish(bridge.cv2_to_imgmsg(frame, "bgr8"))
        except CvBridgeError as e:
            print(e)


        # wait for the amount of time required to achieve the publish rate
        rate.sleep()

        if DISPLAY:
            cv2.imshow('frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # release the capture
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    try:
       board_tracker()
    except rospy.ROSInterruptException:
        pass
