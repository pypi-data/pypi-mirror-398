"""
Prompt template for generating conversation titles.

Generates concise Chinese or English titles based on conversation language.
"""

TITLE_PROMPT = """
Based on the following conversation records,
analyze the language composition and generate a concise, summary title.
If the content is predominantly in Chinese, generate a Chinese title.
If the content is predominantly in English, generate an English title.
Only return the title, do not include any additional explanations or punctuation:
"""
