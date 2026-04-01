# Calli: AI 기반 실시간 음성 비서 (김실장)

Calli는 현장 중심의 비즈니스(인테리어 및 설비)를 위해 설계된 전문 AI 음성 수신 시스템이다. OpenAI Realtime API와 Twilio를 통합하여, 사용자가 고위험 작업 중일 때 걸려오는 전화를 대신 받고 용건을 정리한다.

## 주요 기능

* **실시간 음성 상호작용**: `gpt-4o-realtime-preview` 모델을 사용하여 한국어 기반의 저지연 음성 대화 구현.
* **전화 통신 통합**: Twilio Media Streams를 통한 양방향 오디오 스트리밍 (G.711 u-law, 8kHz 포맷).
* **의도 기반 필터링**: 통화 의도를 긴급 상황, 일반 행정, 비즈니스 문의, 스팸 등으로 자동 분류.
* **법적 가드레일**: 허위 긴급 보고 방지를 위해 고위험 상황 발생 시 법적 책임 고지(Liability Warning) 로직 실행.
* **Barge-in 기능**: 사용자가 말을 시작하면 즉시 AI의 음성 재생을 중단하고 다시 듣기 상태로 전환.
* **자동 로그 생성**: 모든 대화 내용을 타임스탬프와 함께 구조화된 텍스트 로그로 저장.

## 기술 스택

* **Backend**: FastAPI, WebSockets, asyncio.
* **AI Engine**: OpenAI Realtime API.
* **Telephony**: Twilio Voice & Media Streams.
* **Frontend**: HTML5, Tailwind CSS, Web Audio API.
* **Environment**: Python 3.10+.

## 시스템 아키텍처

1. **전화 수신**: Twilio가 전화를 수신하면 `/incoming-call` 엔드포인트 호출.
2. **미디어 스트리밍**: FastAPI가 Twilio와 OpenAI 사이의 웹소켓 연결 매개.
3. **데이터 처리**: 김실장(AI 에이전트)이 인테리어/설비 도메인 지식을 바탕으로 실시간 대응.
4. **리드 캡처**: 상담 내용을 요약하여 시스템 로그에 저장.

## 성능 및 최적화

* **시간 복잡도**: 의도 분류 및 로그 기록 로직은 메시지 길이에 대해 $O(1)$ ~ $O(N)$의 복잡도를 가짐.
* **지연 시간 최적화**: REST API 폴링 대신 지속적 웹소켓(Persistent WebSockets)을 사용하여 RTT(Round Trip Time) 최소화.
* **리소스 효율성**: 가상 환경 및 `requirements.txt` 관리를 통해 배포 시 리소스 낭비 방지.

## 설치 방법

```bash
git clone [https://github.com/your-username/calli-ai-assistant.git](https://github.com/your-username/calli-ai-assistant.git)
pip install -r requirements.txt
uvicorn mainserver:app --host 0.0.0.0 --port 8000
```
**작성자**: 정현태
