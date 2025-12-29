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
Video2DResult.py

This module defines a result for a 2D pose estimation of a video.

Author: Jonas David Stephan, Nathalie Dollmann, Benjamin Ernst Otto Bruch
Date: 2025-12-09
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
from dataclasses import dataclass
from typing import List
from .Image2DResult import Image2DResult

@dataclass
class Video2DResult:
    """
        frame_results:    list of Image2DResult for each frame
        total_frames:     total number of frames
        fps:              frames per second
        processing_time:  time of processing (seconds)
    """
    frame_results: List[Image2DResult]
    total_frames: int
    fps: float
    processing_time: float