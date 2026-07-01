import httpx
import os
from dotenv import load_dotenv

load_dotenv()

org_id = os.getenv("DEVIN_ORG_ID")

response = httpx.post(
    f"https://api.devin.ai/v3/organizations/{org_id}/sessions",
    headers={"Authorization": f"Bearer {os.getenv('DEVIN_API_KEY')}"},
    json={"prompt": "Say hello and do nothing else. This is a test."},
)

print(response.status_code)
print(response.json())
