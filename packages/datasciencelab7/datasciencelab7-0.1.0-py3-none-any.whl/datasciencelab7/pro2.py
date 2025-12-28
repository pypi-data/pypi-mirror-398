import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler, StandardScaler, PowerTransformer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
df = pd.read_csv("employee_skewed_dataset.csv")
num = df.select_dtypes(include=np.number)
norm = MinMaxScaler().fit_transform(num)
std = StandardScaler().fit_transform(num)
log_data = np.log1p(num)
power = PowerTransformer().fit_transform(num)
for col in num.columns:
    plt.figure(figsize=(9,3))
    plt.subplot(1,3,1); plt.hist(num[col], bins=30)
    plt.subplot(1,3,2); plt.hist(log_data[col], bins=30)
    plt.subplot(1,3,3); plt.hist(power[:, num.columns.get_loc(col)], bins=30)
    plt.tight_layout(); plt.show()
print("Skewness before:\n", num.skew())
print("After log:\n", log_data.skew())
print("After power:\n", pd.DataFrame(power, columns=num.columns).skew())
X = num.drop(columns=["Salary"])
y = num["Salary"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = LinearRegression().fit(X_train, y_train)
print("Before:", r2_score(y_test, model.predict(X_test)),
      mean_squared_error(y_test, model.predict(X_test)))
power_df = pd.DataFrame(power, columns=num.columns)
X_p = power_df.drop(columns=["Salary"])
y_p = power_df["Salary"]
X_p_train, X_p_test, y_p_train, y_p_test = train_test_split(X_p, y_p, test_size=0.2, random_state=42)
model.fit(X_p_train, y_p_train)

print("After power:", r2_score(y_p_test, model.predict(X_p_test)),
      mean_squared_error(y_p_test, model.predict(X_p_test)))

