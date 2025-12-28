import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from statsmodels.stats.outliers_influence import variance_inflation_factor


def run(csv_path, vif_threshold=5.0):
    """
    Handle multicollinearity using VIF analysis.

    Parameters:
    csv_path (str): Path to the CSV file
    vif_threshold (float): VIF threshold for dropping features
    """

    df = pd.read_csv(csv_path)

    X = df.select_dtypes(include=[np.number]).copy()
    y = X["Salary"]
    X = X.drop(columns=["Salary"])

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

    def compute_vif(df_numeric):
        X_const = df_numeric.copy()
        X_const.insert(0, "const", 1.0)
        vif_data = []
        for i, col in enumerate(X_const.columns):
            if col != "const":
                vif_data.append({
                    "Feature": col,
                    "VIF": variance_inflation_factor(X_const.values, i)
                })
        return pd.DataFrame(vif_data).sort_values("VIF", ascending=False)

    print("\nInitial VIF Values:\n")
    vif_table = compute_vif(X_scaled)
    print(vif_table)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42
    )

    model_before = LinearRegression()
    model_before.fit(X_train, y_train)
    y_pred_before = model_before.predict(X_test)

    print("\nModel Performance BEFORE Handling Multicollinearity")
    print("R2 Score:", r2_score(y_test, y_pred_before))
    print("RMSE:", np.sqrt(mean_squared_error(y_test, y_pred_before)))

    X_reduced = X_scaled.copy()

    while True:
        vif_table = compute_vif(X_reduced)
        max_vif = vif_table["VIF"].max()
        if max_vif > vif_threshold:
            drop_feature = vif_table.iloc[0]["Feature"]
            print(f"Dropping feature '{drop_feature}' with VIF = {max_vif:.2f}")
            X_reduced = X_reduced.drop(columns=[drop_feature])
        else:
            break

    print("\nFinal VIF Values After Reduction:\n")
    print(compute_vif(X_reduced))

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X_reduced, y, test_size=0.3, random_state=42
    )

    model_after = LinearRegression()
    model_after.fit(X_train_r, y_train_r)
    y_pred_after = model_after.predict(X_test_r)

    print("\nModel Performance AFTER Handling Multicollinearity")
    print("R2 Score:", r2_score(y_test_r, y_pred_after))
    print("RMSE:", np.sqrt(mean_squared_error(y_test_r, y_pred_after)))

    print("\nProgram executed successfully!")

    return X_reduced
