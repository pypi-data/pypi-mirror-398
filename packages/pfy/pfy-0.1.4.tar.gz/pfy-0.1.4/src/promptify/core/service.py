"""Business logic for prompt refinement"""
from typing import Protocol
from promptify.utils.errors import ServiceError, rate_limit_error, network_error

class PromptifyService:
    """Main service orchestrating prompt refinement"""
    
    def __init__(self, graph):
        self.graph = graph
    
    def refine(self, query: str, model_provider: str = None, model_name: str = None, api_key: str = None) -> dict:
        """Refine a prompt using the agent graph"""
        initial_state = {
            "user_query": query,
            "model_config": {
                "provider": model_provider,
                "model": model_name,
                "api_key": api_key
            },
            "intent": "",
            "critique": None,
            "expert_suggestions": "",
            "final_prompt_draft": "",
            "iteration_count": 0
        }
        
        try:
            return self.graph.invoke(initial_state)
        
        except Exception as e:
            error_message = str(e).lower()
            
            # Handle specific error types
            if "429" in error_message or "rate limit" in error_message:
                raise rate_limit_error()
            
            elif "network" in error_message or "connection" in error_message:
                raise network_error()
            
            elif "api key" in error_message or "authentication" in error_message:
                from promptify.utils.errors import api_key_missing_error
                raise api_key_missing_error()
            
            else:
                # Generic service error
                raise ServiceError(
                    f"Agent processing failed: {e}",
                    hint="Try running with --verbose to see more details"
                )
