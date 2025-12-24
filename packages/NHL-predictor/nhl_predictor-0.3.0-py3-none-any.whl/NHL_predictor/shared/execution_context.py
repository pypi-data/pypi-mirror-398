import os
from pathlib import Path

import typer
from nhlpy import NHLClient


class ExecutionContext:
    """A singleton execution context to track values needed throughout
    processing.
    """
    _app_name = "nhlpredictor"
    _app_dir_set = False
    
    def __new__(cls):
        """Overload __new__ to create only one instance.
        """
        if not getattr(cls, '_instance', None):
            cls._instance = super(type(ExecutionContext), cls).__new__(cls)
        return cls._instance

    @property
    def client(self) -> NHLClient:
        """Get the NHLClient for the application run.

        Returns:
            NHLClient: An NHLClient to use.
        """
        if getattr(self, '_client', None) is None:
            self._client = NHLClient()
        return self._client
    
    @property
    def summarizer_type(self) -> str:
        """Get the summarizer type for the application run.

        Returns:
            str: The summarizer type.
        """
        return self._summarizer

    @summarizer_type.setter
    def summarizer_type(self, value: str):
        """Set the summarizer type.

        Args:
            value (str): The value to set the summarizer type to.
        """
        self._summarizer = value

    @property
    def allow_update(self) -> bool:
        """Get if update is allowed.

        Returns:
            bool: Boolean indicating if update is allowed.
        """
        return self._allow_update

    @allow_update.setter
    def allow_update(self, value: bool):
        """Set if update is allowed.

        Args:
            value (bool): The value to set allow_update to.
        """
        self._allow_update = value
    
    @property
    def model(self) -> str:
        """Get the model file name.

        Returns:
            str: The model file name.
        """
        return self._model
    
    @model.setter
    def model(self, value: str):
        """Set the model file name.

        Args:
            value (str): The value to set the model file name.
        """
        self._model = value

    @property   
    def output_file(self) -> str:
        """Get the output file name.

        Returns:
            str: The output file name.
        """
        return self._output_file
    
    @output_file.setter
    def output_file(self, value: str):
        """Set the output file name.

        Args:
            value (str): The value to set the output file name to.
        """
        self._output_file = value

    @property
    def app_dir(self) -> Path:
        """Get the configured application directory.

        Returns:
            Path: The Path to the application directory.
        """
        if not getattr(self, "_app_dir", None):
            self.app_dir = typer.get_app_dir(ExecutionContext._app_name)
        return self._app_dir

    @app_dir.setter
    def app_dir(self, value: Path):
        """Set the application directory.

        Args:
            value (Path): Path to the application directory.

        Raises:
            Exception: Thrown if application directory is already set.
            RuntimeError: Thrown if path is invalid.
        """
        # TODO: shouldn't use general exceptions
        if ExecutionContext._app_dir_set:
            raise Exception("File path already set.")
        value = os.path.expanduser(value)
        if not os.path.isabs(value):
            value = os.path.abspath(value)
        if not os.path.isabs(value):
            raise RuntimeError("Error: could not resolve path.")
        if not os.path.exists(value):
            Path(value).mkdir()

        self._app_dir = value
        ExecutionContext._app_dir_set = True
    
    def _ensure_app_dir(self):
        """Method to ensure that the application directory has been initizlized.
        """
        self.app_dir