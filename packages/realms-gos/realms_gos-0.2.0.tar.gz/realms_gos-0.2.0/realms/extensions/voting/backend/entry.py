"""
Voting Extension Backend Entry Point
Governance voting system using GGG entities
"""

import hashlib
import json
import traceback
from datetime import datetime
from typing import Any, Dict, List

from ggg import Proposal, User, Vote, Codex
from kybra import Async
from kybra_simple_logging import get_logger
from core.http_utils import download_file_from_url

logger = get_logger("extensions.voting")


def _proposal_to_dict(proposal: Proposal) -> Dict[str, Any]:
    """Convert Proposal entity to dictionary"""
    # Get timestamps from TimestampedMixin's serialize method
    timestamps = proposal.serialize() if hasattr(proposal, 'serialize') else {}
    return {
        "id": proposal.proposal_id,
        "title": proposal.title,
        "description": proposal.description,
        "code_url": proposal.code_url,
        "code_checksum": proposal.code_checksum,
        "proposer": proposal.proposer.id if proposal.proposer else "unknown",
        "status": proposal.status,
        "created_at": timestamps.get("timestamp_created", ""),
        "voting_deadline": (
            proposal.voting_deadline if proposal.voting_deadline else None
        ),
        "votes": {
            "yes": int(proposal.votes_yes),
            "no": int(proposal.votes_no),
            "abstain": int(proposal.votes_abstain),
        },
        "total_voters": int(proposal.total_voters),
        "required_threshold": proposal.required_threshold,
    }


def get_proposals(args: str) -> Dict[str, Any]:
    """Get all proposals with optional filtering"""
    logger.info(f"get_proposals called with args: {args}")

    try:
        # Parse JSON string to dictionary
        if isinstance(args, str):
            args_dict = json.loads(args) if args.strip() else {}
        else:
            args_dict = args

        status_filter = args_dict.get("status", None)

        # Load proposals from database
        all_proposals = Proposal.instances()

        # Filter by status if requested
        if status_filter:
            filtered_proposals = [p for p in all_proposals if p.status == status_filter]
        else:
            filtered_proposals = all_proposals

        # Convert to dictionaries
        proposals = [_proposal_to_dict(p) for p in filtered_proposals]

        return json.dumps(
            {"success": True, "data": {"proposals": proposals, "total": len(proposals)}}
        )
    except Exception as e:
        logger.error(f"Error in get_proposals: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def get_proposal(args: str) -> Dict[str, Any]:
    """Get a specific proposal by ID"""
    logger.info(f"get_proposal called with args: {args}")

    try:
        # Parse JSON string to dictionary
        if isinstance(args, str):
            args_dict = json.loads(args) if args.strip() else {}
        else:
            args_dict = args

        proposal_id = args_dict.get("proposal_id")
        if not proposal_id:
            return json.dumps({"success": False, "error": "proposal_id is required"})

        # Find proposal in database
        all_proposals = Proposal.instances()
        proposal = next(
            (p for p in all_proposals if p.proposal_id == proposal_id), None
        )

        if not proposal:
            return json.dumps({"success": False, "error": "Proposal not found"})

        return json.dumps({"success": True, "data": _proposal_to_dict(proposal)})
    except Exception as e:
        logger.error(f"Error in get_proposal: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def submit_proposal(args: str) -> Dict[str, Any]:
    """Submit a new proposal"""
    logger.info(f"submit_proposal called with args: {args}")

    try:
        # Parse JSON string to dictionary
        if isinstance(args, str):
            args_dict = json.loads(args) if args.strip() else {}
        else:
            args_dict = args

        required_fields = ["title", "description", "code_url", "proposer"]
        for field in required_fields:
            if field not in args_dict:
                return json.dumps({"success": False, "error": f"{field} is required"})

        # Find proposer user
        proposer_id = args_dict["proposer"]
        all_users = User.instances()
        proposer = next((u for u in all_users if u.id == proposer_id), None)

        if not proposer:
            return json.dumps(
                {"success": False, "error": f"User {proposer_id} not found"}
            )

        # Use provided checksum or leave empty for later verification
        code_checksum = args_dict.get("code_checksum", "")

        # Generate unique proposal ID
        existing_proposals = Proposal.instances()
        proposal_num = len(existing_proposals) + 1
        proposal_id = f"prop_{proposal_num:03d}"

        # Create new proposal in database
        new_proposal = Proposal(
            proposal_id=proposal_id,
            title=args_dict["title"],
            description=args_dict["description"],
            code_url=args_dict["code_url"],
            code_checksum=code_checksum,
            proposer=proposer,
            status="pending_review",
            voting_deadline="",
            votes_yes=0.0,
            votes_no=0.0,
            votes_abstain=0.0,
            total_voters=0.0,
            required_threshold=0.6,
            metadata="{}",
        )

        return json.dumps({"success": True, "data": _proposal_to_dict(new_proposal)})
    except Exception as e:
        logger.error(f"Error in submit_proposal: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def cast_vote(args: str) -> Dict[str, Any]:
    """Cast a vote on a proposal"""
    logger.info(f"cast_vote called with args: {args}")

    try:
        # Parse JSON string to dictionary
        if isinstance(args, str):
            args_dict = json.loads(args) if args.strip() else {}
        else:
            args_dict = args

        proposal_id = args_dict.get("proposal_id")
        vote_choice = args_dict.get("vote")  # 'yes', 'no', 'abstain'
        voter_id = args_dict.get("voter")

        if not all([proposal_id, vote_choice, voter_id]):
            return json.dumps(
                {"success": False, "error": "proposal_id, vote, and voter are required"}
            )

        if vote_choice not in ["yes", "no", "abstain"]:
            return json.dumps(
                {"success": False, "error": "vote must be 'yes', 'no', or 'abstain'"}
            )

        # Find proposal
        all_proposals = Proposal.instances()
        proposal = next(
            (p for p in all_proposals if p.proposal_id == proposal_id), None
        )

        if not proposal:
            return json.dumps({"success": False, "error": "Proposal not found"})

        # Find voter
        all_users = User.instances()
        voter = next((u for u in all_users if u.id == voter_id), None)

        if not voter:
            return json.dumps({"success": False, "error": f"User {voter_id} not found"})

        # Check if user already voted
        all_votes = Vote.instances()
        existing_vote = next(
            (
                v
                for v in all_votes
                if v.proposal.id == proposal.id and v.voter.id == voter.id
            ),
            None,
        )

        if existing_vote:
            # Update existing vote counts
            if existing_vote.vote_choice == "yes":
                proposal.votes_yes -= 1
            elif existing_vote.vote_choice == "no":
                proposal.votes_no -= 1
            elif existing_vote.vote_choice == "abstain":
                proposal.votes_abstain -= 1

            # Update vote choice
            existing_vote.vote_choice = vote_choice
        else:
            # Create new vote
            new_vote = Vote(
                proposal=proposal, voter=voter, vote_choice=vote_choice, metadata="{}"
            )
            proposal.total_voters += 1

        # Update proposal vote counts
        if vote_choice == "yes":
            proposal.votes_yes += 1
        elif vote_choice == "no":
            proposal.votes_no += 1
        elif vote_choice == "abstain":
            proposal.votes_abstain += 1

        return json.dumps(
            {"success": True, "data": {"message": "Vote cast successfully"}}
        )
    except Exception as e:
        logger.error(f"Error in cast_vote: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def fetch_proposal_code(args: str) -> Async[str]:
    """Fetch the code from a proposal's code_url using download_file_from_url"""
    logger.info(f"fetch_proposal_code called with args: {args}")

    try:
        if isinstance(args, str):
            args_dict = json.loads(args) if args.strip() else {}
        else:
            args_dict = args

        proposal_id = args_dict.get("proposal_id")
        if not proposal_id:
            return json.dumps({"success": False, "error": "proposal_id is required"})

        # Find proposal
        all_proposals = Proposal.instances()
        proposal = next(
            (p for p in all_proposals if p.proposal_id == proposal_id), None
        )

        if not proposal:
            return json.dumps({"success": False, "error": "Proposal not found"})

        code_url = proposal.code_url
        if not code_url:
            return json.dumps({"success": False, "error": "Proposal has no code URL"})

        # Fetch code from URL using main.py's download function
        logger.info(f"Fetching code from: {code_url}")
        success, result = yield download_file_from_url(code_url)
        
        if success:
            code_content = result
            checksum = f"sha256:{hashlib.sha256(code_content.encode()).hexdigest()}"
            return json.dumps({
                "success": True,
                "data": {
                    "code": code_content,
                    "code_url": code_url,
                    "checksum": checksum
                }
            })
        else:
            return json.dumps({"success": False, "error": f"Failed to fetch code: {result}"})

    except Exception as e:
        logger.error(f"Error in fetch_proposal_code: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def approve_proposal(args: str) -> str:
    """Demo feature: Approve a proposal and mark it as accepted"""
    logger.info(f"approve_proposal called with args: {args}")

    try:
        if isinstance(args, str):
            args_dict = json.loads(args) if args.strip() else {}
        else:
            args_dict = args

        proposal_id = args_dict.get("proposal_id")
        if not proposal_id:
            return json.dumps({"success": False, "error": "proposal_id is required"})

        # Find proposal
        all_proposals = Proposal.instances()
        proposal = next(
            (p for p in all_proposals if p.proposal_id == proposal_id), None
        )

        if not proposal:
            return json.dumps({"success": False, "error": "Proposal not found"})

        if proposal.status == "accepted":
            return json.dumps({"success": False, "error": "Proposal already accepted"})

        if proposal.status == "executed":
            return json.dumps({"success": False, "error": "Proposal already executed"})

        # Update proposal status to accepted
        proposal.status = "accepted"
        
        logger.info(f"Proposal {proposal_id} approved successfully")

        return json.dumps({
            "success": True,
            "data": {
                "message": "Proposal approved successfully",
                "proposal": _proposal_to_dict(proposal)
            }
        })

    except Exception as e:
        logger.error(f"Error in approve_proposal: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def execute_proposal(args: str) -> Async[str]:
    """Execute an approved proposal by creating/updating the codex"""
    logger.info(f"execute_proposal called with args: {args}")

    try:
        if isinstance(args, str):
            args_dict = json.loads(args) if args.strip() else {}
        else:
            args_dict = args

        proposal_id = args_dict.get("proposal_id")
        if not proposal_id:
            return json.dumps({"success": False, "error": "proposal_id is required"})

        # Find proposal
        all_proposals = Proposal.instances()
        proposal = next(
            (p for p in all_proposals if p.proposal_id == proposal_id), None
        )

        if not proposal:
            return json.dumps({"success": False, "error": "Proposal not found"})

        if proposal.status != "accepted":
            return json.dumps({
                "success": False, 
                "error": f"Proposal must be accepted before execution. Current status: {proposal.status}"
            })

        # Get codex name from metadata
        try:
            metadata = json.loads(proposal.metadata) if proposal.metadata else {}
        except:
            metadata = {}
        
        codex_name = metadata.get("codex_name", f"proposal_{proposal_id}_codex")

        # Fetch the code using main.py's download function
        code_url = proposal.code_url
        if not code_url:
            return json.dumps({"success": False, "error": "Proposal has no code URL"})

        logger.info(f"Fetching code from: {code_url}")
        success, result = yield download_file_from_url(code_url)
        
        if not success:
            return json.dumps({"success": False, "error": f"Failed to fetch code: {result}"})
        
        code_content = result
        
        # Check if codex with this name already exists
        existing_codexes = Codex.instances()
        existing_codex = next(
            (c for c in existing_codexes if c.name == codex_name), None
        )

        if existing_codex:
            # Update existing codex
            existing_codex.code = code_content
            existing_codex.description = f"Updated by proposal {proposal_id}: {proposal.title}"
            action = "updated"
        else:
            # Create new codex
            Codex(
                name=codex_name,
                description=f"Created by proposal {proposal_id}: {proposal.title}",
                code=code_content
            )
            action = "created"

        # Update proposal status to executed
        proposal.status = "executed"
        
        logger.info(f"Proposal {proposal_id} executed: codex '{codex_name}' {action}")

        return json.dumps({
            "success": True,
            "data": {
                "message": f"Proposal executed successfully. Codex '{codex_name}' {action}.",
                "codex_name": codex_name,
                "action": action,
                "proposal": _proposal_to_dict(proposal)
            }
        })

    except Exception as e:
        logger.error(f"Error in execute_proposal: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def get_user_vote(args: str) -> str:
    """Get the current user's vote on a proposal"""
    logger.info(f"get_user_vote called with args: {args}")

    try:
        if isinstance(args, str):
            args_dict = json.loads(args) if args.strip() else {}
        else:
            args_dict = args

        proposal_id = args_dict.get("proposal_id")
        voter_id = args_dict.get("voter")

        if not proposal_id or not voter_id:
            return json.dumps({"success": False, "error": "proposal_id and voter are required"})

        # Find proposal
        all_proposals = Proposal.instances()
        proposal = next(
            (p for p in all_proposals if p.proposal_id == proposal_id), None
        )

        if not proposal:
            return json.dumps({"success": False, "error": "Proposal not found"})

        # Find user's vote
        all_votes = Vote.instances()
        user_vote = next(
            (v for v in all_votes 
             if v.proposal.id == proposal.id and v.voter.id == voter_id),
            None
        )

        if user_vote:
            return json.dumps({
                "success": True,
                "data": {
                    "has_voted": True,
                    "vote_choice": user_vote.vote_choice
                }
            })
        else:
            return json.dumps({
                "success": True,
                "data": {
                    "has_voted": False,
                    "vote_choice": None
                }
            })

    except Exception as e:
        logger.error(f"Error in get_user_vote: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


# Extension API endpoints
EXTENSION_FUNCTIONS = {
    "get_proposals": get_proposals,
    "get_proposal": get_proposal,
    "submit_proposal": submit_proposal,
    "cast_vote": cast_vote,
    "fetch_proposal_code": fetch_proposal_code,
    "approve_proposal": approve_proposal,
    "execute_proposal": execute_proposal,
    "get_user_vote": get_user_vote,
}
