import os
import httpx

async def send_slack_alert(message: str, record_url: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("Error: Falta SLACK_WEBHOOK_URL")
        return

    payload = {
        "text": message,
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Atención:* {message}"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"-> {record_url} | Completar en Atio"}
            }
        ]
    }

    async with httpx.AsyncClient as client:
        try:
            await client.post(webhook_url, json=payload)
        except Exception as e:
            print(f"Error enviando a Slack: {e}")