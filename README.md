This is a repo by following up the quickstart of Azure AI Agent Service:
https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-openai

# How to run locally?

Set up the resources by following the [quickstart](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-openai)

Fill in the project connection string in `.env`

```
poetry install
```

If using windows, do:
```
poetry install --no-root
```

Run the script:
```
python run_with_azure_sdk.py
```