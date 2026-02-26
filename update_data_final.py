import json
import os

items_41_50 = [
  {
    "resume_id": "RES-2026-041",
    "category": "tech",
    "resume_text": "EXPERIENCE: Senior Data Scientist at RetailPulse (2020-Present). Implemented demand forecasting models using Prophet and XGBoost, increasing inventory turnover by 22%. SKILLS: Python, SQL, Spark, XGBoost, AWS SageMaker.",
    "structured_claims": {
      "name": "David Thorne",
      "claimed_years_experience": 6,
      "skills": ["Python", "XGBoost", "SageMaker"],
      "current_title": "Senior Data Scientist"
    },
    "digital_footprint": {
      "github_username": "dthorne-data",
      "repo_count": 25,
      "account_created_year": 2019,
      "last_commit_days_ago": 4,
      "top_language": "Python"
    },
    "email": {
      "address": "d.thorne@retailpulse.ai",
      "domain": "retailpulse.ai",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Clean profile. Consistent timeline and skill-language alignment."
    }
  },
  {
    "resume_id": "RES-2026-042",
    "category": "healthcare",
    "resume_text": "SUMMARY: Medical AI Researcher specialized in Pathology Image Analysis. 5 years experience at NIH. SKILLS: PyTorch, MONAI, DICOM, Python, C++.",
    "structured_claims": {
      "name": "Dr. Aris Varma",
      "claimed_years_experience": 5,
      "skills": ["MONAI", "PyTorch", "Medical Imaging"],
      "current_title": "Medical AI Researcher"
    },
    "digital_footprint": {
      "github_username": "avarma-nih-research",
      "repo_count": 14,
      "account_created_year": 2020,
      "last_commit_days_ago": 15,
      "top_language": "Python"
    },
    "email": {
      "address": "avarma@mail.nih.gov",
      "domain": "nih.gov",
      "domain_type": "university"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "High-trust profile validated by government domain and specialized repo content."
    }
  },
  {
    "resume_id": "RES-2026-043",
    "category": "tech",
    "resume_text": "EXPERIENCE: Flutter Developer at Nomad Apps (2022-2026). Published 5+ cross-platform apps on Play Store and App Store. SKILLS: Dart, Flutter, Firebase, Bloc.",
    "structured_claims": {
      "name": "Isabel Luna",
      "claimed_years_experience": 4,
      "skills": ["Flutter", "Dart", "Firebase"],
      "current_title": "Flutter Developer"
    },
    "digital_footprint": {
      "github_username": "luna-dart-dev",
      "repo_count": 22,
      "account_created_year": 2021,
      "last_commit_days_ago": 2,
      "top_language": "Dart"
    },
    "email": {
      "address": "isabel.luna@nomadapps.co",
      "domain": "nomadapps.co",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Clean profile. Strong alignment between Dart activity and Flutter developer claims."
    }
  },
  {
    "resume_id": "RES-2026-044",
    "category": "business",
    "resume_text": "SUMMARY: Quant Analyst with 8 years experience in algorithmic trading. Developed HFT strategies using C++ and Python. SKILLS: C++, Python, KDB+, Quantitative Research.",
    "structured_claims": {
      "name": "Samuel Zhang",
      "claimed_years_experience": 8,
      "skills": ["C++", "Algorithmic Trading", "Python"],
      "current_title": "Senior Quant Analyst"
    },
    "digital_footprint": {
      "github_username": "szhang-quant",
      "repo_count": 31,
      "account_created_year": 2017,
      "last_commit_days_ago": 10,
      "top_language": "C++"
    },
    "email": {
      "address": "s.zhang@citadel.alumni.com",
      "domain": "citadel.alumni.com",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Verified professional profile with consistent long-term footprint."
    }
  },
  {
    "resume_id": "RES-2026-045",
    "category": "tech",
    "resume_text": "EXPERIENCE: Cloud Security Engineer. Managed IAM and VPC security for high-traffic SaaS. SKILLS: AWS, Terraform, Python, Go, Kubernetes Security.",
    "structured_claims": {
      "name": "Jordan P. Miller",
      "claimed_years_experience": 4,
      "skills": ["AWS Security", "Terraform", "IAM"],
      "current_title": "Cloud Security Engineer"
    },
    "digital_footprint": {
      "github_username": "jmiller-sec-ops",
      "repo_count": 18,
      "account_created_year": 2021,
      "last_commit_days_ago": 6,
      "top_language": "HCL"
    },
    "email": {
      "address": "jordan.miller@cloudguard.io",
      "domain": "cloudguard.io",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Clean profile. Language validation (HCL for Terraform) matches claims."
    }
  },
  {
    "resume_id": "RES-2026-046",
    "category": "tech",
    "resume_text": "SUMMARY: Principal ML Architect. 12 years lead experience in Large Scale Distributed Systems and Neural Architecture Search. SKILLS: Python, PyTorch, Distributed Systems, Rust.",
    "structured_claims": {
      "name": "Julian Thorne",
      "claimed_years_experience": 12,
      "skills": ["PyTorch", "Distributed Systems", "NAS"],
      "current_title": "Principal ML Architect"
    },
    "digital_footprint": {
      "github_username": "julian-ai-architect",
      "repo_count": 2,
      "account_created_year": 2025,
      "last_commit_days_ago": 80,
      "top_language": "HTML"
    },
    "email": {
      "address": "julian.thorne@ai-visionary.net",
      "domain": "ai-visionary.net",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "skill_inflation",
      "reason": "Extreme Skill Inflation: Claims 12 years of 'Principal' ML leadership but has a novice-level GitHub account with 2 HTML repos created in 2025."
    }
  },
  {
    "resume_id": "RES-2026-047",
    "category": "design",
    "resume_text": "SUMMARY: UX Director with 15 years experience. Built design teams for Fortune 50 companies. SKILLS: Design Strategy, Figma, CSS, Accessibility.",
    "structured_claims": {
      "name": "Maria Garcia",
      "claimed_years_experience": 15,
      "skills": ["Design Strategy", "Accessibility"],
      "current_title": "UX Director"
    },
    "digital_footprint": {
      "github_username": "garcia-design-lead",
      "repo_count": 0,
      "account_created_year": 2026,
      "last_commit_days_ago": 0,
      "top_language": ""
    },
    "email": {
      "address": "m.garcia@design-pro.biz",
      "domain": "design-pro.biz",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "timeline_conflict",
      "reason": "Timeline Red Flag: 15-year veteran has zero digital footprint until the current year (2026), suggesting a fabricated professional history."
    }
  },
  {
    "resume_id": "RES-2026-048",
    "category": "business",
    "resume_text": "EXPERIENCE: Product Lead at CryptoSphere (2021-Present). Spearheaded the launch of 3 dApps with 500k monthly users. SKILLS: Product Management, Web3, Solidity, Agile.",
    "structured_claims": {
      "name": "Alex Rivet",
      "claimed_years_experience": 6,
      "skills": ["Web3", "Solidity", "Product Management"],
      "current_title": "Product Lead"
    },
    "digital_footprint": {
      "github_username": "alex-product-web3",
      "repo_count": 4,
      "account_created_year": 2024,
      "last_commit_days_ago": 300,
      "top_language": "JavaScript"
    },
    "email": {
      "address": "a.rivet@temp-mail.org",
      "domain": "temp-mail.org",
      "domain_type": "disposable"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "disposable_email",
      "reason": "Fraud signal: Use of a disposable email for a senior-level position. Low activity on GitHub (last commit 300 days ago) also flags risk."
    }
  },
  {
    "resume_id": "RES-2026-049",
    "category": "tech",
    "resume_text": "SUMMARY: Senior Backend Engineer specializing in Java and Spring Boot. 10 years experience in banking systems. SKILLS: Java, Spring Boot, Microservices, Oracle.",
    "structured_claims": {
      "name": "Robert Downey",
      "claimed_years_experience": 10,
      "skills": ["Java", "Spring Boot", "Microservices"],
      "current_title": "Senior Backend Engineer"
    },
    "digital_footprint": {
      "github_username": "IronCoder_2026",
      "repo_count": 88,
      "account_created_year": 2022,
      "last_commit_days_ago": 1,
      "top_language": "Python"
    },
    "email": {
      "address": "robert.d@banking-pro.com",
      "domain": "banking-pro.com",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "identity_mismatch",
      "reason": "Identity & Skill Mismatch: Generic/Aliased username 'IronCoder_2026' has no link to 'Robert Downey'. Furthermore, the profile is Python-dominant while the resume claims Java expertise."
    }
  },
  {
    "resume_id": "RES-2026-050",
    "category": "tech",
    "resume_text": "SUMMARY: Rust Systems Developer with 7 years experience in high-performance computing. SKILLS: Rust, C++, Linux, Docker.",
    "structured_claims": {
      "name": "Li Na",
      "claimed_years_experience": 7,
      "skills": ["Rust", "Systems Programming"],
      "current_title": "Senior Rust Developer"
    },
    "digital_footprint": {
      "github_username": "lina-systems-dev",
      "repo_count": 2,
      "account_created_year": 2026,
      "last_commit_days_ago": 5,
      "top_language": "CSS"
    },
    "email": {
      "address": "lina.na@tech-core.cn",
      "domain": "tech-core.cn",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "skill_inflation",
      "reason": "High-risk inflation: 7 years of specialized Rust experience is claimed, but the GitHub footprint consists of basic CSS repos created this year."
    }
  }
]

file_path = r'c:\Users\raipr\OneDrive\Desktop\resume\training_data.json'

with open(file_path, 'r') as f:
    data = json.load(f)

data.extend(items_41_50)

with open(file_path, 'w') as f:
    json.dump(data, f, indent=4)
