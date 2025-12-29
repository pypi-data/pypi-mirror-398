# Voting Extension Data

This directory contains initial data for the voting extension.

## voting_data.json

Contains governance proposals with realistic data pointing to actual codex files on GitHub:

1. **Implement Automated Tax Collection** (`tax_collection_codex.py`)
2. **Enable Social Benefits Distribution** (`social_benefits_codex.py`)

### Timestamp Placeholders

The file uses placeholders that are **automatically replaced** during `realms realm create`:

- `__REALM_CREATION_TIME__`: Replaced with realm creation timestamp
- `__VOTING_DEADLINE_24H__`: Replaced with timestamp 24 hours from creation

### Data Structure

Each record includes:

- **_type**: Entity type (e.g., "Proposal")
- **_id**: Unique identifier for the entity
- **Standard fields**: timestamp_created, timestamp_updated, creator, updater, owner
- **Entity-specific fields**: 
  - proposal_id: Human-readable proposal ID (e.g., "prop_001")
  - title: Proposal title
  - description: Detailed description
  - code_url: URL to the proposal code (actual GitHub raw URLs)
  - code_checksum: SHA256 checksum of the code
  - proposer: Reference to User entity ID
  - status: Current status (voting, pending_vote, accepted, executed, rejected)
  - voting_deadline: ISO format timestamp
  - votes_yes, votes_no, votes_abstain: Vote counts
  - total_voters: Total number of voters
  - required_threshold: Threshold for approval (0.0-1.0)
  - metadata: JSON with codex_name for execution

## Loading Data

The data is automatically loaded when deploying a realm:

```bash
# Create a new realm (placeholders are automatically replaced)
realms realm create --realm-name my-realm

# Deploy the realm - voting data is uploaded automatically
cd .realms/realm/realm_my-realm_*/
bash scripts/2-deploy-canisters.sh
bash scripts/3-upload-data.sh
```

The `upload_data.sh` script automatically discovers and imports extension data files from `extensions/*/data/*.json`.

## Demo Features

The voting extension includes demo features for quick demonstrations:

1. **Real Code Display**: Proposals fetch and display actual Python code from GitHub
2. **Demo Approve**: Instantly approve a proposal without waiting for voting to complete
3. **Demo Execute**: Execute the approved proposal, creating the codex in the realm

These features are accessible from the proposal detail page when viewing a proposal with "Voting Active" status.

## Notes

- The `proposer` field references User entity ID "2" (first citizen user after system)
- Code URLs point to real codex files in the realms repository
- The `metadata` field contains `codex_name` which determines the codex name when executed
- Adjust user references based on your actual realm data
