from typing import TypedDict, Optional
class AgentState(TypedDict):
    user_query: str
    intent: str                 # Populated by Triage (e.g., "coding", "writing")
    critique: Optional[str]     # Populated by The Critic
    expert_suggestions: str # Populated by The Expert
    final_prompt_draft: str     # Populated by Prompt Smith
    iteration_count: int        # To prevent infinite loops if we add a retry cycle later
    model_config: Optional[dict] # Configuration for the model to use


