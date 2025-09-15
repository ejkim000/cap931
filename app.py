import streamlit as st
import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Check if key was loaded
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in .env file")

# Set Hugging Face’s inference library
client = InferenceClient(
    provider="novita",
    api_key=HF_TOKEN,
)

# Set the inputs
st.title("Sales Assistant")

product_name = st.text_input(
    "Product Name",
    placeholder="What product are you selling?")

product_category = st.text_input(
    "Product Category",
    placeholder="This could be one word or a sentence")

competitors = st.text_input(
    "Competitors",
    placeholder="URLs of competitors(similar to the company URL input).")

value_proposition = st.text_input(
    "Value Proposition",
    placeholder="A sentence summarizing the product’s value.")

target_customer = st.text_input(
    "Target Customer",
    placeholder="Name of the person you are trying to sell to.")


# Max file size (2 MB)
MAX_FILE_SIZE = 2 * 1024 * 1024

# Optional file upload : only txt files are allowed
optional_file = st.file_uploader(
    "Optional: Upload a product overview sheet or deck. (Max 2 MB)",
    type=["txt"],
    help="Upload a product overview sheet or deck. (Max 2 MB)"
)

# Create a prompt
prompt = f"""
Here’s a clean and structured **prompt template** you can use to generate a simple one-pager for sales reps. It’s designed so that the LLM knows exactly what to do with the inputs you provide:

---

**Prompt:**

You are a sales assistant that generates concise, insight-driven one-pagers for sales representatives based on publicly available web data.

Use the inputs provided below to research and summarize the target company, its strategy, leadership, and competitive environment. Then create a **one-page briefing** with the following sections:

### **Inputs**

1. **Product Name:** {product_name}
2. **Product Category:** {product_category}
3. **Competitors:** {competitors}
4. **Value Proposition:** {value_proposition}
5. **Target Customer:** {target_customer}
6. **Optional Product Overview File:** {optional_file}

---

### **Output Structure (One-Pager)**

**1. Company Strategy**

* Summarize the company’s activities in the relevant industry/product area.
* Highlight any public statements, press releases, or executive interviews relevant to the product category.
* Extract signals from job postings (skills, technologies, roles) that hint at the company’s strategy or stack.

**2. Competitor Mentions**

* Note where the company has mentioned or competed against the provided competitors.
* Provide supporting context from articles or press releases.

**3. Leadership Information**

* List key leaders (e.g., CDO, CTO, CCO) with names, titles, and relevance.
* Highlight leaders quoted in press releases or articles in the past 12 months.

**4. Product/Strategy Summary (Public Companies Only)**

* Summarize insights from the company’s 10-Ks, annual reports, or other regulatory filings.
* Include high-level positioning relevant to the product category.

**5. Article & Source Links**

* Provide direct links to referenced articles, press releases, job postings, and filings.

---

**Formatting Instructions**

* Keep the one-pager **short, clear, and actionable** (ideally one screen/page).
* Use **bullet points** for clarity.
* Include source links inline or at the bottom of each section.
* Maintain a professional, sales-focused tone.

---
"""

# Check the result's session
if "result" not in st.session_state:
    st.session_state.result = ""

# Create a "Run" button with the "Thinking..." spinner while waiting for the result
if st.button("Run"):
    with st.spinner("Thinking..."):
        file_content = ""

        if optional_file is not None:
            if optional_file.size > MAX_FILE_SIZE:
                st.error("File too large! Please upload a file smaller than 2 MB.")
            else:
                raw_bytes = optional_file.read()
                try:
                    # Try decoding as UTF-8 (works for txt/markdown/csv)
                    file_content = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    # For non-text files (pdf/docx/pptx), you’d need parsing libraries
                    file_content = "[Uploaded file is binary and not directly readable.]"

        # Build final prompt
        final_prompt = prompt
        if file_content:
            final_prompt += f"\n\n---\nFile content:\n{file_content}"

        # Only call LLM if not empty
        if final_prompt.strip():
            completion = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3-8B-Instruct",
                messages=[{"role": "user", "content": final_prompt}],
            )

            #st.write(completion.choices[0].message["content"])

            # Save result to session
            st.session_state.result = completion.choices[0].message.content

        else:
            st.warning("Please enter a prompt or upload a file before running.")


# Show result if result's session exists
if st.session_state.result:
    st.write(st.session_state.result)

    # Download button : download result to text file
    st.download_button(
        label="Download Result",
        data=st.session_state.result,
        file_name=f"sales_insight_{product_name}.txt",
        mime="text/plain"
    )