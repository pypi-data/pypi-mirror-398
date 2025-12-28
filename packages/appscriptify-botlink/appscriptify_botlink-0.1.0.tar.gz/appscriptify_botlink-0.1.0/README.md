# Botlink Python SDK

Official Python SDK for Botlink by AppScriptify.

## Install
```bash
pip install appscriptify-botlink
```

## Usage
```python
from botlink import Botlink

client = Botlink(api_key="as-api-key_xxx")

print(client.projects) # Projects List

project = client.projects["project_id"]
print(project.agent.chat("Hello!"))
```

## Environment Variable
```bash
export BOTLINK_API_KEY=as_live_xxx
```