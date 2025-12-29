# Copyright 2025 Jonas David Stephan, Nathalie Dollmann
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
utils.py

This module provides utility functions for converting between different data structures.

Author: Jonas David Stephan, Nathalie Dollmann
Date: 2025-12-19
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
from typing import List

from .Image2DResult import Image2DResult
from .Image3DResult import Image3DResult
from .RTMPoseNames import RTMPoseNames
from .Video3DResult import Video3DResult

from pose_estimation_recognition_utils import (Save2DData, Save2DDataWithConfidence, Save2DDataWithName,
                                               Save2DDataWithNameAndConfidence, SkeletonDataPoint,
                                               SkeletonDataPointWithConfidence, SkeletonDataPointWithName,
                                               SkeletonDataPointWithNameAndConfidence, ImageSkeletonData,
                                               VideoSkeletonData)

def image2d_result_to_save_2d_data(result: Image2DResult) -> List[Save2DData]:
    '''
    Function to convert Image2DResult to a list of Save2DData.

    Args:
        result (Image2DResult): The input Image2DResult object.

    Returns:
        List[Save2DData]: A list of Save2DData objects.
    '''
    back = []
    i = 0

    for point in result.keypoints[0]:
        back.append(Save2DData(i, point[0], point[1]))
        i+=1

    return back

def image2d_result_to_save_2d_data_with_confidence(result: Image2DResult) -> List[Save2DDataWithConfidence]:
    '''
    Function to convert Image2DResult to a list of Save2DDataWithConfidence.

    Args:
        result (Image2DResult): The input Image2DResult object.

    Returns:
        List[Save2DDataWithConfidence]: A list of Save2DDataWithConfidence objects.
    '''
    back = []
    i = 0

    for point in result.keypoints[0]:
        back.append(Save2DDataWithConfidence(i, point[0], point[1], result.scores[0][i]))
        i+=1

    return back

def image2d_result_to_save_2d_data_with_name(result: Image2DResult) -> List[Save2DDataWithName]:
    '''
    Function to convert Image2DResult to a list of Save2DDataWithName.

    Args:
        result (Image2DResult): The input Image2DResult object.

    Returns:
        List[Save2DDataWithName]: A list of Save2DDataWithName objects.
    '''
    name_list = RTMPoseNames(model_type=result.keypoints[0].shape[0])
    back = []
    i = 0

    for point in result.keypoints[0]:
        back.append(Save2DDataWithName(i, name_list.get_name(i), point[0], point[1]))
        i+=1

    return back

def image2d_result_to_save_2d_data_with_name_and_confidence(result: Image2DResult) -> List[Save2DDataWithNameAndConfidence]:
    '''
    Function to convert Image2DResult to a list of Save2DDataWithNameAndConfidence.

    Args:
        result (Image2DResult): The input Image2DResult object.

    Returns:
        List[Save2DDataWithNameAndConfidence]: A list of Save2DDataWithNameAndConfidence objects.
    '''
    name_list=RTMPoseNames(model_type=result.keypoints[0].shape[0])
    back=[]
    i=0

    for point in result.keypoints[0]:
        back.append(Save2DDataWithNameAndConfidence(i, name_list.get_name(i), point[0], point[1], result.scores[0][i]))
        i+=1

    return back

def image3d_result_to_skeleton_data_point(result: Image3DResult) -> List[SkeletonDataPoint]:
    '''
    Function to convert Image3DResult to a list of SkeletonDataPoint.

    Args:
        result (Image3DResult): The input Image3DResult object.

    Returns:
        List[SkeletonDataPoint]: A list of SkeletonDataPoint objects.  
    '''
    back = []
    i=0
    for point in result.keypoints_3d[0]:
        back.append(SkeletonDataPoint(i, point[0], point[1], point[2]))
        i+=1

    return back

def image3d_result_to_skeleton_data_point_with_confidence(result: Image3DResult) -> List[SkeletonDataPointWithConfidence]:
    '''
    Function to convert Image3DResult to a list of SkeletonDataPointWithConfidence.

    Args:
        result (Image3DResult): The input Image3DResult object.

    Returns:
        List[SkeletonDataPointWithConfidence]: A list of SkeletonDataPointWithConfidence objects. 
    '''
    back = []
    i=0

    for point in result.keypoints_3d[0]:
        back.append(SkeletonDataPointWithConfidence(i, point[0], point[1], point[2], result.scores_3d[0][i]))
        i+=1

    return back

def image3d_result_to_skeleton_data_point_with_name(result: Image3DResult) -> List[SkeletonDataPointWithName]:
    '''
    Function to convert Image3DResult to a list of SkeletonDataPointWithName.

    Args:
        result (Image3DResult): The input Image3DResult object.

    Returns:
        List[SkeletonDataPointWithName]: A list of SkeletonDataPointWithName objects.
    '''
    name_list=RTMPoseNames(model_type=result.keypoints_3d[0].shape[0])
    back = []
    i=0

    for point in result.keypoints_3d[0]:
        back.append(SkeletonDataPointWithName(i, name_list.get_name(i), point[0], point[1], point[2]))
        i+=1

    return back

def image3d_result_to_skeleton_data_point_with_name_and_confidence(result: Image3DResult) -> List[SkeletonDataPointWithConfidence]:
    '''
    Function to convert Image3DResult to a list of SkeletonDataPointWithNameAndConfidence.

    Args:
        result (Image3DResult): The input Image3DResult object.

    Returns:
        List[SkeletonDataPointWithNameAndConfidence]: A list of SkeletonDataPointWithNameAndConfidence objects.
    '''
    name_list=RTMPoseNames(model_type=result.keypoints_3d[0].shape[0])
    back = []
    i=0

    for point in result.keypoints_3d[0]:
        back.append(SkeletonDataPointWithNameAndConfidence(i, name_list.get_name(i), point[0], point[1], point[2], result.scores_3d[0][i]))
        i+=1

    return back

def image3d_result_to_image_skeleton_data(result: Image3DResult) -> ImageSkeletonData:
    '''
    Function to convert Image3DResult to a list of ImageSkeletonData.

    Args:
        result (Image3DResult): The input Image3DResult object.

    Returns:
        List[ImageSkeletonData]: A list of ImageSkeletonData objects.
    '''
    back = ImageSkeletonData()

    points = image3d_result_to_skeleton_data_point(result)

    for point in points:
        back.add_data_point(point)

    return back

def image3d_result_to_image_skeleton_data_with_confidence(result: Image3DResult) -> ImageSkeletonData:
    '''
    Function to convert Image3DResult to a list of ImageSkeletonData.

    Args:
        result (Image3DResult): The input Image3DResult object.

    Returns:
        List[ImageSkeletonData]: A list of ImageSkeletonData objects.
    '''
    back = ImageSkeletonData()

    points = image3d_result_to_skeleton_data_point_with_confidence(result)

    for point in points:
        back.add_data_point(point)

    return back

def image3d_result_to_image_skeleton_data_with_name(result: Image3DResult) -> ImageSkeletonData:
    '''
    Function to convert Image3DResult to a list of ImageSkeletonData.

    Args:
        result (Image3DResult): The input Image3DResult object.

    Returns:
        List[ImageSkeletonData]: A list of ImageSkeletonData objects.
    '''
    back = ImageSkeletonData()

    points = image3d_result_to_skeleton_data_point_with_name(result)

    for point in points:
        back.add_data_point(point)

    return back

def image3d_result_to_image_skeleton_data_with_name_and_confidence(result: Image3DResult) -> ImageSkeletonData:
    '''
    Function to convert Image3DResult to a list of ImageSkeletonData.

    Args:
        result (Image3DResult): The input Image3DResult object.

    Returns:
        List[ImageSkeletonData]: A list of ImageSkeletonData objects.
    '''
    back = ImageSkeletonData()

    points = image3d_result_to_skeleton_data_point(result)

    for point in points:
        back.add_data_point(point)

    return back

def video3d_result_to_video_skeleton_data(result: Video3DResult) -> List[VideoSkeletonData]:
    '''
    Function to convert Video3DResult to a list of VideoSkeletonData.

    Args:
        result (Video3DResult): The input Video3DResult object.

    Returns:
        List[VideoSkeletonData]: A list of VideoSkeletonData objects.
    '''
    back = []
    i = 0

    for frame in result.frame_results:
        vsd = VideoSkeletonData(i)

        for point in image3d_result_to_skeleton_data_point(frame):
            vsd.add_data_point(point)

        back.append(vsd)
        i+=1

    return back

def video3d_result_to_video_skeleton_data_with_confidence(result: Video3DResult) -> List[VideoSkeletonData]:
    '''
    Function to convert Video3DResult to a list of VideoSkeletonData.

    Args:
        result (Video3DResult): The input Video3DResult object.

    Returns:
        List[VideoSkeletonData]: A list of VideoSkeletonData objects.
    '''
    back = []
    i = 0

    for frame in result.frame_results:
        vsd = VideoSkeletonData(i)

        for point in image3d_result_to_skeleton_data_point_with_confidence(frame):
            vsd.add_data_point(point)

        back.append(vsd)
        i+=1

    return back

def video3d_result_to_video_skeleton_data_with_name(result: Video3DResult) -> List[VideoSkeletonData]:
    '''
    Function to convert Video3DResult to a list of VideoSkeletonData.

    Args:
        result (Video3DResult): The input Video3DResult object.

    Returns:
        List[VideoSkeletonData]: A list of VideoSkeletonData objects.
    '''
    back = []
    i = 0

    for frame in result.frame_results:
        vsd = VideoSkeletonData(i)

        for point in image3d_result_to_skeleton_data_point_with_name(frame):
            vsd.add_data_point(point)

        back.append(vsd)
        i+=1

    return back

def video3d_result_to_video_skeleton_data_with_name_and_confidence(result: Video3DResult) -> List[VideoSkeletonData]:
    '''
    Function to convert Video3DResult to a list of VideoSkeletonData.

    Args:
        result (Video3DResult): The input Video3DResult object.

    Returns:
        List[VideoSkeletonData]: A list of VideoSkeletonData objects.
    '''
    back = []
    i = 0

    for frame in result.frame_results:
        vsd = VideoSkeletonData(i)

        for point in image3d_result_to_skeleton_data_point_with_name_and_confidence(frame):
            vsd.add_data_point(point)

        back.append(vsd)
        i+=1

    return back