import json

def get_cv_prompt(job_details, cv_data):
    return f"""
You are an expert ATS-optimized resume writer and data structurer. Your task is to analyze the user's information and the job description, then generate a structured JSON object representing a highly tailored, ATS-friendly CV.

**Job Description:**
{job_details['description']}

**User's Full CV Information:**
{cv_data}

**Instructions & Logic:**

1.  **Analyze Job Type:** First, determine if the job is primarily 'IT/Technical' or 'Design/Creative'. This is crucial for the next step.
2.  **Conditional Links:**
    *   If the job is 'IT/Technical', include the `github` URL in the `personal_info` object.
    *   If the job is 'Design/Creative', include the `portfolio` URL.
    *   If it's neither or a mix, do not include either link to keep it focused.
3.  **Intelligent Summary:**
    *   Deeply analyze the user's entire profile (experience, skills, education) against the job description.
    *   Craft a **Professional Summary** that is a perfect synthesis of the user's strengths as they relate to the job's key requirements. Do not just list skills; create a compelling narrative.
4.  **Relevant Experience:**
    *   From the user's full experience, select **only the most relevant** positions for this specific job. Omit irrelevant ones.
    *   For each selected position, rewrite the `responsibilities` to subtly embed keywords from the job description. The language must sound natural and achievement-oriented.
5.  **Keyword Integration:** The primary goal is to naturally weave keywords from the job description throughout the `summary` and `experience` sections.
6.  **Full Education History:** Include all education entries provided by the user, do not omit any.

**JSON Output Format:**
The JSON object must follow this exact structure. Note that the `skills` field has been intentionally omitted.

```json
{{
  "personal_info": {{
    "full_name": "string",
    "title": "string (The most relevant title for the job)",
    "location": "string",
    "phone": "string",
    "email": "string",
    "portfolio": "string (URL, ONLY if Design/Creative job)",
    "github": "string (URL, ONLY if IT/Technical job)"
  }},
  "summary": "string (A compelling, tailored summary with keywords integrated.)",
  "experience": [
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "period": "string",
      "responsibilities": [
        "string (Achievement-oriented responsibility with integrated keywords.)"
      ]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "institution": "string",
      "period": "string",
      "details": [ "string" ]
    }}
  ]
}}
```

**IMPORTANT:** Respond with ONLY the JSON object. The entire response must be a single, valid JSON. Do not include `\```json` wrappers, explanations, or any other text.
"""