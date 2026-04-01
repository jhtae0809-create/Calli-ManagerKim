# Calli: AI-Powered Real-Time Voice Assistant (Manager Kim)

Calli is a specialized AI voice receptionist system designed for on-site businesses. It integrates the OpenAI Realtime API with Twilio to manage incoming calls, filter requests through legal warnings, and capture business leads while the user is engaged in high-risk site operations.

## Key Features

* **Real-Time Voice Interaction**: Implements low-latency Korean speech interaction using the `gpt-4o-realtime-preview` model.
* **Telephony Integration**: Seamless bi-directional audio streaming via Twilio Media Streams (G.711 u-law, 8kHz).
* **Intent-Based Filtering**: Classifies call intent into Life-Critical, Urgent Admin, Business, or Spam categories.
* **Legal Guardrails**: Automatically issues a "Liability Warning" for high-risk reports to mitigate fraudulent emergency claims.
* **Barge-in Support**: Immediate audio playback interruption and state reset when user speech is detected.
* **Automated Documentation**: Generates structured conversation logs with timestamps for every session.

## Tech Stack

* **Backend**: FastAPI, WebSockets, asyncio.
* **AI Engine**: OpenAI Realtime API (WebSocket-based).
* **Telephony**: Twilio Voice & Media Streams.
* **Frontend**: HTML5, Tailwind CSS, Web Audio API (PCM16).
* **Environment**: Python 3.10+.

## System Architecture

1. **Call Ingestion**: Twilio receives a call and triggers the `/incoming-call` endpoint.
2. **Media Streaming**: FastAPI establishes a WebSocket connection between Twilio and OpenAI.
3. **Processing**: Manager Kim (AI Agent) processes audio in real-time, applying domain-specific instructions for construction and interior services.
4. **Lead Generation**: Relevant business data is captured and logged.

## Performance Analysis

* **Time Complexity**: Intent classification and logging logic operate at $O(1)$ to $O(N)$ relative to message length.
* **Optimization**: Minimized RTT (Round Trip Time) by utilizing persistent WebSockets instead of RESTful polling.
* **Resource Efficiency**: Optimized Docker image size by isolating core dependencies in `requirements.txt`.

## Installation

```bash
git clone [https://github.com/your-username/calli-ai-assistant.git](https://github.com/your-username/calli-ai-assistant.git)
pip install -r requirements.txt
uvicorn mainserver:app --host 0.0.0.0 --port 8000
```

**Author**: Hyuntae Jeong
