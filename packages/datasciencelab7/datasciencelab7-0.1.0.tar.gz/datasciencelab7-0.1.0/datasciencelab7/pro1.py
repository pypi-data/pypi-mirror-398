11111……… import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.impute import KNNImputer
df = pd.read_csv("KNN-imputed_dataset.csv")
print("Original Dataset:")
print(df.head())
print("\nMissing values per feature:")
print(df.isnull().sum())
df_mean = df.fillna(df.mean(numeric_only=True))
df_median = df.fillna(df.median(numeric_only=True))
df_mode = df.fillna(df.mode().iloc[0])
print("\nDataset after Mean Imputation:")
print(df_mean.head())
print("\nDataset after Median Imputation:")
print(df_median.head())
print("\nDataset after Mode Imputation:")
print(df_mode.head())
numeric_df = df.select_dtypes(include=np.number)
imputer = KNNImputer(n_neighbors=3)
df_knn = pd.DataFrame(
    imputer.fit_transform(numeric_df),
    columns=numeric_df.columns
)
print("\nDataset after KNN Imputation:")
print(df_knn.head())
for col in df_knn.columns:
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    sns.boxplot(y=df_knn[col])
    plt.subplot(1, 2, 2)
    plt.scatter(range(len(df_knn)), df_knn[col])
    plt.tight_layout()
    plt.show()
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