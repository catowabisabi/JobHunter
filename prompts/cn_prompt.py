import json

def get_cn_prompt(cover_letter_md):
    return f"""
Translate the following English cover letter in Markdown format into Traditional Chinese (繁體中文).
The translated version must also be in pure Markdown format.

**English Cover Letter (Markdown):**
{cover_letter_md}

**Translation Requirements:**
1.  Translate all professional text into natural and fluent Traditional Chinese (繁體中文).
2.  Keep all names (e.g., company names, personal names), dates, and links in their original English form.
3.  Preserve the original Markdown formatting exactly (e.g., paragraph breaks, `**bold**` text, etc.).
4.  The output must be only the translated Markdown text.

**IMPORTANT:** Respond with ONLY the translated cover letter in pure Markdown. Do not include `\```html` or `\```markdown` wrappers, explanations, or any other text.
"""