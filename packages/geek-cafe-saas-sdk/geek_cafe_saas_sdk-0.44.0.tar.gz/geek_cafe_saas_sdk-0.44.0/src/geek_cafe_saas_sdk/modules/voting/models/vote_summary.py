
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
import datetime as dt
from typing import Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel

class VoteSummary(BaseTenantUserModel):
    def __init__(self):
        super().__init__()
        self._content: Dict[str, Any] = {}
        self._target_id: str | None = None
        
        # Enhanced summary fields
        self._vote_type: str = "single_choice"  # Type of voting used
        self._choice_breakdown: Dict[str, int] = {}  # {"A": 150, "B": 100, "C": 50}
        self._choice_percentages: Dict[str, float] = {}  # {"A": 50.0, "B": 33.3, "C": 16.7}
        self._choice_averages: Dict[str, float] = {}  # For rating votes: {"A": 4.5, "B": 3.2}
        self._total_participants: int = 0  # Number of people who voted
        self._total_selections: int = 0  # For multi-select: total selections made
        
        # Legacy fields (for backward compatibility)
        self._total_up_votes: int = 0
        self._total_down_votes: int = 0
        self._total_votes: int = 0

        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)

    def _setup_indexes(self):
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("vote-summary", self.id)
        )

        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("vote-summary", self.id))
        self.indexes.add_primary(primary)
        
        ## GSI: 1
        # GSI: all vote summaries
        gsi: DynamoDBIndex = DynamoDBIndex()
        
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("vote-summary", "all"))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
           ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 2
        # GSI: vote summary by target_id (for quick lookup by target)
        gsi: DynamoDBIndex = DynamoDBIndex()
        
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("target", self.target_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
           ("model", "vote-summary")
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 3
        # GSI: vote summaries by tenant
        gsi: DynamoDBIndex = DynamoDBIndex()
        
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
           ("model", "vote-summary"),("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        

    @property
    def content(self) -> Dict[str, Any]:
        """Get content (boto3-assist v0.30.0+ auto-converts Decimals to float)."""
        return self._content

    @content.setter
    def content(self, value: Dict[str, Any]):
        """Set content (store as-is for boto3-assist compatibility)."""
        self._content = value if value is not None else {}
    
    
    @property
    def total_up_votes(self) -> int:
        return self._total_up_votes
    
    @total_up_votes.setter
    def total_up_votes(self, value: int):
        self._total_up_votes = value

    @property
    def total_down_votes(self) -> int:
        return self._total_down_votes
    
    @total_down_votes.setter
    def total_down_votes(self, value: int):
        self._total_down_votes = value
    
    @property
    def total_votes(self) -> int:
        return self._total_votes
    
    @total_votes.setter
    def total_votes(self, value: int):
        self._total_votes = value
    
    @property
    def target_id(self) -> str | None:
        return self._target_id

    @target_id.setter
    def target_id(self, value: str | None):
        self._target_id = value
    
    @property
    def vote_type(self) -> str:
        return self._vote_type

    @vote_type.setter
    def vote_type(self, value: str):
        self._vote_type = value
    
    @property
    def choice_breakdown(self) -> Dict[str, int]:
        return self._choice_breakdown

    @choice_breakdown.setter
    def choice_breakdown(self, value: Dict[str, int]):
        self._choice_breakdown = value
    
    @property
    def choice_percentages(self) -> Dict[str, float]:
        return self._choice_percentages

    @choice_percentages.setter
    def choice_percentages(self, value: Dict[str, float]):
        self._choice_percentages = value
    
    @property
    def choice_averages(self) -> Dict[str, float]:
        """Average ratings for rating-type votes (boto3-assist v0.30.0+ auto-converts Decimals)."""
        return self._choice_averages

    @choice_averages.setter
    def choice_averages(self, value: Dict[str, float]):
        self._choice_averages = value
    
    @property
    def total_participants(self) -> int:
        return self._total_participants

    @total_participants.setter
    def total_participants(self, value: int):
        self._total_participants = value
    
    @property
    def total_selections(self) -> int:
        return self._total_selections

    @total_selections.setter
    def total_selections(self, value: int):
        self._total_selections = value
    
    # Helper methods
    def calculate_percentages(self):
        """Calculate percentages from choice breakdown."""
        if self.total_participants > 0:
            self.choice_percentages = {
                choice: (count / self.total_participants * 100)
                for choice, count in self.choice_breakdown.items()
            }
        else:
            self.choice_percentages = {}
    
    def get_winning_choice(self) -> str | None:
        """Get the choice with the most votes."""
        if not self.choice_breakdown:
            return None
        return max(self.choice_breakdown.items(), key=lambda x: x[1])[0]
    
    def get_choice_percentage(self, choice_id: str) -> float:
        """Get percentage for a specific choice."""
        return self.choice_percentages.get(choice_id, 0.0)