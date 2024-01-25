This project is meant to process a conversation transcript between a customer support agent and customer with OpenAI's API and intelligently create a new bug fix or feature request issue or comment on an existing issue in Linear.

To run the project:
1. Install necessary dependencies
2. Set following API Keys in either .env file or as environment variables:
```
LINEAR_API_KEY = {linear-api-key}
OPEN_AI_API_KEY = {open-ai-api-key}
```
3. Run `python3 main.py` and follow prompts (either input a conversation transcript or use ChatGPT to generate one)