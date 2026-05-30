import pandas as pd
import pickle

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

import matplotlib.pyplot as plt
import seaborn as sns

# LOAD CSV
df = pd.read_csv(r"C:\Users\user\OneDrive\Desktop\Relaxo Monitor\data.csv")

# KEEP REQUIRED COLUMNS
df = df[['BPM', 'Temp', 'Stress']]

# REMOVE EMPTY VALUES
df = df.dropna()

# CONVERT STRESS LABELS TO NUMBERS
stress_map = {
    'LOW': 0,
    'MEDIUM': 1,
    'HIGH': 2
}

df['Stress'] = df['Stress'].map(stress_map)

# REMOVE INVALID VALUES
df = df.dropna()

# FEATURES
X = df[['BPM', 'Temp']]

# TARGET
y = df['Stress']

# TRAIN TEST SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# MODEL
model = LogisticRegression()

# TRAIN MODEL
model.fit(X_train, y_train)

# PREDICTION
y_pred = model.predict(X_test)

# ACCURACY
accuracy = accuracy_score(y_test, y_pred)

print("\n✅ Accuracy:")
print(accuracy * 100)

# CLASSIFICATION REPORT
print("\n✅ Classification Report:")
print(classification_report(y_test, y_pred))

# CONFUSION MATRIX
cm = confusion_matrix(y_test, y_pred)

print("\n✅ Confusion Matrix:")
print(cm)

# CONFUSION MATRIX GRAPH
labels = ['LOW', 'MEDIUM', 'HIGH']

plt.figure(figsize=(7,5))

sns.heatmap(
    cm,
    annot=True,
    fmt='d',
    cmap='viridis',
    xticklabels=labels,
    yticklabels=labels
)

plt.title("Confusion Matrix - Output")
plt.xlabel("Predicted")
plt.ylabel("Actual")

plt.show()

# SAVE MODEL
pickle.dump(model, open('model.pkl', 'wb'))

print("\n✅ Model trained and saved successfully!")

