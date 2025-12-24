import os
from pickle import dump

import numpy as np
import statsmodels.api as sm
from ansimarkup import ansiprint as print
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from model.summarizer_manager import SummarizerTypes
from shared.constants.database import Database as DB
from shared.execution_context import ExecutionContext
from shared.logging_config import LoggingConfig
from shared.utility import Utility as utl

logger = LoggingConfig.get_logger(__name__)
execution_context = ExecutionContext()
_model_filename_part = "LinearRegression"

class TrainLinearRegression:
    """Static class to train a linear regression model on NHL data.
    """
    
    @staticmethod
    def train() -> None:
        """Entry point for linear regression model training.
        """
        logger.info("Start of model training.")
        
        data = utl.get_pandas_tables(
            DB.players_table_name,
            DB.skater_stats_table_name,
            DB.goalie_stats_table_name,
            DB.games_table_name,
            DB.meta_table_name,
            path=execution_context.app_dir
        )

        summarizer = SummarizerTypes.get_summarizer(execution_context.summarizer_type)
        game_data = summarizer.summarize(data)

        train, test = train_test_split(game_data, test_size=0.2)

        # TODO: This assumes that the last column is our winner column.  The
        # summarizer needs to either guarantee this or return them separately.
        targetsColumnName = train.columns[len(train.columns)-1]
        train_targets = train[targetsColumnName].to_list()
        train.drop(targetsColumnName, axis=1, inplace=True)
        targetsColumnName = test.columns[len(test.columns)-1]
        test_targets = test[targetsColumnName].to_list()
        test.drop(targetsColumnName, axis=1, inplace=True)

        # create LR model
        model = LinearRegression()

        # Fit
        model.fit(train, train_targets)

        summary_table = []
        pvalue_table = []

        # r-squared
        train_pred = model.predict(train)
        r_squared = r2_score(train_targets, train_pred)
        summary_table.append(["R-squared", str(r_squared)])

        # P-Values
        x_intercept = sm.add_constant(train)
        model_sm = sm.OLS(train_targets, x_intercept).fit()
        pvalue_table = list(map(list, model_sm.pvalues.items()))
        for idx in range(len(pvalue_table)):
            pvalue_table[idx][1] = np.format_float_scientific(pvalue_table[idx][1])
        
        summary_table.append([
            "Mean squared error:",
            "%.2f" % mean_squared_error(train_targets, train_pred)
        ])

        print("<green>Stats from train operation:</green>")
        utl.print_table(summary_table)
        print("<blue>PValues:</blue>")
        utl.print_table(pvalue_table)
        
        summary_table = []
        pvalue_table = []

        test_pred = model.predict(test)
        r_squared = r2_score(test_targets, test_pred)
        summary_table.append(["R-squared: ", str(r_squared)])

        # P-Values
        x_intercept = sm.add_constant(test)
        model_sm = sm.OLS(test_targets, x_intercept).fit()
        pvalue_table = list(map(list, model_sm.pvalues.items()))
        for idx in range(len(pvalue_table)):
            pvalue_table[idx][1] = np.format_float_scientific(pvalue_table[idx][1])

        summary_table.append([
            "Mean squared error:",
            "%.2f" % mean_squared_error(test_targets, test_pred)
        ])

        print("<green>Stats from test operation:</green>")
        utl.print_table(summary_table)
        print("<blue>PValues:</blue>")
        utl.print_table(pvalue_table)

        # Coefficients
        # metrics_table.append(["Coef: ", str(model.coef_)])
        # metrics_table.append(["Intercept: ", str(model.intercept_)])
        # print("Coef: ", model.coef_)
        # print("Intercept: ", model.intercept_)

        if execution_context.output_file:
            filename = execution_context.output_file
        else:
            filename = f"{summarizer.get_filename_prefix()}_{_model_filename_part}.pkl"

        with open(os.path.join(execution_context.app_dir, filename), "wb") as file:
            dump(model, file, protocol=5)

        logger.info("End of model training.")