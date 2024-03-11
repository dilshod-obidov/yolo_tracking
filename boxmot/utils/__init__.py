# Mikel Broström 🔥 Yolo Tracking 🧾 AGPL-3.0 license

import sys
from pathlib import Path

import numpy as np

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]  # root directory
DATA = ROOT / 'data'
BOXMOT = ROOT / "boxmot"
EXAMPLES = ROOT / "tracking"
TRACKER_CONFIGS = ROOT / "boxmot" / "configs"
WEIGHTS = ROOT / "tracking" / "weights"
REQUIREMENTS = ROOT / "requirements.txt"

# global logger
from loguru import logger

logger.remove()
logger.add(sys.stderr, colorize=True, level="DEBUG")


class PerClassDecorator:
    def __init__(self, method):
        # Store the method that will be decorated
        self.update = method
        self.nr_classes = 80
        self.per_class_active_tracks = {}
        for i in range(self.nr_classes):
            self.per_class_active_tracks[i] = []

    def __get__(self, instance, owner):
        # This makes PerClassDecorator a non-data descriptor that binds the method to the instance
        def wrapper(*args, **kwargs):
            # Unpack arguments for clarity
            modified_args = list(args)
            dets = modified_args[0]
            im = modified_args[1]
            
            if instance.per_class is True and dets.size > 0:
                # Organize detections by class ID for per-class processing
                detections_by_class = {
                    int(class_id): np.array([det for det in dets if det[5] == class_id])
                    for class_id in set(det[5] for det in dets)
                }

                # Initialize an array to store modified detections
                per_class_tracks = []

                for cls_id in range(self.nr_classes):
                    if cls_id in detections_by_class:
                        class_dets = detections_by_class.get(int(cls_id), np.empty((0, 6)))
                        logger.debug(f"Processing class {int(cls_id)}: {class_dets.shape}")

                        instance.active_tracks = self.per_class_active_tracks[cls_id]
                        
                        # Update detections using the decorated method
                        tracks = self.update(instance, class_dets, im)

                        # save active tracks
                        self.per_class_active_tracks[cls_id] = instance.active_tracks

                        instance.per_class_active_tracks = self.per_class_active_tracks

                        if tracks.size > 0:
                            per_class_tracks.append(tracks)
                
                if per_class_tracks:
                    # Convert the list of arrays to a single NumPy array
                    per_class_tracks = np.vstack(per_class_tracks)
                    
                else:
                    # If no detections were updated, initialize an empty array with the correct shape
                    per_class_tracks = np.empty(shape=(0, 8))
                # logger.debug(f"Per-class update result: {per_class_tracks.shape}")
                tracks = per_class_tracks
            else:
                # Process all detections at once if per_class is False or detections are empty
                tracks = self.update(instance, dets, im)
            
            print('tracks.shape', tracks.shape)
            return tracks

        return wrapper