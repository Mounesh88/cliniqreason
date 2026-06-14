import os

files = [
    'mcp_server/tools/symptom_tool.py',
    'mcp_server/tools/risk_tool.py',
    'mcp_server/tools/drug_tool.py',
    'mcp_server/tools/protocol_tool.py',
    'mcp_server/tools/report_tool.py'
]

old = '''client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-12-01-preview"
)'''

new = '''_azure_client = None

def get_azure_client():
    global _azure_client
    if _azure_client is None:
        _azure_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_API_KEY"),
            api_version="2024-12-01-preview"
        )
    return _azure_client'''

for filepath in files:
    if not os.path.exists(filepath):
        print('NOT FOUND:', filepath)
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        # Replace client. with get_azure_client().
        content = content.replace('client.chat.completions', 'get_azure_client().chat.completions')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Fixed:', filepath)
    else:
        print('Pattern not found:', filepath)

print('Done!')