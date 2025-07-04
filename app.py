import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openai import AsyncOpenAI

load_dotenv()

openai = AsyncOpenAI(api_key = os.getenv("OPENAI_API_KEY"))
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

app = FastAPI()

# 로컬 환경에서 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # 실제로 배포할 때는, 도메인 제한해야함.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    message: str


# 일반 챗봇
@app.post("/chat")
async def chat_endpoint(req: MessageRequest):
    # Call the OpenAI ChatCompletion endpoint
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": req.message},
        ]
    )

    # Extract assistant message
    assistant_reply = response.choices[0].message.content
    return {"reply": assistant_reply}


# 논문봇
@app.post("/assistant")
async def assistant_endpoint(req: MessageRequest):
    assistant = await openai.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # 사용자 메시지를 위해 새로운 스레드 생성
    thread = await openai.beta.threads.create(
        messages=[{"role": "user", "content": req.message}]
    )

    run = await openai.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )

    # 특정 실행을 통한 message를 얻는다.
    messages = list(
        await openai.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    )

    # 첫 번재 메시지 content와 annotation 실행
    message_content = messages[0][1][0].content[0].text
    annotations = message_content.annotations
    citations = []

    # 인용 마커로 annotations를 대체하고 인용 list 생성
    for idx, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(
            annotation.text, f"[{idx}]"
        )

        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = await openai.files.retrieve(file_citation.file_id)
            citations.append(f"[{idx}] {cited_file.filename}")

    # 뭐라도 존재한다면 인용과 메시지를 합쳐주기
    assistant_reply = message_content.value
    if citations:
        assistant_reply += "\n\n" + "\n".join(citations)

    return {"reply": assistant_reply}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)