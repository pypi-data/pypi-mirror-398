import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.impute import KNNImputer


def run(csv_path, show_plots=True):
    """
    Perform missing value imputation and outlier treatment on a dataset.

    Parameters:
    csv_path (str): Path to the CSV file
    show_plots (bool): Whether to display plots
    """

    # Load dataset
    df = pd.read_csv(csv_path)

    print("Original Dataset:")
    print(df.head())

    print("\nMissing values per feature:")
    print(df.isnull().sum())

    # Basic imputations
    df_mean = df.fillna(df.mean(numeric_only=True))
    df_median = df.fillna(df.median(numeric_only=True))
    df_mode = df.fillna(df.mode().iloc[0])

    print("\nDataset after Mean Imputation:")
    print(df_mean.head())

    print("\nDataset after Median Imputation:")
    print(df_median.head())

    print("\nDataset after Mode Imputation:")
    print(df_mode.head())

    # KNN Imputation (numeric only)
    numeric_df = df.select_dtypes(include=np.number)

    imputer = KNNImputer(n_neighbors=3)
    df_knn = pd.DataFrame(
        imputer.fit_transform(numeric_df),
        columns=numeric_df.columns
    )

    print("\nDataset after KNN Imputation:")
    print(df_knn.head())

    # Visualization
    if show_plots:
        for col in df_knn.columns:
            plt.figure(figsize=(10, 4))

            plt.subplot(1, 2, 1)
            sns.boxplot(y=df_knn[col])
            plt.title(f"Boxplot of {col}")

            plt.subplot(1, 2, 2)
            plt.scatter(range(len(df_knn)), df_knn[col])
            plt.title(f"Scatter plot of {col}")

            plt.tight_layout()
            plt.show()

    # Outlier treatment using IQR
    df_cleaned = df_knn.copy()

    for col in df_cleaned.columns:
        Q1 = df_cleaned[col].quantile(0.25)
        Q3 = df_cleaned[col].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        df_cleaned[col] = np.where(
            (df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound),
            np.nan,
            df_cleaned[col]
        )

    df_cleaned.fillna(df_cleaned.median(), inplace=True)

    print("\nFinal Cleaned Dataset after Imputation and Outlier Treatment:")
    print(df_cleaned.head())

    print("\nProgram executed successfully!")

    return df_cleaned