import pandas as pd
import category_encoders as ce
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score


def run(csv_path, salary_threshold=60000):
    """
    Perform categorical encoding comparison (One-Hot, Label, Target).

    Parameters:
    csv_path (str): Path to the CSV file
    salary_threshold (int): Threshold for high salary classification
    """

    df = pd.read_csv(csv_path)
    df["HighSalary"] = (df["Salary"] >= salary_threshold).astype(int)

    X = df.drop(columns=["Salary", "HighSalary"])
    y = df["HighSalary"]

    cat_cols = X.select_dtypes(include="object").columns

    # One-Hot Encoding
    X_ohe = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    # Label Encoding
    X_label = X.copy()
    for col in cat_cols:
        X_label[col] = LabelEncoder().fit_transform(X[col])

    # Target Encoding
    X_target = ce.TargetEncoder(cols=cat_cols).fit_transform(X, y)

    print("Memory usage (KB):")
    print("Original:", df.memory_usage(deep=True).sum() / 1024)
    print("One-Hot:", X_ohe.memory_usage(deep=True).sum() / 1024)
    print("Label:", X_label.memory_usage(deep=True).sum() / 1024)
    print("Target:", X_target.memory_usage(deep=True).sum() / 1024)

    def test_model(X_data, name):
        X_train, X_test, y_train, y_test = train_test_split(
            X_data, y, test_size=0.2, random_state=42
        )
        model = LogisticRegression(max_iter=500)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        print(
            name,
            "Accuracy:",
            accuracy_score(y_test, y_pred),
            "F1:",
            f1_score(y_test, y_pred, zero_division=0)
        )

    test_model(X_ohe, "One-Hot")
    test_model(X_label, "Label")
    test_model(X_target, "Target")

    print("\nProgram executed successfully!")

    return {"one_hot": X_ohe, "label": X_label, "target": X_target}