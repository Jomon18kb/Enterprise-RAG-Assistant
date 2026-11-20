import requests
from groq import Groq

from app.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from app.retrieval import search_documents


def get_llm_response(prompt):
    """Generate response using configured LLM (Groq or Gemini)."""
    # Prefer Groq if key is present
    if GROQ_API_KEY:
        groq_client = Groq(api_key=GROQ_API_KEY)
        candidate_models = [GROQ_MODEL, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        last_error = None
        for model in candidate_models:
            if not model:
                continue
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1000,
                )
                return response.choices[0].message.content or "No answer was generated."
            except Exception as e:
                last_error = e
                # If model is deprecated or not found on this API account, try next available model
                if "model_not_found" in str(e) or "404" in str(e) or "does not exist" in str(e):
                    continue
                raise e
        if last_error:
            raise last_error

    # Fallback to Google Gemini if GEMINI_API_KEY is present
    if GEMINI_API_KEY:
        model_name = GEMINI_MODEL or "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1000,
            }
        }
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "No answer was generated.")
        return "No answer was generated."

    # If neither key is configured
    return None


def ask_question(question):
    """Perform RAG retrieval and answer generation."""
    # Step 1: Retrieve relevant documents
    documents = search_documents(question, limit=5)

    if not documents:
        return {
            "answer": "I could not find relevant information in the uploaded documents. Please upload relevant PDF files first or try a different question.",
            "sources": []
        }

    # Step 2: Prepare context
    context_chunks = []
    for index, document in enumerate(documents, start=1):
        context_chunks.append(
            f"SOURCE [{index}]\n"
            f"Document: {document['document_name']}\n"
            f"Page: {document['page_number']}\n"
            f"Content: {document['text']}\n"
        )
    context = "\n--------------------\n".join(context_chunks)

    # Step 3: Prepare prompt
    prompt = f"""You are an Enterprise AI Knowledge Assistant.
Answer the user's question accurately using ONLY the provided context below.

Rules:
1. Ground every statement in the context. Do not invent facts or extrapolate.
2. If the context does not contain enough information to answer, state clearly: "The uploaded documents do not contain sufficient information to answer this question."
3. Provide clear, well-structured answers using formatting like bullet points when appropriate.
4. Always cite your sources in brackets like [1], [2] matching the source numbers.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""

    # Step 4: Generate answer using LLM
    try:
        raw_answer = get_llm_response(prompt)
    except Exception as e:
        raw_answer = f"Error communicating with LLM provider: {str(e)}"

    if raw_answer is None:
        answer = (
            "**No LLM API Key Configured.**\n\n"
            "Retrieved relevant context chunks from your uploaded documents (see sources below). "
            "To generate AI synthesis, add your `GROQ_API_KEY` or `GEMINI_API_KEY` to the `.env` file in your project folder."
        )
    else:
        answer = raw_answer

    # Step 5: Prepare citations
    sources = []
    for index, document in enumerate(documents, start=1):
        sources.append({
            "source_number": index,
            "document_name": document["document_name"],
            "page_number": document["page_number"],
            "relevance_score": round(document["score"], 4),
            "snippet": document["text"][:300] + ("..." if len(document["text"]) > 300 else "")
        })

    return {
        "answer": answer,
        "sources": sources
    }
