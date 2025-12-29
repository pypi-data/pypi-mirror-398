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
Image3DResult.py

This module defines a result for a 3D pose estimation.

Author: Jonas David Stephan, Nathalie Dollmann
Date: 2025-12-09
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
import numpy as np
from dataclasses import dataclass

@dataclass
class Image3DResult:
    """
        frame_idx:     frame number (used for videos)
        keypoints_3d:     array of persons with keypoints [persons, points, X/Y/Z]
        keypoints_2d:     array of persons with keypoints [persons, points, X/Y]
        scores_3d:        accuracy of every point [persons, accuracies]
        scores_2d:        accuracy of every point [persons, accuracies]
        bboxes_3d:        box around persons (3d) [persons, [p1, p2, p3, p4, accuracy]]
        bboxes_2d:        box around persons (2d) [persons, [p1, p2, p3, p4, accuracy]]
        num_persons:   number of persons detected
        method:         method of pose estimation
    """
    frame_idx: int
    keypoints_3d: np.ndarray   # Shape: [persons, 133, 3]
    keypoints_2d: np.ndarray   # Shape: [persons, 133, 2]
    scores_3d: np.ndarray      # Shape: [persons, 133]
    scores_2d: np.ndarray      # Shape: [persons, 133]
    bboxes_3d: np.ndarray      # Shape: [persons, 7] (x, y, z, w, h, d, confidence)
    bboxes_2d: np.ndarray      # Shape: [persons, 5] (x1, y1, x2, y2, confidence)
    num_persons: int
    method: str