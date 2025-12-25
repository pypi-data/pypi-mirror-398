
from sfn_blueprint import BaseLangChainAgent
from .config import GluonConfig
from .constants import format_autogluon_config_prompt
from .models import AutoGluonConfig
from typing import Dict, Any, Tuple, Optional
import logging


class AutoGluonConfigAgent(BaseLangChainAgent):
    def __init__(self, config: Optional[GluonConfig] = None):
        super().__init__(config or GluonConfig())

    def configure_training(
        self, 
        domain: Dict[str, str], 
        use_case: Dict[str, str], 
        methodology: str, 
        dataset_insights: Dict[str, Any]
    ) :
        """
        Generates an AutoGluon configuration based on domain context and data insights.
        """

        system_prompt, user_prompt = format_autogluon_config_prompt(
            domain=domain, 
            use_case=use_case, 
            methodology=methodology, 
            dataset_insights=dataset_insights
        )

        response, cost_summary = self.route_with_langchain(
            system_prompt, 
            user_prompt, 
            AutoGluonConfig
        )

        return response, cost_summary

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper to execute via standard task dictionary interface.
        """

        config_recommendation, cost = self.configure_training(
            domain=task_data["domain"],
            use_case=task_data["use_case"],
            methodology=task_data["methodology"],
            dataset_insights=task_data["dataset_insights"]
        )

        return {
            "configuration": config_recommendation.model_dump(),
            "cost_summary": cost
        }
    def __call__(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute_task(task_data)