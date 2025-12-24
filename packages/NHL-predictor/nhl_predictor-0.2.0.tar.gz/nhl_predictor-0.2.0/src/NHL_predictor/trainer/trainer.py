from model.algorithms import Algorithms
from shared.logging_config import LoggingConfig
from trainer.linear_regression import TrainLinearRegression

logger = LoggingConfig.get_logger(__name__)

class Trainer:
    """Static class providing an entry point for training machine learning
    models.
    """

    @staticmethod
    def train(algorithm: Algorithms) -> None:
        """Train a model using the specified algorithm.

        Args:
            algorithm (Algorithms): The machine learning Algorithm to train a
            model for.
        """
        match algorithm:
            case Algorithms.linear_regression:
                TrainLinearRegression.train()
            case _:
                logger.error("Invalid algorithm provided to train.")