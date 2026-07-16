# Data Governance & Compliance

## Overview
This project adheres to the University of Texas at Austin data governance standards, specifically focusing on FERPA compliance for student records.

## FERPA Masking Implementation
- **Pseudonymization:** Student IDs are transformed using SHA-256 hashing with a unique salt to prevent re-identification.
- **PII Redaction:** Names, SSNs, and exact birthdates are excluded from the analytics and compliance datasets.
- **Aggregate Views:** Public-facing or secondary views (in the `compliance` dataset) only expose high-level trends (e.g., GPA by Major) rather than individual records.

## Access Control
- **Staging Layer:** Restricted to Data Engineering staff.
- **Analytics Layer:** Restricted to authorized Institutional Researchers.
- **Compliance Layer:** Accessible by Department Heads and CNS Leadership for strategic planning.