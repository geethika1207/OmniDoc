import asyncio

async def extract_pdf_content(reader):
    page_texts = []
    total_pages = len(reader.pages)

    # Read every page and store it in a list
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            page_texts.append(extracted)
        else:
            page_texts.append("")
            
        # Yields control so the server doesn't freeze on huge PDFs
        await asyncio.sleep(0) 

    # Combine all pages for full text
    full_text = "\n".join(page_texts)

    # Take the LAST 3 pages (Conclusions, Recommendations, Key Findings)
    if total_pages > 3:
        sample_slice = page_texts[-3:]
    else:
        sample_slice = page_texts

    file_sample = "\n\n".join(sample_slice).strip()
    file_sample = file_sample[:3500]

    return full_text, file_sample