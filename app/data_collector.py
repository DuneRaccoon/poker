# data_collector.py

import pandas as pd
from typing import List, Dict, Any, Optional

class DataCollector:
    """
    Collects data from poker game simulations for machine learning purposes.
    """

    def __init__(self):
        # Initialize an empty list to store records
        self.records: List[Dict[str, Any]] = []

    def record_decision_point(self, data: Dict[str, Any]) -> None:
        """
        Records data at each decision point.

        Parameters:
            data (Dict[str, Any]): A dictionary containing data fields.
        """
        self.records.append(data)
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Returns statistics about the collected data.

        Returns:
            Dict[str, Any]: A dictionary containing statistics.
        """
        stats = {}
        if self.records:
            stats['num_records'] = len(self.records)
            stats['fields'] = list(self.records[0].keys())
        else:
            stats['num_records'] = 0
            stats['fields'] = []
        return stats

    def get_dataset(self) -> pd.DataFrame:
        """
        Returns the collected data as a Pandas DataFrame.

        Returns:
            pd.DataFrame: The dataset.
        """
        return pd.DataFrame(self.records)

    def save_to_csv(self, filename: str) -> None:
        """
        Saves the dataset to a CSV file.

        Parameters:
            filename (str): The name of the CSV file.
        """
        df = self.get_dataset()
        df.to_csv(filename, index=False)

    def reset(self) -> None:
        """
        Clears the collected records.
        """
        self.records = []
