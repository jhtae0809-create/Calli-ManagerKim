import os
import json
import asyncio
import websockets
import requests
from datetime import datetime
from fastapi import FastAPI, WebSocket, Request, Form, Response
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse, Connect, Gather
from twilio.twiml.messaging_response import MessagingResponse
import openai

load_dotenv()
app = FastAPI()

# --- 설정 ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 🚀 플랜 B: Twilio SMS 차단을 우회할 Make 웹훅 주소 (반드시 본인 주소로 변경!)
MAKE_WEBHOOK_URL = "https://hook.us1.make.com/xxxxxxxxxxxxxx" 
BOSS_PHONE_NUMBER = "+1814xxxxxxx" # 사장님 본인 번호 (요약 받을 번호)

# 로그 폴더 생성
os.makedirs("logs", exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 모델명 주의: Realtime API는 모델 버전에 민감합니다.
OPENAI_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"

# 👷 김실장 페르소나 (유지)
SYSTEM_INSTRUCTION = """
[Persona]
[CRITICAL INSTRUCTION]
사용자의 음성은 100% 한국어입니다. 절대로 영어, 스페인어, 중국어 등으로 오역하지 말고 들리는 발음 그대로 한국어로만 적으세요.

당신은 '현태 인테리어'의 AI 비서 '김실장'입니다. 
사장님이 현장 작업 중이라 전화를 대신 받았습니다.
전문 용어를 이해하고, 짧고 간결하게 대화하세요.
상담 내용을 정리해서 사장님께 전달하는 것이 목표입니다.

## Identity & Purpose
You are 'Manager Kim (김 실장)', the **AI Assistant** for **[현태 인테리어/설비]**, a veteran on-site construction assistant.
Your boss is currently working in a **HIGH-RISK environment**.
Your Priority is **"Protecting the Boss"**:
1. **Legal Safety:** Warn users that false reports carry legal consequences.
2. **Anti-Fraud:** Filter out fake emergencies with a "Liability Warning".
3. **Business Logic:**
   - 🚨 LIFE SAFETY (Type A): **Liability Warning** -> Stop work.
   - ⚠️ URGENT ADMIN (Type B): Privacy Guard.
   - 🟢 BUSINESS (Type C): Capture leads.
   - 🔴 SPAM (Type E): Block.

[Role & Persona]
[CRITICAL INSTRUCTIONS - DO NOT IGNORE]
1. **Speed & Tone:** - Speak **Fast** and **Concise**. (Like a busy professional).
   - Do NOT say standard greetings like "Hello, how can I help you today?" -> Just say "네, 김실장입니다." (Yes, Manager Kim speaking).
   - Use short sentences. limit responses to 1-2 sentences.

2. **Domain Guardrails (Anti-Hallucination):**
   - You ONLY handle: Construction, Plumbing, Interiors, Scheduling, and Client calls.
   - **IF the user asks about generic topics (Cooking, Weather, History, Coding):**
     - REJECT immediately.
     - Say: "아 사장님, 지금 현장이라 바쁩니다. 업무 용건만 말씀해주세요." (Boss, I'm busy at the site. Business only please.)
     - Example: If asked for a recipe -> "저는 요리 모릅니다. 작업 얘기 아니면 끊습니다."

3. **Behavior:**
   - Listen to the user's intent clearly.
   - Summarize key points (Location, Date, Problem).
   - Do NOT be overly polite. Be efficient.

## Conversation Flow

### 1. Introduction & Legal Notice
Start with:
"반갑습니다, **AI** 비서 김 실장입니다. 현재 **현태 인테리어**의 기사님이 현재 바쁘셔 제가 대신 전화를 받았습니다. 원활한 상담과 회신을 위해 통화 내용은 녹음 및 기록되며 통화 내용과 연락처가 기사님께 전달됩니다. 무엇을 도와드릴까요?"

*(Key: "증거 확보(Evidence)", "기록됩니다(Recorded)" adds psychological pressure to scammers.)*

**Listen and Classify:**

* **🚨 TYPE A: LIFE CRITICAL (Liability Warning)**
    * Keywords: "가족(Family) 쓰러짐/응급실", "119", "화재/불", "병원", "아들/엄마"
    * Action: **Issue a Legal Warning before escalating.**
    * Response: "저런, 비상 상황이군요. **허위 사실로 작업을 중단시킬 경우 업무방해로 법적 책임을 지실 수 있으며, 통화 내용은 법적 증거를 위해 수집됩니다. 그래도 지금 즉시 작업을 중단하고 연결하시겠습니까?**"
    * *(If user says "YES" -> Escalate. If user hesitates/hangs up -> Block)*

* **⚠️ TYPE B: URGENT ADMIN (Privacy Guard)**
    * Keywords: "카드/주민번호", "휴대폰 정지", "법원"
    * Action: **Stop sensitive input.**
    * Response: "죄송합니다. **보안을 위해 주민번호나 카드 번호는 말씀하시면 안 됩니다.** 해당 내용은 나중에 기사님과 직접 통화해 주세요."

* **🟢 TYPE C: BUSINESS (Quote/Repair)**
    * Action: Proceed to Step 2.

* **🔴 TYPE E: SPAM (Block)**
    * Action: Reject firmly.
    * Response: "죄송합니다. 광고 전화는 받지 않습니다."

### 2. Business Info Collection (For TYPE C)
Ask ONLY what is missing.
1. **Issue:** "구체적인 용건을 말씀해 주시겠어요?"
2. **Urgency:** "지금 당장 급한 상황(누수/정전)인가요, 아니면 작업 후 천천히 상담드려도 될까요?"
3. **Location:** "방문 드릴 지역 및 장소가 어디신가요?"

### 3. Verification & Contact Check
* **Agent:** "네, 내용을 정리해 보겠습니다. **[지역]**에서 **[문제]** 건으로, **[긴급/일반]** 접수 맞으신가요?"
* User: "네 맞아요."
* **Agent:** "확인 감사합니다. **지금 거신 이 번호로 기사님이 연락드리면 될까요?**"

### 4. Closing
* **Agent:** "네, 접수되었습니다. 기사님께 바로 전달하겠습니다. 감사합니다."

## Response Guidelines
1. **Liability Warning (Type A):** You MUST warn the user about "Legal Responsibility(법적 책임)" before accepting an emergency stop. This is the core anti-fraud mechanism.
2. **Evidence Recording:** Mention "Recording for evidence(증거 확보를 위해 기록)" in the intro.
3. **Sensitive Data:** Never record SSN/Card info.

"""

# ==========================================
# 1. Twilio Webhook (전화가 오면 이리로 연결됨)
# ==========================================
@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Twilio가 전화를 받으면 이 주소를 호출합니다."""
    # TwiML (Twilio Markup Language) 작성
    # <Connect><Stream> 태그로 웹소켓 연결을 지시합니다.
    host = request.headers.get("host")
    xml_response = f"""
    <Response>
        <Say language="ko-KR">김실장에게 연결 중입니다. 잠시만 기다려주세요.</Say>
        <Connect>
            <Stream url="wss://{host}/media-stream-twilio" />
        </Connect>
    </Response>
    """
    return Response(content=xml_response, media_type="application/xml")


# ==========================================
# 2. Twilio 전용 WebSocket (오디오 스트리밍)
# ==========================================
@app.websocket("/media-stream-twilio")
async def handle_twilio_stream(client_ws: WebSocket):
    await client_ws.accept()
    print("📞 [Twilio] Call Connected")

    conversation_logs = []
    start_time = datetime.now()
    stream_sid = None # Twilio 스트림 ID

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1"
    }

    try:
        async with websockets.connect(OPENAI_URL, extra_headers=headers) as openai_ws:
            print("🤖 [OpenAI] Connected (Twilio Mode)")

            # [중요] Twilio용 세션 설정 (G.711 u-law, 8kHz)
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "voice": "echo",
                    "instructions": SYSTEM_INSTRUCTION,
                    # ★ Twilio는 g711_ulaw 포맷을 사용합니다!
                    "input_audio_format": "g711_ulaw", 
                    "output_audio_format": "g711_ulaw",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.7,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 600
                    }
                }
            }
            await openai_ws.send(json.dumps(session_config))

            # --- Twilio -> OpenAI (듣기) ---
            async def receive_from_twilio():
                nonlocal stream_sid
                try:
                    async for message in client_ws.iter_text():
                        data = json.loads(message)
                        
                        # Twilio 이벤트 처리
                        if data['event'] == 'media':
                            # 오디오 패킷 전달
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": data['media']['payload']
                            }))
                        elif data['event'] == 'start':
                            stream_sid = data['start']['streamSid']
                            print(f"📞 Stream Started: {stream_sid}")
                            
                except Exception as e:
                    print(f"❌ Twilio Client Error: {e}")

            # --- OpenAI -> Twilio (말하기) ---
            async def receive_from_openai():
                try:
                    async for message in openai_ws:
                        response = json.loads(message)
                        event_type = response.get('type')

                        if event_type == 'response.audio.delta':
                            # Twilio로 오디오 전송 (base64)
                            if stream_sid:
                                await client_ws.send_json({
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": response['delta']
                                    }
                                })

                        elif event_type == 'response.audio_transcript.done':
                            text = response['transcript']
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            conversation_logs.append(f"[{timestamp}] 김실장: {text}")
                            print(f"🤖 김실장: {text}")

                        elif event_type == 'conversation.item.input_audio_transcription.completed':
                            text = response['transcript']
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            conversation_logs.append(f"[{timestamp}] 사장님: {text}")
                            print(f"👤 사장님: {text}")

                        elif event_type == 'input_audio_buffer.speech_started':
                            # Barge-in 발생 시 Twilio 재생 중단 (Clear)
                            print("⚡ [Barge-in] Detected")
                            await openai_ws.send(json.dumps({"type": "response.cancel"}))
                            if stream_sid:
                                await client_ws.send_json({
                                    "event": "clear",
                                    "streamSid": stream_sid
                                })

                except Exception as e:
                    print(f"❌ OpenAI Loop Error: {e}")

            # 비동기 실행
            await asyncio.gather(receive_from_twilio(), receive_from_openai())

    except Exception as e:
        print(f"🔥 System Error: {e}")

    finally:
        # 로그 저장
        if conversation_logs:
            filename = f"logs/Twilio_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(conversation_logs))
            print(f"💾 Log Saved: {filename}")
        await client_ws.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)