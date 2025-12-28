import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.under_sampling import RandomUnderSampler


def run(csv_path, target_column="target", show_plots=True):
    """
    Handle class imbalance using oversampling, undersampling, and SMOTE.

    Parameters:
    csv_path (str): Path to the CSV file
    target_column (str): Name of the target column
    show_plots (bool): Whether to display plots
    """

    df = pd.read_csv(csv_path)

    print("Original Dataset:\n", df.head(), "\n")

    X = df.drop(columns=[target_column])
    y = df[target_column]

    print("Original Class Distribution:")
    print(y.value_counts(), "\n")

    if show_plots:
        plt.figure(figsize=(5, 4))
        sns.countplot(x=y)
        plt.title("Original Class Distribution")
        plt.show()

    def train_and_evaluate(X_data, y_data, name):
        X_train, X_test, y_train, y_test = train_test_split(
            X_data, y_data, test_size=0.3, random_state=42, stratify=y_data
        )

        model = LogisticRegression(max_iter=1000)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        print(f"\n{name} Dataset Performance")
        print("Accuracy :", accuracy_score(y_test, y_pred))
        print("Precision:", precision_score(y_test, y_pred))
        print("Recall   :", recall_score(y_test, y_pred))
        print("F1-score :", f1_score(y_test, y_pred))

    train_and_evaluate(X, y, "Original")

    # Oversampling
    ros = RandomOverSampler(random_state=42)
    X_over, y_over = ros.fit_resample(X, y)

    print("\nAfter Oversampling:")
    print(pd.Series(y_over).value_counts())

    if show_plots:
        plt.figure(figsize=(5, 4))
        sns.countplot(x=y_over)
        plt.title("Oversampled Class Distribution")
        plt.show()

    train_and_evaluate(X_over, y_over, "Oversampled")

    # Undersampling
    rus = RandomUnderSampler(random_state=42)
    X_under, y_under = rus.fit_resample(X, y)

    print("\nAfter Undersampling:")
    print(pd.Series(y_under).value_counts())

    if show_plots:
        plt.figure(figsize=(5, 4))
        sns.countplot(x=y_under)
        plt.title("Undersampled Class Distribution")
        plt.show()

    train_and_evaluate(X_under, y_under, "Undersampled")

    # SMOTE
    smote = SMOTE(random_state=42)
    X_smote, y_smote = smote.fit_resample(X, y)

    print("\nAfter SMOTE:")
    print(pd.Series(y_smote).value_counts())

    if show_plots:
        plt.figure(figsize=(5, 4))
        sns.countplot(x=y_smote)
        plt.title("SMOTE Class Distribution")
        plt.show()

    train_and_evaluate(X_smote, y_smote, "SMOTE")

    print("\nProgram executed successfully!")

    return {"oversampled": (X_over, y_over), "undersampled": (X_under, y_under), "smote": (X_smote, y_smote)}