# Kisan Shakti — Future WhatsApp Business API Integration Blueprint
> [!IMPORTANT]
> **Status:** Architecture & Specification Only. **No WhatsApp integration code is implemented in this phase.** Live WhatsApp integration will only be developed upon explicit future request after web application demonstration.

---

## 1. Architectural Readiness
The Kisan Shakti backend is already architected to seamlessly interface with the Meta WhatsApp Cloud API / WhatsApp Business Platform without modifying core AI modules:
- Reusable REST endpoints (`/query`, `/predict/disease`, `/recommend/scheme`, `/expert`) accept standard JSON and multipart payloads.
- Modular services return structured responses that can be mapped directly into WhatsApp interactive messages (buttons, list pickers, image attachments, audio replies).

---

## 2. Inbound Message Routing Workflow

```
+------------------------------------+
|  Farmer WhatsApp Message           |
|  (Text, Leaf Photo, or Voice Memo) |
+------------------+-----------------+
                   |
                   v (Webhook Event)
+------------------------------------+
|  WhatsApp Cloud API (Meta Graph)   |
+------------------+-----------------+
                   |
                   v (HTTPS POST)
+------------------------------------+
|  Future FastAPI Webhook Handler    |
|  `POST /webhook/whatsapp`          |
+------------------+-----------------+
                   |
     +-------------+-------------+
     | (Image Message)           | (Text / Audio Message)
     v                           v
[Download Media via Graph API]  [Pass text to /query Orchestrator]
     |                           |
     v                           v
[POST /predict/disease]         [Receive Structured Response]
     |                           |
     +-------------+-------------+
                   |
                   v
+------------------------------------+
|  Format Response into WhatsApp     |
|  Interactive Message Template      |
+------------------+-----------------+
                   |
                   v
+------------------------------------+
|  Send Reply via Meta Graph API     |
+------------------------------------+
```

---

## 3. Handling Different Message Types

### A. Leaf Photo (Image Diagnosis)
1. Meta sends a webhook notification with a `media_id` for the uploaded photo.
2. Webhook handler calls Meta Graph API `GET /v18.0/{media_id}` to retrieve the temporary download URL.
3. Media bytes are fetched with bearer token authorization and passed directly to `disease_service.predict(image_bytes)`.
4. The diagnostic result is formatted into a WhatsApp message:
   ```
   🌾 *Kisan Shakti Diagnosis*
   *Crop:* Tomato
   *Condition:* Early Blight (Alternaria linariae)
   *Confidence:* 89.4%
   
   🌿 *Recommended Action:*
   Prune infected bottom leaves. Spray Mancozeb @ 2.5 g/L.
   
   ⚠️ *Notice:* Preliminary AI assessment. Please confirm with your local KVK.
   ```

### B. Text Inquiry (Schemes, Crops, or Queries)
1. Webhook handler forwards `message.text.body` to `orchestrator_service.route_and_execute(query, user_language)`.
2. Returned answers are sent as plain text or quick-reply button menus.

### C. Voice Notes (Audio Guidance)
1. Meta sends audio memo `.ogg` (opus codec).
2. Media is transcribed using a speech-to-text service (e.g. Bhashini / Whisper).
3. The transcribed text is routed to the orchestrator, and the response is sent back as both text and synthesized audio.

---

## 4. Meta Verification & Security Requirements
When implementing the live integration:
1. **Webhook Verification**: FastAPI will handle `GET /webhook/whatsapp` with `hub.mode`, `hub.verify_token`, and `hub.challenge`.
2. **Payload Signature Verification**: Validate `X-Hub-Signature-256` using HMAC-SHA256 with Meta App Secret.
3. **Permanent Token**: Store `WHATSAPP_ACCESS_TOKEN` and `PHONE_NUMBER_ID` in `.env`.
4. **HTTPS Public Endpoint**: Deploy backend with public SSL URL (via reverse proxy, AWS, GCP, or ngrok for staging).
