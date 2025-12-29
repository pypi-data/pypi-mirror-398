# Copyright 2025 Nathalie Dollmann, Jonas David Stephan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
RTMPoseEstimationFrom3DFrame.py

This module defines a class for extracting Pose Estimation from 3D frames with RTM Lib.

Author: Nathalie Dollmann, Jonas David Stephan
Date: 2025-12-10
License: Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
"""

from pose_estimation_recognition_utils import (SAD, SkeletonDataPoint, SkeletonDataPointWithName,
                                               SkeletonDataPointWithConfidence, SkeletonDataPointWithNameAndConfidence)
from .RTMPoseNames import RTMPoseNames
from .rtm_pose_estimator_2d import RTMPoseEstimator2D
from .utils import (image2d_result_to_save_2d_data_with_confidence)
import numpy as np
from typing import List, Union, Tuple

def add_names_to_result(result, RTMPoseNames):
    """
    Add names to the skeleton data points in the result.

    Args:
        result (List[SkeletonDataPoint]): List of skeleton data points without names.
        RTMPoseNames (RTMPoseNames): Instance of RTMPoseNames to get joint names.

    Returns:
        back (List[SkeletonDataPointWithName]): List of skeleton data points with names.
    """
    back = []
    for point in result:
        name = RTMPoseNames.get_name(point.id)
        back.append(SkeletonDataPointWithName(point.id, name, point.x, point.y, point.z))
    return back

def add_confidence_to_result(result, pixel_list_left, pixel_list_right):
    """
    Add confidence to the skeleton data points in the result.

    Args:
        result (List[SkeletonDataPoint]): List of skeleton data points without confidence.
        pixel_list_left (List[Save2DDataWithConfidence]): List of 2D data points from the left image with confidence.
        pixel_list_right (List[Save2DDataWithConfidence]): List of 2D data points from the right image with confidence.

    Returns:
        back (List[SkeletonDataPointWithConfidence]): List of skeleton data points with confidence.
    """
    back = []
    for point in result:
        confidence_left = next((p.confidence for p in pixel_list_left if p.id == point.id), 0)
        confidence_right = next((p.confidence for p in pixel_list_right if p.id == point.id), 0)
        if confidence_left < confidence_right:
            confidence = confidence_left
        else:
            confidence = confidence_right
        back.append(SkeletonDataPointWithConfidence(point.id, point.x, point.y, point.z, confidence))
    return back

def add_names_and_confidence_to_result(result, pixel_list_left, pixel_list_right):
    """
    Add names and confidence to the skeleton data points in the result.

    Args:
        result (List[SkeletonDataPoint]): List of skeleton data points without name and confidence.
        pixel_list_left (List[Save2DDataWithConfidence]): List of 2D data points from the left image with confidence.
        pixel_list_right (List[Save2DDataWithConfidence]): List of 2D data points from the right image with confidence.

    Returns:
        back (List[SkeletonDataPointWithNameAndConfidence]): List of skeleton data points with names and confidence.
    """
    back = []
    for point in result:
        name = RTMPoseNames.get_name(point.id)
        confidence_left = next((p.confidence for p in pixel_list_left if p.id == point.id), 0)
        confidence_right = next((p.confidence for p in pixel_list_right if p.id == point.id), 0)
        if confidence_left < confidence_right:
            confidence = confidence_left
        else:
            confidence = confidence_right
        back.append(SkeletonDataPointWithNameAndConfidence(point.id, name, point.x, point.y, point.z, confidence))
    return back

class RTMPoseEstimationFrom3DFrame:
    
    def __init__(self,
                 focal_length: float,
                 distance: float, 
                 cx_left: int, 
                 cy_left: int, 
                 with_names: bool = False,
                 with_confidence: bool = False,
                 mode: str = 'performance',
                 backend: str = 'onnxruntime',
                 device: str = 'cpu',
                 to_openpose: bool = False,
                 kpt_threshold: float = 0.8,
                 det_model_path: str = None,
                 pose_model_path: str = None,
                 pose_input_size: tuple = (288, 384),
                 det_input_size: tuple = (640, 640)
                 ):
        
        """
        Initialize a new SkeletonDataPoint instance.

        Args:
            focal_length (float): Focal length of the camera.
            distance (float): Distance between the two cameras.
            cx_left (int): Principal point x-coordinate of the left camera.
            cy_left (int): Principal point y-coordinate of the left camera.
            with_names (bool): Whether to include joint names in the output.
            with_confidence (bool): Whether to include confidence scores in the output.
            mode (str): Mode for pose estimation: 'performance', 'balanced', 'lightweight', 'individual'.
            backend (str): Backend for RTM Lib: 'onnxruntime', 'tensorflow', 'torch'.
            device (str): Device for RTM Lib: 'cpu', 'cuda', 'mps'.
            to_openpose (bool): Whether to convert keypoints to OpenPose format.
            kpt_threshold (float): Keypoint threshold for RTM Lib.
            det_model_path (str): Path to the detection model.
            pose_model_path (str): Path to the pose model.
            pose_input_size (tuple): Input size for the pose model.
            det_input_size (tuple): Input size for the detection model.
            model (RTMPoseEstimator2D): Instance of RTMPoseEstimator2D for 2D pose estimation.
            sad (SAD): Instance of SAD for 3D pose estimation. 

        Raises:
            ValueError: If mode is not allowed.
        """
        
        # Initialize pose estimation class
        self.model = RTMPoseEstimator2D(
            mode=mode,
            backend=backend,
            device=device,
            to_openpose=to_openpose,
            kpt_threshold=kpt_threshold,
            det_model_path=det_model_path,
            pose_model_path=pose_model_path,
            pose_input_size=pose_input_size,
            det_input_size=det_input_size
        )
        self.sad: SAD = SAD(focal_length, distance, cx_left, cy_left)
       
        self.with_names: bool = with_names
        if with_names:
            self.RTMPoseNames = RTMPoseNames()

        self.with_confidence = with_confidence

    def extract_frame(self, frame: np.ndarray) -> List[Union[SkeletonDataPoint, SkeletonDataPointWithName,
                                                             SkeletonDataPointWithConfidence,
                                                             SkeletonDataPointWithNameAndConfidence]]:

        """
        Extracts frames in two frames with pixel.

        Args:
            frame (np.ndarray): Video frame

        Returns:
            result: List[Union[SkeletonDataPoint, SkeletonDataPointWithName, SkeletonDataPointWithConfidence,
                                                             SkeletonDataPointWithNameAndConfidence]]: 3D coordinates
        """

        frame_left, frame_right = self.divide_3d_frame(frame)

        #detecting the object using rtmlib
        results_left = self.model.process_image(frame_left)
        results_right = self.model.process_image(frame_right)

        pixel_list_left = image2d_result_to_save_2d_data_with_confidence(results_left)
        pixel_list_right = image2d_result_to_save_2d_data_with_confidence(results_right)

        result = self.sad.merge_pixel(pixel_list_left, pixel_list_right)

        if self.with_confidence:
            if self.with_names:
                result = add_names_and_confidence_to_result(result, pixel_list_left, pixel_list_right)
            else:
                result = add_confidence_to_result(result, pixel_list_left, pixel_list_right)
        else:
            if self.with_names:
                result = add_names_to_result(result, self.RTMPoseNames)

        return result
        
    @staticmethod
    def divide_3d_frame(frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """
        Divides 3D frame in two frames.

        Args:
            frame (np.ndarray): Video frame

        Returns:
            Tuple[np.ndarray, np.ndarray]: left frame and right frame
        """

        frame_width = frame.shape[1]
        dividing_point = frame_width//2
        frame_left = frame[:, :dividing_point]
        frame_right = frame[:, dividing_point:]
        return (frame_left, frame_right)