from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
（在這裡貼上我先前給你的「最終 System Prompt 檔」全文）
"""

conversation_history = []

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    conversation_history.append({"role": "user", "content": user_text})
    if len(conversation_history) > 6:
        conversation_history.pop(0)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *conversation_history
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )

    reply_text = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply_text})

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
