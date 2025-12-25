import pytest
from unittest.mock import patch, MagicMock
from experiment_config_agent.agent import AutoGluonConfigAgent
from experiment_config_agent.models import AutoGluonConfig

@pytest.fixture
def agent():
    """Fixture to create an AutoGluonConfigAgent instance."""
    return AutoGluonConfigAgent()

@pytest.fixture
def task_data():
    """Fixture to provide sample task data."""
    return {
        "domain": {"name": "Finance", "description": "Credit scoring"},
        "use_case": {"name": "Loan Default Prediction", "description": "Predict if a customer will default on a loan"},
        "methodology": "binary_classification",
        "dataset_insights": {"samples": 10000, "features": 15}
    }

def test_configure_training(agent, task_data):
    """Test the configure_training method."""
    mock_response = AutoGluonConfig(
        eval_metric='f1',
        preset='high_quality',
        additional_metrics=['roc_auc', 'accuracy'],
        time_limit=3600,
        num_bag_folds=5,
        num_bag_sets=1,
        num_stack_levels=1
    )
    mock_cost = {"total_cost": 0.05}

    with patch.object(AutoGluonConfigAgent, 'route_with_langchain', return_value=(mock_response, mock_cost)) as mock_route:
        response, cost_summary = agent.configure_training(
            domain=task_data["domain"],
            use_case=task_data["use_case"],
            methodology=task_data["methodology"],
            dataset_insights=task_data["dataset_insights"]
        )

        assert response == mock_response
        assert cost_summary == mock_cost
        mock_route.assert_called_once()
        system_prompt, user_prompt, model = mock_route.call_args[0]
        assert "You are an expert AutoGluon configuration advisor" in system_prompt
        assert "DOMAIN INFORMATION" in user_prompt


def test_execute_task(agent, task_data):
    """Test the execute_task method."""
    mock_config = AutoGluonConfig(
        eval_metric='f1',
        preset='good_quality',
        additional_metrics=['accuracy'],
        time_limit=600,
        num_bag_folds=0,
        num_bag_sets=0,
        num_stack_levels=0
    )
    mock_cost = {"total_cost": 0.02}
    
    expected_config_dump = mock_config.model_dump()

    with patch.object(AutoGluonConfigAgent, 'configure_training', return_value=(mock_config, mock_cost)) as mock_configure:
        result = agent.execute_task(task_data)

        mock_configure.assert_called_once_with(
            domain=task_data["domain"],
            use_case=task_data["use_case"],
            methodology=task_data["methodology"],
            dataset_insights=task_data["dataset_insights"]
        )
        
        assert "configuration" in result
        assert "cost_summary" in result
        assert result["configuration"] == expected_config_dump
        assert result["cost_summary"] == mock_cost

def test_call_method(agent, task_data):
    """Test that the __call__ method invokes execute_task."""
    mock_result = {
        "configuration": {"eval_metric": "f1"},
        "cost_summary": {"total_cost": 0.01}
    }
    with patch.object(AutoGluonConfigAgent, 'execute_task', return_value=mock_result) as mock_execute:
        result = agent(task_data)
        mock_execute.assert_called_once_with(task_data)
        assert result == mock_result
