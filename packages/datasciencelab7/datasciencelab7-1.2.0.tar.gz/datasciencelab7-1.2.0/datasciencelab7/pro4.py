import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import kurtosis, pearsonr, spearmanr


def run(csv_path, show_plots=True):
    """
    Perform exploratory data analysis with statistics and visualizations.

    Parameters:
    csv_path (str): Path to the CSV file
    show_plots (bool): Whether to display plots
    """

    df = pd.read_csv(csv_path)
    num_cols = df.select_dtypes(include=np.number).columns

    print("Summary Statistics\n")
    for col in num_cols:
        print(
            f"{col}: Mean={df[col].mean():.2f}, "
            f"Median={df[col].median():.2f}, "
            f"Mode={df[col].mode()[0]:.2f}"
        )
        if show_plots:
            plt.figure(figsize=(10, 4))
            plt.subplot(1, 2, 1)
            sns.histplot(df[col], kde=True)
            plt.title(f"{col} - Histogram")
            plt.subplot(1, 2, 2)
            sns.boxplot(x=df[col])
            plt.title(f"{col} - Boxplot")
            plt.tight_layout()
            plt.show()

    print("\nSkewness & Kurtosis\n")
    for col in num_cols:
        print(
            f"{col}: Skewness={df[col].skew():.2f}, "
            f"Kurtosis={kurtosis(df[col]):.2f}"
        )

    if show_plots:
        sns.pairplot(df[num_cols])
        plt.show()

        plt.figure(figsize=(8, 6))
        sns.heatmap(df[num_cols].corr(), annot=True, cmap="coolwarm")
        plt.title("Correlation Heatmap")
        plt.show()

    print("\nPearson & Spearman Correlation\n")
    for i in range(len(num_cols)):
        for j in range(i + 1, len(num_cols)):
            col1, col2 = num_cols[i], num_cols[j]
            p_corr, _ = pearsonr(df[col1], df[col2])
            s_corr, _ = spearmanr(df[col1], df[col2])
            print(
                f"{col1} vs {col2}: "
                f"Pearson={p_corr:.2f}, "
                f"Spearman={s_corr:.2f}"
            )

    print("\nProgram executed successfully!")

    return df
