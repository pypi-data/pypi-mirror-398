from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
import litellm

# Import our custom provider selection logic
from promptify.core.providerSelection.config import PromptifyConfig
from promptify.core.providerSelection.providers import get_provider

from promptify.prompt.TriageAgentPrompt import TRIAGE_AGENT_PROMPT
from promptify.prompt.CriticAgentPrompt import CRITIQUE_AGENT_PROMPT
from promptify.prompt.expertAgentPrompt import EXPERT_AGENT_PROMPT
from promptify.prompt.promptSmith import PROMPT_SMITH_PROMPT
from promptify.agent.state import AgentState


def call_llm(prompt_value, config: dict = None) -> str:
    """
    Custom Runnable that takes a LangChain PromptValue,
    converts it to LiteLLM messages, selects the provider from config,
    and returns the string response.
    """
    # 1. Convert LangChain PromptValue to standard list-of-dicts messages
    messages = []
    for m in prompt_value.to_messages():
        role = "user"
        if m.type == "system":
            role = "system"
        elif m.type == "ai":
            role = "assistant"
        elif m.type == "human":
            role = "user"
        
        messages.append({"role": role, "content": m.content})

    # 2. Load Configuration (defaults to Cerebras/Free if file not found)
    try:
        cfg = PromptifyConfig.load()
    except Exception as e:
        print(f"⚠️ [Config] Warning: {e}. Using defaults.")
        cfg = PromptifyConfig()
    
    # 3. Prepare Provider Arguments
    # Start with defaults from loaded config
    provider_kwargs = {
        "model": cfg.model.model,
        "temperature": cfg.model.temperature,
    }
    # Only forward optional fields if they exist from loaded config
    if cfg.model.api_base:
        provider_kwargs["api_base"] = cfg.model.api_base
    if cfg.model.api_key:
        provider_kwargs["api_key"] = cfg.model.api_key

    # OVERRIDE with dynamic config if provided
    if config:
        if config.get("model"):
            provider_kwargs["model"] = config["model"]
        if config.get("api_key"):
            provider_kwargs["api_key"] = config["api_key"]
        
        # If provider is explicitly passed in dynamic config, use it
        # Note: We need the provider type to get the right provider class
        # Ideally, config should have 'provider' key.
        # But get_provider takes 'provider_name' as first arg.
    
    provider_name = config.get("provider", cfg.model.provider) if config else cfg.model.provider

    # 4. Get Provider & Params
    try:
        provider = get_provider(provider_name, **provider_kwargs)
        litellm_params = provider.get_litellm_params()
        
        # 5. Call LiteLLM
        # litellm.completion handles the API calls
        response = litellm.completion(messages=messages, **litellm_params)
        
        return response.choices[0].message.content or ""
        
    except Exception as e:
        error_msg = f"❌ [LLM Error] {str(e)}"
        print(error_msg)
        return error_msg  # Or raise, depending on desired robustness


def create_chain(system_prompt: str, include_user_msg: bool = True, model_config: dict = None):
    """Factory function to create prompt chains using dynamic LLM"""
    messages = [("system", system_prompt)]
    if include_user_msg:
        messages.append(("user", "{user_input}"))
    
    template = ChatPromptTemplate.from_messages(messages)
    
    # Pipe: Template -> Custom LLM Caller
    # We don't need StrOutputParser because call_llm returns a string.
    # Bind the config to the call_llm function
    return template | RunnableLambda(lambda x: call_llm(x, config=model_config))


PERSONA_MAP = {
    "ARCHITECT": "Senior Solutions Architect & Strategist",
    "BUILDER": "Senior Software Engineer & Implementation Specialist",
    "MENTOR": "Expert Educator & Technical Communicator",
    "ANALYST": "Lead Quality Assurance & Data Analyst"
}


def triageAgent(state: AgentState) -> dict:
    """Classifies user intent"""
    print("🔍 [TRIAGE] Analyzing...")
    chain = create_chain(TRIAGE_AGENT_PROMPT, model_config=state.get("model_config"))
    response = chain.invoke({"user_input": state["user_query"]})
    
    intent = response.strip().upper()
    valid_intents = list(PERSONA_MAP.keys())
    result = intent if intent in valid_intents else "ARCHITECT"
    
    print(f"✅ [TRIAGE] {result}")
    return {"intent": result}


def criticAgent(state: AgentState) -> dict:
    """Identifies gaps in the user query"""
    print("🔍 [CRITIC] Analyzing...")
    chain = create_chain(CRITIQUE_AGENT_PROMPT, model_config=state.get("model_config"))
    response = chain.invoke({"user_input": state["user_query"]})
    
    print("✅ [CRITIC] Done")
    return {"critique": response.strip()}


def expertAgent(state: AgentState) -> dict:
    """Provides domain-specific expert advice"""
    print(f"🔍 [EXPERT] Consulting {state['intent']} expert...")
    
    selected_persona = PERSONA_MAP.get(state["intent"], "Helpful AI Assistant")
    
    # ✅ CORRECT: Use placeholders, not f-strings
    template = ChatPromptTemplate.from_messages([
        ("system", EXPERT_AGENT_PROMPT),
        ("user", """Context:
- User's Intent Mode: {intent}
- Original Query: {user_query}
- Critique (Gaps Identified): {critique}

Provide your expert suggestions now.""")
    ])
    
    chain = template | RunnableLambda(lambda x: call_llm(x, config=state.get("model_config")))
    
    response = chain.invoke({
        "persona": selected_persona,
        "intent": state["intent"],
        "user_query": state["user_query"],
        "critique": state["critique"]
    })
    
    print("✅ [EXPERT] Done")
    return {"expert_suggestions": response.strip()}


def promptSmith(state: AgentState) -> dict:
    """Synthesizes the final structured prompt"""
    print("🔍 [SMITH] Crafting final prompt...")
    
    template = ChatPromptTemplate.from_messages([
        ("system", PROMPT_SMITH_PROMPT),
        ("user", """Inputs for synthesis:

1. Original Query: {user_query}
2. Expert Advice: {expert_suggestions}
3. Identified Gaps: {critique}

Create the final refined prompt now.""")
    ])
    
    chain = template | RunnableLambda(lambda x: call_llm(x, config=state.get("model_config")))
    
    response = chain.invoke({
        "user_query": state["user_query"],
        "expert_suggestions": state["expert_suggestions"],
        "critique": state["critique"]
    })
    
    print("✅ [SMITH] Done")
    return {"final_prompt_draft": response.strip()}
