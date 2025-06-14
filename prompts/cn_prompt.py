import json

def get_cn_prompt(cover_letter_md) :
    return f"""
        Translate the following English cover letter into Traditional Chinese (繁體中文) while maintaining the same HTML structure and professional tone.
        Keep all formatting, dates, and names in their original form.

        English Cover Letter:
        {cover_letter_md}

        Requirements:
        1. Maintain the same HTML structure and CSS
        2. Keep the same professional tone
        3. Ensure the translation is natural and fluent in Traditional Chinese (繁體中文)
        4. Keep all dates, names, and company information in their original form
        5. Maintain the same level of formality
        6. Keep all HTML tags and formatting intact
        7. Do not add any additional styling or scripts
        8. Use Traditional Chinese characters (繁體中文) for all translated content
        9. Keep the same font size and line height settings

        Respond with ONLY the translated cover letter in HTML, no explanations or additional text.
        """