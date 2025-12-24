import os
from pathlib import Path
from typing import Dict, List

import pandas as pd
from sqlitedict import SqliteDict


class Utility:
    """Static class with utility methods.

    """
    
    @staticmethod
    def json_value_or_default(
        json_data: Dict[str, object],
        *keys: str,
        default=0
    ) -> object:
        """
        Check the json_data for a value associated with the provided key.  If no
        such key exists, return the default value instead.

        TODO: Use dictionary unpacking to manage multiple indexing.
        TODO: Update all the dictionary indexing with this method.

        Args:
            json_data (Dict[str, object]): Data to parse value from.
            default (int, optional): Default value to return if any failure occurs.
            Defaults to 0.

        Returns:
            object: The parsed value or default.
        """
        try:
            value = json_data
            for key in keys:
                value = value[key]
            return value
        except KeyError:
            # TODO: Log
            return default

    @staticmethod
    def print_table(
        table: List[List[str]],
        align: str="",
        hasHeader: bool=False,
        pad: int=2,
        isGrid: bool=False
    ):
        """
        Takes a 2 dimensional list of strings and prints the contents out in the form
        of a table.
        
        Values must be of type string or method will throw.

        Args:
            table (List[List[str]]): A list of lists of strings holding the data
            to be tabulated.
            align (str, optional): Specify cell alignment. Defaults to "".
            hasHeader (bool, optional): Specify if data contains a header.
            Defaults to False.
            pad (int, optional): Specify the amount of cell padding to use.
            Defaults to 2.
            isGrid (bool, optional): Specify if the grid should be printed.
            Defaults to False.
        """
        table = [row[:] for row in table] # copy table
        numRows, numCols = len(table), len(table[0]) # table size
        align = align.ljust(numCols,"L") # align left by default
        align = ["RC".find(c)+1 for c in align] # convert to index (?RC=012)
        widths = [max(len(row[col]) for row in table) for col in range(numCols)] # column widths

        # --- apply column widths with alignments ---
        if hasHeader: # header is centered
            for x in range(numCols):
                table[0][x] = table[0][x].center(widths[x])
        for y in range(hasHeader, numRows): # apply column alignments
            for x in range(numCols):
                c = table[y][x]
                table[y][x] = [c.ljust, c.rjust, c.center][align[x]](widths[x])

        # --- data for printing
        P = " "*pad
        LSEP,SEP,RSEP = "│"+P, P+"│"+P, P+"│"
        lines = ["─"*(widths[col]+pad*2) for col in range(numCols)]

        drawLine = [isGrid]*numRows
        drawLine[0]|=hasHeader
        drawLine[-1] = False
        if hasHeader or isGrid:
            gridLine = "├"+"┼".join(lines)+"┤" # if any(drawLine)

        # --- print rows ---
        print("┌"+"┬".join(lines)+"┐")
        for y in range(numRows):
            print(LSEP+SEP.join(table[y])+RSEP)
            if drawLine[y]:
                print(gridLine)
        print("└"+"┴".join(lines)+"┘")

    @staticmethod
    def get_db_path(path: Path) -> str:
        """Get database file full path.

        Args:
            path (Path): Path where database file should reside.

        Returns:
            str: Full path to database file.
        """
        return os.path.join(path, "NHLPredictor.sqlite")
    
    @staticmethod
    def split_save_try_pair(value: str) -> tuple[int, ...]:
        """Method to split columns using compound values separated by a known
        delimeter.
        
        TODO: We should generalize this.

        Args:
            value (str): Value to be split

        Returns:
            tuple[int, ...]: Tuple containing the separated values.
        """
        parts = str(value).split('/')
        parts = [int(part) for part in parts]

        return tuple(parts)

    @staticmethod
    def get_sqlitedict_tables(
        *names: str,
        path: Path,
        update_db: bool = False,
        read_only: bool = False
    ) -> Dict[str, SqliteDict]:
        """Get a dictionary of table names to SqliteDict database objects.

        Args:
            names (str): Database table names.
            path (Path): Path to location to find or save database file.
            update_db (bool, optional): Indicates if tables should be cleared first. Defaults to False.
            read_only (bool, optional): Indicates if tables should be editable. Defaults to False.

        Returns:
            Dict[str, SqliteDict]: Dictionary of database tables.
        """
        DBs = {}
        if update_db:
            # Empty the database on open
            flag = "w"
        else:
            # Open for read/write without modification
            flag = "c"
        if read_only:
            # Process readonly flag last as we want it to take precedence.
            flag = "r"

        for name in names:
            DBs[name] = SqliteDict(
                Utility.get_db_path(path),
                tablename=name,
                autocommit=True,
                flag=flag
            )
        return DBs
    
    def get_pandas_tables(
        *names: str,
        path: Path
    ) -> Dict[str, pd.DataFrame]:
        """_summary_

        Args:
            names (str): Database table names.
            path (Path): Path to location to find or save database file.

        Returns:
            Dict[str, pd.DataFrame]: Dictionary of table names to pandas
            DataFrames holding each table's data.
        """
        DBs = Utility.get_sqlitedict_tables(
            *names,
            path=path,
            read_only=True
        )
        for name in names:
            DBs[name] = pd.DataFrame(list(DBs[name].values()), index=list(DBs[name].keys()))
        return DBs