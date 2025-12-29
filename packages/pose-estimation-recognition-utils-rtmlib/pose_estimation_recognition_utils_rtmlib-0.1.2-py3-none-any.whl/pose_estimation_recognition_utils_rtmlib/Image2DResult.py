# Copyright 2025 Jonas David Stephan, Nathalie Dollmann, Bejamin Ernst Otto Bruch
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
Image2DResult.py

This module defines a result for a 2D pose estimation.

Author: Jonas David Stephan, Nathalie Dollmann, Benjamin Ernst Otto Bruch
Date: 2025-12-09
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
import numpy as np
from dataclasses import dataclass

@dataclass
class Image2DResult:
    """
        frame_idx:     frame number (used for videos)
        keypoints:     array of persons with keypoints [persons, points, X/Y]
        scores:        confidence of every point [persons, confidence]
        bboxes:        box around persons [persons, [x1, y1, x2, y2, confidence]]
        num_persons:   number of persons detected
    """
    frame_idx: int
    keypoints: np.ndarray
    scores: np.ndarray
    bboxes: np.ndarray
    num_persons: int