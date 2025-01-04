import pytest
import asyncio
from unittest.mock import patch, AsyncMock

# Assuming your module is named 'your_module' and it contains the 'ask_gpt_result' function and 'SessionData' class.
from gpt import ask_gpt_result, SessionData

# Define a fixture for the mocked SessionData
@pytest.fixture
def mock_session_data():
    mock_session = AsyncMock(SessionData)
    mock_session.get_chat_history_as_string.return_value = "Customer: I bought an onigiri.\nClerk: Thank you."
    mock_session.mission.stringify_objectives_for_result.return_value = "1. Buy an onigiri\n2. Get a receipt"
    return mock_session

@pytest.mark.asyncio
async def test_ask_gpt_result(mock_session_data):
    expected_output = "1,0,1,1"

    with patch('your_module.ask_gpt', new=AsyncMock(return_value=expected_output)) as mock_ask_gpt:
        result = await ask_gpt_result(mock_session_data)
        assert result == expected_output
        mock_ask_gpt.assert_called_once()

# Run the test
if __name__ == "__main__":
    pytest.main()
