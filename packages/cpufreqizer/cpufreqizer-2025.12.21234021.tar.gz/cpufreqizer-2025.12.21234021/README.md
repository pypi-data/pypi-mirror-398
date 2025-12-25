# CPUFreqRizer
[![PyPI version](https://badge.fury.io/py/cpufreqizer.svg)](https://badge.fury.io/py/cpufreqizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/cpufreqizer)](https://pepy.tech/project/cpufreqizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

Balancing Power Efficiency and Performance with CPU Scaling Configuration
======================================

Overview
--------

CPUFreqRizer is a Python package that determines the optimal CPU scaling configuration for your system based on your workload. It takes user input, such as task type, expected load, and performance requirements, and generates a structured response with recommended CPU scaling policies.

## Installation

```bash
pip install cpufreqizer
```

## Overview of Functionality

CPUFreqRizer uses an LLM (Large Language Model) to generate a structured response with CPU scaling recommendations. The user provides details about their workload, and the package returns a list of recommended CPU scaling policies, including the appropriate governor and kernel parameters.

## Using the Package

```python
from cpufreqizer import cpufreqizer

response = cpufreqizer(user_input={"task_type": "cpu-intensive", "expected_load": 0.8, "performance_requirements": "high"})
```

### Default Behavior

By default, CPUFreqRizer uses the `llm7` LLM from the `langchain_llm7` package. This is a free-tier LLM with sufficient rate limits for most use cases. You can safely pass your own `llm` instance (based on [these docs](https://docs.languagedev.ai/)) if you want to use a different LLM. For example, to use the `openai` LLM:

```python
from langchain_openai import ChatOpenAI
from cpufreqizer import cpufreqizer

llm = ChatOpenAI()
response = cpufreqizer(user_input={"task_type": "cpu-intensive", "expected_load": 0.8, "performance_requirements": "high"}, llm=llm)
```

### Obtaining a Free API Key

To use a different LLM with a higher rate limit, you can obtain a free API key on the [llm7.io website](https://token.llm7.io/). You can then pass this API key via environment variable `LLM7_API_KEY` or directly to the `cpufreqizer` function:

```python
cpufreqizer(user_input={"task_type": "cpu-intensive", "expected_load": 0.8, "performance_requirements": "high"}, api_key="your_api_key")
```

## GitHub and Contact Information

You can find the source code for this package on [GitHub](https://github.com/chigwell/cpufreqizer).

If you have any questions or need help with using the package, please don't hesitate to reach out to me at [hi@euegne.plus](mailto:hi@euegne.plus).

## Citing the Package

If you use the `cpufreqizer` package in your research, please cite it as follows:

E. Evstafev, "CPUFreqRizer: A Python Package for Determining Optimal CPU Scaling Configuration"