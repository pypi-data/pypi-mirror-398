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
rtm_pose_estimator_2d.py

This module provides a class for 2D pose estimation using RTM models.

Author: Jonas David Stephan, Nathalie Dollmann
Date: 2025-12-19
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
try:
    from rtmlib import Wholebody, draw_skeleton, Body
except ImportError:
    raise ImportError("RTMLib nicht gefunden. Installiere mit: pip install rtmlib")

from typing import Union, List, Tuple, Optional
from pathlib import Path
import numpy as np
import cv2
import time
from tqdm import tqdm

from .Image2DResult import Image2DResult
from .Video2DResult import Video2DResult

def filter_keypoints(keypoints, scores, ignore_indices=None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Function to filter out specified keypoints by setting their coordinates and scores to zero.

    Args:
        keypoints: Array of shape (num_persons, num_keypoints, 2)
        scores: Array of shape (num_persons, num_keypoints)
        ignore_indices: List of keypoint indices to ignore

    Returns:
        Filtered keypoints and scores arrays.
    """
    if ignore_indices is None:
        return keypoints.copy(), scores.copy()
    
    keypoints_filtered = keypoints.copy()
    scores_filtered = scores.copy()
    
    for idx in ignore_indices:
        if idx < keypoints_filtered.shape[1]: 
            keypoints_filtered[:, idx, :] = 0
            scores_filtered[:, idx] = 0

    return keypoints_filtered, scores_filtered

def draw_skeleton_filtered(image, keypoints, scores, ignore_indices=None, kpt_thr=0.3, draw_style = 'small') -> np.ndarray:
    """
    Function to draw skeleton on image while ignoring specified keypoints.

    Args:
        image: Input image as a numpy array.
        keypoints: Array of shape (num_persons, num_keypoints, 2)
        scores: Array of shape (num_persons, num_keypoints)
        ignore_indices: List of keypoint indices to ignore
        kpt_thr: Keypoint confidence threshold for drawing
        draw_style: 'small' or 'full' for different skeleton styles

    Returns:
        Annotated image as a numpy array.
    """

    #TODO: Midsize model

    available_styles = {'small', 'full'}
    if draw_style not in available_styles:
        raise ValueError(f"Invalid draw_style '{draw_style}'. Available styles: {available_styles}")
    
    if ignore_indices is None:
        from rtmlib import draw_skeleton
        return draw_skeleton(image, keypoints, scores, kpt_thr=kpt_thr)

    BODY_CONNECTIONS = [
        (0, 1), (0, 2), (1, 3), (2, 4),
        (3, 5), (4, 6), (5, 6),
        (5, 7), (7, 9),
        (6, 8), (8, 10),
        (5, 11), (6, 12), (11, 12),
        (11, 13), (13, 15),
        (12, 14), (14, 16)
    ]

    if len(keypoints) > 0 and keypoints.shape[1] == 133 and draw_style == 'full':
        #TODO: Add right connections for full body
        BODY_CONNECTIONS += [
            (11, 23), (12, 24),
            (23, 24), (23, 25), (25, 27),
            (24, 26), (26, 28),
            (27, 29), (28, 30),
            (29, 31), (30, 32),
            (33, 34), (35, 36), (37, 38),
            (39, 40), (41, 42), (43, 44),
            (45, 46), (47, 48), (49, 50),
            (51, 52), (53, 54), (55, 56),
            (57, 58), (59, 60), (61, 62)
        ]
    
    annotated_image = image.copy()
    ignore_set = set(ignore_indices)
    
    for person_idx in range(len(keypoints)):
        kpts = keypoints[person_idx]
        conf = scores[person_idx]
        
        for start_idx, end_idx in BODY_CONNECTIONS:
            if start_idx not in ignore_set and end_idx not in ignore_set:
                if conf[start_idx] > kpt_thr and conf[end_idx] > kpt_thr:
                    pt1 = tuple(kpts[start_idx].astype(int))
                    pt2 = tuple(kpts[end_idx].astype(int))
                    cv2.line(annotated_image, pt1, pt2, (0, 255, 0), 1)
        
        for idx in range(len(kpts)):
            if idx not in ignore_set and conf[idx] > kpt_thr:
                pt = tuple(kpts[idx].astype(int))
                cv2.circle(annotated_image, pt, 1, (0, 0, 255), -1)
    
    return annotated_image


class RTMPoseEstimator2D:

    def __init__(
            self,
            mode: str = 'performance',
            backend: str = 'onnxruntime',
            device: str = 'cpu',
            to_openpose: bool = False,
            kpt_threshold: float = 0.8,
            det_model_path: str = None,
            pose_model_path: str = None,
            pose_input_size: tuple = (288, 384),
            det_input_size: tuple = (640, 640),
            num_keypoints: int = 133,
    ):
        """
        Initialize the RTM 2D Pose Estimator.

        Args:
            mode: One of 'performance', 'balanced', 'lightweight', or 'individual'
            backend: Backend to use ('onnxruntime', 'tensorrt', etc.)
            device: Device to run the model on ('cpu', 'cuda', etc.)
            to_openpose: Whether to convert keypoints to OpenPose format
            kpt_threshold: Keypoint confidence threshold for filtering
            det_model_path: Path to custom detection model (required for 'individual' mode)
            pose_model_path: Path to custom pose model (required for 'individual' mode)
            pose_input_size: Input size for the pose model (required for 'individual' mode)
            det_input_size: Input size for the detection model (required for 'individual' mode)
            num_keypoints: Number of keypoints to use

        Raises:
            ValueError: If invalid mode is provided or required parameters for 'individual' mode are missing or
                invalid keypoint number
            RuntimeError: If there is an error initializing the RTMLib Wholebody model
        """

        available_modes={'performance', 'balanced', 'lightweight', 'individual'}

        if mode not in available_modes:
            raise ValueError(f"Invalid mode '{mode}'. Available modes: {available_modes}")

        if mode == 'individual':
            if det_model_path is None or pose_model_path is None:
                raise ValueError("For the 'individual' mode, det_model_path and pose_model_path must be specified.")
            if pose_input_size is None or det_input_size is None:
                raise ValueError("For the 'individual' mode, pose_input_size and det_input_size must be specified.")

        # TODO to add midsize model
        if num_keypoints not in [17, 133]:
            raise ValueError(f"Invalid num_keypoints {num_keypoints}.")

        self.backend=backend
        self.device=device
        self.to_openpose=to_openpose
        self.kpt_threshold=kpt_threshold
        self.mode=mode
        self.det_model_path=det_model_path
        self.pose_model_path=pose_model_path
        self.pose_input_size=pose_input_size
        self.det_input_size=det_input_size
        self.num_keypoints=num_keypoints

        try:
            if mode == 'individual':
                if num_keypoints == 133:
                    self.model=Wholebody(
                        mode=mode,
                        backend=backend,
                        device=device,
                        to_openpose=to_openpose,
                        det=det_model_path,
                        pose=pose_model_path,
                        pose_input_size=pose_input_size,
                        det_input_size=det_input_size
                    )
                else:
                    self.model=Body(
                        mode=mode,
                        backend=backend,
                        device=device,
                        to_openpose=to_openpose,
                        det=det_model_path,
                        pose=pose_model_path,
                        pose_input_size=pose_input_size,
                        det_input_size=det_input_size
                    )
            else:
                if num_keypoints == 133:
                    self.model=Wholebody(
                        mode=mode,
                        backend=backend,
                        device=device,
                        to_openpose=to_openpose
                    )
                else:
                    self.model=Body(
                        mode=mode,
                        backend=backend,
                        device=device,
                        to_openpose=to_openpose
                    )
        except Exception as e:
            raise RuntimeError(f"Error initializing RTMLib Wholebody model: {e}")

    def process_image(self, image: np.ndarray, image_idx: int = 0) -> Image2DResult:
        """
        Process 2D pose estimation on a single image.

        Args:
            image: Input image as a numpy array.
            image_idx: Index of the image (for videos)

        Returns:
            Image2DResult containing keypoints, scores, bounding boxes, and number of persons detected
        """
        try:
            keypoints, scores=self.model(image)

            if keypoints is None or len(keypoints) == 0:
                return Image2DResult(
                    frame_idx=image_idx,
                    keypoints=np.empty((0, self.num_keypoints, 2)),
                    scores=np.empty((0, self.num_keypoints)),
                    bboxes=np.empty((0, 5)),
                    num_persons=0
                )

            keypoints=np.array(keypoints)
            scores=np.array(scores)

            logits=np.array(scores)
            confidence_scores=1 / (1 + np.exp(-logits))

            if keypoints.ndim == 2:
                keypoints=keypoints[np.newaxis, ...]

            if confidence_scores.ndim == 1:
                confidence_scores=confidence_scores[np.newaxis, ...]

            num_persons=keypoints.shape[0]

            bboxes=[]
            for i in range(num_persons):
                kpts=keypoints[i].copy()
                conf_scores_flat=confidence_scores[i]

                low_confidence_mask=conf_scores_flat <= self.kpt_threshold
                kpts[low_confidence_mask, 0]=0
                kpts[low_confidence_mask, 1]=0
                keypoints[i]=kpts

                non_zero_mask=(kpts != 0).any(axis=1)
                valid_kpts=kpts[non_zero_mask]

                if len(valid_kpts) > 0:
                    x_coords=valid_kpts[:, 0]
                    y_coords=valid_kpts[:, 1]
                    x1, y1=np.min(x_coords), np.min(y_coords)
                    x2, y2=np.max(x_coords), np.max(y_coords)

                    padding=20
                    x1=max(0, x1 - padding)
                    y1=max(0, y1 - padding)
                    x2=min(image.shape[1], x2 + padding)
                    y2=min(image.shape[0], y2 + padding)

                    high_confidence_scores=conf_scores_flat[conf_scores_flat > self.kpt_threshold]
                    confidence=np.mean(high_confidence_scores) if len(high_confidence_scores) > 0 else 0

                    bboxes.append([x1, y1, x2, y2, confidence])
                else:
                    bboxes.append([0, 0, 0, 0, 0])

            bboxes_array=np.array(bboxes)

            return Image2DResult(
                frame_idx=image_idx,
                keypoints=keypoints,
                scores=confidence_scores,
                bboxes=bboxes_array,
                num_persons=num_persons
            )

        except Exception as e:
            print(f"Error processing image: {e}")
            return Image2DResult(
                frame_idx=image_idx,
                keypoints=np.empty((0, self.num_keypoints, 2)),
                scores=np.empty((0, self.num_keypoints)),
                bboxes=np.empty((0, 5)),
                num_persons=0
            )

    def process_image_from_file(self, image_path: Union[str, Path]) -> Image2DResult:
        """
        Process 2D pose estimation on an image from a file path.

        Args:
            image_path: Path to the input image file.

        Returns:
            Image2DResult containing keypoints, scores, bounding boxes, and number of persons detected
        """
        image_path=Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image=cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        result=self.process_image(image, image_idx=0)

        return result

    def process_image_with_annotation(
            self,
            image: np.ndarray,
            draw_bbox: bool = True,
            draw_keypoints: bool = True,
            keypoint_threshold: float = 0.3,
            ignore_keypoints: Optional[List[int]] = None,
            image_idx: int = 0,
            draw_style: str = 'small'
    ) -> Tuple[np.ndarray, Image2DResult]:
        """
        Process 2D pose estimation on an image and return annotated image.

        Args:
            image: Input image as a numpy array.
            draw_bbox: Whether to draw bounding boxes
            draw_keypoints: Whether to draw keypoints and skeleton
            keypoint_threshold: Keypoint confidence threshold for drawing
            ignore_keypoints: List of keypoint indices to ignore when drawing
            image_idx: Index of the image (for videos)
            draw_style: 'small' or 'full' for different skeleton styles

        Returns:
            Tuple of (annotated_image, Image2DResult)
        """

        result=self.process_image(image, image_idx)

        if ignore_keypoints is not None:
            result.keypoints, result.scores=filter_keypoints(
                result.keypoints,
                result.scores,
                ignore_keypoints
            )

        annotated_image=image.copy()

        if result.num_persons > 0:
            if draw_bbox and len(result.bboxes) > 0:
                for bbox in result.bboxes:
                    x1, y1, x2, y2=bbox[:4].astype(int)
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if draw_keypoints:
                annotated_image=draw_skeleton_filtered(
                    annotated_image,
                    result.keypoints,
                    result.scores,
                    ignore_keypoints,
                    kpt_thr=keypoint_threshold,
                    draw_style=draw_style
                )

        return annotated_image, result

    def process_image_with_annotation_from_file(
            self,
            image_path: Union[str, Path],
            draw_bbox: bool = True,
            draw_keypoints: bool = True,
            keypoint_threshold: float = 0.3,
            ignore_keypoints: Optional[List[int]] = None,
            draw_type: str = 'small',
    ) -> Tuple[np.ndarray, Image2DResult]:
        """
        Process 2D pose estimation on an image from a file path and return annotated image.

        Args:
            image_path: Path to the input image file.
            draw_bbox: Whether to draw bounding boxes
            draw_keypoints: Whether to draw keypoints and skeleton
            keypoint_threshold: Keypoint confidence threshold for drawing
            ignore_keypoints: List of keypoint indices to ignore when drawing
            draw_type: 'small' or 'full' for different skeleton styles

        Returns:
            Tuple of (annotated_image, Image2DResult)

        Raises:
            ValueError: If the image cannot be loaded
        """
        image_path=Path(image_path)

        image=cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Image cannot be loaded: {image_path}")

        return self.process_image_with_annotation(
            image,
            draw_bbox=draw_bbox,
            draw_keypoints=draw_keypoints,
            keypoint_threshold=keypoint_threshold,
            ignore_keypoints=ignore_keypoints,
            image_idx=0,
            draw_style=draw_type
        )

    def process_video(
            self,
            video_path: Union[str, Path],
            output_dir: Optional[Union[str, Path]] = None,
            save_frames: bool = False,
            max_frames: Optional[int] = None
    ) -> Video2DResult:
        """
        Process 2D pose estimation on a video and return results.

        Args:
            video_path: Path to the input video file.
            output_dir: Directory to save annotated frames (if save_frames is True)
            save_frames: Whether to save annotated frames
            max_frames: Maximum number of frames to process (for testing)

        Returns:
            Video2DResult containing per-frame results, total frames, fps, and processing time

        Raises:
            FileNotFoundError: If the video file does not exist
            ValueError: If the video cannot be opened
        """
        video_path=Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap=cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Video cannot be opened: {video_path}")

        fps=cap.get(cv2.CAP_PROP_FPS)
        total_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if max_frames:
            total_frames=min(total_frames, max_frames)

        if output_dir and save_frames:
            output_dir=Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        frame_results=[]
        start_time=time.time()

        pbar=tqdm(total=total_frames)
        for frame_idx in range(total_frames):
            ret, frame=cap.read()
            if not ret:
                break

            result=self.process_image(frame, frame_idx)
            frame_results.append(result)

            if save_frames and output_dir and result.num_persons > 0:
                annotated_frame=draw_skeleton_filtered(
                    frame.copy(),
                    result.keypoints,
                    result.scores,
                    kpt_thr=self.kpt_threshold
                )
                frame_filename=output_dir / f"frame_{frame_idx:05d}.jpg"
                cv2.imwrite(str(frame_filename), annotated_frame)
            pbar.update(1)

        cap.release()
        pbar.close()

        processing_time=time.time() - start_time

        return Video2DResult(
            frame_results=frame_results,
            total_frames=len(frame_results),
            fps=fps,
            processing_time=processing_time
        )