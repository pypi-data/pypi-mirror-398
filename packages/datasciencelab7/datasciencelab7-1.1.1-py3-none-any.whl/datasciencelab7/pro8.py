import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf

df = pd.read_csv()
df.set_index("date", inplace=True)

ts = df["value"]

seasonal_decompose(ts, model="additive", period=12).plot()
plt.tight_layout()
plt.show()

ts.rolling(window=12).mean().plot()
plt.show()

plot_acf(ts, lags=30)
plt.show()
