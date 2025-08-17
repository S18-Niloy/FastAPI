import os, base64, io, asyncio
from typing import Dict, Any
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from .schemas import AiTaskRequest, AiTaskResponse, LoginRequest, TokenResponse
from .auth import create_token, verify_token
from .db import init_db, SessionLocal, Answer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Load envs
load_dotenv()
MODEL = os.getenv("DEFAULT_MODEL","gpt-4o-mini")
IMG_MODEL = os.getenv("IMAGE_MODEL","gpt-image-1")

app = FastAPI(title="Softvence Omega AI Task API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.on_event("startup")
async def startup():
    await init_db()

@app.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    # Demo login (static) — replace with real user store if needed
    if req.username and req.password:
        return TokenResponse(access_token=create_token(req.username))
    raise HTTPException(status_code=400, detail="Invalid credentials")

@app.post("/ai-task", response_model=AiTaskResponse)
async def ai_task(req: AiTaskRequest, user: str = Depends(verify_token)):
    if req.task == "qa":
        if not req.prompt:
            raise HTTPException(status_code=400, detail="prompt is required for qa")
        content = await do_qa(req.prompt, req.extras or {})
        await save_answer("qa", content)
        return AiTaskResponse(task="qa", data={"answer": content})
    elif req.task == "latest":
        latest = await get_latest_answer()
        return AiTaskResponse(task="latest", data=latest or {"message":"no answers yet"})
    elif req.task == "image":
        if not req.prompt:
            raise HTTPException(status_code=400, detail="prompt is required for image")
        img_b64 = await gen_image_b64(req.prompt)
        await save_answer("image", "[image generated]")
        return AiTaskResponse(task="image", data={"image_b64": img_b64})
    elif req.task == "platform_content":
        if not req.prompt or not req.platform:
            raise HTTPException(status_code=400, detail="prompt and platform are required")
        text = await gen_platform_content(req.platform, req.prompt, req.extras or {})
        await save_answer("platform_content", text)
        return AiTaskResponse(task="platform_content", data={"text": text})
    else:
        raise HTTPException(status_code=400, detail=f"Unknown task {req.task}")

# ----------------- helpers -----------------

async def do_qa(prompt: str, extras: Dict[str, Any]) -> str:
    # Optional: call MCP tool before LLM for demonstration
    try:
        from .mcp_client import call_upper
        mcp_out = await call_upper(prompt)
        tool_hint = f"(MCP upper tool says: {mcp_out})\n"
    except Exception:
        tool_hint = ""
    msgs = [
        {"role":"system","content":"You are a concise Q&A assistant."},
        {"role":"user","content": tool_hint + prompt}
    ]
    resp = client.chat.completions.create(model=MODEL, messages=msgs, temperature=0.2)
    return resp.choices[0].message.content

async def gen_image_b64(prompt: str) -> str:
    img = client.images.generate(model=IMG_MODEL, prompt=prompt, size="1024x1024")
    # Return base64 so it's portable per spec
    b64 = img.data[0].b64_json
    return b64

async def gen_platform_content(platform: str, prompt: str, extras: Dict[str, Any]) -> str:
    style_map = {
        "twitter":"Short, punchy, <=280 chars, add relevant hashtag and emoji if appropriate.",
        "x":"Short, punchy, <=280 chars, add relevant hashtag and emoji if appropriate.",
        "facebook":"Friendly paragraph, 1–2 sentences, add call-to-action.",
        "linkedin":"Professional tone, 2–3 sentences, value-focused, no slang.",
        "instagram":"Casual, vibe-forward, include 2–3 tasteful hashtags.",
        "tiktok":"High energy hook + 1 line idea for visuals; 1–2 hashtags.",
        "reddit":"Neutral, discussion-starting, avoid emojis.",
        "medium":"Thoughtful intro paragraph, 3–5 sentences."
    }
    style = style_map.get(platform.lower(), "Neutral style.")
    msgs = [
        {"role":"system","content":f"You craft platform-tailored content. Style guide: {style}"},
        {"role":"user","content":prompt}
    ]
    resp = client.chat.completions.create(model=MODEL, messages=msgs, temperature=0.7)
    return resp.choices[0].message.content

async def save_answer(task: str, content: str):
    async with SessionLocal() as session:  # type: AsyncSession
        session.add(Answer(task=task, content=content))
        await session.commit()

async def get_latest_answer():
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Answer).order_by(Answer.created_at.desc()))
        row = result.scalars().first()
        if not row:
            return None
        return {"id": row.id, "task": row.task, "content": row.content, "created_at": str(row.created_at)}
