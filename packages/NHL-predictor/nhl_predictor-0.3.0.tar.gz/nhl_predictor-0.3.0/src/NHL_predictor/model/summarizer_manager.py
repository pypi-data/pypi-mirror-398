from __future__ import annotations
from enum import Enum

import model.summarizers.average_player_summarizer as avsum
from model.summarizers.summarizer import Summarizer


class SummarizerTypes(str, Enum):
    """Enumeration of the supported summarizer types.
    """
    none = "none"
    average_player_summarizer = "average"

    @staticmethod
    def get_summarizer(summarizer_type: SummarizerTypes) -> Summarizer:
        """Build a summarizer instance from the specified summarizer type.

        Args:
            summarizer_type (SummarizerTypes): The type of summarizer to get.

        Raises:
            Exception: Throws if summarizer type cannot be found.

        Returns:
            Summarizer: A summarizer instance of the requested type.
        """
        match summarizer_type:
            case SummarizerTypes.average_player_summarizer:
                return avsum.AveragePlayerSummarizer()
            case _:
                # TODO: Shouldn't throw generic Exception
                raise Exception("Unsupported summarizer specified.")