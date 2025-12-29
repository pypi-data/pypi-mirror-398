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
RTMPoseNames.py

This module provides a class to get keypoint names for RTMLib's 17-point and 133-point models.

Author: Jonas David Stephan, Nathalie Dollmann
Date: 2025-12-19
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
class RTMPoseNames:
    """
    A class to get keypoint names for RTMLib's 17-point and 133-point models.
    Indexing starts at 0.
    """

    def __init__(self, model_type:int = '17'):
        """
        Initialize the keypoint names for the specified model.

        Args:
            model_type: Either '17' for 17-point model or '133' for 133-point model

        Raises:
            ValueError: If model_type is not '17' or '133'
        """
        self.model_type=str(model_type)

        if self.model_type == '17':
            self._names_17=self._get_17_keypoint_names()
            self.names=self._names_17
            self.num_points=17
        elif self.model_type == '133':
            self._names_133=self._get_133_keypoint_names()
            self.names=self._names_133
            self.num_points=133
        else:
            raise ValueError(f"Model type must be '17' or '133', got '{model_type}'")

    @staticmethod
    def _get_17_keypoint_names():
        """
        Get names for the 17-point COCO model.

        Returns:
            List of 17 keypoint names.
        """
        return [
            'nose',
            'left_eye',
            'right_eye',
            'left_ear',
            'right_ear',
            'left_shoulder',
            'right_shoulder',
            'left_elbow',
            'right_elbow',
            'left_wrist',
            'right_wrist',
            'left_hip',
            'right_hip',
            'left_knee',
            'right_knee',
            'left_ankle',
            'right_ankle'
        ]

    def _get_133_keypoint_names(self):
        """
        Get names for the 133-point COCO-WholeBody model.
        
        Returns:
            List of 133 keypoint names.
        """
        names=[]
        body_names=self._get_17_keypoint_names()
        names.extend(body_names)

        foot_names=[
            'left_big_toe',
            'left_small_toe',
            'left_heel',
            'right_big_toe',
            'right_small_toe',
            'right_heel'
        ]
        names.extend(foot_names)

        for i in range(17):
            names.append(f'jaw_{i}')

        for i in range(5):
            names.append(f'left_eyebrow_{i}')

        for i in range(5):
            names.append(f'right_eyebrow_{i}')

        for i in range(9):
            names.append(f'nose_{i}')

        for i in range(6):
            names.append(f'left_eye_{i}')

        for i in range(6):
            names.append(f'right_eye_{i}')

        for i in range(20):
            names.append(f'mouth_{i}')

        left_hand_names=[
            'left_wrist_hand',
            'left_thumb_1', 'left_thumb_2', 'left_thumb_3', 'left_thumb_tip',
            'left_index_1', 'left_index_2', 'left_index_3', 'left_index_tip',
            'left_middle_1', 'left_middle_2', 'left_middle_3', 'left_middle_tip',
            'left_ring_1', 'left_ring_2', 'left_ring_3', 'left_ring_tip',
            'left_pinky_1', 'left_pinky_2', 'left_pinky_3', 'left_pinky_tip'
        ]
        names.extend(left_hand_names)

        right_hand_names=[
            'right_wrist_hand',
            'right_thumb_1', 'right_thumb_2', 'right_thumb_3', 'right_thumb_tip',
            'right_index_1', 'right_index_2', 'right_index_3', 'right_index_tip',
            'right_middle_1', 'right_middle_2', 'right_middle_3', 'right_middle_tip',
            'right_ring_1', 'right_ring_2', 'right_ring_3', 'right_ring_tip',
            'right_pinky_1', 'right_pinky_2', 'right_pinky_3', 'right_pinky_tip'
        ]
        names.extend(right_hand_names)

        return names

    def get_name(self, index):
        """
        Get the keypoint name for the given index.

        Args:
            index: Integer index of the keypoint (0-based)

        Returns:
            String name of the keypoint
        """
        if index < 0 or index >= len(self.names):
            raise IndexError(f"Index {index} out of range for {self.model_type}-point model (0-{len(self.names) - 1})")
        return self.names[index]

    def __getitem__(self, index):
        """
        Allow dictionary-like access with square brackets.
        
        Args:
            index: Integer index of the keypoint (0-based)
            
        Returns:
            String name of the keypoint
        """
        return self.get_name(index)

    def __len__(self):
        """
        Return the number of keypoints in the model.
        
        Returns:
            Integer number of keypoints
        """
        return self.num_points

    def get_all_names(self):
        """
        Get all keypoint names as a list.
        
        Returns:
            List of all keypoint names
        """
        return self.names.copy()

    def find_index(self, name):
        """
        Find the index of a keypoint by name.

        Args:
            name: String name of the keypoint

        Returns:
            Integer index of the keypoint, or -1 if not found
        """
        try:
            return self.names.index(name)
        except ValueError:
            return -1

    def get_body_part(self, index) -> str:
        """
        Get the body part category for a keypoint.

        Args:
            index: Integer index of the keypoint (0-based)

        Returns:
            String category: 'body', 'foot', 'face', 'left_hand', or 'right_hand'
        """
        if self.model_type == '17':
            return 'body'

        if index < 17:
            return 'body'
        elif index < 23:
            return 'foot'
        elif index < 91:
            return 'face'
        elif index < 112:
            return 'left_hand'
        else:
            return 'right_hand'

    def print_summary(self):
        """
        Print a summary of the keypoint model.
        """
        print(f"RTMLib Keypoint Model: {self.model_type}-point")
        print(f"Total keypoints: {self.num_points}")

        if self.model_type == '133':
            categories={
                'body': (0, 16),
                'foot': (17, 22),
                'face': (23, 90),
                'left_hand': (91, 111),
                'right_hand': (112, 132)
            }

            print("\nBreakdown by body part:")
            for category, (start, end) in categories.items():
                count=end - start + 1
                print(f"  {category}: {count} keypoints (indices {start}-{end})")