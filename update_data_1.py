import json
import os

# New items 31-40
items_31_40 = [
  {
    "resume_id": "RES-2026-031",
    "category": "tech",
    "resume_text": "EXPERIENCE: Senior Smart Contract Engineer at EtherFlow. Developed and audited DeFi protocols managing $50M+ TVL. Expert in gas optimization and security patterns. SKILLS: Solidity, Hardhat, Ethers.js, Rust, Go.",
    "structured_claims": {
      "name": "Julian Thorne",
      "claimed_years_experience": 5,
      "skills": ["Solidity", "Hardhat", "DeFi"],
      "current_title": "Senior Smart Contract Engineer"
    },
    "digital_footprint": {
      "github_username": "j-thorne-web3",
      "repo_count": 41,
      "account_created_year": 2021,
      "last_commit_days_ago": 2,
      "top_language": "Solidity"
    },
    "email": {
      "address": "j.thorne@etherflow.io",
      "domain": "etherflow.io",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Clean profile. Strong alignment between claimed Web3 expertise and Solidity-dominant GitHub activity."
    }
  },
  {
    "resume_id": "RES-2026-032",
    "category": "tech",
    "resume_text": "SUMMARY: AI Engineer with a focus on Computer Vision and Edge AI. 4 years experience deploying YOLO models for industrial quality control. SKILLS: Python, C++, OpenCV, TensorFlow, PyTorch.",
    "structured_claims": {
      "name": "Li Wei",
      "claimed_years_experience": 4,
      "skills": ["Computer Vision", "OpenCV", "PyTorch"],
      "current_title": "AI Engineer"
    },
    "digital_footprint": {
      "github_username": "li-wei-cv",
      "repo_count": 18,
      "account_created_year": 2022,
      "last_commit_days_ago": 7,
      "top_language": "Python"
    },
    "email": {
      "address": "li.wei@tsinghua.org.cn",
      "domain": "tsinghua.org.cn",
      "domain_type": "university"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Verified academic and professional alignment."
    }
  },
  {
    "resume_id": "RES-2026-033",
    "category": "design",
    "resume_text": "EXPERIENCE: Lead Product Designer at NeoBank. Pioneered the mobile-first design system now used by 2M+ users. SKILLS: Figma, Design Systems, Prototyping, User Research.",
    "structured_claims": {
      "name": "Sarah Connor",
      "claimed_years_experience": 8,
      "skills": ["Design Systems", "Figma", "User Research"],
      "current_title": "Lead Product Designer"
    },
    "digital_footprint": {
      "github_username": "sconnor-design",
      "repo_count": 12,
      "account_created_year": 2018,
      "last_commit_days_ago": 45,
      "top_language": "CSS"
    },
    "email": {
      "address": "sarah.connor@neobank.com",
      "domain": "neobank.com",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Consistent design profile. Corporate domain and 2018 account age support seniority."
    }
  },
  {
    "resume_id": "RES-2026-034",
    "category": "business",
    "resume_text": "SUMMARY: FinTech Analyst specializing in fraud detection systems and risk modeling. 5 years experience at a Tier-1 bank. SKILLS: SQL, Python, SAS, Risk Management.",
    "structured_claims": {
      "name": "Arjun Rao",
      "claimed_years_experience": 5,
      "skills": ["Risk Modeling", "SQL", "Python"],
      "current_title": "FinTech Analyst"
    },
    "digital_footprint": {
      "github_username": "arao-risk-dev",
      "repo_count": 9,
      "account_created_year": 2020,
      "last_commit_days_ago": 14,
      "top_language": "Python"
    },
    "email": {
      "address": "a.rao@standardchartered.com",
      "domain": "standardchartered.com",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Legitimate profile with high-trust corporate domain."
    }
  },
  {
    "resume_id": "RES-2026-035",
    "category": "healthcare",
    "resume_text": "EXPERIENCE: Health Data Scientist. Developed predictive models for patient readmission rates using hospital EHR data. SKILLS: R, SQL, Tableau, Healthcare Analytics.",
    "structured_claims": {
      "name": "Elena Belova",
      "claimed_years_experience": 3,
      "skills": ["Healthcare Analytics", "R", "SQL"],
      "current_title": "Health Data Scientist"
    },
    "digital_footprint": {
      "github_username": "ebelova-health",
      "repo_count": 14,
      "account_created_year": 2023,
      "last_commit_days_ago": 8,
      "top_language": "R"
    },
    "email": {
      "address": "ebelova@med-analytics.ru",
      "domain": "med-analytics.ru",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 0,
      "fraud_type": "none",
      "reason": "Consistent data points for a mid-level healthcare analyst."
    }
  },
  {
    "resume_id": "RES-2026-036",
    "category": "tech",
    "resume_text": "SUMMARY: Senior Blockchain Architect with 6 years experience in Rust-based chains (Solana, Polkadot). Expert in runtime logic and P2P networking. SKILLS: Rust, Solidity, C++, WASM.",
    "structured_claims": {
      "name": "Kevin Flynn",
      "claimed_years_experience": 6,
      "skills": ["Rust", "WASM", "Blockchain Architecture"],
      "current_title": "Senior Blockchain Architect"
    },
    "digital_footprint": {
      "github_username": "kflynn-dev",
      "repo_count": 3,
      "account_created_year": 2025,
      "last_commit_days_ago": 90,
      "top_language": "JavaScript"
    },
    "email": {
      "address": "kevin.flynn.crypto@gmail.com",
      "domain": "gmail.com",
      "domain_type": "public"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "skill_inflation",
      "reason": "Skill-Language Mismatch: Claims seniority in Rust/Blockchain architecture, but GitHub is 1 year old and consists of basic JavaScript projects."
    }
  },
  {
    "resume_id": "RES-2026-037",
    "category": "tech",
    "resume_text": "EXPERIENCE: LLM Research Engineer. 10 years experience in NLP and Large Language Models. Lead developer on 'Global-GPT' initiative. SKILLS: Transformers, Python, PyTorch, Cuda.",
    "structured_claims": {
      "name": "Mina Harker",
      "claimed_years_experience": 10,
      "skills": ["Transformers", "PyTorch", "NLP"],
      "current_title": "LLM Research Engineer"
    },
    "digital_footprint": {
      "github_username": "mina-h-nlp",
      "repo_count": 2,
      "account_created_year": 2026,
      "last_commit_days_ago": 1,
      "top_language": "Python"
    },
    "email": {
      "address": "mina.harker@temp-inbox.com",
      "domain": "temp-inbox.com",
      "domain_type": "disposable"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "timeline_conflict",
      "reason": "Timeline and Email Red Flags: Claims 10 years in a highly specialized field (LLMs), but uses a 2026-created GitHub account and a disposable email domain."
    }
  },
  {
    "resume_id": "RES-2026-038",
    "category": "tech",
    "resume_text": "SUMMARY: Cloud Operations Lead. 12 years experience managing Kubernetes clusters at scale for global logistics firms. SKILLS: Kubernetes, Docker, Terraform, Go, Bash.",
    "structured_claims": {
      "name": "Victor Stone",
      "claimed_years_experience": 12,
      "skills": ["Kubernetes", "Terraform", "Go"],
      "current_title": "Cloud Operations Lead"
    },
    "digital_footprint": {
      "github_username": "vstone-ops",
      "repo_count": 5,
      "account_created_year": 2024,
      "last_commit_days_ago": 200,
      "top_language": "HTML"
    },
    "email": {
      "address": "v.stone@logistics-pro.com",
      "domain": "logistics-pro.com",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "skill_inflation",
      "reason": "Inflation detected: Claims 12 years of high-level Ops (K8s/Go), but GitHub shows only basic HTML and has been stagnant for nearly a year."
    }
  },
  {
    "resume_id": "RES-2026-039",
    "category": "tech",
    "resume_text": "EXPERIENCE: Full Stack Developer specializing in React and Node.js. 4 years of experience building scalable SaaS platforms. SKILLS: React, Node.js, MongoDB, AWS.",
    "structured_claims": {
      "name": "Sofia Ramirez",
      "claimed_years_experience": 4,
      "skills": ["React", "Node.js", "MongoDB"],
      "current_title": "Full Stack Developer"
    },
    "digital_footprint": {
      "github_username": "X-Terminator-9000",
      "repo_count": 65,
      "account_created_year": 2021,
      "last_commit_days_ago": 3,
      "top_language": "JavaScript"
    },
    "email": {
      "address": "sofia.ramirez88@outlook.com",
      "domain": "outlook.com",
      "domain_type": "public"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "identity_mismatch",
      "reason": "Identity desynchronization: Resume name 'Sofia Ramirez' has zero correlation with the highly active but anonymous/aliased GitHub handle 'X-Terminator-9000'."
    }
  },
  {
    "resume_id": "RES-2026-040",
    "category": "tech",
    "resume_text": "SUMMARY: Lead DevSecOps Engineer. 15 years experience in secure infrastructure and automated compliance. SKILLS: AWS, Jenkins, Python, Terraform, Vault.",
    "structured_claims": {
      "name": "Thomas Anderson",
      "claimed_years_experience": 15,
      "skills": ["DevSecOps", "Terraform", "Vault"],
      "current_title": "Lead DevSecOps Engineer"
    },
    "digital_footprint": {
      "github_username": "t-anderson-sec",
      "repo_count": 1,
      "account_created_year": 2026,
      "last_commit_days_ago": 1,
      "top_language": "Python"
    },
    "email": {
      "address": "t.anderson@corporate-secure.net",
      "domain": "corporate-secure.net",
      "domain_type": "corporate"
    },
    "ground_truth": {
      "fraud_label": 1,
      "fraud_type": "timeline_conflict",
      "reason": "Extreme timeline conflict: A 15-year veteran in DevSecOps would not have a GitHub account created in the current year with only a single repository."
    }
  }
]

file_path = r'c:\Users\raipr\OneDrive\Desktop\resume\training_data.json'

with open(file_path, 'r') as f:
    data = json.load(f)

data.extend(items_31_40)

with open(file_path, 'w') as f:
    json.dump(data, f, indent=4)
