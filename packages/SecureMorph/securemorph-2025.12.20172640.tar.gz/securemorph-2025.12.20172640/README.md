# SecureMorph

SecureMorph is a Python package designed to process and validate text inputs related to advanced security protocols, such as secrets erasure upon observation. It utilizes structured pattern matching with regex to interpret user instructions, verify system behaviors—including formal verification results—and produce clear, structured summaries of the security mechanisms involved. This tool enables organizations to automate the validation, documentation, and analysis of complex security models, ensuring sensitive information remains protected under specified observable conditions through verified and repeatable procedures.

## Installation

Install SecureMorph via pip:

```bash
pip install SecureMorph
```

## Usage

Here's an example of how to use SecureMorph in your Python projects:

```python
from SecureMorph import SecureMorph

# Example input string
user_input = "Verify that secrets are erased when observed."

# Call the function
result = SecureMorph(user_input)

# Output the extracted data or verification results
print(result)
```

### Customizing the Language Model

SecureMorph defaults to using the ChatLLM7 model from `langchain_llm7`, which can be installed from [PyPI](https://pypi.org/project/langchain-llm7/). You can also pass your own LLM instance if desired:

```python
from langchain_llm7 import YourCustomLLM

my_llm = YourCustomLLM()
result = SecureMorph(user_input, llm=my_llm)
```

### API Keys and Rate Limits

For higher rate limits or access to the LLM7 API, you can:

- Set your API key as an environment variable `LLM7_API_KEY`.
- Or pass it directly in the function call:

```python
result = SecureMorph(user_input, api_key="your_api_key_here")
```

You can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Configuration

- The default LLM is ChatLLM7 from `langchain_llm7`.
- You may specify a different LLM instance for custom integrations.
- The API key must be provided for API access if not using the default setup.

## Issues

For bugs, feature requests, or support, please open an issue on GitHub:  
[https://github.com/yourusername/SecureMorph/issues](https://github.com/yourusername/SecureMorph/issues)

## Author

Eugene Evstafev  
Email: hi@euegne.plus

## License

This project is licensed under the MIT License.