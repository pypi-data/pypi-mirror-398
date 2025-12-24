"""
PrefID Tools for LangChain
Official LangChain integration for preference-aware AI agents
"""

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from prefid import PrefID


class PrefIDPreferenceInput(BaseModel):
    """Input for PrefIDPreferenceTool"""
    domain: str = Field(
        description="Domain to get preferences for. Options: 'food_profile', 'music_preferences', 'travel_profile', 'coding_profile', 'career_profile', 'finance_profile', 'general_profile'"
    )


class PrefIDPreferenceTool(BaseTool):
    """
    Tool for getting user preferences from PrefID.
    
    Use this to understand what the user likes across different domains.
    Returns preference data that can guide recommendations and responses.
    """
    
    name: str = "get_user_preferences"
    description: str = (
        "Get user's preferences for a specific domain. "
        "Use this to understand what the user likes (food, music, travel, etc). "
        "Input should be a domain name like 'food_profile' or 'music_preferences'."
    )
    args_schema: Type[BaseModel] = PrefIDPreferenceInput
    
    prefid_client: PrefID = Field(exclude=True)
    
    def _run(
        self,
        domain: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get preferences for domain"""
        try:
            prefs = self.prefid_client.get_preferences(domain)
            return str(prefs)
        except Exception as e:
            return f"Error getting preferences: {str(e)}"


class PrefIDThinkingInput(BaseModel):
    """Input for PrefIDThinkingTool"""
    user_id: str = Field(description="User ID to get thinking preferences for")


class PrefIDThinkingTool(BaseTool):
    """
    Tool for getting how the user wants AI to respond (Atom of Thought).
    
    Returns agent hints that describe HOW to structure responses:
    - Reasoning style (stepwise, summary_first, default)
    - Decision style (recommend, tradeoffs, options, default)
    - Verbosity (concise, detailed, examples, default)
    - Autonomy (proactive, confirm_first, clarify_first, default)
    """
    
    name: str = "get_thinking_preferences"
    description: str = (
        "Get how the user prefers AI to respond. "
        "Returns thinking preferences that govern response structure, "
        "verbosity, decision-making style, and autonomy level. "
        "Use this BEFORE making recommendations to adapt your response style."
    )
    args_schema: Type[BaseModel] = PrefIDThinkingInput
    
    prefid_client: PrefID = Field(exclude=True)
    
    def _run(
        self,
        user_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get thinking preferences"""
        try:
            hints = self.prefid_client.get_agent_hints(user_id)
            return (
                f"Reasoning: {hints['reasoning']}\n"
                f"Decision: {hints['decision']}\n"
                f"Verbosity: {hints['verbosity']}\n"
                f"Autonomy: {hints['autonomy']}\n\n"
                f"{hints['description']}"
            )
        except Exception as e:
            return f"Error getting thinking preferences: {str(e)}"


class PrefIDLearnInput(BaseModel):
    """Input for PrefIDLearnTool"""
    user_id: str = Field(description="User ID")
    thought: str = Field(
        description="Natural language statement about how the user wants AI to respond. Example: 'I prefer step-by-step explanations'"
    )


class PrefIDLearnTool(BaseTool):
    """
    Tool for learning new thinking preferences from the user.
    
    When the user expresses how they want responses structured,
    use this tool to remember it for future conversations.
    """
    
    name: str = "learn_thinking_preference"
    description: str = (
        "Learn and remember how the user wants AI to respond. "
        "Use this when the user expresses preferences about response style, "
        "such as 'I prefer brief answers' or 'Give me step-by-step explanations'. "
        "Input should be the user's natural language preference statement."
    )
    args_schema: Type[BaseModel] = PrefIDLearnInput
    
    prefid_client: PrefID = Field(exclude=True)
    
    def _run(
        self,
        user_id: str,
        thought: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Learn thinking preference"""
        try:
            self.prefid_client.learn_thought(user_id, thought)
            return f"Learned: {thought}"
        except Exception as e:
            return f"Error learning preference: {str(e)}"


class PrefIDWhyInput(BaseModel):
    """Input for PrefIDWhyTool"""
    user_id: str = Field(description="User ID")


class PrefIDWhyTool(BaseTool):
    """
    Tool for explaining why AI is responding in a certain way.
    
    Provides introspection into which thinking preferences are active
    and how they're affecting the response style.
    """
    
    name: str = "explain_response_style"
    description: str = (
        "Explain why you're responding in a certain way. "
        "Use this to provide transparency when the user asks "
        "'Why are you responding like this?' or wants to understand "
        "how their preferences are being applied."
    )
    args_schema: Type[BaseModel] = PrefIDWhyInput
    
    prefid_client: PrefID = Field(exclude=True)
    
    def _run(
        self,
        user_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get explanation"""
        try:
            why = self.prefid_client.get_why(user_id)
            explanation = why['explanation']
            atoms = why['active_atoms']
            
            result = f"{explanation}\n\nActive preferences:\n"
            for atom in atoms:
                result += f"- {atom['atom']}: {atom['effect']}\n"
            
            return result
        except Exception as e:
            return f"Error getting explanation: {str(e)}"


# Helper function to create all tools at once
def create_prefid_tools(
    client_id: str,
    access_token: str,
    user_id: str,
) -> list[BaseTool]:
    """
    Create all PrefID tools for LangChain agents.
    
    Args:
        client_id: PrefID client ID
        access_token: User's access token
        user_id: User ID for thinking preferences
        
    Returns:
        List of configured PrefID tools
        
    Example:
        >>> from langchain_prefid import create_prefid_tools
        >>> tools = create_prefid_tools(
        >>>     client_id="your-client-id",
        >>>     access_token="user-token",
        >>>     user_id="user_123"
        >>> )
        >>> # Use with LangChain agent
    """
    prefid = PrefID(client_id=client_id, access_token=access_token)
    
    return [
        PrefIDPreferenceTool(prefid_client=prefid),
        PrefIDThinkingTool(prefid_client=prefid),
        PrefIDLearnTool(prefid_client=prefid),
        PrefIDWhyTool(prefid_client=prefid),
    ]
