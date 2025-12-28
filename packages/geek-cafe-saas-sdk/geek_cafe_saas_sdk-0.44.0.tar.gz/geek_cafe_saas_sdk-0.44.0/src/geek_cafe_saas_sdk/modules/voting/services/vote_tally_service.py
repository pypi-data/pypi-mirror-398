# Vote Tally Service

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.request_context import RequestContext
from .vote_service import VoteService
from .vote_summary_service import VoteSummaryService
from geek_cafe_saas_sdk.modules.voting.models import Vote, VoteSummary
from aws_lambda_powertools import Logger
import os
import time

logger = Logger()


class VoteTallyService:
    """Service for tallying votes and updating vote summaries."""
    
    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None, request_context: RequestContext):
        """
        Initialize tally service with child services.
        
        NOTE: This service keeps custom __init__ because it creates child services.
        Simple services inherit DatabaseService.__init__ directly.
        """
        self.vote_service = VoteService(dynamodb=dynamodb, table_name=table_name, request_context=request_context)
        self.vote_summary_service = VoteSummaryService(dynamodb=dynamodb, table_name=table_name, request_context=request_context)
        self.page_size = 100  # Configurable page size for pagination
        
        # Pagination monitoring configuration from environment variables
        self.max_pagination_iterations = int(os.getenv('TALLY_MAX_PAGINATION_ITERATIONS', '50'))
        self.max_pagination_time_seconds = int(os.getenv('TALLY_MAX_PAGINATION_TIME_SECONDS', '30'))
        self.halt_on_pagination_limit = os.getenv('TALLY_HALT_ON_PAGINATION_LIMIT', 'false').lower() == 'true'
    
    @service_method("tally_votes_for_target")

    
    def tally_votes_for_target(self, target_id: str) -> ServiceResult[VoteSummary]:
        """
        Tally all votes for a specific target and update/create the vote summary.
        
        This method handles all voting patterns: single_choice, multi_select, ranking, rating.
        
        Args:
            target_id: The target to tally votes for
            tenant_id: Tenant ID for access control
            user_id: User ID for audit trail
            
        Returns:
            ServiceResult containing the updated VoteSummary
        """
        try:
            logger.info(f"Starting enhanced vote tally for target: {target_id}")
            
            # Get all votes for this target with pagination support
            all_votes = []
            start_key = None
            pagination_iterations = 0
            pagination_start_time = time.time()
            
            while True:
                pagination_iterations += 1
                pagination_elapsed = time.time() - pagination_start_time
                
                # Check pagination limits
                if pagination_iterations > self.max_pagination_iterations:
                    logger.warning(
                        "Pagination iteration limit exceeded",
                        extra={
                            "metric_name": "TallyPaginationIterationsExceeded",
                            "metric_value": pagination_iterations,
                            "target_id": target_id,
                            "votes_collected": len(all_votes),
                            "max_iterations": self.max_pagination_iterations
                        }
                    )
                    if self.halt_on_pagination_limit:
                        logger.error(f"Halting pagination after {pagination_iterations} iterations")
                        break
                
                if pagination_elapsed > self.max_pagination_time_seconds:
                    logger.warning(
                        "Pagination time limit exceeded",
                        extra={
                            "metric_name": "TallyPaginationTimeExceeded",
                            "metric_value": pagination_elapsed,
                            "target_id": target_id,
                            "votes_collected": len(all_votes),
                            "max_time_seconds": self.max_pagination_time_seconds
                        }
                    )
                    if self.halt_on_pagination_limit:
                        logger.error(f"Halting pagination after {pagination_elapsed:.2f} seconds")
                        break
                
                votes_result = self.vote_service.list_by_target(target_id, start_key=start_key)
                
                if not votes_result.success:
                    logger.error(f"Failed to retrieve votes for target {target_id}: {votes_result.message}")
                    return ServiceResult.error_result(
                        message=f"Failed to retrieve votes: {votes_result.message}",
                        error_code=votes_result.error_code
                    )
                
                # Add this page of results
                if votes_result.data:
                    all_votes.extend(votes_result.data)
                
                # Check if there are more pages via error_details
                if (votes_result.error_details and 
                    'last_evaluated_key' in votes_result.error_details):
                    start_key = votes_result.error_details['last_evaluated_key']
                    logger.debug(f"Fetching next page of votes, total so far: {len(all_votes)}")
                else:
                    # No more pages
                    break
            
            # Log pagination metrics
            logger.info(
                "Pagination completed for vote tally",
                extra={
                    "metric_name": "TallyPaginationCompleted",
                    "iterations": pagination_iterations,
                    "elapsed_seconds": pagination_elapsed,
                    "votes_collected": len(all_votes),
                    "target_id": target_id
                }
            )
            
            votes = all_votes
            
            if not votes:
                # No votes - create empty summary
                return self._create_empty_summary(target_id)
            
            # Determine vote type from first vote (all should be same type for a target)
            vote_type = votes[0].vote_type if votes else "single_choice"
            
            # Tally based on vote type
            if vote_type == "single_choice":
                summary_data = self._tally_single_choice_votes(votes)
            elif vote_type == "multi_select":
                summary_data = self._tally_multi_select_votes(votes)
            elif vote_type == "ranking":
                summary_data = self._tally_ranking_votes(votes)
            elif vote_type == "rating":
                summary_data = self._tally_rating_votes(votes)
            elif vote_type == "legacy":
                # Legacy binary votes
                summary_data = self._tally_legacy_votes(votes)
            else:
                # Default to legacy for unknown types
                summary_data = self._tally_legacy_votes(votes)
            
            logger.info(f"Tallying complete for target {target_id}: {len(votes)} votes processed")
            
            # Create or update the vote summary
            summary_result = self._create_or_update_summary(
                target_id, vote_type, summary_data
            )
            
            if summary_result.success:
                logger.info(f"Vote summary updated for target {target_id}: {summary_data}")
            
            return summary_result
            
        except Exception as e:
            logger.error(f"Error tallying votes for target {target_id}: {str(e)}")
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.OPERATION_FAILED,
                context=f"Failed to tally votes for target {target_id}"
            )

    def _tally_single_choice_votes(self, votes) -> Dict[str, Any]:
        """Tally single choice votes (A/B/C/D tests)."""
        choice_counts = {}
        total_participants = len(votes)
        
        # Legacy counters for backward compatibility
        total_up_votes = 0
        total_down_votes = 0
        
        for vote in votes:
            # Count legacy fields
            total_up_votes += vote.up_vote
            total_down_votes += vote.down_vote
            
            # Count choices from enhanced data
            selected_choices = vote.get_selected_choices()
            for choice in selected_choices:
                choice_counts[choice] = choice_counts.get(choice, 0) + 1
        
        return {
            "choice_breakdown": choice_counts,
            "total_participants": total_participants,
            "total_selections": total_participants,  # Same as participants for single choice
            "total_up_votes": total_up_votes,
            "total_down_votes": total_down_votes,
            "total_votes": total_up_votes + total_down_votes
        }

    def _tally_multi_select_votes(self, votes) -> Dict[str, Any]:
        """Tally multi-select votes."""
        choice_counts = {}
        total_participants = len(votes)
        total_selections = 0
        
        for vote in votes:
            selected_choices = vote.get_selected_choices()
            total_selections += len(selected_choices)
            
            for choice in selected_choices:
                choice_counts[choice] = choice_counts.get(choice, 0) + 1
        
        return {
            "choice_breakdown": choice_counts,
            "total_participants": total_participants,
            "total_selections": total_selections,
            "total_up_votes": total_selections,  # Legacy: total selections
            "total_down_votes": 0,
            "total_votes": total_selections
        }

    def _tally_ranking_votes(self, votes) -> Dict[str, Any]:
        """Tally ranking votes with weighted scoring."""
        choice_scores = {}
        choice_counts = {}
        total_participants = len(votes)
        
        for vote in votes:
            for choice_id, choice_data in vote.choices.items():
                rank = choice_data.get("rank", 999)
                value = choice_data.get("value", 0)
                
                choice_scores[choice_id] = choice_scores.get(choice_id, 0) + value
                choice_counts[choice_id] = choice_counts.get(choice_id, 0) + 1
        
        return {
            "choice_breakdown": choice_counts,
            "choice_scores": choice_scores,  # Weighted scores
            "total_participants": total_participants,
            "total_selections": sum(choice_counts.values()),
            "total_up_votes": sum(choice_scores.values()),  # Legacy: total score
            "total_down_votes": 0,
            "total_votes": sum(choice_scores.values())
        }

    def _tally_rating_votes(self, votes) -> Dict[str, Any]:
        """Tally rating votes with average ratings."""
        choice_ratings = {}
        choice_counts = {}
        total_participants = len(votes)
        
        for vote in votes:
            for choice_id, choice_data in vote.choices.items():
                rating = choice_data.get("rating", 0)
                
                if choice_id not in choice_ratings:
                    choice_ratings[choice_id] = []
                choice_ratings[choice_id].append(rating)
                choice_counts[choice_id] = choice_counts.get(choice_id, 0) + 1
        
        # Calculate average ratings
        choice_averages = {
            choice: sum(ratings) / len(ratings)
            for choice, ratings in choice_ratings.items()
        }
        
        return {
            "choice_breakdown": choice_counts,
            "choice_averages": choice_averages,  # Average ratings
            "total_participants": total_participants,
            "total_selections": sum(choice_counts.values()),
            "total_up_votes": int(sum(choice_averages.values())),  # Legacy: sum of averages
            "total_down_votes": 0,
            "total_votes": int(sum(choice_averages.values()))
        }

    def _tally_legacy_votes(self, votes) -> Dict[str, Any]:
        """Tally legacy binary votes."""
        total_up_votes = sum(vote.up_vote for vote in votes)
        total_down_votes = sum(vote.down_vote for vote in votes)
        
        # Create choice breakdown from binary data
        choice_breakdown = {}
        if total_up_votes > 0:
            choice_breakdown["up"] = total_up_votes
        if total_down_votes > 0:
            choice_breakdown["down"] = total_down_votes
        
        return {
            "choice_breakdown": choice_breakdown,
            "total_participants": len(votes),
            "total_selections": total_up_votes + total_down_votes,
            "total_up_votes": total_up_votes,
            "total_down_votes": total_down_votes,
            "total_votes": total_up_votes + total_down_votes
        }

    def _create_empty_summary(self, target_id: str) -> ServiceResult[VoteSummary]:
        """Create an empty summary for targets with no votes."""
        return self.vote_summary_service.create(
            target_id=target_id,
            vote_type="single_choice",
            choice_breakdown={},
            choice_percentages={},
            total_participants=0,
            total_selections=0,
            total_up_votes=0,
            total_down_votes=0,
            total_votes=0,
            content={
                "last_tallied_utc_ts": self._get_current_timestamp(),
                "vote_count": 0
            }
        )

    def _create_or_update_summary(self, target_id: str, 
                                 vote_type: str, summary_data: Dict[str, Any]) -> ServiceResult[VoteSummary]:
        """Create or update vote summary with enhanced data."""
        
        # Calculate percentages
        choice_breakdown = summary_data["choice_breakdown"]
        total_participants = summary_data["total_participants"]
        
        choice_percentages = {}
        if total_participants > 0:
            choice_percentages = {
                choice: (count / total_participants * 100)
                for choice, count in choice_breakdown.items()
            }
        
        return self.vote_summary_service.create(
            target_id=target_id,
            vote_type=vote_type,
            choice_breakdown=choice_breakdown,
            choice_percentages=choice_percentages,
            choice_averages=summary_data.get("choice_averages", {}),  # For rating votes
            total_participants=total_participants,
            total_selections=summary_data["total_selections"],
            total_up_votes=summary_data["total_up_votes"],
            total_down_votes=summary_data["total_down_votes"],
            total_votes=summary_data["total_votes"],
            content={
                "last_tallied_utc_ts": self._get_current_timestamp(),
                "vote_count": total_participants
            }
        )
    
    def _get_votes_page(self, target_id: str, start_key: Optional[dict] = None) -> ServiceResult[Dict[str, Any]]:
        """
        Get a page of votes for a target using the vote service's list_by_target method.
        
        Returns:
            ServiceResult with data containing 'items' and optional 'last_evaluated_key'
        """
        try:
            # For simplicity in testing, we'll get all votes at once
            # In production, you would implement proper pagination here
            result = self.vote_service.list_by_target(target_id)
            
            if result.success:
                items = result.data
                
                # For testing purposes, return all items at once
                # In production, you would implement proper DynamoDB pagination
                page_items = items
                has_more = False
                
                return ServiceResult.success_result({
                    'items': page_items,
                    'last_evaluated_key': {'page': 'next'} if has_more else None
                })
            else:
                return result
                
        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_QUERY_FAILED,
                context=f"Failed to query votes for target {target_id}"
            )
    
    @service_method("tally_votes_for_multiple_targets")

    
    def tally_votes_for_multiple_targets(self, target_ids: List[str]) -> ServiceResult[List[VoteSummary]]:
        """
        Tally votes for multiple targets efficiently.
        
        This is useful for batch processing or scheduled jobs.
        
        Args:
            target_ids: List of target IDs to process
            tenant_id: Tenant ID for access control
            user_id: User ID for audit trail
            
        Returns:
            ServiceResult containing list of updated VoteSummaries
        """
        try:
            logger.info(f"Starting batch tally for {len(target_ids)} targets")
            
            summaries = []
            failed_targets = []
            
            for target_id in target_ids:
                result = self.tally_votes_for_target(target_id)
                
                if result.success:
                    summaries.append(result.data)
                else:
                    failed_targets.append({
                        'target_id': target_id,
                        'message': result.message,
                        'error_code': result.error_code
                    })
                    logger.warning(f"Failed to tally votes for target {target_id}: {result.message}")
            
            if failed_targets:
                logger.warning(f"Batch tally completed with {len(failed_targets)} failures out of {len(target_ids)} targets")
                return ServiceResult.error_result(
                    message=f"Batch tally completed with failures: {len(failed_targets)}/{len(target_ids)} failed",
                    error_code=ErrorCode.PARTIAL_FAILURE,
                    error_details={
                        'successful_count': len(summaries),
                        'failed_count': len(failed_targets),
                        'failed_targets': failed_targets,
                        'successful_summaries': summaries
                    }
                )
            else:
                logger.info(f"Batch tally completed successfully for all {len(target_ids)} targets")
                return ServiceResult.success_result(summaries)
                
        except Exception as e:
            logger.error(f"Error in batch tally operation: {str(e)}")
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.BATCH_OPERATION_FAILED,
                context="Failed to process batch tally operation"
            )
    
    def get_stale_targets(self, hours_threshold: int = 24) -> ServiceResult[List[str]]:
        """
        Get list of targets that haven't been tallied recently.
        
        This is useful for identifying targets that need re-tallying.
        
        Args:
            tenant_id: Tenant ID to scope the search
            hours_threshold: Hours since last tally to consider stale
            
        Returns:
            ServiceResult containing list of target IDs that need tallying
        """
        try:
            # Get all vote summaries for the tenant
            summaries_result = self.vote_summary_service.list_by_tenant()
            
            if not summaries_result.success:
                return summaries_result
            
            current_time = self._get_current_timestamp()
            threshold_time = current_time - (hours_threshold * 3600)  # Convert hours to seconds
            
            stale_targets = []
            
            for summary in summaries_result.data:
                last_tallied = summary.content.get('last_tallied_utc_ts', 0)
                
                if last_tallied < threshold_time:
                    stale_targets.append(summary.target_id)
            
            logger.info(f"Found {len(stale_targets)} stale targets (older than {hours_threshold} hours)")
            return ServiceResult.success_result(stale_targets)
            
        except Exception as e:
            logger.error(f"Error finding stale targets: {str(e)}")
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_QUERY_FAILED,
                context="Failed to query for stale targets"
            )
    
    def _get_current_timestamp(self) -> float:
        """Get current UTC timestamp."""
        import datetime as dt
        return dt.datetime.now(dt.UTC).timestamp()


class VoteTallyServiceEnhanced(VoteTallyService):
    """
    Enhanced version with true pagination support.
    
    This version demonstrates how to implement proper pagination
    when the underlying service supports it.
    """
    
    def _get_votes_page_with_pagination(self, target_id: str, start_key: Optional[dict] = None) -> ServiceResult[Dict[str, Any]]:
        """
        Enhanced version that would use true pagination if the vote service supported it.
        
        This is how you would implement it with proper DynamoDB pagination:
        """
        try:
            # Create a vote model for querying
            vote_model = Vote()
            vote_model.target_id = target_id
            
            # Use the database service's _query_by_index method directly with pagination
            # This would require access to the underlying database service
            # For now, we'll simulate the structure
            
            # In a real implementation, you might do:
            # result = self.vote_service._query_by_index(
            #     vote_model, 
            #     "gsi5",  # target index
            #     start_key=start_key,
            #     limit=self.page_size
            # )
            
            # For demonstration, we'll use the existing method
            result = self.vote_service.list_by_target(target_id)
            
            if result.success:
                return ServiceResult.success_result({
                    'items': result.data,
                    'last_evaluated_key': None  # Would come from DynamoDB response
                })
            else:
                return result
                
        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_QUERY_FAILED,
                context=f"Failed to query votes with pagination for target {target_id}"
            )
