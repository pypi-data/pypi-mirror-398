# Evaluate
Want to evaluate your LLM? We offer a framework. Follow the steps below to evaluate your large language model.

> Reference: Tan, S., & Feng, M. (2025). How to use StataMCP improve your social science research? Shanghai Bayes Views Information Technology Co., Ltd.

Bibtex follows:
```bibtex
@techreport{tan2025stataMCP,
  author = {Tan, Song and Feng, Muyao},
  title = {Stata-MCP: A research report on AI-assisted empirical research},
  year = {2025},
  month = {September},
  day = {21},
  language = {English},
  address = {Shanghai, China},
  institution = {Shanghai Bayes Views Information Technology Co., Ltd.},
  url = {https://www.statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research}
}
```

## Step 1: Set your environment
Set api-key, base-url, and model-name
```bash
export OPENAI_API_KEY=<your-api-key>
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL=gpt-3.5-turbo
export CHAT-MODEL=gpt-3.5-turbo
export THINKING_MODEL=gpt-5

# For DeepSeek models (alternative)
export DEEPSEEK_API_KEY=<your-deepseek-api-key>
export DEEPSEEK_BASE_URL=<your-deepseek-base-url>
```

## Step 2: Run your evaluation task with AgentRunner

We provide a convenient `AgentRunner` class to help you execute tasks and extract results. The AgentRunner supports OpenAI-compatible APIs and can process Stata-related tasks automatically.

### Option A: Using AgentRunner (Recommended)

```python
from stata_mcp.evaluate import AgentRunner, ScoreModel

# Define your evaluation task
YOUR_TASK: str = ...

GIVEN_ANSWER: str = ...

# Initialize and run AgentRunner
runner = AgentRunner(
    model="gpt-3.5-turbo",  # or "deepseek-chat" for DeepSeek models
    api_key="your-api-key",
    base_url="https://api.openai.com/v1"  # or your DeepSeek base URL
)

# Execute the task
result = runner.run(YOUR_TASK)

# Extract conversation history and final answer
HIST_MSG = AgentRunner.get_processer(result)
FINAL_ANSWER = AgentRunner.get_final_result(result)

print(f"Conversation has {len(HIST_MSG)} items")
print(f"Final answer: {FINAL_ANSWER}")
```

### Option B: Manual Agent Setup

```python
# If you prefer to set up the agent manually
from openai import OpenAI
from agents import Agent, Runner

client = OpenAI(api_key="your-api-key")
agent = Agent(
    instructions="You are a helpful assistant specialized in Stata analysis.",
    model="gpt-3.5-turbo"
)

result = client.agent.run(agent, input=YOUR_TASK)
# Then extract data manually as needed
```

## Step 3: Evaluate with ScoreModel

Once you have the task results, use `ScoreModel` to evaluate the performance:

```python
from stata_mcp.evaluate import ScoreModel

# Convert conversation history to string format (required by ScoreModel)
hist_msg_str = "\n".join([
    f"{item['role']}: {item['content']}"
    for item in HIST_MSG
])

sm = ScoreModel(
    task=YOUR_TASK,
    reference_answer=GIVEN_ANSWER,
    processer=hist_msg_str,  # Now supports string format from conversation history
    results=FINAL_ANSWER,
    task_id="eval_001"  # Optional: set a unique ID for tracking
)

# Get the evaluation score
score = sm.score_it()
print(f"Evaluation Score: {score}")

# The ScoreModel evaluates:
# - Task completion accuracy
# - Quality of analysis
# - Statistical correctness
# - Clarity of explanation
```

## Advanced Usage

### Batch Evaluation

For evaluating multiple tasks:

```python
tasks = [
    {
        "task": "Analyze the relationship between education and income using census data",
        "reference": "Expected analysis includes correlation, regression, and policy implications"
    },
    {
        "task": "Conduct a difference-in-differences analysis of a policy intervention",
        "reference": "Should include pre/post comparison, control group, and statistical significance"
    }
]

runner = AgentRunner(model="gpt-3.5-turbo", api_key="your-api-key")
results = []

for i, task_data in enumerate(tasks):
    result = runner.run(task_data["task"])
    hist_msg = AgentRunner.get_processer(result)
    final_answer = AgentRunner.get_final_result(result)

    sm = ScoreModel(
        task=task_data["task"],
        reference_answer=task_data["reference"],
        processer="\n".join([f"{item['role']}: {item['content']}" for item in hist_msg]),
        results=final_answer,
        task_id=f"batch_eval_{i+1}"
    )

    score = sm.score_it()
    results.append({"task_id": f"batch_eval_{i+1}", "score": score})

print("Batch Evaluation Results:")
for result in results:
    print(f"Task {result['task_id']}: Score = {result['score']}")
```

### Custom Evaluation Criteria

You can extend the evaluation framework with custom metrics:

```python
# The AgentRunner provides structured data that can be used for custom evaluation
conversation_analysis = {
    "total_turns": len(HIST_MSG),
    "tool_usage_count": len([item for item in HIST_MSG if item["role"] == "tool"]),
    "has_stata_commands": any("stata" in item["content"].lower() for item in HIST_MSG),
    "final_answer_length": len(FINAL_ANSWER)
}

# Use these metrics alongside the ScoreModel score
print(f"Conversation Analysis: {conversation_analysis}")
```



