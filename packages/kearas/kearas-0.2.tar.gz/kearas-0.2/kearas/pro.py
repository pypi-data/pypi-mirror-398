def pro1():
    print(
        '''import pandas as pd
data = pd.read_csv("Missing_value_counts_per_column.csv")

print("Sample dataset:\n", data.head())

missing_counts = data.isnull().sum()

print("\nMissing values in each feature:\n")
print(missing_counts)
import pandas as pd

data = pd.read_csv("sample_missing_dataset for 1b.csv")

print("Original Dataset with Missing Values:\n")
print(data.head())

data_mean = data.copy()
for col in data_mean.select_dtypes(include=['float64', 'int64']).columns:
    data_mean[col].fillna(data_mean[col].mean(), inplace=True)

print("\nDataset after Mean Imputation:\n")
print(data_mean.head())

data_median = data.copy()
for col in data_median.select_dtypes(include=['float64', 'int64']).columns:
    data_median[col].fillna(data_median[col].median(), inplace=True)

print("\nDataset after Median Imputation:\n")
print(data_median.head())

data_mode = data.copy()
for col in data_mode.columns:
    data_mode[col].fillna(data_mode[col].mode()[0], inplace=True)

print("\nDataset after Mode Imputation:\n")
print(data_mode.head())

import pandas as pd

data = pd.read_csv("employee_missing_dataset for 1c.csv")
print(data)
print("\nMissing values per column:\n", data.isnull().sum())

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv("employee_outlier_dataset for 1d.csv")

plt.figure(figsize=(12,5))

plt.subplot(1,2,1)
sns.boxplot(y=data['Age'])
plt.title("Box Plot - Age")

plt.subplot(1,2,2)
sns.boxplot(y=data['Salary'])
plt.title("Box Plot - Salary")

plt.show()

plt.figure(figsize=(12,5))

plt.subplot(1,2,1)
plt.scatter(data.index, data['Age'])
plt.title("Scatter Plot - Age")
plt.xlabel("Index")
plt.ylabel("Age")

plt.subplot(1,2,2)
plt.scatter(data.index, data['Salary'])
plt.title("Scatter Plot - Salary")
plt.xlabel("Index")
plt.ylabel("Salary")

plt.show()

import pandas as pd

data = pd.read_csv("employee_outlier_dataset for 1e.csv")

print("Original Dataset:\n")
print(data)

def detect_and_remove_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    print(f"\n{column} - Q1: {Q1}, Q3: {Q3}, IQR: {IQR}")
    print(f"Lower Bound: {lower_bound}, Upper Bound: {upper_bound}")

    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    print(f"\nDetected Outliers in {column}:\n", outliers)

    df_cleaned = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    return df_cleaned

cleaned_data = data.copy()
for col in ["Age", "Salary"]:
    cleaned_data = detect_and_remove_outliers(cleaned_data, col)

print("\nCleaned Dataset (Outliers Removed):\n")
print(cleaned_data)

import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer

data = pd.read_csv("employee_outlier_dataset for 1d.csv")

print("Original Dataset:\n", data)

data_imputed = data.copy()
for col in ["Age", "Salary"]:
    data_imputed[col].fillna(data_imputed[col].mean(), inplace=True)

print("\nDataset after Imputation (Mean used for numeric columns):\n", data_imputed)

def remove_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

cleaned_data = data_imputed.copy()
for col in ["Age", "Salary"]:
    cleaned_data = remove_outliers_iqr(cleaned_data, col)

print("\nCleaned Dataset after Imputation & Outlier Treatment:\n", cleaned_data)

''')
    
def pro2():
    print(
        '''import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

data = {
    "Age": [25, 30, 35, 40, 45, 50],
    "Salary": [50000, 60000, 75000, 80000, 90000, 100000],
    "Experience": [1, 3, 5, 7, 9, 12]
}
df = pd.DataFrame(data)

print("Original Dataset:\n", df)

scaler_minmax = MinMaxScaler()
df_normalized = pd.DataFrame(scaler_minmax.fit_transform(df), columns=df.columns)

print("\nNormalized Dataset (0–1 range):\n", df_normalized)

scaler_standard = StandardScaler()
df_standardized = pd.DataFrame(scaler_standard.fit_transform(df), columns=df.columns)

print("\nStandardized Dataset (mean=0, std=1):\n", df_standardized)

next cell
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import PowerTransformer
csv_path = "employee_skewed_dataset.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    np.random.seed(42)
    df = pd.DataFrame({
        "Age": np.random.randint(22, 65, 100),
        "Experience": np.random.randint(1, 40, 100),
        "Salary": np.random.exponential(scale=30000, size=100).astype(int) + 20000
    })
    df.to_csv(csv_path, index=False)

print("Dataset preview:\n", df.head())

df_log = df.copy()
df_log["Salary_log"] = np.log1p(df_log["Salary"])

pt = PowerTransformer(method="yeo-johnson")
df_power = df.copy()
df_power["Salary_power"] = pt.fit_transform(df_power[["Salary"]])


def skew(x):
    return pd.Series(x).skew()

print("\nSkewness:")
print(f"Original Salary:      {skew(df['Salary']):.3f}")
print(f"Log-transformed:      {skew(df_log['Salary_log']):.3f}")
print(f"Power-transformed:    {skew(df_power['Salary_power']):.3f}")

plt.figure(figsize=(15, 5))

# 1) Original
plt.subplot(1, 3, 1)
plt.hist(df["Salary"], bins=30)
plt.title("Original Skewed Salary")
plt.xlabel("Salary")
plt.ylabel("Count")

# 2) Log transformed
plt.subplot(1, 3, 2)
plt.hist(df_log["Salary_log"], bins=30)
plt.title("Log Transformed Salary")
plt.xlabel("Salary_log")
plt.ylabel("Count")

# 3) Power transformed (Yeo-Johnson)
plt.subplot(1, 3, 3)
plt.hist(df_power["Salary_power"], bins=30)
plt.title("Power Transformed Salary")
plt.xlabel("Salary_power")
plt.ylabel("Count")

plt.tight_layout()
plt.show()

next cell
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import PowerTransformer

df = pd.read_csv("employee_skewed_dataset.csv")

print("Dataset preview:\n", df.head())

df["Salary_log"] = np.log1p(df["Salary"])

pt = PowerTransformer(method="yeo-johnson")
df["Salary_power"] = pt.fit_transform(df[["Salary"]])

skew_original = df["Salary"].skew()
skew_log = df["Salary_log"].skew()
skew_power = df["Salary_power"].skew()

print("\nSkewness Comparison:")
print(f"Original Salary:   {skew_original:.3f}")
print(f"Log Transformed:   {skew_log:.3f}")
print(f"Power Transformed: {skew_power:.3f}")

plt.figure(figsize=(15,5))

# Original
plt.subplot(1,3,1)
plt.hist(df["Salary"], bins=30, color="red")
plt.title(f"Original Salary\nSkew={skew_original:.2f}")
plt.xlabel("Salary")
plt.ylabel("Count")

# Log Transformed
plt.subplot(1,3,2)
plt.hist(df["Salary_log"], bins=30, color="blue")
plt.title(f"Log Transformed\nSkew={skew_log:.2f}")
plt.xlabel("Salary (log)")
plt.ylabel("Count")

# Power Transformed
plt.subplot(1,3,3)
plt.hist(df["Salary_power"], bins=30, color="green")
plt.title(f"Power Transformed\nSkew={skew_power:.2f}")
plt.xlabel("Salary (power)")
plt.ylabel("Count")

plt.tight_layout()
plt.show()

next cell
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PowerTransformer

df = pd.read_csv("employee_skewed_dataset.csv")

X = df[["Age", "Experience"]]
y = df["Salary"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model_original = LinearRegression()
model_original.fit(X_train, y_train)

y_pred_orig = model_original.predict(X_test)

mse_orig = mean_squared_error(y_test, y_pred_orig)
r2_orig = r2_score(y_test, y_pred_orig)

y_train_log = np.log1p(y_train)
y_test_log = np.log1p(y_test)

model_log = LinearRegression()
model_log.fit(X_train, y_train_log)

y_pred_log = model_log.predict(X_test)
y_pred_log_back = np.expm1(y_pred_log)   

mse_log = mean_squared_error(y_test, y_pred_log_back)
r2_log = r2_score(y_test, y_pred_log_back)

pt = PowerTransformer(method="yeo-johnson")
y_train_power = pt.fit_transform(y_train.values.reshape(-1, 1))
y_test_power = pt.transform(y_test.values.reshape(-1, 1))

model_power = LinearRegression()
model_power.fit(X_train, y_train_power)

y_pred_power = model_power.predict(X_test)
y_pred_power_back = pt.inverse_transform(y_pred_power)

mse_power = mean_squared_error(y_test, y_pred_power_back)
r2_power = r2_score(y_test, y_pred_power_back)

results = pd.DataFrame({
    "Model": ["Original", "Log-Transformed", "Power-Transformed"],
    "MSE": [mse_orig, mse_log, mse_power],
    "R² Score": [r2_orig, r2_log, r2_power]
})

print("\nLinear Regression Performance Comparison:")
print(results)
        '''
    )

def pro3():
    print(
        '''import pandas as pd
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

df = pd.read_csv("employee_encoding_dataset.csv")
print("Original Dataset:\n", df, "\n")

ohe = OneHotEncoder(drop=None, sparse_output=False)  
one_hot_encoded = pd.DataFrame(
    ohe.fit_transform(df[["Department", "Gender"]]),
    columns=ohe.get_feature_names_out(["Department", "Gender"])
)

df_ohe = pd.concat([df, one_hot_encoded], axis=1)
print("One-Hot Encoded Dataset:\n", df_ohe, "\n")

df_le = df.copy()
le_dep = LabelEncoder()
le_gen = LabelEncoder()
df_le["Department_LE"] = le_dep.fit_transform(df_le["Department"])
df_le["Gender_LE"] = le_gen.fit_transform(df_le["Gender"])

print("Label Encoded Dataset:\n", df_le, "\n")

try:
    import category_encoders as ce
    target_enc = ce.TargetEncoder(cols=["Department", "Gender"])
    df_te = df.copy()
    df_te[["Department_TE", "Gender_TE"]] = target_enc.fit_transform(
        df_te[["Department", "Gender"]], df_te["Salary"]
    )
    print("Target Encoded Dataset:\n", df_te, "\n")
except ImportError:
    print("⚠️ category_encoders not installed. Run `pip install category_encoders` to enable Target Encoding.")

    next cell
    import pandas as pd
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

df = pd.read_csv("employee_encoding_dataset.csv")
print("Original Dataset:\n", df, "\n")

def memory_usage(df, name):
    mem = df.memory_usage(deep=True).sum()
    print(f"{name} Memory Usage: {mem} bytes")
    return mem

print("Original Memory Usage:")
memory_usage(df, "Original")

ohe = OneHotEncoder(drop=None, sparse_output=False)
one_hot_encoded = pd.DataFrame(
    ohe.fit_transform(df[["Department", "Gender"]]),
    columns=ohe.get_feature_names_out(["Department", "Gender"])
)
df_ohe = pd.concat([df, one_hot_encoded], axis=1)
memory_usage(df_ohe, "One-Hot Encoded")

df_le = df.copy()
le_dep = LabelEncoder()
le_gen = LabelEncoder()
df_le["Department_LE"] = le_dep.fit_transform(df_le["Department"])
df_le["Gender_LE"] = le_gen.fit_transform(df_le["Gender"])
memory_usage(df_le, "Label Encoded")

df_te = df.copy()
dept_mean = df.groupby("Department")["Salary"].mean().to_dict()
gender_mean = df.groupby("Gender")["Salary"].mean().to_dict()

df_te["Department_TE"] = df_te["Department"].map(dept_mean)
df_te["Gender_TE"] = df_te["Gender"].map(gender_mean)
memory_usage(df_te, "Target Encoded")

summary = pd.DataFrame({
    "Encoding": ["Original", "One-Hot", "Label", "Target"],
    "Memory (bytes)": [
        df.memory_usage(deep=True).sum(),
        df_ohe.memory_usage(deep=True).sum(),
        df_le.memory_usage(deep=True).sum(),
        df_te.memory_usage(deep=True).sum()
    ],
    "Interpretability": [
        "High (raw categories)",
        "Very High (clear 0/1 meaning)",
        "Low (arbitrary integers)",
        "Medium-High (reflects target mean)"
    ]
})

print("\nSummary Comparison:\n", summary)

next cell
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

df = pd.read_csv("employee_encoding_dataset.csv")

df["HighSalary"] = (df["Salary"] >= 60000).astype(int)

print("Original Dataset:\n", df, "\n")

def evaluate_model(X, y, encoding_name):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\n🔹 {encoding_name} Encoding Results:")
    print("Accuracy :", accuracy_score(y_test, y_pred))
    print("Precision:", precision_score(y_test, y_pred))
    print("Recall   :", recall_score(y_test, y_pred))
    print("F1-score :", f1_score(y_test, y_pred))

ohe = OneHotEncoder(drop=None, sparse_output=False)
X_ohe = pd.DataFrame(
    ohe.fit_transform(df[["Department", "Gender"]]),
    columns=ohe.get_feature_names_out(["Department", "Gender"])
)
evaluate_model(X_ohe, df["HighSalary"], "One-Hot")

df_le = df.copy()
le_dep = LabelEncoder()
le_gen = LabelEncoder()
df_le["Department_LE"] = le_dep.fit_transform(df_le["Department"])
df_le["Gender_LE"] = le_gen.fit_transform(df_le["Gender"])

X_le = df_le[["Department_LE", "Gender_LE"]]
evaluate_model(X_le, df_le["HighSalary"], "Label")

df_te = df.copy()
dept_mean = df.groupby("Department")["HighSalary"].mean().to_dict()
gender_mean = df.groupby("Gender")["HighSalary"].mean().to_dict()
df_te["Department_TE"] = df_te["Department"].map(dept_mean)
df_te["Gender_TE"] = df_te["Gender"].map(gender_mean)

X_te = df_te[["Department_TE", "Gender_TE"]]
evaluate_model(X_te, df_te["HighSalary"], "Target")

''')
    
def pro4():
    print('''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statistics import mode as py_mode, StatisticsError

df = pd.read_csv("employee_analysis_dataset.csv")

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
summary = []
for col in numeric_cols:
    series = df[col].dropna()
    try:
        m = py_mode(series.tolist())
    except StatisticsError:
        m = series.mode().iloc[0]
    summary.append({
        "Feature": col,
        "Count": series.shape[0],
        "Mean": round(series.mean(), 2),
        "Median": round(series.median(), 2),
        "Mode": m,
        "StdDev": round(series.std(ddof=1), 2),
        "Min": round(series.min(), 2),
        "Max": round(series.max(), 2),
        "Skew": round(series.skew(), 2)
    })

summary_df = pd.DataFrame(summary)
print("\n=== Univariate Summary Statistics ===")
print(summary_df)

for col in numeric_cols:
    plt.figure(figsize=(6,4))
    plt.hist(df[col].dropna(), bins=20)
    plt.title(f"Histogram of {col}")
    plt.xlabel(col)
    plt.ylabel("Frequency")
    plt.show()

    plt.figure(figsize=(4,4))
    plt.boxplot(df[col].dropna(), labels=[col])
    plt.title(f"Box Plot of {col}")
    plt.show()
    
    next cell
    import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis

df = pd.read_csv("employee_analysis_dataset.csv")

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

results = []
for col in numeric_cols:
    series = df[col].dropna()
    results.append({
        "Feature": col,
        "Skewness": round(skew(series), 3),
        "Kurtosis": round(kurtosis(series, fisher=False), 3) 
    })

results_df = pd.DataFrame(results)
print("\n=== Skewness and Kurtosis ===")
print(results_df)

for col in numeric_cols:
    plt.figure(figsize=(6,4))
    plt.hist(df[col].dropna(), bins=20, color="skyblue", edgecolor="black")
    plt.title(f"Distribution of {col}\nSkew={results_df.loc[results_df['Feature']==col,'Skewness'].values[0]}, "
              f"Kurtosis={results_df.loc[results_df['Feature']==col,'Kurtosis'].values[0]}")
    plt.xlabel(col)
    plt.ylabel("Frequency")
    plt.show()

next cell
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix

csv_path = "employee_analysis_dataset.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    np.random.seed(42)
    df = pd.DataFrame({
        "Age": np.random.randint(22, 65, 200),
        "Salary": (np.random.normal(70000, 15000, 200)).astype(int),
        "Experience": np.random.randint(0, 35, 200)
    })
    df.loc[np.random.choice(df.index, 3, replace=False), "Salary"] *= 2
    df.to_csv(csv_path, index=False)

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
print("Numeric features:", numeric_cols)

def scatter_plot(xcol, ycol):
    plt.figure(figsize=(6, 4))
    plt.scatter(df[xcol], df[ycol])
    plt.title(f"Scatter Plot: {xcol} vs {ycol}")
    plt.xlabel(xcol)
    plt.ylabel(ycol)
    plt.tight_layout()
    plt.show()

for i in range(len(numeric_cols)):
    for j in range(i + 1, len(numeric_cols)):
        scatter_plot(numeric_cols[i], numeric_cols[j])

corr = df[numeric_cols].corr()

plt.figure(figsize=(6, 5))
im = plt.imshow(corr.values, interpolation='nearest', aspect='auto')
plt.title("Correlation Heat Map")
plt.xticks(ticks=range(len(numeric_cols)), labels=numeric_cols, rotation=45, ha="right")
plt.yticks(ticks=range(len(numeric_cols)), labels=numeric_cols)
plt.colorbar(im, fraction=0.046, pad=0.04)
plt.tight_layout()
plt.show()

print("\nCorrelation matrix:\n", corr.round(3))

axs = scatter_matrix(df[numeric_cols], figsize=(8, 8), diagonal='hist')
for ax in axs.ravel():
    ax.set_xlabel(ax.get_xlabel(), rotation=45)
    ax.set_ylabel(ax.get_ylabel(), rotation=0)
plt.suptitle("Pair Plot (Scatter Matrix)", y=1.02)
plt.tight_layout()
plt.show()

next cell
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

df = pd.read_csv("employee_analysis_dataset.csv")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

pearson_corr = df[numeric_cols].corr(method="pearson")
print("\n=== Pearson Correlation Matrix ===")
print(pearson_corr.round(3))

spearman_corr = df[numeric_cols].corr(method="spearman")
print("\n=== Spearman Correlation Matrix ===")
print(spearman_corr.round(3))

for i in range(len(numeric_cols)):
    for j in range(i+1, len(numeric_cols)):
        print(f"\n🔹 {numeric_cols[i]} vs {numeric_cols[j]}:")
        print(f"   Pearson : {pearson_corr.loc[numeric_cols[i], numeric_cols[j]]:.3f}")
        print(f"   Spearman: {spearman_corr.loc[numeric_cols[i], numeric_cols[j]]:.3f}")


''')
    

def pro5():
    print('''import os
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler

csv_path = "employee_analysis_dataset.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    np.random.seed(42)
    n = 300
    age = np.random.randint(22, 65, n)
    exp = np.clip(age - 22 + np.random.normal(0, 3, n), 0, None)  # correlated with age
    salary = 30000 + 1500*exp + np.random.normal(0, 8000, n)
    exp2 = exp * 1.05 + np.random.normal(0, 0.5, n)
    df = pd.DataFrame({"Age": age, "Experience": exp, "Experience2": exp2, "Salary": salary})

X = df.select_dtypes(include=[np.number]).copy()

if "Salary" in X.columns:
    X = X.drop(columns=["Salary"])

scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

def compute_vif(df_numeric: pd.DataFrame) -> pd.DataFrame:
    X_with_const = df_numeric.copy()
    X_with_const.insert(0, "const", 1.0)
    vifs = []
    for i, col in enumerate(X_with_const.columns):
        if col == "const":
            continue
        vif_val = variance_inflation_factor(X_with_const.values, i)
        vifs.append({"Feature": col, "VIF": float(vif_val)})
    return pd.DataFrame(vifs).sort_values("VIF", ascending=False).reset_index(drop=True)

vif_table = compute_vif(X_scaled)
print("\n=== VIF (Variance Inflation Factor) ===")
print(vif_table.to_string(index=False))
  
def flag_multicollinearity(vif_df, threshold=5.0):
    flagged = vif_df[vif_df["VIF"] >= threshold].copy()
    if flagged.empty:
        print(f"\nNo multicollinearity flagged (all VIF < {threshold}).")
    else:
        print(f"\nFeatures with VIF ≥ {threshold} (potential multicollinearity):")
        print(flagged.to_string(index=False))
    return flagged

flag_multicollinearity(vif_table, threshold=5.0)  # common thresholds: 5 or 10
          
    next cell
    import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor


df = pd.read_csv("employee_analysis_dataset.csv")

X = df.select_dtypes(include=[np.number]).copy()
if "Salary" in X.columns:
    X = X.drop(columns=["Salary"])

scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

def compute_vif(df_numeric: pd.DataFrame) -> pd.DataFrame:
    X_with_const = df_numeric.copy()
    X_with_const.insert(0, "const", 1.0)
    vifs = []
    for i, col in enumerate(X_with_const.columns):
        if col == "const":
            continue
        vif_val = variance_inflation_factor(X_with_const.values, i)
        vifs.append({"Feature": col, "VIF": float(vif_val)})
    return pd.DataFrame(vifs).sort_values("VIF", ascending=False).reset_index(drop=True)

vif_table = compute_vif(X_scaled)
print("\n=== Initial VIF Values ===")
print(vif_table)

threshold = 5.0
X_reduced = X_scaled.copy()

while True:
    vif_table = compute_vif(X_reduced)
    max_vif = vif_table["VIF"].max()
    if max_vif > threshold:
        feature_to_drop = vif_table.iloc[0]["Feature"]  # highest VIF feature
        print(f"\nDropping '{feature_to_drop}' (VIF={max_vif:.2f}) to reduce multicollinearity...")
        X_reduced = X_reduced.drop(columns=[feature_to_drop])
    else:
        break

print("\n=== Final VIF Values (After Reduction) ===")
print(compute_vif(X_reduced))
print("\nSelected Features After Multicollinearity Handling:", list(X_reduced.columns))
          
    next cell
    import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import train_test_split

df = pd.read_csv("employee_analysis_dataset.csv")
X = df.select_dtypes(include=[np.number]).copy()
y = X["Salary"]
X = X.drop(columns=["Salary"])  # predictors only

def compute_vif(df_numeric: pd.DataFrame) -> pd.DataFrame:
    X_with_const = df_numeric.copy()
    X_with_const.insert(0, "const", 1.0)
    vifs = []
    for i, col in enumerate(X_with_const.columns):
        if col == "const":
            continue
        vif_val = variance_inflation_factor(X_with_const.values, i)
        vifs.append({"Feature": col, "VIF": float(vif_val)})
    return pd.DataFrame(vifs).sort_values("VIF", ascending=False).reset_index(drop=True)

scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)

model_before = LinearRegression()
model_before.fit(X_train, y_train)
y_pred_before = model_before.predict(X_test)

r2_before = r2_score(y_test, y_pred_before)
rmse_before = np.sqrt(mean_squared_error(y_test, y_pred_before))

print("\n=== Model Performance BEFORE Handling Multicollinearity ===")
print(f"R² Score: {r2_before:.3f}")
print(f"RMSE    : {rmse_before:.2f}")

vif_table = compute_vif(X_scaled)
print("\nInitial VIFs:\n", vif_table)

threshold = 5.0
X_reduced = X_scaled.copy()
while True:
    vif_table = compute_vif(X_reduced)
    max_vif = vif_table["VIF"].max()
    if max_vif > threshold:
        feature_to_drop = vif_table.iloc[0]["Feature"]
        print(f"Dropping '{feature_to_drop}' (VIF={max_vif:.2f})")
        X_reduced = X_reduced.drop(columns=[feature_to_drop])
    else:
        break

print("\nFinal VIFs:\n", compute_vif(X_reduced))

X_train_r, X_test_r, y_train, y_test = train_test_split(X_reduced, y, test_size=0.3, random_state=42)

model_after = LinearRegression()
model_after.fit(X_train_r, y_train)
y_pred_after = model_after.predict(X_test_r)

r2_after = r2_score(y_test, y_pred_after)
rmse_after = np.sqrt(mean_squared_error(y_test, y_pred_after))

print("\n=== Model Performance AFTER Handling Multicollinearity ===")
print(f"R² Score: {r2_after:.3f}")
print(f"RMSE    : {rmse_after:.2f}")

''')
    

def pro6():
    print('''import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

csv_path = "classification_imbalance_dataset.csv"

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    np.random.seed(42)
    n = 1000
    X1 = np.random.normal(0, 1, n)
    X2 = np.random.normal(2, 1.5, n)
    y = np.array([0]*900 + [1]*100)  # 90% of class 0, 10% of class 1
    idx = np.random.permutation(n)   # shuffle to remove ordering bias
    df = pd.DataFrame({
        "feature_1": X1[idx],
        "feature_2": X2[idx],
        "target": y[idx]
    })
    df.to_csv(csv_path, index=False)

print(f"Dataset path: {csv_path}  |  shape={df.shape}")

counts = df["target"].value_counts().sort_index()
percentages = (counts / counts.sum() * 100).round(2)
imbalance_ratio = round(counts.max() / counts.min(), 2) if counts.min() > 0 else float("inf")

summary = pd.DataFrame({
    "Class": counts.index,
    "Count": counts.values,
    "Percentage": percentages.values
})

print("\n=== Class Distribution Summary ===")
print(summary.to_string(index=False))
print(f"\nImbalance Ratio (majority/minority): {imbalance_ratio}:1")

plt.figure(figsize=(6, 4))
plt.bar(summary["Class"].astype(str), summary["Count"])
plt.title("Class Counts")
plt.xlabel("Class")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

plt.figure(figsize=(5, 5))
plt.pie(summary["Percentage"], labels=summary["Class"].astype(str),
        autopct="%1.1f%%", startangle=90)
plt.title("Class Distribution (%)")
plt.tight_layout()
plt.show()
          
next cell
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

csv_path = "classification_imbalance_dataset.csv"

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    np.random.seed(42)
    n = 1000
    X1 = np.random.normal(0, 1, n)
    X2 = np.random.normal(2, 1.5, n)
    y = np.array([0]*900 + [1]*100)  # 90% class 0, 10% class 1
    idx = np.random.permutation(n)
    df = pd.DataFrame({
        "feature_1": X1[idx],
        "feature_2": X2[idx],
        "target": y[idx]
    })
    df.to_csv(csv_path, index=False)

print(f"Loaded dataset: {csv_path}  |  shape={df.shape}")

def show_distribution(y_series, title):
    counts = y_series.value_counts().sort_index()
    perc = (counts / counts.sum() * 100).round(2)
    print(f"\n=== {title} ===")
    print(pd.DataFrame({"Class": counts.index, "Count": counts.values, "Percent": perc.values}).to_string(index=False))

    plt.figure(figsize=(5, 4))
    plt.bar(counts.index.astype(str), counts.values)
    plt.title(f"Class Counts - {title}")
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()

show_distribution(df["target"], "Original")

def random_oversample(df, target_col="target", random_state=42):
    rng = np.random.default_rng(random_state)
    counts = df[target_col].value_counts()
    majority_class = counts.idxmax()
    minority_class = counts.idxmin()
    n_major = counts.max()

    minority_df = df[df[target_col] == minority_class]
    sample_needed = n_major - len(minority_df)
    extra = minority_df.sample(n=sample_needed, replace=True, random_state=random_state)
    return pd.concat([df, extra], ignore_index=True)

df_over = random_oversample(df, "target")
show_distribution(df_over["target"], "Random Oversampling")
df_over.to_csv("classification_imbalance_oversampled.csv", index=False)

def random_undersample(df, target_col="target", random_state=42):
    counts = df[target_col].value_counts()
    majority_class = counts.idxmax()
    minority_class = counts.idxmin()
    n_minor = counts.min()

    majority_df = df[df[target_col] == majority_class].sample(n=n_minor, replace=False, random_state=random_state)
    minority_df = df[df[target_col] == minority_class]
    return pd.concat([majority_df, minority_df], ignore_index=True)

df_under = random_undersample(df, "target")
show_distribution(df_under["target"], "Random Undersampling")
df_under.to_csv("classification_imbalance_undersampled.csv", index=False)

try:
    from imblearn.over_sampling import SMOTE
    X = df.drop(columns=["target"])
    y = df["target"]
    sm = SMOTE(random_state=42, k_neighbors=5)
    X_res, y_res = sm.fit_resample(X, y)
    df_smote = pd.DataFrame(X_res, columns=X.columns)
    df_smote["target"] = y_res
    show_distribution(df_smote["target"], "SMOTE")
    df_smote.to_csv("classification_imbalance_smote.csv", index=False)
except Exception as e:
    print(f"\nSMOTE not available: {e}\nInstall with: pip install imbalanced-learn")
          
next cell
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

csv_path = "classification_imbalance_dataset.csv"

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    np.random.seed(42)
    n = 1000
    X1 = np.random.normal(0, 1, n)
    X2 = np.random.normal(2, 1.5, n)
    y = np.array([0]*900 + [1]*100)
    idx = np.random.permutation(n)
    df = pd.DataFrame({
        "feature_1": X1[idx],
        "feature_2": X2[idx],
        "target": y[idx]
    })
    df.to_csv(csv_path, index=False)

X = df.drop(columns=["target"])
y = df["target"]

def random_oversample(df, target_col="target", random_state=42):
    counts = df[target_col].value_counts()
    majority_class = counts.idxmax()
    minority_class = counts.idxmin()
    n_major = counts.max()

    minority_df = df[df[target_col] == minority_class]
    sample_needed = n_major - len(minority_df)
    extra = minority_df.sample(n=sample_needed, replace=True, random_state=random_state)
    return pd.concat([df, extra], ignore_index=True)

def random_undersample(df, target_col="target", random_state=42):
    counts = df[target_col].value_counts()
    majority_class = counts.idxmax()
    minority_class = counts.idxmin()
    n_minor = counts.min()

    majority_df = df[df[target_col] == majority_class].sample(n=n_minor, replace=False, random_state=random_state)
    minority_df = df[df[target_col] == minority_class]
    return pd.concat([majority_df, minority_df], ignore_index=True)

df_over = random_oversample(df)
df_under = random_undersample(df)

try:
    from imblearn.over_sampling import SMOTE
    sm = SMOTE(random_state=42, k_neighbors=5)
    X_sm, y_sm = sm.fit_resample(X, y)
    df_smote = pd.DataFrame(X_sm, columns=X.columns)
    df_smote["target"] = y_sm
except Exception as e:
    df_smote = None
    print(f"SMOTE not available: {e}")

def evaluate_dataset(df, title):
    X = df.drop(columns=["target"])
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    model = LogisticRegression(solver="liblinear", class_weight=None, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\n=== {title} ===")
    print(classification_report(y_test, y_pred, digits=3))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

evaluate_dataset(df, "Original Imbalanced Data")
evaluate_dataset(df_over, "Oversampled Data")
evaluate_dataset(df_under, "Undersampled Data")
if df_smote is not None:
    evaluate_dataset(df_smote, "SMOTE Data")

''')
    
def pro7():
    print('''import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

csv_path = "eda_anomaly_dataset.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    np.random.seed(42)
    n = 500
    df = pd.DataFrame({
        "feature_A": np.random.normal(loc=50, scale=10, size=n),
        "feature_B": np.random.normal(loc=100, scale=20, size=n),
        "feature_C": np.random.exponential(scale=30, size=n)  # skewed
    })
    out_idx = np.random.choice(n, size=8, replace=False)
    df.loc[out_idx[:4], "feature_A"] += 5 * df["feature_A"].std()
    df.loc[out_idx[4:], "feature_B"] -= 5 * df["feature_B"].std()
    df.to_csv(csv_path, index=False)

print(f"Loaded: {csv_path} | shape={df.shape}")

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
if not num_cols:
    raise ValueError("No numeric columns found for anomaly detection.")

def zscore_anomalies(df: pd.DataFrame, cols, threshold=3.0):
    zs = (df[cols] - df[cols].mean()) / df[cols].std(ddof=1)
    flags = (zs.abs() > threshold)
    return flags, zs

z_flags, zscores = zscore_anomalies(df, num_cols, threshold=3.0)

def iqr_anomalies(df: pd.DataFrame, cols, k=1.5):
    bounds = {}
    flags = pd.DataFrame(False, index=df.index, columns=cols)
    for c in cols:
        q1 = df[c].quantile(0.25)
        q3 = df[c].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - k * iqr
        upper = q3 + k * iqr
        bounds[c] = (lower, upper, q1, q3, iqr)
        flags[c] = (df[c] < lower) | (df[c] > upper)
    return flags, bounds

iqr_flags, iqr_bounds = iqr_anomalies(df, num_cols, k=1.5)

summary_rows = []
for c in num_cols:
    summary_rows.append({
        "Feature": c,
        "Z-score anomalies": int(z_flags[c].sum()),
        "IQR anomalies": int(iqr_flags[c].sum())
    })
summary = pd.DataFrame(summary_rows).set_index("Feature")
summary["Any anomaly (union)"] = (z_flags | iqr_flags).sum()
print("\n=== Anomaly Summary (counts) ===")
print(summary.to_string())

any_anomaly_idx = (z_flags | iqr_flags).any(axis=1)
print(f"\nTotal rows with any anomaly (union): {int(any_anomaly_idx.sum())} / {len(df)}")

def plot_index_scatter_with_anomalies(series: pd.Series, z_flag: pd.Series, iqr_flag: pd.Series):
    """Index vs value scatter, highlighting Z-score and IQR anomalies."""
    idx = series.index
    normal_mask = ~(z_flag | iqr_flag)
    # Normal points
    plt.figure(figsize=(7,4))
    plt.scatter(idx[normal_mask], series[normal_mask], s=14, label="Normal")
    # Z-score only
    z_only = z_flag & ~iqr_flag
    if z_only.any():
        plt.scatter(idx[z_only], series[z_only], s=28, marker="^", label="Z-score anomaly")
    # IQR only
    iqr_only = iqr_flag & ~z_flag
    if iqr_only.any():
        plt.scatter(idx[iqr_only], series[iqr_only], s=28, marker="s", label="IQR anomaly")
    # Both
    both = z_flag & iqr_flag
    if both.any():
        plt.scatter(idx[both], series[both], s=40, marker="x", label="Both (Z & IQR)")
    plt.title(f"Index vs Value — {series.name}")
    plt.xlabel("Index")
    plt.ylabel(series.name)
    plt.legend()
    plt.tight_layout()
    plt.show()

def boxplot_with_iqr_bounds(series: pd.Series, bounds):
    """Box plot with IQR whisker bounds drawn."""
    lower, upper, q1, q3, iqr = bounds
    plt.figure(figsize=(4,4))
    plt.boxplot(series.dropna(), vert=True, labels=[series.name])
    # horizontal lines for IQR bounds (optional visual aid)
    plt.axhline(lower, linestyle="--")
    plt.axhline(upper, linestyle="--")
    plt.title(f"Box Plot with IQR Bounds — {series.name}")
    plt.tight_layout()
    plt.show()


for c in num_cols:
    # Index vs Value scatter highlighting anomalies
    plot_index_scatter_with_anomalies(df[c], z_flags[c], iqr_flags[c])
    # Box plot with IQR bounds
    boxplot_with_iqr_bounds(df[c], iqr_bounds[c])

flagged = df.copy()
for c in num_cols:
    flagged[f"{c}_z_anom"] = z_flags[c]
    flagged[f"{c}_iqr_anom"] = iqr_flags[c]

flagged.to_csv("eda_anomalies_flagged.csv", index=False)
print("\nFlagged rows saved to: eda_anomalies_flagged.csv")
          
next cell
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("eda_anomaly_dataset.csv")

def remove_iqr_outliers(df, cols, k=1.5):
    cleaned = df.copy()
    for c in cols:
        q1 = cleaned[c].quantile(0.25)
        q3 = cleaned[c].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - k * iqr, q3 + k * iqr
        cleaned = cleaned[(cleaned[c] >= lower) & (cleaned[c] <= upper)]
    return cleaned

num_cols = df.select_dtypes(include="number").columns
df_clean = remove_iqr_outliers(df, num_cols)

print(f"Original shape: {df.shape}, After anomaly removal: {df_clean.shape}")

print("\n=== Summary Statistics (Original) ===")
print(df[num_cols].describe())

print("\n=== Summary Statistics (After Removing Anomalies) ===")
print(df_clean[num_cols].describe())

for col in num_cols:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Histogram
    axes[0].hist(df[col], bins=30, alpha=0.6, label="Original")
    axes[0].hist(df_clean[col], bins=30, alpha=0.6, label="Cleaned")
    axes[0].set_title(f"Histogram - {col}")
    axes[0].legend()

    # Boxplot
    axes[1].boxplot([df[col], df_clean[col]], labels=["Original", "Cleaned"])
    axes[1].set_title(f"Boxplot - {col}")

    plt.suptitle(f"Distribution Comparison: {col}", fontsize=12)
    plt.tight_layout()
    plt.show()

          
    next cell
    import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("eda_anomaly_dataset.csv")
num_cols = df.select_dtypes(include="number").columns

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[num_cols])

iso = IsolationForest(contamination=0.02, random_state=42)  # assume ~2% anomalies
df["anomaly_iforest"] = iso.fit_predict(X_scaled)

df["anomaly_iforest"] = df["anomaly_iforest"].map({1: "Normal", -1: "Anomaly"})

print("\nAnomaly Counts (Isolation Forest):")
print(df["anomaly_iforest"].value_counts())

plt.figure(figsize=(7,5))
colors = {"Normal": "blue", "Anomaly": "red"}
plt.scatter(df["feature_A"], df["feature_B"],
            c=df["anomaly_iforest"].map(colors), alpha=0.6)
plt.xlabel("feature_A")
plt.ylabel("feature_B")
plt.title("Isolation Forest Anomaly Detection")
plt.show()
''')
    
def pro8():
    print('''import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose, STL

csv_path = "time_series_data.csv"
if os.path.exists(csv_path):
    ts = pd.read_csv(csv_path, parse_dates=["date"])
    ts = ts.sort_values("date").set_index("date")
    y = ts["value"].asfreq("D")  # set to daily frequency; change if your data differs
else:
    rng = pd.date_range("2021-01-01", periods=500, freq="D")
    np.random.seed(42)
    trend = np.linspace(10, 20, len(rng))
    season = 2.5 * np.sin(2 * np.pi * rng.dayofyear / 7)  # weekly seasonality
    noise = np.random.normal(0, 1.0, len(rng))
    y = pd.Series(trend + season + noise, index=rng, name="value")
    ts = y.to_frame("value")
    ts.to_csv(csv_path, index=True)
    print(f"Generated sample data → {csv_path}")

y = y.interpolate()

period = 7  # change as needed (e.g., 12 for monthly with yearly seasonality)
model = "additive"  # or "multiplicative" if seasonal fluctuations scale with level

result = seasonal_decompose(y, model=model, period=period, extrapolate_trend="freq")

fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
axes[0].plot(y.index, y.values)
axes[0].set_title(f"Observed")

axes[1].plot(result.trend.index, result.trend.values)
axes[1].set_title("Trend")

axes[2].plot(result.seasonal.index, result.seasonal.values)
axes[2].set_title("Seasonal")

axes[3].plot(result.resid.index, result.resid.values)
axes[3].axhline(0, color="black", linewidth=0.8)
axes[3].set_title("Residual")

plt.suptitle(f"Time Series Decomposition ({model.capitalize()}, period={period})", y=0.95)
plt.tight_layout()
plt.show()

use_stl = True
if use_stl:
    stl = STL(y, period=period, robust=True)
    stl_res = stl.fit()

    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(y.index, y.values)
    axes[0].set_title("Observed (STL)")

    axes[1].plot(stl_res.trend.index, stl_res.trend.values)
    axes[1].set_title("Trend (STL)")

    axes[2].plot(stl_res.seasonal.index, stl_res.seasonal.values)
    axes[2].set_title("Seasonal (STL)")

    axes[3].plot(stl_res.resid.index, stl_res.resid.values)
    axes[3].axhline(0, color="black", linewidth=0.8)
    axes[3].set_title("Residual (STL)")

    plt.suptitle(f"STL Decomposition (period={period}, robust=True)", y=0.95)
    plt.tight_layout()
    plt.show()
          
    next cell
    import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf

df = pd.read_csv("time_series_data.csv", parse_dates=["date"])
df = df.sort_values("date").set_index("date")
y = df["value"]

window_sizes = [7, 30]  # weekly and monthly smoothing

plt.figure(figsize=(12,6))
plt.plot(y, label="Original", alpha=0.7)

for w in window_sizes:
    y.rolling(window=w).mean().plot(label=f"Rolling Mean ({w} days)")

plt.title("Moving Averages of Time Series")
plt.legend()
plt.show()

plt.figure(figsize=(12,6))
plt.plot(y.rolling(window=30).std(), label="Rolling Std (30 days)", color="orange")
plt.title("Rolling Standard Deviation (30-day)")
plt.legend()
plt.show()

plt.figure(figsize=(10,5))
plot_acf(y, lags=50)
plt.title("Autocorrelation Function (ACF)")
plt.show()
          
next cell
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from statsmodels.tsa.seasonal import STL
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.stattools import acf
from scipy.signal import periodogram

df = pd.read_csv("time_series_data.csv", parse_dates=["date"])
df = df.sort_values("date").set_index("date")
y = df["value"].asfreq("D").interpolate()  # daily freq + fill small gaps

max_lag = 60
acf_vals = acf(y, nlags=max_lag, fft=True)
lags = np.arange(len(acf_vals))
candidate_lags = lags[2:]  # ignore lag 0/1
best_lag = candidate_lags[np.argmax(acf_vals[2:])]

print(f"Top ACF peak lag (2..{max_lag}): {best_lag} days  |  ACF={acf_vals[best_lag]:.3f}")

period = int(best_lag) if best_lag > 1 else 7  # fallback
stl = STL(y, period=period, robust=True)
stl_res = stl.fit()
trend, seasonal, resid = stl_res.trend, stl_res.seasonal, stl_res.resid

seasonal_strength = 1 - (np.var(resid.dropna()) / np.var((seasonal + resid).dropna()))
print(f"Seasonal strength (STL): {seasonal_strength:.3f}  (closer to 1 = strong seasonality)")

plt.figure(figsize=(9,4))
plot_acf(y, lags=60)
plt.title("ACF (first 60 lags)")
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
axes[0].plot(y);                 axes[0].set_title("Observed")
axes[1].plot(trend);             axes[1].set_title("Trend")
axes[2].plot(seasonal);          axes[2].set_title(f"Seasonal (period ≈ {period} days)")
axes[3].plot(resid); axes[3].axhline(0, color="black", lw=0.8); axes[3].set_title("Residual")
plt.suptitle("STL Decomposition", y=0.95)
plt.tight_layout()
plt.show()

weekday = y.copy()
weekday.index = weekday.index.dayofweek  # 0=Mon .. 6=Sun
labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

fig, ax = plt.subplots(1, 1, figsize=(9,4))
ax.boxplot([weekday[weekday.index == i] for i in range(7)], labels=labels, showfliers=False)
ax.set_title("Seasonal Subseries (by Weekday)")
ax.set_ylabel("value")
plt.tight_layout()
plt.show()

detrended = y - trend
detrended = detrended.dropna()

freqs, power = periodogram(detrended.values)  # assumes unit sampling interval (1 day)
mask = freqs > 0
freqs, power = freqs[mask], power[mask]

dom_idx = np.argmax(power)
dom_freq = freqs[dom_idx]
dom_period = 1.0 / dom_freq if dom_freq > 0 else np.nan

print(f"Dominant frequency (periodogram): {dom_freq:.4f} cycles/day → period ≈ {dom_period:.2f} days")

plt.figure(figsize=(9,4))
plt.plot(freqs, power)
plt.title("Periodogram (detrended series)")
plt.xlabel("Frequency (cycles/day)")
plt.ylabel("Power")
plt.tight_layout()
plt.show()

print("\nINTERPRETATION:")
print(f"- ACF peaks and STL suggest a repeating cycle around ~{period} days.")
print("- Seasonal subseries boxplot shows systematic differences by weekday (if daily series).")
print("- Periodogram peak corroborates the dominant cycle (1/f).")
print("- Seasonal strength close to 1 indicates strong, stable seasonality; near 0 means weak.")
               
''')    
    
pro3()