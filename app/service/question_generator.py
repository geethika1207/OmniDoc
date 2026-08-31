from groq import AsyncGroq
from app.core.config import settings

# Initializing the async Groq client
client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def ask_groq(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=150
    )
    
    # Returning the text 
    return response.choices[0].message.content.strip()


async def generate_suggested_questions(sample_texts: list):

    if not sample_texts:
        return [
            "What is the main topic of this document?", 
            "Can you summarize the key points?"
        ]


    combined_text = "\n\n".join(sample_texts)[:4000]

    prompt = f"""
        You are an expert analytical assistant. Your task is to generate exactly 3 highly focused, thought-provoking questions based on the provided document excerpts.

        Question Requirements:
        - Target the most critical facts, concepts, or underlying themes in the text.
        - Be highly specific to the content provided. NEVER ask generic questions like "What is this document about?" or "Can you summarize this?"
        - Keep them concise, clear, and designed to test a reader's deep understanding.

        STRICT FORMATTING CONSTRAINTS:
        - Output exactly 3 questions.
        - Place each question on a new line.
        - DO NOT include any numbers (1., 2., 3.), bullet points, or hyphens.
        - DO NOT include any introductory text, conversational filler, or concluding remarks. Just the questions.

        Document Excerpts:
        {combined_text}

    """    

    raw_response = await ask_groq(prompt)
    
    # Clean up the AI's mess. Even if we tell it "no numbers", it sometimes 
    # sneaks in bullet points or "1. ". This loop strips all that garbage out.

    clean_questions = [
        line.strip("- *1234567890. ") 
        for line in raw_response.split('\n') 
        if line.strip()
    ]
    
    return clean_questions