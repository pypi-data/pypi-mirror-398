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
model_loader.py

This module provides a class to intelligently load and cache models from the Hugging Face Hub.

Author: Jonas David Stephan, Nathalie Dollmann
Date: 2025-12-18
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional
from huggingface_hub import hf_hub_download, HfApi, model_info
from huggingface_hub.constants import HF_HUB_CACHE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelLoader:
    """
    Class to intelligently load and cache models from the Hugging Face Hub.
    """

    def __init__(
        self,
        repo_id: str,
        model_filename: str,
        cache_dir: Optional[os.PathLike] = None,
        local_model_dir: Optional[os.PathLike] = None
    ):
        """
        Initializes the ModelLoader.

        Args:
            repo_id (str): The HF Repo-ID (e.g., 'fhswf/rtm133lifting').
            model_filename (str): The filename of the model in the repo (e.g., 'rtm133lifting.pth').
            cache_dir (os.PathLike, optional): Base cache directory. Defaults to the standard HF cache or
                                                ~/.cache/huggingface/hub. If None
                                                ~/.cache/huggingface/hub used.
            local_model_dir (os.PathLike, optional): Specific folder for local model. Overrides the cache structure.
        """
        self.repo_id = repo_id
        self.model_filename = model_filename
        self.hf_api = HfApi()

        if local_model_dir is not None:
            self.model_dir = Path(local_model_dir)
        else:
            if cache_dir is not None:
                base_cache = Path(cache_dir)
            else:
                base_cache = Path(HF_HUB_CACHE)

            safe_repo_name = repo_id.replace("/", "--")
            self.model_dir = base_cache / f"models--{safe_repo_name}"

            self.model_dir.mkdir(parents=True, exist_ok=True)

            self.local_model_path = self.model_dir / model_filename
            self.metadata_path = self.model_dir / "model_metadata.json"

            self.local_metadata = self._load_local_metadata()

    def _load_local_metadata(self) -> dict:
        """
        Loads local metadata of the cached model if available.

        Returns
            dict: meta data dictionary or empty dict if none exists.
        """
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Meta data file {self.metadata_path} is corrupted.")
        return {}

    def _save_local_metadata(self, metadata: dict):
        """
        Saves metadata to the local metadata file.
        
        Args:
            metadata (dict): The metadata to save.
        """
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _get_remote_metadata(self) -> Optional[dict]:
        """
        Retrieves remote metadata from the Hugging Face Hub.
        
        Returns:
            dict: Remote metadata dictionary or None if retrieval fails.

        Raises:
            Exception: If there is an error fetching the metadata.
        """
        try:
            info = model_info(self.repo_id, files_metadata=True)

            for file_info in info.siblings:
                if file_info.rfilename == self.model_filename:
                    latest_commit_hash = info.sha 

                    return {
                        "repo_id": self.repo_id,
                        "model_filename": self.model_filename,
                        "last_remote_commit": latest_commit_hash,
                    }
            logger.error(f"File '{self.model_filename}' not found in repository '{self.repo_id}'.")
            return None
        except Exception as e:
            logger.error(f"Error fetching remote metadata: {e}")
            return None

    def check_for_update(self) -> bool:
        """
        Checks if a newer version of the model is available on the Hugging Face Hub.

        Returns:
            bool: True, if an update is available,
                  False, if the local model is up-to-date.
        """
        if not self.local_model_path.exists():
            logger.info("No local model file found. Download required.")
            return True

        remote_meta = self._get_remote_metadata()
        if remote_meta is None:
            logger.warning("Could not check remote status. Using local file.")
            return False

        local_commit = self.local_metadata.get("last_remote_commit")
        remote_commit = remote_meta.get("last_remote_commit")

        if local_commit != remote_commit:
            logger.info(f"Update available! Local Commit: {local_commit}, Remote Commit: {remote_commit}")
            return True
        else:
            logger.info("Local model is up-to-date.")
            return False

    def download_model(self, force_download: bool = False) -> Path:
        """
        Downloads the model from the Hugging Face Hub if needed.

        Args:
            force_download (bool): If True, forces a re-download of the model.

        Returns:
            Path: Path to the local model file.
        """
        needs_download = force_download or self.check_for_update()

        if needs_download:
            logger.info(f"Downloading model to: {self.local_model_path}")
            try:
                downloaded_path = hf_hub_download(
                    repo_id=self.repo_id,
                    filename=self.model_filename,
                    cache_dir=self.model_dir.parent, 
                    force_download=force_download
                )

                import shutil
                shutil.copy2(downloaded_path, self.local_model_path)
                logger.info(f"Model successfully downloaded to {self.local_model_path}.")

                remote_meta = self._get_remote_metadata()
                if remote_meta:
                    self.local_metadata = remote_meta
                    self._save_local_metadata(self.local_metadata)
                else:
                    logger.warning("Model downloaded, but metadata could not be saved.")

            except Exception as e:
                logger.error(f"Download failed: {e}")
                raise
        else:
            logger.info(f"Using existing model at: {self.local_model_path}")

        return self.local_model_path

    def load_model(self, force_download: bool = False, **model_load_kwargs):
        """
        Main method to download (if needed) and load the model.

        Args:
            force_download (bool): If True, forces a re-download of the model.
            **model_load_kwargs: Additional keyword arguments for model loading.

        Returns:
            The loaded model (e.g., a torch.nn.Module).
            You MUST adapt this method to your specific model loading logic!
        """
        model_file_path = self.download_model(force_download=force_download)

        try:
            import torch
            device = model_load_kwargs.get('device', 'cpu')
            map_location = model_load_kwargs.get('map_location', device)

            model_data = torch.load(model_file_path, map_location=map_location)
            logger.info(f"Model successfully loaded from {model_file_path}.")

            return model_data

        except ImportError:
            logger.error("PyTorch (torch) is not installed, required for .pth files.")
            raise
        except Exception as e:
            logger.error(f"Error loading model file: {e}")
            raise