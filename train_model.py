import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score
import pickle

# Load cleaned dataset
df = pd.read_csv("clean_resume_data.csv")

X = df["resume_text"]
y = df["label"]

# Convert text into TF-IDF vectors
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=20000,
    ngram_range=(1,2),
    min_df=2
)
X_vec = vectorizer.fit_transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42
)

# Train model
from sklearn.svm import LinearSVC

model = LinearSVC(class_weight="balanced")
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nDetailed Report:\n")
print(classification_report(y_test, y_pred))

# Save model
pickle.dump(model, open("resume_model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("Model saved successfully.")