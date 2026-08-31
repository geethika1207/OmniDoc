import asyncio

async def extract_pdf_content(reader):
    page_texts = []
    total_pages = len(reader.pages)

    #Read every page and store it in a list
    for page in reader.pages:
        extracted = page.extract_text()
        
        if extracted:
            page_texts.append(extracted)
        else:
            page_texts.append("")
            
        # Yields control so the server doesn't freeze on huge PDFs
        await asyncio.sleep(0) 

    # Combine the list into one giant string for the full text
    full_text = ""
    for text in page_texts:
        full_text = full_text + text + "\n"

    #Figure out where to get the sample text
    if total_pages > 4:
        start_idx = 3
    else:
        start_idx = 0

    # Get just 2 pages for the sample
    sample_slice = page_texts[start_idx : start_idx + 2]
    
    file_sample = ""
    
    for text in sample_slice:
        file_sample = file_sample + text
        
    file_sample = file_sample.strip()
    file_sample = file_sample[:1500]

    return full_text, file_sample