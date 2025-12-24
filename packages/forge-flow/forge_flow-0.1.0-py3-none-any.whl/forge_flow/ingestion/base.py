"""Abstract base class for data sources.

Defines the interface that all data connectors must implement.
"""

from abc import ABC, abstractmethod

import pandas as pd


class DataSource(ABC):
    """Abstract base class for all data connectors.

    All data sources in ForgeFlow must implement this interface,
    ensuring consistent behavior across different connector types.
    """

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """Fetch data from the source.

        Returns:
            DataFrame containing the fetched data.

        Raises:
            IngestionError: If data fetching fails.
        """
        pass
