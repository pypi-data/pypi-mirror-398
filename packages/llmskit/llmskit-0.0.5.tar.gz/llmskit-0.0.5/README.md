# llmskit
统一的LLM客户端与工具

## Documentation

完整的 API 文档待补充

## Installation

```bash
pip install llmskit
```

## Usage

```python3
# 调用embedding
from llmskit import OpenAIEmbeddings, AsyncOpenAIEmbeddings
# 调用LLM
from llmskit import ChatLLM, AsyncChatLLM, OpenAIClient, AsyncOpenAIClient, AzureOpenAIClient,
    AsyncAzureOpenAIClient
```

## Todo
```python3
import openai
openai.responses.create()
```
