import pymupdf


def extract_resume_text(pdf_bytes: bytes) -> str:
    # Open the PDF file from memory
    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    ) as document:

        # Store text from every page
        pages = []

        for page in document:
            text = page.get_text()
            pages.append(text)

        # Combine all pages into one text
        resume_text = "\n".join(pages).strip()

    # Check whether the PDF contains readable text
    if not resume_text:
        raise ValueError(
            "No readable text found in the PDF."
        )

    return resume_text