from groq import AsyncGroq
from app.core.config import settings
import re

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
    
    clean_questions = []
    
    #Cleaning: Loop through the AI's response line by line
    for line in raw_response.split('\n'):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Skipping obvious AI conversational filler that slipped through 
        lower_line = line.lower()
        if "here are" in lower_line or "sure" in lower_line or "questions:" in lower_line:
            continue
            
        # Use Regex to  strip prefixes. 
        # This removes: "1.", "1)", "- ", "* ", "Q:", "Q1:", "Question 1:", etc.
        line = re.sub(r"^(?:[\d\.\-\*\)\s]+|q(?:uestion)?\s*\d*[\.\:\)]?\s*)", "", line, flags=re.IGNORECASE)
        
        # Strip stray quotation marks or markdown bolding the AI might have wrapped the text in
        line = line.strip("\"'* ")
        
        # If there is still a valid string left (more than 5 chars), save it
        if len(line) > 5:
            clean_questions.append(line)
            
    # Fallback: Just in case the AI completely glitched and we filtered everything out
    if not clean_questions:
        return [
            "What is the main topic of this document?", 
            "Can you summarize the key points?"
        ]
        
    # give exactly 3 questions
    return clean_questions[:3]