# Experiment Configuration Agent for AutoGluon

This agent uses a Large Language Model to recommend optimal configurations for AutoGluon's `TabularPredictor` based on your machine learning problem context. By providing details about your domain, use case, and dataset, the agent will generate a set of `TabularPredictor` parameters designed to optimize for performance and efficiency.

## Features

-   **Intelligent Configuration:** Leverages LLMs to recommend `eval_metric`, `presets`, `time_limit`, and ensembling parameters.
-   **Context-Aware:** Considers the business domain, specific use case, ML methodology (e.g., classification, regression), and dataset characteristics.
-   **Flexible Backend:** Powered by `sfn-blueprint`, allowing for a configurable LLM backend.
-   **Multiple Scenarios:** Provides recommendations for different optimization goals, such as maximizing accuracy, balancing performance and speed, or fast prototyping.

## Installation

This project uses `uv` for dependency management and requires Python 3.10 or higher.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/stepfnAI/experiment_config_agent.git
    cd experiment-configuration-agent
    ```

2.  **Set up the environment and install dependencies:**
    It is recommended to use a virtual environment. `uv` can create one for you.
    ```bash
    # Create a virtual environment and install dependencies
    uv sync --extra dev
     source .venv/bin/activate
    ```

## Usage

### Basic usage
```python
python ./examples/basic_usage.py
```

To get a configuration recommendation, instantiate the `AutoGluonConfigAgent` and pass a dictionary containing the problem context.

1.  **Create a `.env` file** in the project root to configure the LLM provider. See the [Configuration](#configuration) section for more details.

    ```
    PROVIDER="openai"
    MODEL="gpt-4-turbo"
    # Add your API key, e.g., OPENAI_API_KEY="sk-..."
    ```

2.  **Create your Python script:**

    ```python
    from experiment_configuration_agent.agent import AutoGluonConfigAgent

    # 1. Define the problem context
    task_data = {
        "domain": {
            "name": "Manufacturing",
            "description": "An automotive parts manufacturing facility with multiple production lines."
        },
        "use_case": {
            "name": "Predictive Maintenance",
            "description": "Detect unusual temporal patterns in sensor data to predict equipment failure and prevent breakdowns."
        },
        "methodology": "binary_classification",
        "dataset_insights": {
            "num_samples": 5000,
            "num_features": 10,
            "target": {
                "name": "failure_flag",
                "imbalance_ratio": 0.05 # Highly imbalanced
            },
            "feature_summary": {
                "sensor_A": {"min": 0.1, "max": 100.5, "dtype": "float"},
                "production_line_id": {"unique_count": 3, "dtype": "category"}
            }
        }
    }

    # 2. Initialize the agent
    agent = AutoGluonConfigAgent()

    # 3. Get the configuration recommendation
    result = agent(task_data)

    # 4. Print the result
    print("Recommended AutoGluon Configuration:")
    print(result.get("configuration"))
    print("\nCost Summary:")
    print(result.get("cost_summary"))

    ```

## Configuration

The agent is configured via environment variables, which can be placed in a `.env` file in the project root. The primary configurations are inherited from the `GluonConfig` class.

-   `PROVIDER`: The LLM provider to use (e.g., `"openai"`, `"anthropic"`).
-   `MODEL`: The specific model to use (e.g., `"gpt-4-turbo"`, `"claude-3-opus-20240229"`).
-   `TEMPERATURE`: The model's temperature setting (e.g., `0.3`).
-   `MAX_TOKENS`: The maximum number of tokens for the response (e.g., `4000`).

You will also need to set the API key for your chosen provider, for example `OPENAI_API_KEY="your-key-here"`.

## Testing

This project uses `pytest`. To run the test suite, execute the following command from the project root:

```bash
pytest
```
