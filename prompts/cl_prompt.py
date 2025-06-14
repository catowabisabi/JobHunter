import json

def get_cl_prompt(job_details, cv_data):
    return f"""
You are a world-class cover letter writer with a high emotional IQ. Your task is to generate a structured JSON object for a cover letter that is persuasive, tailored, and strategically addresses potential skill gaps.

**Job Description:**
{json.dumps(job_details, indent=2)}

**User's Full CV Information (for context):**
{json.dumps(cv_data, indent=2, ensure_ascii=False)}

**Instructions & Logic:**

1.  **Identify Key Skills:** Analyze the job description and extract the top 3-4 most critical skills or requirements.
2.  **Skill Gap Analysis & Content Strategy:** For each key skill, perform this logic:
    *   **If the user HAS the skill:** Write a compelling sentence or two showcasing this skill with an example from their experience.
    *   **If the user LACKS the skill:** Do not lie. Instead, identify the user's *closest related skill*. Write a sentence that (a) acknowledges the required skill, (b) highlights their strength in the related skill, and (c) expresses a strong, credible desire to learn and bridge the gap (e.g., "While my direct experience is in X, its principles of Y are directly applicable, and I am a fast learner, eager to master Z.").
3.  **Synthesize Body:** Weave the sentences generated above into 1-2 coherent body paragraphs.
4.  **Tone:** The tone should be confident, competent, and honest.

**JSON Output Format:**
The JSON object must follow this exact structure.

```json
{{
  "greeting": "### Dear Hiring Manager,",
  "body": [
    "string (Opening paragraph: State the position and express enthusiasm.)",
    "string (Main body paragraph synthesising the skill gap analysis.)",
    "string (Closing paragraph: Reiterate interest and include a strong call to action.)"
  ],
  "closing": "### Sincerely,",
  "signature": "### Your Full Name"
}}
```

**IMPORTANT:** Respond with ONLY the JSON object. The entire response must be a single, valid JSON. Do not include `\```json` wrappers, explanations, or any other text.
"""