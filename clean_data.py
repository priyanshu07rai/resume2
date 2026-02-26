import pandas as pd
from bs4 import BeautifulSoup

# Load CSV
df = pd.read_csv("training_data.csv")  # change filename if needed

# Clean HTML
def clean_html(text):
    if pd.isna(text):
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")

df["clean_resume"] = df["Resume_html"].apply(clean_html)  # column C = resume text

# Keep only needed columns
df_clean = df[["clean_resume", "Category"]]  # B = label column
df_clean.columns = ["resume_text", "label"]

df_clean.to_csv("clean_resume_data.csv", index=False)

print("Cleaning done. Saved as clean_resume_data.csv")