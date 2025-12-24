import logging
from pathlib import Path

from data.data_restructure.restructurers import (
    BaseRestructurer,
    ImageClassificationRestructurer,
    ImageSegmentationRestructurer,
    TextGenerationRestructurer
)

logger = logging.getLogger(__name__)


class Restructurer():
    """
    Main class to handle dataset restructuring based on task type.
    """
    def __init__(self, task_type: str):
        self.restructurer = self._get_restructurer(task_type)

    def _get_restructurer(self, task_type: str) -> BaseRestructurer:
        """
        Factory method to get the appropriate restructurer based on task type.
        """
        RESTRUCTURERS = {
            "image_classification": ImageClassificationRestructurer,
            "image_segmentation": ImageSegmentationRestructurer,
            "text_generation": TextGenerationRestructurer,
            # Future task types can be added here
        }
        restructurer_class = RESTRUCTURERS.get(task_type.lower())
        if not restructurer_class:
            raise ValueError(f"Unsupported task type: '{task_type}'. "
                             f"Available types are: {list(RESTRUCTURERS.keys())}")
        return restructurer_class()
    def restructure(self, input_path: Path, output_path: Path) -> None:
        """
        Executes the restructuring process.
        """
        try:
            summary = self.restructurer.restructure(input_path, output_path)
            return summary
        except Exception as e:
            logger.error(f"Restructuring failed: {e}", exc_info=True)
            return None
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Stops the restructurer's resources.
        """
        self.restructurer.stop()
