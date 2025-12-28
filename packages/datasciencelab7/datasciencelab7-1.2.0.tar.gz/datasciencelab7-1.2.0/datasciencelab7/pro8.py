import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf


def run(csv_path, date_column="date", value_column="value", period=12, show_plots=True):
    """
    Perform time series analysis with decomposition and autocorrelation.

    Parameters:
    csv_path (str): Path to the CSV file
    date_column (str): Name of the date column
    value_column (str): Name of the value column
    period (int): Period for seasonal decomposition
    show_plots (bool): Whether to display plots
    """

    df = pd.read_csv(csv_path, parse_dates=[date_column])
    df.set_index(date_column, inplace=True)

    ts = df[value_column]

    if show_plots:
        seasonal_decompose(ts, model="additive", period=period).plot()
        plt.tight_layout()
        plt.show()

        ts.rolling(window=period).mean().plot()
        plt.title("Rolling Mean")
        plt.show()

        plot_acf(ts, lags=30)
        plt.show()

    print("Time series analysis completed!")
    print(f"Data points: {len(ts)}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    print("\nProgram executed successfully!")

    return ts
