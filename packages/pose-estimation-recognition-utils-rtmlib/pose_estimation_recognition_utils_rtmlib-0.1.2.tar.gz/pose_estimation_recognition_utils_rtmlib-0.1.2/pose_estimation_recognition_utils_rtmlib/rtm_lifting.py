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
rtm_lifting.py

This module provides a class to intelligently load and cache models from the Hugging Face Hub.

Author: Jonas David Stephan, Nathalie Dollmann
Date: 2025-12-18
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
from typing import Optional, Any

from numpy import dtype, ndarray, float64

from .model_loader import ModelLoader
from .Image2DResult import Image2DResult
from .Image3DResult import Image3DResult
from .Simple3DPoseLiftingModel import Simple3DPoseLiftingModel
from pose_estimation_recognition_utils import (
    Save2DData,
    Save2DDataWithName,
    Save2DDataWithConfidence,
    Save2DDataWithNameAndConfidence
)
from typing import List, Union
import numpy as np
import torch
import os


def _normalize_by_bounding_box(keypoints: np.ndarray) -> np.ndarray:
    """
    Normalizes keypoints based on their bounding box to the range [-1, 1].

    Args:
        keypoints: array with shape (num_keypoints, 2)

    Returns:
        Normalized array of the same shape
    """
    x_coords = keypoints[:, 0]
    y_coords = keypoints[:, 1]

    min_x, max_x = np.min(x_coords), np.max(x_coords)
    min_y, max_y = np.min(y_coords), np.max(y_coords)

    normalized = keypoints.copy()

    if max_x - min_x > 0:
        normalized[:, 0] = 2 * (x_coords - min_x) / (max_x - min_x) - 1
    else:
        normalized[:, 0] = 0

    if max_y - min_y > 0:
        normalized[:, 1] = 2 * (y_coords - min_y) / (max_y - min_y) - 1
    else:
        normalized[:, 1] = 0

    return normalized


def _denormalize_by_bounding_box(normalized_keypoints: np.ndarray,
                                 original_keypoints: np.ndarray) -> np.ndarray:
    """
    Denormalizes keypoints from the range [-1, 1] back to original bounding box.

    Args:
        normalized_keypoints: normalized array with shape (num_keypoints, 2)
        original_keypoints: original keypoints for bounding box calculation

    Returns:
        Denormalized array of the same shape
    """
    x_coords = original_keypoints[:, 0]
    y_coords = original_keypoints[:, 1]
    min_x, max_x = np.min(x_coords), np.max(x_coords)
    min_y, max_y = np.min(y_coords), np.max(y_coords)


    denormalized = normalized_keypoints.copy()
    denormalized[:, 0] = (normalized_keypoints[:, 0] + 1) / 2 * (max_x - min_x) + min_x
    denormalized[:, 1] = (normalized_keypoints[:, 1] + 1) / 2 * (max_y - min_y) + min_y

    return denormalized


def _calculate_3d_bboxes(
        keypoints_3d: np.ndarray
) -> np.ndarray:
    """
    Calculates 3D bounding boxes from 3D keypoints.

    Args:
        keypoints_3d: array with shape (N, num_keypoints, 3)
        scores_3d: array with shape (N, num_keypoints)

    Returns:
        Array of shape (N, 6) with bounding boxes in the format
        [center_x, center_y, center_z, width, height, depth]
    """
    bboxes = []

    for i in range(len(keypoints_3d)):
        min_coords = np.min(keypoints_3d, axis=0)
        max_coords = np.max(keypoints_3d, axis=0)
        center = (min_coords + max_coords) / 2
        dimensions = max_coords - min_coords
        bboxes.append(np.concatenate([center, dimensions]))
    else:
        bboxes.append(np.zeros(6))

    return np.array(bboxes)


class RTMLifting:
    def __init__(
            self, 
            num_keypoints: int, 
            mode: str, 
            local_model: Optional[os.PathLike] = None, 
            cache_dir: Optional[os.PathLike] = None,
            device: str = 'cpu'
            ):
        """
        Initializes the RTMLifting class.

        Args:
            num_keypoints: Number of keypoints for the pose estimation.
            mode: Mode of operation (e.g., 'train', 'eval').
            local_model: Optional local model for lifting.
            cache_dir: Optional cache directory for model storage.
        """
        self.num_keypoints = num_keypoints
        self.mode = mode
        self.device = device

        available_modes = ['ai', 'geometric']
        if mode not in available_modes:
            raise ValueError(f"Mode '{mode}' is not supported. Choose from {available_modes}.")

        if mode == 'ai':
            if local_model is None:
                if num_keypoints == 17:
                    self.model=Simple3DPoseLiftingModel(num_keypoints=num_keypoints)
                    self.model.to(device)
                    self.model.eval()

                    model_loader=ModelLoader(
                        repo_id="fhswf/rtm17lifting",
                        model_filename="rtm17lifting.pth",
                        cache_dir=cache_dir,
                    )

                    state_dict=model_loader.load_model(device=device)

                    self.model.load_state_dict(state_dict)

                elif num_keypoints == 26:
                    raise NotImplementedError("AI lifting for 26 keypoints is not implemented yet.")

                elif num_keypoints == 133:
                    self.model=Simple3DPoseLiftingModel(num_keypoints=num_keypoints)
                    self.model.to(device)
                    self.model.eval()

                    model_loader=ModelLoader(
                        repo_id="fhswf/rtm133lifting",
                        model_filename="rtm133lifting.pth",
                        cache_dir=cache_dir,
                    )

                    state_dict=model_loader.load_model(device=device)
                    self.model.load_state_dict(state_dict)
            else:
                model_filename = local_model.split('/')[-1]
                model_path = local_model.split('/')[:-1]
                model_loader = ModelLoader(
                    repo_id="fhswf/rtm133lifting",
                    model_filename=model_filename,
                    local_model_dir=model_path
                )
                self.model = model_loader.load_model(device='cpu')
        else:
            allowed_keypoints = [17, 26, 133]
            if num_keypoints not in allowed_keypoints:
                raise ValueError(f"Number of keypoints '{num_keypoints}' is not supported for geometric lifting.")
            if num_keypoints != 133:
                raise NotImplementedError(f"Geometric lifting for '{num_keypoints}' keypoints is not implemented yet.")

    def lift_pose(self, pose_2d: Image2DResult) -> Image3DResult:
        """
        Lifts a 2D pose to a 3D pose using the loaded model (possible for multiple persons).

        Args:
            pose_2d: Input 2D pose data.

        Returns:
            3D pose data.
        """

        all_3d_poses = []
        
        for keypoints in pose_2d.keypoints:
            if self.mode == 'ai':
                keypoints_3d = self._model_lift(keypoints)
                all_3d_poses.append(keypoints_3d)
                
            elif self.mode == 'geometric':
                keypoints_3d = self._geometric_lift(keypoints)
                all_3d_poses.append(keypoints_3d)
            else:
                raise ValueError(f"Invalid mode '{self.mode}' for lifting.")

        keypoints_3d = np.array(all_3d_poses)

        return Image3DResult(
            frame_idx=pose_2d.frame_idx,
            keypoints_3d=keypoints_3d,
            keypoints_2d=pose_2d.keypoints,
            #TODO to check
            scores_3d=pose_2d.scores,
            scores_2d=pose_2d.scores,
            bboxes_3d=_calculate_3d_bboxes(keypoints_3d),
            bboxes_2d=pose_2d.bboxes,
            num_persons=pose_2d.num_persons,
            method=self.mode
        )

    def lift_pose_Save2DData(self, pose_2d: List[Union[Save2DData, Save2DDataWithName, Save2DDataWithConfidence, 
                                            Save2DDataWithNameAndConfidence]]) -> ndarray:
        """
        Lifts a 2D pose to a 3D pose using the loaded model.

        Args:
            pose_2d: Input 2D pose data.

        Returns:
            3D pose data.
        """
        keypoints = np.array([[item.data['x'], item.data['y']] for item in pose_2d], dtype=np.float32)

        if self.mode == 'ai':
            return self._model_lift(keypoints)
                
        elif self.mode == 'geometric':
            return self._geometric_lift(keypoints)

        else:
            raise ValueError(f"Invalid mode '{self.mode}' for lifting.")
        
    def _model_lift(self, keypoints_2d: np.ndarray) -> ndarray[tuple[Any, ...], dtype[Any]]:
        """
        Internal method to lift 2D keypoints to 3D using the AI model.

        Args:
            keypoints_2d: 2D keypoints array.

        Returns:
            3D keypoints array.
        """
        keypoints_3d = np.zeros((self.num_keypoints, 3))
        keypoints_3d[:, :2] = keypoints_2d
            
        keypoints_2d_normalized = _normalize_by_bounding_box(keypoints_2d)

        input_2d = keypoints_2d_normalized.flatten() 
            
        with torch.no_grad():
            input_tensor = torch.FloatTensor(input_2d).unsqueeze(0).to(self.device)
            output_tensor = self.model(input_tensor)
            output_3d = output_tensor.cpu().numpy().flatten()
        
        output_3d_reshaped = output_3d.reshape(self.num_keypoints, 3)
        keypoints_3d = _denormalize_by_bounding_box(output_3d_reshaped, keypoints_2d)
        
        zero_indices = np.where(np.all(keypoints_2d == [0, 0], axis=1))[0]
        keypoints_3d[zero_indices] = [0, 0, 0]

        return keypoints_3d

    def _geometric_lift(self, keypoints_2d: np.ndarray) -> ndarray[tuple[int, int], dtype[float64]]:
        """
        Internal method to lift 2D keypoints to 3D using geometric heuristics.

        Args:
            keypoints_2d: 2D keypoints array.

        Returns:
            3D keypoints array.
        """
        keypoints_3d = np.zeros((self.num_keypoints, 3))
        keypoints_3d[:, :2] = keypoints_2d
        
        for i in range(self.num_keypoints):
            keypoints_3d[i, 2] = self._estimate_z_by_type(i)

        zero_indices = np.where(np.all(keypoints_2d == [0, 0], axis=1))[0]
        keypoints_3d[zero_indices] = [0, 0, 0]
        
        return keypoints_3d
    
    def _estimate_z_by_type(self, point_idx: int) -> float | None:
        """
        Estimates the Z value based on the keypoint type.

        Args:
            point_idx: Index of the keypoint.

        Returns:
            Estimated Z value.
        """
        if self.num_keypoints == 133:
            if point_idx == 0:
                return 0.1
            elif 1 <= point_idx <= 4:
                return 0.1
            elif 5 <= point_idx <= 12:
                return 0.0
            elif point_idx in [9, 10]:
                return 0.2
            elif 91 <= point_idx <= 111:
                return 0.25
            elif 112 <= point_idx <= 132:
                return 0.25
            elif 23 <= point_idx <= 90:
                return 0.1
            else:
                return 0.0

        else:
            NotImplementedError("Z value estimation is only implemented for 133 keypoints.")
            return None
