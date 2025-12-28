import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.stats import zscore
from sklearn.cluster import DBSCAN

df = pd.read_csv("eda_anomaly_dataset.csv")

print("Original Dataset Shape:", df.shape)
print("\nSummary Statistics (Original Data)")
print(df.describe())

numeric_cols = df.select_dtypes(include=np.number).columns

# ---------------- Z-SCORE METHOD ----------------

z_scores = np.abs(zscore(df[numeric_cols]))
df_zscore = df[(z_scores < 3).all(axis=1)]

print("\nAfter Z-score Removal Shape:", df_zscore.shape)

for col in numeric_cols:
    plt.figure(figsize=(8, 4))
    sns.boxplot(x=df[col])
    plt.title(f"Boxplot of {col} (Before Z-score)")
    plt.show()

# ---------------- IQR METHOD ----------------

df_iqr = df.copy()

for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    df_iqr = df_iqr[(df_iqr[col] >= lower) & (df_iqr[col] <= upper)]

    plt.figure(figsize=(8, 4))
    sns.boxplot(x=df[col])
    plt.title(f"Boxplot of {col} (IQR Detection)")
    plt.show()

print("\nAfter IQR Removal Shape:", df_iqr.shape)

# ---------------- DBSCAN METHOD ----------------

X = df[numeric_cols[:2]]

dbscan = DBSCAN(eps=15, min_samples=5)
df["dbscan_label"] = dbscan.fit_predict(X)

df_dbscan = df[df["dbscan_label"] != -1]

print("\nAfter DBSCAN Removal Shape:", df_dbscan.shape)

plt.figure(figsize=(8, 6))
sns.scatterplot(
    data=df,
    x=numeric_cols[0],
    y=numeric_cols[1],
    hue="dbscan_label",
    palette="viridis"
)
plt.title("DBSCAN Clustering (Outliers = -1)")
plt.show()

# ---------------- EDA COMPARISON ----------------

print("\nSummary Statistics (After IQR Outlier Removal)")
print(df_iqr.describe())
