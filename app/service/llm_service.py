from typing import AsyncGenerator
import litellm
from litellm import token_counter
from app.core.config import settings


# Map internal provider keys to the exact LiteLLM model strings
MODELS = {
    "groq": "groq/openai/gpt-oss-120b",
    "cohere": "cohere/command-r-08-2024",
    "gemini": "gemini/gemini-2.0-flash"
}


API_KEYS = {
    "groq": settings.GROQ_API_KEY,
    "cohere": settings.COHERE_API_KEY,
    "gemini": settings.GEMINI_API_KEY
}

# Define strict routing thresholds to balance speed, cost, and rate limits

GROQ_LIMIT = 4000          
COHERE_LIMIT = 80000       
GEMINI_MAX_LIMIT = 1000000 



def build_messages(context: str, question: str):
    system_prompt = (
        "You are an expert Academic Study Assistant and Document Analyst. "
        "Your goal is to provide crystal-clear, highly structured, and readable answers based strictly on the provided context.\n\n"
        "### STRICT FORMATTING & STRUCTURAL RULES:\n"
        "1. **Visual Hierarchy & Formatting**:\n"
        "   - Never output a single dense wall of text.\n"
        "   - Use clear Markdown headings (`### Core Concepts`, `### Key Takeaways`, `### Detailed Breakdown`).\n"
        "   - Use **bold text** for key terminology, definitions, and formulas.\n"
        "   - Use bullet points (`- `) with clear spacing for lists, properties, and explanations.\n"
        "   - When comparing two or more concepts (e.g. IR vs DBMS), ALWAYS use a clean Markdown **comparison table**.\n\n"
        "2. **Summary & Concept Explanation Guidelines**:\n"
        "   - When asked for a summary or explanation, organize the answer into: \n"
        "     1. **Overview / Executive Summary** (2-3 concise sentences)\n"
        "     2. **Key Topics & Principles** (structured bullet points with bold terms)\n"
        "     3. **Important Formulas / Metrics** (if applicable)\n\n"
        "3. **Strict Context Grounding**:\n"
        "   - Base your answer EXCLUSIVELY on the factual information provided in the Context.\n"
        "   - If the context does not contain enough information, state: 'Based on the provided context, I do not have sufficient details to answer this.'\n"
        "   - Avoid conversational filler (do NOT say 'Based on the context...'). Start directly with the formatted answer."
    )


    user_prompt = f"### Context:\n{context}\n\n### Question:\n{question}\n\n### Formatted Answer:"

    # Structuring the user prompt for the context and query
    user_prompt = f"### Context:\n{context}\n\n### Question:\n{question}\n\n### Answer:"

    # Returning standard LiteLLM chat completion message schema
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]



async def stream_completion(context: str, question: str) -> AsyncGenerator[str, None]:

    messages = build_messages(context, question)
    
    # Count the tokens to figure out how big the token is
    token_count = token_counter(model="gpt-3.5-turbo", messages=messages)

    # If the document is way too huge (over 1M tokens), have to chop it down

    if token_count > GEMINI_MAX_LIMIT:

        # Leaving a 2,000 token buffer for the system prompt, assuming ~4 chars per token
        max_allowed_chars = (GEMINI_MAX_LIMIT - 2000) * 4
        
        # Slice off the extra text so the API doesn't crash with a length error
        context = context[:max_allowed_chars]
        
        # Rebuild the messages and recount just checking for safe
        messages = build_messages(context, question)
        token_count = token_counter(model="gpt-3.5-turbo", messages=messages)

        
    # Pick the right LLM based on the size of the request

    if token_count <= GROQ_LIMIT:
        # Use Groq for small context because it's super fast
        chosen_provider = "groq"

    elif token_count <= COHERE_LIMIT:
        # Command-R handles medium-sized context well
        chosen_provider = "cohere"

    else:
        # Fallback to Gemini for massive documents
        chosen_provider = "gemini"

        
    exact_model = MODELS[chosen_provider]
    chosen_api_key = API_KEYS[chosen_provider]

    
    # stream=True  gives us the typing effect
    response = await litellm.acompletion(
        model=exact_model,
        messages=messages,
        api_key=chosen_api_key,
        stream=True
    )
    

    async for chunk in response:
        # Make sure the chunk isn't empty or broken
        if chunk.choices and len(chunk.choices) > 0:

            # Using getattr prevents a crash if 'content' happens to be missing
            delta = getattr(chunk.choices[0].delta, "content", None)
            
            # If there's actual text, give to the frontend
            if delta:
                yield delta