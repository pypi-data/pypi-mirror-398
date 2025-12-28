
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel

class Vote(BaseTenantUserModel):
    def __init__(self):
        super().__init__()
        self._content: Dict[str, Any] = {}
        self._target_id: str | None = None
        
        # Enhanced voting system fields
        self._vote_type: str = "single_choice"  # single_choice, multi_select, ranking, rating
        self._choices: Dict[str, Any] = {}  # Flexible choice storage
        self._max_selections: int | None = None  # For multi_select limits
        
        # Legacy fields (for backward compatibility)
        self._up_vote: int = 0
        self._down_vote: int = 0

        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)

    def _setup_indexes(self):
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("vote", self.id)
        )

        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("vote", self.id))
        self.indexes.add_primary(primary)
        
        ## GSI: 1
        # GSI: all votes
        gsi: DynamoDBIndex = DynamoDBIndex()
        
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("vote", "all"))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
           ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 2
        # GSI: all votes by user, sorted by created ts
        gsi: DynamoDBIndex = DynamoDBIndex()
        
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.user_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
           ("model", "vote"),("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 3
        # GSI: all votes by tenant, sorted by created ts
        gsi: DynamoDBIndex = DynamoDBIndex()
        
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
           ("model", "vote"),("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 4
        # GSI: enforce uniqueness helper - all votes by user+target (one per target per user)
        gsi: DynamoDBIndex = DynamoDBIndex()
        
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.user_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
           ("target", self.target_id)
        )
        self.indexes.add_secondary(gsi)

        ## GSI: 5
        # GSI: all votes for a target
        gsi: DynamoDBIndex = DynamoDBIndex()
        
        gsi.name = "gsi5"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("target", self.target_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
           ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

    @property
    def content(self) -> Dict[str, Any]:
        return self._content

    @content.setter
    def content(self, value: Dict[str, Any]):
        self._content = value
    
    @property
    def up_vote(self) -> int:
        return self._up_vote
    
    @up_vote.setter
    def up_vote(self, value: int):
        self._up_vote = value
    
    @property
    def down_vote(self) -> int:
        return self._down_vote
    
    @down_vote.setter
    def down_vote(self, value: int):
        self._down_vote = value
    
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
    def choices(self) -> Dict[str, Any]:
        return self._choices

    @choices.setter
    def choices(self, value: Dict[str, Any]):
        self._choices = value
    
    @property
    def max_selections(self) -> int | None:
        return self._max_selections

    @max_selections.setter
    def max_selections(self, value: int | None):
        self._max_selections = value
    
    # Helper methods for different voting patterns
    def set_single_choice(self, choice_id: str, available_choices: list[str] = None):
        """Set a single choice vote (A/B test, single selection)."""
        self.vote_type = "single_choice"
        self.choices = {choice_id: {"selected": True, "value": 1}}
        
        # Set legacy fields for backward compatibility
        if available_choices and len(available_choices) >= 2:
            self.up_vote = 1 if choice_id == available_choices[0] else 0
            self.down_vote = 1 if choice_id == available_choices[1] else 0
        else:
            self.up_vote = 1
            self.down_vote = 0
    
    def set_multi_select(self, selected_choices: list[str], available_choices: list[str] = None, max_selections: int = None):
        """Set multiple choice selections."""
        self.vote_type = "multi_select"
        self.max_selections = max_selections
        
        # Build choices dict
        if available_choices:
            self.choices = {
                choice: {"selected": choice in selected_choices, "value": 1 if choice in selected_choices else 0}
                for choice in available_choices
            }
        else:
            self.choices = {choice: {"selected": True, "value": 1} for choice in selected_choices}
        
        # Set legacy fields
        self.up_vote = len(selected_choices)
        self.down_vote = 0
    
    def set_ranking(self, ranked_choices: list[str]):
        """Set ranked choices (1st, 2nd, 3rd preference)."""
        self.vote_type = "ranking"
        self.choices = {
            choice: {"rank": idx + 1, "value": len(ranked_choices) - idx}
            for idx, choice in enumerate(ranked_choices)
        }
        
        # Set legacy fields
        self.up_vote = len(ranked_choices)
        self.down_vote = 0
    
    def set_rating(self, ratings: Dict[str, float]):
        """Set rating votes (1-5 stars per option)."""
        self.vote_type = "rating"
        self.choices = {
            choice: {"rating": rating, "value": rating}
            for choice, rating in ratings.items()
        }
        
        # Set legacy fields (average rating)
        avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0
        self.up_vote = int(avg_rating)
        self.down_vote = 0
    
    def get_selected_choices(self) -> list[str]:
        """Get list of selected choices for any vote type."""
        if self.vote_type == "single_choice":
            return [choice for choice, data in self.choices.items() if data.get("selected")]
        elif self.vote_type == "multi_select":
            return [choice for choice, data in self.choices.items() if data.get("selected")]
        elif self.vote_type == "ranking":
            # Return choices sorted by rank
            ranked = sorted(self.choices.items(), key=lambda x: x[1].get("rank", 999))
            return [choice for choice, _ in ranked]
        elif self.vote_type == "rating":
            return list(self.choices.keys())
        return []
    
    def get_choice_value(self, choice_id: str) -> Any:
        """Get the value for a specific choice."""
        return self.choices.get(choice_id, {}).get("value", 0)