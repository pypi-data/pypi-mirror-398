# SCADNLP
[![PyPI version](https://badge.fury.io/py/scadnlp.svg)](https://badge.fury.io/py/scadnlp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/scadnlp.svg)](https://pypi.org/project/scadnlp/#history)
[![LinkedIn](https://img.shields.io/static/v1?label=LinkedIn&message=Eugene%20Evstafev&color=E335AB&logo=LinkedIn&logoColor=E335AB)](https://linkedin.com/in/)

**Natural Language to OpenSCAD Code Translator**

**Package Overview**

SCADNLP is a specialized tool designed to bridge the gap between casual text descriptions and precise, structured 3D modeling instructions for OpenSCAD, the powerful yet text-based CAD software. It takes natural language input, parses and refines the description using [llmatch-messages](https://pypi.org/project/llmatch-messages/), and generates clean, structured OpenSCAD code with embedded comments explaining key design choices.

**Example Workflow**

* Input: *"Design a minimalist wall clock with a curved dial, a wooden base, and subtle LED backlighting hints."*
* Output: Structured OpenSCAD code with:
	+ Parametric variables (e.g., `dial_radius = 50`, `base_thickness = 8`)
	+ Modular functions (e.g., `module curved_dial()`)
	+ Comments clarifying design trade-offs (e.g., `# LED hint: Low-poly approximation for simplicity`)
	+ Error handling for ambiguous terms (e.g., *"'wooden base' → assumed linear wood grain texture"*)


**Installation**
```bash
pip install scadnlp
```

**Usage**
```python
from scadnlp import scadnlp

user_input = "Design a minimalist wall clock with a curved dial, a wooden base, and subtle LED backlighting hints."
response = scadnlp(user_input)
print(response)
```
You can customize the LLM instance by passing your own instance as the `llm` parameter:
```python
from langchain_openai import ChatOpenAI
from scadnlp import scadnlp

llm = ChatOpenAI()
response = scadnlp(user_input, llm=llm)
```
Or, you can pass your own API key for LLM7 to increase the rate limits:
```python
import os

os.environ["LLM7_API_KEY"] = "your_api_key_here"
response = scadnlp(user_input)
```
**Author**

Eugene Evstafev (chigwell)

**Contact**

hi@euegne.plus

**Contributions**

Contributions are welcome! Please feel free to open a GitHub issue or create a pull request.

**License**

MIT License

**Acknowledgments**

SCADNLP uses the ChatLLM7 from [langchain_llm7](https://pypi.org/project/langchain_llm7/) by default. You can safely pass your own LLM instance for customization.

**Rate Limits**

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key for LLM7 by setting the `LLM7_API_KEY` environment variable or passing it directly as the `api_key` parameter.

**Getting a Free API Key**

Register at [token.llm7.io](https://token.llm7.io/) to get a free API key.

**GitHub Issues**

https://github.com/chigwell/scadnlp/issues