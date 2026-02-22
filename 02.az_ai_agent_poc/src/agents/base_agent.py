"""
Base Agent using Semantic Kernel
Purpose: Core agent logic with ReAct loop and tool use
"""

from typing import List, Dict, Optional
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelFunction

from config.config import settings
from config.logger import app_logger as logger
from src.memory.conversation_memory import ConversationMemory
from src.tools.search_tool import SearchTool
from src.tools.email_tool import EmailTool
from src.tools.data_tool import DataAnalysisTool


class BaseAgent:
    """
    AI Agent with tool use capabilities
    
    WHY: Semantic Kernel provides:
         - Built-in function calling (tool use)
         - Plugin system for tools
         - Automatic prompt management
         - Native Azure OpenAI integration
    """
    
    def __init__(self, session_id: str):
        """
        Initialize agent
        
        Args:
            session_id: Unique session identifier
        """
        
        self.session_id = session_id
        self.memory = ConversationMemory()
        
        # Initialize Semantic Kernel
        self.kernel = Kernel()
        
        # WHY: Azure OpenAI service configuration
        service_id = "chat_completion"
        self.kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
                deployment_name=settings.azure_openai_deployment,
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key
            )
        )
        
        # Initialize tools
        self.search_tool = SearchTool()
        self.email_tool = EmailTool()
        self.data_tool = DataAnalysisTool()
        
        # Register tools as plugins
        self._register_tools()
        
        # Chat history
        self.chat_history = ChatHistory()
        
        # Load previous conversation
        self._load_conversation_history()
        
        logger.info(f"Agent initialized for session {session_id}")
    
    def _register_tools(self):
        """Register tools as Semantic Kernel plugins"""
        
        # WHY: Semantic Kernel plugins make functions available to LLM
        
        # Search tool
        @self.kernel.function(
            name="search_web",
            description="Search the web for current information"
        )
        def search_web(query: str, max_results: int = 5) -> str:
            result = self.search_tool.search(query, max_results)
            if result["success"]:
                # Format for LLM consumption
                answer = result.get("answer", "")
                sources = "\n".join([
                    f"- {r['title']}: {r['content'][:100]}..."
                    for r in result["results"][:3]
                ])
                return f"Answer: {answer}\n\nTop Sources:\n{sources}"
            else:
                return f"Search failed: {result['error']}"
        
        # Email tool
        @self.kernel.function(
            name="send_email",
            description="Send an email to a recipient"
        )
        def send_email(to_email: str, subject: str, body: str) -> str:
            result = self.email_tool.send_email(to_email, subject, body)
            if result["success"]:
                return result["message"]
            else:
                return f"Email failed: {result['error']}"
        
        # Data analysis tool
        @self.kernel.function(
            name="analyze_data",
            description="Analyze CSV data and generate insights"
        )
        def analyze_data(csv_data: str, analysis_type: str = "summary") -> str:
            result = self.data_tool.analyze_csv(csv_data, analysis_type)
            if result["success"]:
                return f"Analysis complete. Rows: {result['rows']}, Columns: {result['columns']}"
            else:
                return f"Analysis failed: {result['error']}"
        
        logger.info("Tools registered as plugins")
    
    def _load_conversation_history(self):
        """Load previous conversation from memory"""
        
        history = self.memory.get_conversation_history(self.session_id, limit=10)
        
        for msg in history:
            if msg["role"] == "user":
                self.chat_history.add_user_message(msg["content"])
            elif msg["role"] == "assistant":
                self.chat_history.add_assistant_message(msg["content"])
        
        if history:
            logger.info(f"Loaded {len(history)} messages from history")
    
    async def process_task(self, task: str) -> Dict:
        """
        Process a user task using agent with tools
        
        Args:
            task: User task/question
            
        Returns:
            Dictionary with response and metadata
        """
        
        logger.info(f"Processing task: {task}")
        
        # Save user message
        self.memory.save_message(self.session_id, "user", task)
        self.chat_history.add_user_message(task)
        
        try:
            # WHY: FunctionCallBehavior.AutoInvokeKernelFunctions enables automatic tool calling
            execution_settings = {
                "function_call_behavior": FunctionCallBehavior.AutoInvokeKernelFunctions()
            }
            
            # Get chat completion service
            chat_service = self.kernel.get_service(type=ChatCompletionClientBase)
            
            # WHY: get_chat_message_content handles multi-turn conversation with tool calls
            response = await chat_service.get_chat_message_content(
                chat_history=self.chat_history,
                settings=execution_settings,
                kernel=self.kernel
            )
            
            answer = str(response)
            
            # Save assistant response
            self.memory.save_message(self.session_id, "assistant", answer)
            self.chat_history.add_assistant_message(answer)
            
            # Extract tool calls if any
            tool_calls = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_calls.append({
                        "tool": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })
            
            logger.info(f"Task completed. Tools used: {len(tool_calls)}")
            
            return {
                "success": True,
                "response": answer,
                "tool_calls": tool_calls,
                "session_id": self.session_id
            }
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            error_msg = f"I encountered an error: {str(e)}"
            self.memory.save_message(self.session_id, "assistant", error_msg)
            
            return {
                "success": False,
                "response": error_msg,
                "error": str(e)
            }
    
    def clear_history(self):
        """Clear conversation history"""
        self.chat_history = ChatHistory()
        self.memory.clear_session(self.session_id)
        logger.info(f"Cleared history for session {self.session_id}")


# ====================
# USAGE EXAMPLE
# ====================
async def main():
    print("\n🤖 Testing AI Agent...")
    
    agent = BaseAgent(session_id="test-agent-001")
    
    # Test tasks
    tasks = [
        "What is the weather in Seattle?",
        "Search for latest AI agent developments in 2025",
        "Calculate the average of these numbers: 10, 20, 30, 40, 50"
    ]
    
    for task in tasks:
        print(f"\n{'='*80}")
        print(f"Task: {task}")
        print('='*80)
        
        result = await agent.process_task(task)
        
        if result["success"]:
            print(f"\nResponse: {result['response']}")
            if result.get("tool_calls"):
                print(f"\nTools used:")
                for tool_call in result["tool_calls"]:
                    print(f"  - {tool_call['tool']}")
        else:
            print(f"\n✗ Error: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
