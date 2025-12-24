# ============================================================================
# File: agentapps/agent.py
# ============================================================================

"""Core Agent implementation"""

from typing import List, Dict, Any, Optional, Union
import json
import re

from .model import Model, OpenAIChat
from .tools import Tool


class Agent:
    """
    Agent class for building intelligent agents with tools and collaboration
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        role: Optional[str] = None,
        model: Optional[Model] = None,
        tools: Optional[List[Tool]] = None,
        instructions: Optional[List[str]] = None,
        team: Optional[List['Agent']] = None,
        show_tool_calls: bool = False,
        markdown: bool = False,
        description: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize an Agent
        
        Args:
            name: Agent name
            role: Agent role/purpose
            model: LLM model to use
            tools: List of tools available to the agent
            instructions: List of instructions for the agent
            team: List of sub-agents (creates an agent team)
            show_tool_calls: Whether to display tool calls
            markdown: Whether to format output as markdown
            description: Agent description
            temperature: Temperature for model (overrides model default)
            **kwargs: Additional configuration
        """
        self.name = name or "Agent"
        self.role = role or "General Assistant"
        self.model = model
        self.tools = tools or []
        self.instructions = instructions or []
        self.team = team or []
        self.show_tool_calls = show_tool_calls
        self.markdown = markdown
        self.description = description or ""
        self.temperature = temperature
        self.kwargs = kwargs
        
        # Execution state
        self.conversation_history: List[Dict[str, str]] = []
        self.tool_results: List[Dict[str, Any]] = []
        
        # If this is a team agent, inherit instructions
        if self.team:
            self._setup_team()
    
    def _setup_team(self):
        """Setup team agent configuration"""
        if not self.model:
            # Use the first team member's model as default
            for member in self.team:
                if member.model:
                    self.model = member.model
                    break
        
        # Collect all tools from team members
        all_tools = []
        for member in self.team:
            all_tools.extend(member.tools)
        
        # Remove duplicates while preserving order
        seen = set()
        for tool in all_tools:
            if tool.name not in seen:
                seen.add(tool.name)
                self.tools.append(tool)
        
        # Set role if not specified
        if self.role == "General Assistant":
            team_roles = [m.role for m in self.team if m.role]
            if team_roles:
                self.role = f"Team coordinator managing: {', '.join(team_roles)}"
    
    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent"""
        self.tools.append(tool)
        if self.show_tool_calls:
            print(f"✓ Added tool '{tool.name}' to agent '{self.name}'")
    
    def add_team_member(self, agent: 'Agent') -> None:
        """Add a team member"""
        self.team.append(agent)
        # Inherit tools
        self.tools.extend(agent.tools)
        if self.show_tool_calls:
            print(f"✓ Added team member '{agent.name}' to '{self.name}'")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent"""
        prompt_parts = []
        
        # Name and role
        prompt_parts.append(f"You are {self.name}, {self.role}.")
        
        if self.description:
            prompt_parts.append(f"\n{self.description}")
        
        # Instructions
        if self.instructions:
            prompt_parts.append("\n\nInstructions:")
            for instruction in self.instructions:
                prompt_parts.append(f"- {instruction}")
        
        # Team information - UPDATED FOR SEQUENTIAL WORK
        if self.team:
            prompt_parts.append("\n\nYou coordinate a team with these capabilities:")
            for member in self.team:
                prompt_parts.append(f"- {member.name} ({member.role}): Tools available - {', '.join([t.name for t in member.tools])}")
            
            prompt_parts.append("\n\nYou have DIRECT ACCESS to all team tools - use them in the order needed:")
            prompt_parts.append("1. If the task requires finding information first, use search tools")
            prompt_parts.append("2. If you get URLs from search, use web_scraper to read them")
            prompt_parts.append("3. Use multiple tool calls in sequence as needed")
            prompt_parts.append("4. Complete each step before moving to the next")
        
        # Tools information
        if self.tools:
            prompt_parts.append("\n\nYour available tools:")
            for tool in self.tools:
                prompt_parts.append(f"- {tool.name}: {tool.description}")
        
        return "".join(prompt_parts)
    
    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results"""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            tool_args = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            
            # Find the tool
            tool = next((t for t in self.tools if t.name == tool_name), None)
            
            if tool:
                if self.show_tool_calls:
                    print(f"\n🔧 Calling tool: {tool_name}")
                    print(f"   Arguments: {tool_args}")
                
                try:
                    result = tool.execute(**tool_args)
                    results.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": result,
                        "status": "success"
                    })
                    
                    if self.show_tool_calls:
                        print(f"   ✓ Result: {result}")
                        
                except Exception as e:
                    results.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "error": str(e),
                        "status": "error"
                    })
                    
                    if self.show_tool_calls:
                        print(f"   ✗ Error: {str(e)}")
            else:
                results.append({
                    "tool": tool_name,
                    "error": f"Tool '{tool_name}' not found",
                    "status": "error"
                })
        
        return results
    
    def _delegate_to_team(self, query: str) -> Optional[str]:
        """Delegate query to appropriate team member"""
        if not self.team:
            return None
        
        # Simple delegation based on role matching
        query_lower = query.lower()
        
        for member in self.team:
            role_keywords = member.role.lower().split()
            if any(keyword in query_lower for keyword in role_keywords):
                if self.show_tool_calls:
                    print(f"\n👥 Delegating to team member: {member.name}")
                return member.run(query)
        
        # If no specific match, use first team member
        return self.team[0].run(query)
    
    def run(
        self, 
        message: str, 
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        Run the agent with a message
        
        Args:
            message: User message
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Agent response
        """
        if not self.model:
            error_msg = "Error: No model configured for this agent"
            print(error_msg)
            return error_msg
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
            ]
            
            # Add conversation history
            messages.extend(self.conversation_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Generate response
            if stream:
                return self._stream_response(messages, **kwargs)
            else:
                return self._generate_response(messages, **kwargs)
        
        except Exception as e:
            error_msg = f"Error running agent: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def _generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a non-streaming response"""
        try:
            # Override temperature if set at agent level
            if self.temperature is not None:
                kwargs["temperature"] = self.temperature
            
            # Add tool configuration if tools are available
            if self.tools:
                kwargs["tools"] = [tool.to_openai_tool() for tool in self.tools]
                kwargs["tool_choice"] = "auto"
            
            if self.show_tool_calls:
                print(f"\n🔄 Generating response...")
            
            response = self.model.generate(messages, **kwargs)
            
            # Check if response is a dict (from API) or string (already processed)
            if isinstance(response, dict):
                # Handle function calling response
                if response.get("tool_calls"):
                    return self._handle_tool_calls(messages, response, **kwargs)
                else:
                    content = response.get("content", "")
            else:
                content = response
            
            # Update conversation history
            self.conversation_history.append(messages[-1])
            self.conversation_history.append({"role": "assistant", "content": content})
            
            return content
        
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def _handle_tool_calls(self, messages: List[Dict[str, str]], response: Dict, **kwargs) -> str:
        """Handle tool calls from the model with support for multiple rounds"""
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            tool_calls = response.get("tool_calls", [])
            
            if not tool_calls:
                # No more tool calls, return the content
                content = response.get("content", "") if isinstance(response, dict) else response
                return content if content else "No response generated"
            
            if self.show_tool_calls:
                print(f"\n🔧 Model requested {len(tool_calls)} tool call(s) (round {iteration})")
            
            # Execute tools
            tool_results = []
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                # Find and execute the tool
                tool = next((t for t in self.tools if t.name == function_name), None)
                
                if tool:
                    if self.show_tool_calls:
                        print(f"   Calling: {function_name}")
                        print(f"   Args: {function_args}")
                    
                    result = tool.execute(**function_args)
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": str(result)
                    })
                    
                    if self.show_tool_calls:
                        print(f"   Result: {result[:100]}...")
            
            # Add assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": response.get("content"),
                "tool_calls": tool_calls
            })
            
            # Add tool results
            for tool_result in tool_results:
                messages.append(tool_result)
            
            if self.show_tool_calls:
                print(f"\n🤔 Processing tool results...")
            
            # Get next response - WITHOUT tool parameter to prevent issues
            final_params = {k: v for k, v in kwargs.items() if k not in ['tools', 'tool_choice']}
            
            # Add tools back for the next call so model can make more tool calls if needed
            if self.tools:
                final_params["tools"] = [tool.to_openai_tool() for tool in self.tools]
                final_params["tool_choice"] = "auto"
            
            response = self.model.generate(messages, **final_params)
            
            # If response is just a string, we're done
            if isinstance(response, str):
                return response
            
            # If response is a dict but has no tool_calls, we're done
            if isinstance(response, dict) and not response.get("tool_calls"):
                return response.get("content", "")
            
            # Otherwise, loop continues to handle the next round of tool calls
        
        # Max iterations reached
        if self.show_tool_calls:
            print(f"\n⚠ Reached max iterations ({max_iterations})")
        
        return response.get("content", "") if isinstance(response, dict) else str(response)
    
    def _stream_response(self, messages: List[Dict[str, str]], **kwargs):
        """Generate a streaming response"""
        full_response = ""
        
        for chunk in self.model.stream(messages, **kwargs):
            full_response += chunk
            yield chunk
        
        # Update conversation history
        self.conversation_history.append(messages[-1])
        self.conversation_history.append({"role": "assistant", "content": full_response})
    
    def print_response(self, message: str, stream: bool = False, **kwargs) -> None:
        """
        Run the agent and print the response
        
        Args:
            message: User message
            stream: Whether to stream the response
            **kwargs: Additional parameters
        """
        try:
            if self.show_tool_calls:
                print(f"\n{'='*60}")
                print(f"Agent: {self.name}")
                print(f"Role: {self.role}")
                print(f"{'='*60}\n")
                print(f"Query: {message}\n")
            
            if stream:
                if self.show_tool_calls:
                    print("Response:\n")
                
                for chunk in self.run(message, stream=True, **kwargs):
                    print(chunk, end="", flush=True)
                print()  # New line at the end
            else:
                response = self.run(message, stream=False, **kwargs)
                
                if self.show_tool_calls:
                    print("Response:\n")
                
                print(response)
            
            if self.show_tool_calls:
                print(f"\n{'='*60}\n")
        
        except Exception as e:
            print(f"\n❌ Error in print_response: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
        self.tool_results.clear()
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "role": self.role,
            "model": str(self.model) if self.model else None,
            "tools": [tool.name for tool in self.tools],
            "team": [member.name for member in self.team],
            "instructions": self.instructions,
            "conversation_turns": len(self.conversation_history) // 2
        }
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', role='{self.role}', tools={len(self.tools)}, team={len(self.team)})"
