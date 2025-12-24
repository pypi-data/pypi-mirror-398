from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd
from sqlitedict import SqliteDict

class Summarizer(ABC):
    """Represents an abstract summarizer that is used to process raw data from
    the database into a single Pandas DataFrame to be used by machine learning
    algorithm.
    
    Subclasses must implement the 'get_filename_prefix' and 'summarize' metods.
    """
    
    @abstractmethod
    def get_filename_prefix() -> str:
        """Provides a default prefix to use if the user does not specify an
        output file name. Prefix should be descriptive of the style used to
        reduce player stats.

        Returns:
            str: Prefix for model output filename.
        """
        pass

    @abstractmethod
    def summarize(
        self,
        data: Dict[str, SqliteDict]
    ) -> pd.DataFrame:
        """Summarizes stats into the final data set to be used by the learning
        module.

        Args:
            data (Dict[str, SqliteDict]): Dictionary containing the tables of
            raw data. Keys are table names as strings, each table is a SqliteDict.

        Returns:
            pd.DataFrame: Pandas DataFrame with the final data set for machine
            learning.
        """
        pass