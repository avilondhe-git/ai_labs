"""
Test Suite for Azure AI Agent POC
Purpose: Comprehensive tests for agent, tools, and API endpoints
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================
# TOOL TESTS
# ============================================

def test_search_tool_initialization():
    """Test search tool initializes correctly"""
    from src.tools.search_tool import SearchTool
    
    with patch('src.tools.search_tool.settings') as mock_settings:
        mock_settings.tavily_api_key = None
        tool = SearchTool()
        assert tool.client is None
        
        mock_settings.tavily_api_key = "test-key"
        tool = SearchTool()
        assert tool.client is not None


def test_email_tool_initialization():
    """Test email tool initializes correctly"""
    from src.tools.email_tool import EmailTool
    
    with patch('src.tools.email_tool.settings') as mock_settings:
        mock_settings.sendgrid_api_key = None
        tool = EmailTool()
        assert tool.client is None
        
        mock_settings.sendgrid_api_key = "test-key"
        tool = EmailTool()
        assert tool.client is not None


def test_data_tool_csv_analysis():
    """Test data analysis tool with CSV data"""
    from src.tools.data_tool import DataAnalysisTool
    
    tool = DataAnalysisTool()
    
    csv_data = """name,age,salary
John,30,50000
Jane,25,60000"""
    
    result = tool.analyze_csv(csv_data, analysis_type="summary")
    
    assert result["success"] is True
    assert result["rows"] == 2
    assert result["columns"] == 3
    assert "name" in result["column_names"]


def test_data_tool_statistics():
    """Test statistics calculation"""
    from src.tools.data_tool import DataAnalysisTool
    
    tool = DataAnalysisTool()
    numbers = [10, 20, 30, 40, 50]
    
    result = tool.calculate_statistics(numbers)
    
    assert result["success"] is True
    assert result["mean"] == 30.0
    assert result["median"] == 30.0
    assert result["count"] == 5


# ============================================
# MEMORY TESTS
# ============================================

@pytest.mark.asyncio
async def test_conversation_memory_save_message():
    """Test saving messages to memory"""
    from src.memory.conversation_memory import ConversationMemory
    
    with patch('src.memory.conversation_memory.CosmosClient'):
        memory = ConversationMemory()
        
        # Mock container
        memory.container = Mock()
        memory.container.upsert_item = Mock(return_value={"id": "test-msg-1"})
        
        result = memory.save_message("session-1", "user", "Hello")
        
        assert memory.container.upsert_item.called
        assert result["id"] == "test-msg-1"


@pytest.mark.asyncio
async def test_conversation_memory_get_history():
    """Test retrieving conversation history"""
    from src.memory.conversation_memory import ConversationMemory
    
    with patch('src.memory.conversation_memory.CosmosClient'):
        memory = ConversationMemory()
        
        # Mock container
        mock_messages = [
            {"id": "1", "session_id": "s1", "role": "user", "content": "Hi"},
            {"id": "2", "session_id": "s1", "role": "assistant", "content": "Hello"}
        ]
        memory.container = Mock()
        memory.container.query_items = Mock(return_value=mock_messages)
        
        history = memory.get_conversation_history("s1")
        
        assert len(history) == 2
        assert history[0]["role"] == "user"


# ============================================
# AGENT TESTS
# ============================================

@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initializes with all components"""
    from src.agents.base_agent import BaseAgent
    
    with patch('src.agents.base_agent.ConversationMemory'), \
         patch('src.agents.base_agent.settings') as mock_settings:
        
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_api_key = "test-key"
        mock_settings.azure_openai_deployment = "gpt-4o-mini"
        
        agent = BaseAgent(session_id="test-session")
        
        assert agent.session_id == "test-session"
        assert agent.search_tool is not None
        assert agent.email_tool is not None
        assert agent.data_tool is not None


@pytest.mark.asyncio
async def test_agent_process_task():
    """Test agent processes task and returns response"""
    from src.agents.base_agent import BaseAgent
    
    with patch('src.agents.base_agent.ConversationMemory'), \
         patch('src.agents.base_agent.settings') as mock_settings, \
         patch('src.agents.base_agent.Kernel') as mock_kernel:
        
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_api_key = "test-key"
        mock_settings.azure_openai_deployment = "gpt-4o-mini"
        
        # Mock kernel response
        mock_response = Mock()
        mock_response.__str__ = lambda self: "Test response"
        mock_response.tool_calls = []
        
        agent = BaseAgent(session_id="test-session")
        agent.kernel.get_service = Mock(return_value=Mock(
            get_chat_message_content=AsyncMock(return_value=mock_response)
        ))
        
        result = await agent.process_task("Test task")
        
        assert result["success"] is True
        assert result["session_id"] == "test-session"


# ============================================
# API TESTS
# ============================================

@pytest.mark.asyncio
async def test_api_root_endpoint():
    """Test root endpoint returns health info"""
    from httpx import AsyncClient
    from src.app import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Azure AI Agent"
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_create_session():
    """Test session creation endpoint"""
    from httpx import AsyncClient
    from src.app import app
    
    with patch('src.app.BaseAgent'):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/session/create")
            
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert data["message"] == "Session created successfully"


@pytest.mark.asyncio
async def test_api_process_task():
    """Test task processing endpoint"""
    from httpx import AsyncClient
    from src.app import app
    
    with patch('src.app.BaseAgent') as mock_agent_class:
        # Mock agent instance
        mock_agent = Mock()
        mock_agent.process_task = AsyncMock(return_value={
            "success": True,
            "response": "Test response",
            "tool_calls": []
        })
        mock_agent_class.return_value = mock_agent
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/agent/task",
                json={"task": "Test task", "session_id": "test-session"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["response"] == "Test response"


@pytest.mark.asyncio
async def test_api_health_check():
    """Test health check endpoint"""
    from httpx import AsyncClient
    from src.app import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_sessions" in data


# ============================================
# INTEGRATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_end_to_end_agent_workflow():
    """Test complete workflow: session -> task -> history"""
    from httpx import AsyncClient
    from src.app import app
    
    with patch('src.app.BaseAgent') as mock_agent_class:
        # Mock agent with conversation history
        mock_agent = Mock()
        mock_agent.process_task = AsyncMock(return_value={
            "success": True,
            "response": "Task completed",
            "tool_calls": []
        })
        mock_agent.memory.get_conversation_history = Mock(return_value=[
            {"role": "user", "content": "Test task"},
            {"role": "assistant", "content": "Task completed"}
        ])
        mock_agent_class.return_value = mock_agent
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session
            create_response = await client.post("/session/create")
            session_id = create_response.json()["session_id"]
            
            # Process task
            task_response = await client.post(
                "/agent/task",
                json={"task": "Test task", "session_id": session_id}
            )
            assert task_response.status_code == 200
            
            # Get history
            history_response = await client.get(f"/session/{session_id}/history")
            assert history_response.status_code == 200
            history_data = history_response.json()
            assert len(history_data["messages"]) == 2


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
