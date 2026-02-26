import json
from ml_engine import predict_fraud_probability

# Test data similar to what app.py constructs
test_data_clean = {
    "structured_claims": {
        "claimed_years_experience": 5,
        "skills": ["Python", "React"]
    },
    "digital_footprint": {
        "account_created_year": 2019,
        "repo_count": 25,
        "last_commit_days_ago": 5,
        "top_language": "Python"
    },
    "email": {
        "domain_type": "corporate"
    }
}

test_data_fraud = {
    "structured_claims": {
        "claimed_years_experience": 12,
        "skills": ["Solidity", "Rust"]
    },
    "digital_footprint": {
        "account_created_year": 2024,
        "repo_count": 2,
        "last_commit_days_ago": 150,
        "top_language": "HTML"
    },
    "email": {
        "domain_type": "disposable"
    }
}

print(f"Clean Data Prob: {predict_fraud_probability(test_data_clean)}%")
print(f"Fraud Data Prob: {predict_fraud_probability(test_data_fraud)}%")
