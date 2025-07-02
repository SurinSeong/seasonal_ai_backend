import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

openai = AsyncOpenAI(aip_key=os.getenv("OPENAI_API_KEY"))
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

app = FastAPI()

# 로컬 개발 환경에서 CORS 허용하기
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 메시지 요청 클래스
class MessageRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat_endpoint(req: MessageRequest):
    # OpenAI의 ChatCompletion endpoint 호출
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": req.message},
        ],
        # 창의성 조절
        temperature=0.7
    )
    # assistant message 추출
    assistant_reply = response.choices[0].message.content
    return {"retry": assistant_reply}


@app.post("/assistant")
async def assistant_endpoint(req: MessageRequest):
    # 논문봇을 불러온다 -> RAG
    assistant = await openai.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # 사용자 메시지의 새로운 스레드를 생성
    thread = await openai.beta.threads.create(
        messages=[{"role": "user", "content": req.message}]
    )

    # 실행 및 helper 메서드 사용해서 completion 진행
    run = await openai.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )

    # 특정한 실행에서 메시지를 얻는다.
    messages = list(
        await openai.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    )

    # 첫 번째 메시지의 내용과 annotation을 보낸다.
    message_content = messages[0][1][0].content[0].text
    annotations = message_content.annotations
    citations = []

    # 인용에 대한 것 이쁘게 출력하기
    for idx, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(
            annotation.text, f"[{idx}]"
        )
        if file_citation := getattr(annotations, "file_citation", None):    # ※ := 해치 연산자
            cited_file = await openai.files.retrieve(file_citation.file_id)
            citations.append(f"[{idx}] {cited_file.filename}")
    
    # 인용 + 메시지
    assistant_reply = message_content.value
    if citations:
        assistant_reply += "\n\n" + "\n".join(citations)

    return {"reply": assistant_reply}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
