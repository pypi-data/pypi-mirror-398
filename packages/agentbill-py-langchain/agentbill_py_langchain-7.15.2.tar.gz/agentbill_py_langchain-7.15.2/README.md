# AgentBill LangChain Integration

Automatic usage tracking and billing for LangChain applications.

[![PyPI version](https://badge.fury.io/py/agentbill-langchain.svg)](https://pypi.org/project/agentbill-langchain/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

Install via pip:

```bash
pip install agentbill-langchain
```

With OpenAI support:
```bash
pip install agentbill-langchain[openai]
```

With Anthropic support:
```bash
pip install agentbill-langchain[anthropic]
```

## Quick Start

```python
from agentbill_langchain import AgentBillCallback
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# 1. Initialize AgentBill callback
callback = AgentBillCallback(
    api_key="agb_your_api_key_here",  # Get from AgentBill dashboard
    base_url="https://bgwyprqxtdreuutzpbgw.supabase.co",
    customer_id="customer-123",
    debug=True
)

# 2. Create LangChain chain with callback
llm = ChatOpenAI(model="gpt-4o-mini")
prompt = PromptTemplate.from_template("Tell me a joke about {topic}")
chain = LLMChain(llm=llm, prompt=prompt)

# 3. Run - everything is auto-tracked!
result = chain.invoke(
    {"topic": "programming"},
    config={"callbacks": [callback]}
)

print(result["text"])

# ✅ Automatically captured:
# - Prompt text (hashed for privacy)
# - Model name (gpt-4o-mini)
# - Provider (openai)
# - Token usage (prompt + completion)
# - Latency (ms)
# - Costs (calculated automatically)
```

## Features

- ✅ **Zero-config instrumentation** - Just add the callback
- ✅ **Automatic token tracking** - Captures all LLM calls
- ✅ **Multi-provider support** - OpenAI, Anthropic, any LangChain LLM
- ✅ **Chain tracking** - Tracks entire chain executions
- ✅ **Cost calculation** - Auto-calculates costs per model
- ✅ **Prompt profitability** - Compare costs vs revenue
- ✅ **OpenTelemetry compatible** - Standard observability

## Advanced Usage

### Track Custom Revenue

```python
# Track revenue for profitability analysis
callback.track_revenue(
    event_name="chat_completion",
    revenue=0.50,  # What you charged the customer
    metadata={"subscription_tier": "pro"}
)
```

### Use with Agents

```python
from langchain.agents import initialize_agent, load_tools

tools = load_tools(["serpapi", "llm-math"], llm=llm)
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    callbacks=[callback]  # Add callback here
)

# All agent steps auto-tracked!
response = agent.run("What is 25% of 300?")
```

### Use with Sequential Chains

```python
from langchain.chains import SimpleSequentialChain

# All chain steps tracked automatically
overall_chain = SimpleSequentialChain(
    chains=[chain1, chain2, chain3],
    callbacks=[callback]
)

result = overall_chain.run(input_text)
```

## Configuration

```python
callback = AgentBillCallback(
    api_key="agb_...",           # Required - get from dashboard
    base_url="https://...",      # Required - your AgentBill instance
    customer_id="customer-123",  # Optional - for multi-tenant apps
    account_id="account-456",    # Optional - for account-level tracking
    debug=True,                  # Optional - enable debug logging
    batch_size=10,               # Optional - batch signals before sending
    flush_interval=5.0           # Optional - flush interval in seconds
)
```

## How It Works

The callback hooks into LangChain's lifecycle:

1. **on_llm_start** - Captures prompt, model, provider
2. **on_llm_end** - Captures tokens, latency, response
3. **on_llm_error** - Captures errors and retries
4. **on_chain_start** - Tracks chain execution start
5. **on_chain_end** - Tracks chain completion

All data is sent to AgentBill via the `record-signals` API endpoint with proper authentication.

## Supported Models

Auto-cost calculation for:
- OpenAI: GPT-4, GPT-4o, GPT-3.5-turbo, etc.
- Anthropic: Claude 3.5 Sonnet, Claude 3 Opus, etc.
- Any LangChain-compatible LLM

## Troubleshooting

### Not seeing data in dashboard?

1. Check API key is correct
2. Enable `debug=True` to see logs
3. Verify `base_url` matches your instance
4. Check network connectivity to AgentBill

### Token counts are zero?

- Some LLMs don't return token usage
- Callback will estimate based on response length
- OpenAI/Anthropic provide accurate counts

## License

MIT
