# How to write a task prompt?

> Catalog
> - [Introduction](#introduction)
> - [Prompt Deconstruction](#deconstructing-agent-prompts)
> - [An Example](#powerful-example)
> - [Prompt Generator Usage](#prompt-generator)

## Introduction
As we know, good prompts can produce good results. [OpenAI](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf), [Google](https://services.google.com/fh/files/misc/gemini-for-google-workspace-prompting-guide-101.pdf), and Anthropic have all released tutorials on how to write effective prompts.

### OpenAI
- main: [OpenAI](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
- 2025.08.07: [OpenAI/gpt-5-prompting-guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide)
- 2025.04.14: [OpenAI/gpt-4.1-prompting-guide](https://cookbook.openai.com/examples/gpt4-1_prompting_guide)

### Google
- [Google/what-is-prompt-engineering](https://cloud.google.com/discover/what-is-prompt-engineering)
- [Google/gemini-prompting-strategies](https://services.google.com/fh/files/misc/1_vertex_ai_gemini_prompting_strategies.pdf)
- [Google/multimodal-prompting](https://services.google.com/fh/files/misc/2_vertex_ai_gemini_multimodal_prompting.pdf)
- [Google/prompting-guide-101](https://services.google.com/fh/files/misc/gemini-for-google-workspace-prompting-guide-101.pdf), I think it is the best one.

### Anthropic
- [Anthropic/prompt-eng-interactive-tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial)
- [Anthropic/claude-docs](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview)

### Others
> The following resources are in Chinese. If you are not Chinese, I would recommend reading the prompt engineering tutorials published by OpenAI and Google instead.  
> 下面的为中文内容，如果你擅长英语，建议阅读OpenAI和Google发出的原文档，这会更有收获。

- [飞书/元神智算](https://fcn1zeymybeg.feishu.cn/wiki/OtOhwTzsPiE0z5kCGmFcWaaXnrf)
- [Twitter/宝玉](https://x.com/dotey/status/1903833401582346601)
- ...

More information you can search on website or let LLMs help you find something news.

## Deconstructing Agent Prompts
### Overview
Taking the Agent in this project as an example, in the simplest agent implementation we can break down the prompt into two parts: instructions and agent input (here we refer to it as tasks for better clarity).  
Instructions are the system-level tasks descriptions provided to the agent during construction, mainly covering its capabilities, how it should carry out work, what it should and should not do, and when to stop. Tasks, on the other hand, is closer to a concrete work assignment—imagine the kind of assignment your advisor gives you; that is what tasks resembles. More specifically:

### Instructions
Instructions can be considered as the system prompts for the Agent, which concentrate on the expectations and requirements for the Agent. They typically include the following core elements:

1. **Role Definition** - Clarify the Agent's identity and professional domain
   - "You are a professional Stata data analysis expert"
   - "You are skilled in statistical analysis and data visualization"

2. **Capability Scope** - Describe the types of tasks the Agent can perform
   - "Able to conduct descriptive statistics, regression analysis, hypothesis testing"
   - "Able to generate statistical charts and reports"

3. **Behavioral Norms** - Specify how the Agent should work
   - "Follow scientific research processes for data analysis"
   - "Ensure the accuracy and reproducibility of analysis results"

4. **Constraints** - Clearly define what the Agent should not do
   - "Do not modify original data files"
   - "Do not delete variables without sufficient justification"

5. **Output Requirements** - Specify the format and content of final deliverables
   - "All results must be saved to the specified directory"
   - "Generate detailed code comments and explanations"

Instructions are usually relatively stable and generic, and do not change frequently with specific tasks.

### Tasks
Tasks are specific task descriptions, equivalent to concrete work instructions for the Agent. They typically include the following key information:

1. **Data Sources** - Specify the data files used for analysis
   - `datas="~/data/analysis.dta"`
   - `datas="Use Stata's built-in auto dataset"`

2. **Research Objectives** - Clearly define the purpose and questions of the analysis
   - `aims="Explore the relationship between variable a and variable b"`
   - `aims="Compare differences in variable c across different groups"`

3. **Data Description** - Provide basic information about the data (optional)
   - `datas_describe="Includes variables a, b, c; sample size about 1000"`
   - `datas_describe="Panel data with time span from 2010 to 2020"`

4. **Deliverables** - Specify the content that needs to be produced
   - `deliverables="Regression result tables and visualization charts required"`
   - `deliverables="Generate detailed statistical reports and code files"`

5. **Output Path** - Specify where results should be saved
   - `root="~/Downloads/analysis_results"`

Tasks are usually specific and variable, and may differ each time a task is executed. They are designed based on the capability scope defined in Instructions to create specific analysis tasks.

### Difference
The core differences between Instructions and Tasks lie in their abstraction levels, stability, and scope of application:

| Dimension | Instructions | Tasks |
|-----------|--------------|-------|
| **Abstraction Level** | High-level, generic | Specific, targeted |
| **Stability** | Relatively stable, rarely changed | May differ with each task |
| **Scope** | Defines Agent's "capabilities" | Defines specific "work" |
| **Analogy** | Like an employee's job description | Like a specific project assignment |
| **Content Focus** | Defines "what can be done", "what cannot be done" | Defines "what to do this time" |

**Specific Differences:**

1. **Different Levels of Abstraction**
   - Instructions: "You are a data analysis expert capable of regression analysis and visualization"
   - Tasks: "Please analyze the relationship between variables a and b in data.dta, generate regression results and scatter plots"

2. **Different Update Frequencies**
   - Instructions: Once set, usually remain unchanged throughout the project lifecycle
   - Tasks: Need to be redefined each time a new task is executed

3. **Different Targets of Action**
   - Instructions: Act on the Agent's "identity" and "capabilities"
   - Tasks: Act on specific "task execution"


## Powerful Example
### ReAct (Reasoning and Action)

**Instructions**:
```markdown
You are a Stata data analysis expert. You will analyze data using the ReAct (Reasoning and Action) framework:

1. **Think**: Reason step-by-step about the problem before taking action
2. **Act**: Execute Stata commands based on your reasoning
3. **Observe**: Check the results and adjust your approach if needed

Capabilities:
- Perform descriptive statistics, regression analysis, hypothesis testing
- Generate data visualizations and summary tables
- Handle missing data and data cleaning

Constraints:
- Do not modify original data files
- Save all results to the specified output directory
- Provide detailed explanations for each analysis step

Output Requirements:
- Save all Stata code in .do files
- Generate summary reports in .txt or .md format
- Export visualizations as .png or .pdf files
```

**Tasks**:
```markdown
Data Source: ~/data/auto.dta
Research Objective: Analyze the relationship between car price (price) and car weight (weight), and examine how this relationship differs by car origin (foreign)

Data Description: This dataset contains information about 74 cars, including price, weight, mpg, and origin (domestic/foreign)

Deliverables:
- Descriptive statistics for all variables
- Scatter plot of price vs weight with regression line
- Regression analysis of price on weight, controlling for origin
- Comparison of regression coefficients between domestic and foreign cars

Output Path: ~/Downloads/auto_analysis/
```

**Analysis of Instructions and Tasks:**

**Strengths:**
- **Instructions**: Clear role definition, structured ReAct framework, comprehensive capability scope, appropriate constraints
- **Tasks**: Specific research question, well-defined deliverables, clear data source and output path

**Weaknesses:**
- **Instructions**: Could be more specific about error handling and validation steps
- **Tasks**: Missing information about expected statistical significance levels or confidence intervals

**Core Information Elements:**

1. **Task Description**: The ReAct framework provides a structured approach for agents to reason before acting, ensuring more reliable and explainable results. This is crucial for data analysis where each step should be justified and reproducible.

2. **Clear Role Definition**: Instructions establish the agent as a "Stata data analysis expert" with specific capabilities, setting appropriate expectations for the quality and type of analysis.

3. **Structured Workflow**: The Think-Act-Observe cycle ensures systematic problem-solving rather than random trial-and-error, leading to more robust analysis outcomes.

4. **Comprehensive Deliverables**: Tasks specify multiple output types (code, reports, visualizations) ensuring complete documentation of the analysis process.

5. **Data Protection**: Constraints prevent modification of original data files, ensuring data integrity and reproducibility of analysis.

### Co-Work
Collaborative Working Patterns between Instructions and Tasks:

**Collaborative Mechanisms:**
- **Instructions Provide Framework**: Define the Agent's capability boundaries and behavioral norms
- **Tasks Provide Specific Content**: Specify concrete work tasks within the Instructions framework
- **Mutual Constraints**: Tasks cannot exceed the capability scope defined in Instructions

**Practical Application Scenarios:**

1. **Multi-Task Reuse**:
   - The same set of Instructions can be used for multiple different Tasks
   - Example: Data analysis expert Instructions can be used for regression analysis, descriptive statistics, visualization, and other Tasks

2. **Progressive Optimization**:
   - Optimize Instructions based on Task execution results
   - Example: If the Agent performs poorly in a certain area, adjust the capability descriptions in Instructions

3. **Modular Design**:
   - Instructions can be designed as pluggable modules
   - Example: Basic analysis Instructions + Advanced statistics Instructions + Visualization Instructions

**Best Practices:**
- Keep Instructions relatively stable and avoid frequent modifications
- Design Tasks considering the capability scope defined in Instructions
- Validate and optimize Instructions accuracy through Task execution results

## Prompt Generator
### Overview
To lower the threshold for writing prompts and ensure the stability of generated results, this project implements a rule-driven prompt generator (PromptGenerator) based on current best practices. You do not need to manually write complex prompts. Instead, by selecting a template and passing in the necessary parameters, you can quickly generate prompts that conform to the ReAct or other structures. This approach not only improves reusability but also significantly reduces debugging time.

### Why Generator?
- Stability: The templates we have debugged have been validated in multiple scenarios, avoiding common errors. 
- Ease of use: No need to master the details of prompt engineering—just provide data and tasks directly. 
- Flexibility: Supports multiple templates (such as ReAct, Common, etc.), and new templates can be extended as needed. 
- Controllability: Through parameter configuration, users can easily control the language, output path, template content, and more.


### Templates
- ReAct (default): A LangChain prompt based on hwchase17/react, suitable for agents that require the think + act cycle. 
- Common (currently disabled): Custom template mode, where users need to provide instructions_template and tasks_template. Suitable for DIY use. 
- CoT (in development): Chain-of-Thought mode, supporting step-by-step reasoning.

### How to Use
1. Initialize generator
    ```python
    from prompt_generator import PromptGenerator
    
    # Initialize generator
    generator = PromptGenerator(
        template_name="ReAct",      # Optional: ReAct, Common, CoT
        language="English",         # Output language, can also be "Chinese", etc.
        agent_provider="openai",    # Optional: openai or langchain, depending on your agent type
        ROOT="~/Downloads/StataAgent"  # Global output path, optional; default is ~/Downloads/StataAgent
    )
    ```

2. Generate Instructions
    ```python
    instructions = generator.instructions(
        root="~/Downloads/StataAgent"  # Optional, specify global output path
    )
    print(instructions)
    ```

3. Generate Tasks  
    Tasks are used to generate concrete task descriptions, emphasizing data sources, research goals, and final deliverables.
    ```python
    tasks = generator.tasks(
        datas="~/Downloads/StataAgent/data.dta",   # Required: data path
        aims="Explore the relationship between a and b",  # Required: research goal
        datas_describe="Includes variables a, b, c; sample size about 1000",   # Optional: data description
        deliverables="Regression result tables and visualization figures required",   # Optional: deliverables description
        root="~/Downloads/StataAgent/results"      # Optional: output path
    )
    print(tasks)
    ```

4. Minimal Example
    ```python
    from prompt_generator import PromptGenerator
    
    generator = PromptGenerator()
    
    instructions = generator.instructions()
    tasks = generator.tasks(
        datas="use Stata default data",  # you can use natural language to set teh paths of data.
        aims="Explore the relationship between a and b"
    )
    
    print(instructions)
    print(tasks)
    ```

