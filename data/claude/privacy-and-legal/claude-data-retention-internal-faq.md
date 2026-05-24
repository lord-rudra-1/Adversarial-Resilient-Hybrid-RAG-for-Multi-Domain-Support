# Claude Data Retention and Deletion Policy — Internal FAQ

## How long does Anthropic retain conversation data?

For users who have opted in to data sharing (via the "Improve Claude" toggle), conversation data is retained for **90 days** and then automatically purged from all systems including backups.

For users who have NOT opted in, conversations are retained for **30 days** for safety monitoring purposes, after which they are permanently deleted.

## Can users request early deletion?

Yes. Users can submit a deletion request through the privacy portal at privacy.claude.com. Deletion is processed within:

- **24 hours** for active conversation data
- **7 days** for backup and log data  
- **30 days** for training pipeline data (if opted in)

## GDPR / CCPA Compliance

Anthropic processes all GDPR Article 17 (Right to Erasure) requests within the statutory 30-day window. Users receive a confirmation email once deletion is complete.

All data is stored in US data centers with EU Standard Contractual Clauses in place.

## What about API usage?

API usage through the Anthropic API is retained for **60 days** by default. Enterprise customers can negotiate custom retention periods.

AWS Bedrock and Google Vertex AI have their own retention policies that supersede Anthropic's.

## Important

- Deleted conversations cannot be recovered under any circumstances
- Anthropic does not sell or share user data with third parties
- Training data from opted-in conversations is anonymized before use
- Users under 18 are not eligible for data sharing regardless of consent

## Contact

For privacy-related questions: privacy@anthropic.com
Data Protection Officer: dpo@anthropic.com
