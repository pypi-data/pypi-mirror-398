# Scout SDK Reference - ALWAYS USE THESE FUNCTIONS FIRST

**CRITICAL**: Before using any external libraries, check if Scout SDK already provides the functionality below.

## Quick Function Index

```python
from scoutsdk import ScoutAPI
scout = ScoutAPI()  # Auto-loads from SCOUT_CONTEXT env vars

# CHAT & COMPLETIONS
scout.chat.completion(messages, response_format, model, assistant_id, stream, allowed_tools)

# ASSISTANTS - CRUD
scout.assistants.create(name, description, instructions, **options)
scout.assistants.update(assistant_id, **options)
scout.assistants.get(assistant_id)
scout.assistants.list_all()
scout.assistants.delete(assistant_id)

# ASSISTANTS - FILES
scout.assistants.upload_file(assistant_id, file_path, file_type)
scout.assistants.upload_avatar(assistant_id, file_path)
scout.assistants.list_files(assistant_id)
scout.assistants.edit_file(assistant_id, file_uid, filename, description)
scout.assistants.delete_file(assistant_id, file_uid)

# ASSISTANTS - DATA (RAG/Embeddings)
scout.assistants.create_data(assistant_id, data)
scout.assistants.update_data(assistant_id, data_id, metadata, content, embedding)
scout.assistants.search_data(assistant_id, query, strategy, where)
scout.assistants.query_data(assistant_id, where)
scout.assistants.delete_data(assistant_id, id, where)

# ASSISTANTS - FUNCTIONS
scout.assistants.execute_function(assistant_id, function_name, payload, response_model)
scout.assistants.get_functions(assistant_id)

# CONVERSATIONS
scout.conversations.create(messages, assistant_id, model, title, user_data)
scout.conversations.delete(conversation_id)
scout.conversations.get_user_data(conversation_id, model_class)
scout.conversations.update_user_data(conversation_id, user_data)
scout.conversations.get_signed_upload_url(conversation_id, file_path)
scout.conversations.get_signed_url(conversation_id, file_path)

# AUDIO
scout.audio.text_to_speech(text, model, voice, api_args) -> bytes
scout.audio.transcribe_file(file_path, conversation_id, execute_async=True)
scout.audio.transcribe_url(protected_url, filename, conversation_id, execute_async=True)

# IMAGES
scout.image.get_models(tags)
scout.image.generate(prompt, aspect_ratio, quality, nb_outputs, async_job=True)
scout.image.edit(prompt, images, mask, aspect_ratio, quality, async_job=True)

# UTILITIES
scout.utils.create_embeddings(texts) -> list[list[float]]
scout.utils.chunk_document(file_path) -> dict with chunks
scout.utils.get_document_text(file_path, args) -> dict
scout.utils.llm_filter_documents(query, context, documents, batch_size, model_id)
scout.utils.download_protected_file(protected_url) -> bytes

# GENERIC HTTP (for custom endpoints)
scout.get(url, params, response_model)
scout.post(url, data, response_model, files)
scout.put(url, data, response_model)
scout.delete(url, params, response_model)
```

---


## 1. Chat API (`scout.chat`)

### `scout.chat.completion()`

**Purpose**: Send chat requests with structured output validation

**Key Parameters**:
- `messages`: `list[ConversationMessage]` or `str` (single user message)
- `response_format`: `Type[BaseModel]` - Returns validated Pydantic model (PREFERRED)
- `assistant_id`: Use assistant's tools/knowledge
- `allowed_tools`: `list[str]` (None=all, []=none)

```python
# Simple text
response = scout.chat.completion("What is 2+2")
print(response.messages[-1].content)

# Structured output (ALWAYS PREFER THIS)
from pydantic import BaseModel

class Answer(BaseModel):
    result: int
    explanation: str

answer: Answer = scout.chat.completion("What is 2+2", response_format=Answer)
print(answer.result)  # Type-safe
```

---

## 2. Assistants API (`scout.assistants`)

**Key Methods:**
- `create(name, description, instructions, **opts)` - visibility_type, allowed_functions, variables, secrets
- `update(assistant_id, **opts)` - All params optional
- `get(assistant_id)` / `list_all()` / `delete(assistant_id)`
- `upload_file(assistant_id, file_path, file_type)` - Use `FileType.KNOWLEDGE` or `FileType.CUSTOM_FUNCTIONS`
- `upload_avatar(assistant_id, file_path)`
- `list_files(assistant_id)` / `edit_file(...)` / `delete_file(...)`

---

## 3. Assistant Data (RAG)

```python
from scouttypes.assistants import AssistantData, AssistantDataList

# Create data (single or batch)
data = AssistantData(
    metadata={"source": "manual", "page": 5},
    content="Product X costs $599",
    embedding=None  # Auto-generated if None
)
scout.assistants.create_data("asst_123", data)

# Batch insert
data_list = AssistantDataList(list=[...])
scout.assistants.create_data("asst_123", data_list)

# Vector search with metadata filter
results = scout.assistants.search_data(
    assistant_id="asst_123",
    query="pricing info",
    where={"source": "manual"}
)
for r in results:
    print(f"{r.content} (score: {r.score})")

# Update/delete
scout.assistants.update_data(assistant_id, data_id, metadata, content)
scout.assistants.delete_data(assistant_id, id=..., where=...)  # Provide one
```

---

## 4. Custom Functions

```python
# Execute with validation
result: MyModel = scout.assistants.execute_function(
    assistant_id="asst_123",
    function_name="analyze_data",
    payload={"data_id": "xyz"},
    response_model=MyModel  # Optional Pydantic model
)

# Get available functions
scout.assistants.get_functions(assistant_id)
```

---

## 5. Conversations

```python
# Create with user data
conv = scout.conversations.create(
    title="Support Chat",
    assistant_id="asst_123",
    user_data={"customer_id": "cust_456"}
)

# Get/update user data (with optional Pydantic validation)
context: MyModel = scout.conversations.get_user_data(conv.id, model_class=MyModel)
scout.conversations.update_user_data(conv.id, {"status": "resolved"})

# File upload
from scoutsdk.api import upload_file_to_signed_url
signed_url = scout.conversations.get_signed_upload_url(conv.id, "file.pdf")
upload_file_to_signed_url(signed_url, "file.pdf")
# Use: signed_url.protected_url in messages

scout.conversations.delete(conv.id)
```

---

## 6. Audio

```python
# Text-to-speech -> bytes
audio = scout.audio.text_to_speech("Hello!", voice="alloy")
with open("out.mp3", "wb") as f:
    f.write(audio)

# Transcription (async recommended)
job = scout.audio.transcribe_file("meeting.mp3", execute_async=True)
# OR sync: result = scout.audio.transcribe_file("short.mp3", execute_async=False)

# From URL
scout.audio.transcribe_url(protected_url, execute_async=True)
```

---

## 7. Images

```python
from scouttypes.images import ImageAspectRatio, ImageQuality

# Generate (async recommended)
job = scout.image.generate(
    prompt="A futuristic city",
    aspect_ratio=ImageAspectRatio.LANDSCAPE,
    quality=ImageQuality.HIGH,
    async_job=True
)

# Edit existing
images = [{"filename": "x.jpg", "content_type": "image/jpeg", "protected_url": "/protected/..."}]
scout.image.edit(prompt="Make sky dramatic", images=images, async_job=True)

# Get models
scout.image.get_models(tags=...)
```

---

## 8. Utils

```python
# Embeddings
embeddings = scout.utils.create_embeddings(["text1", "text2"])  # -> list[list[float]]

# Document processing
result = scout.utils.chunk_document("doc.pdf")
chunks = result["file"]["chunks"]  # Each chunk has "content" field

text_dict = scout.utils.get_document_text("doc.pdf")

# LLM document filtering
docs = {"id1": "content1", "id2": "content2"}
relevant_ids = scout.utils.llm_filter_documents(
    query="...",
    context="Select relevant docs",
    documents=docs
)

# Download protected file
file_bytes = scout.utils.download_protected_file("/protected/conversations/.../file.pdf")
```

---

## 9. Important Types

```python
# Conversations
from scouttypes.conversations import (
    ConversationMessage,
    MessageRole,  # USER, ASSISTANT, SYSTEM, TOOL
    ConversationMessageContentPartTextParam,
    ConversationMessageContentPartImageParam
)

# Assistants
from scouttypes.assistants import (
    AssistantData, AssistantDataList,
    FileType,  # KNOWLEDGE, CUSTOM_FUNCTIONS, etc.
)

# Images
from scouttypes.images import (
    ImageAspectRatio,  # SQUARE, LANDSCAPE, PORTRAIT
    ImageQuality,      # LOW, MEDIUM, HIGH, DEFAULT
)
```

## 10. Generic HTTP

For custom endpoints:
```python
scout.get(url, params, response_model)
scout.post(url, data, response_model, files)
scout.put(...) / scout.delete(...)
```

---

## 11. Best Practices

✅ **ALWAYS use `response_format`** with Pydantic models for structured outputs
✅ **Use `execute_async=True`** for audio/image operations
✅ **Prefer Scout SDK** over external libraries (requests, openai, etc.)
✅ **Use metadata filters** in `search_data()` for efficient RAG
✅ **Set `allowed_tools=[]`** when you don't want assistant tools
✅ **Use `variables` for config**, `secrets` for API keys

---

## 12. Complete RAG Example

```python
from scoutsdk import ScoutAPI
from scouttypes.assistants import AssistantData, AssistantDataList
from pydantic import BaseModel

scout = ScoutAPI()

# 1. Create assistant
asst = scout.assistants.create(
    name="KB Assistant",
    description="Answers from docs",
    instructions="Answer based on knowledge base only"
)

# 2. Chunk → Embed → Store
result = scout.utils.chunk_document("handbook.pdf")
chunks = [c["content"] for c in result["file"]["chunks"]]
embeddings = scout.utils.create_embeddings(chunks)

data_list = [
    AssistantData(metadata={"page": i}, content=text, embedding=emb)
    for i, (text, emb) in enumerate(zip(chunks, embeddings))
]
scout.assistants.create_data(asst.id, AssistantDataList(list=data_list))

# 3. Query with structured output
class Answer(BaseModel):
    answer: str
    confidence: str
    pages: list[int]

result: Answer = scout.chat.completion(
    "What's the vacation policy",
    assistant_id=asst.id,
    response_format=Answer
)
print(f"{result.answer} (confidence: {result.confidence}, pages: {result.pages})")
```

---

**Environment**: SDK reads `SCOUT_API_URL` and `SCOUT_API_ACCESS_TOKEN` from env (set by `scoutcli init`)
