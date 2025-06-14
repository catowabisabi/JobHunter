import json

def get_cl_prompt(job_details, cv_data) :
    return f"""
        Analyze the job posting and my information, then create a professionally written cover letter in HTML.

        Job Details:
        {json.dumps(job_details, indent=2)}

        My Information (select the most relevant parts for this specific role):
        {json.dumps(cv_data, indent=2, ensure_ascii=False)}

        Task:
        1. Analyze the job requirements and my experience
        2. Select the most relevant information for this specific role
        3. Create a targeted cover letter that highlights my best matching qualifications

        Format the cover letter using this exact HTML template:

        <style>
        .cover-letter {{
            font-size: 11pt;
            line-height: 1.5;
        }}
        </style>

        <div class="cover-letter">

        **Dear Hiring Manager,**

        <p>[Opening Paragraph]
        - Mention the specific position and company name
        - Show enthusiasm for the role
        - Mention how you found the position
        - Briefly introduce your most relevant qualification</p>

        <p>[Body Paragraph 1]
        - Summarize your experience relevant to the position
        - Focus on your most relevant achievements
        - Connect your experience to the job requirements</p>

        <p>[Body Paragraph 2]
        - Provide specific examples from your past roles
        - Demonstrate how you've used the required skills
        - Include metrics and results where possible</p>

        <p>[Body Paragraph 3]
        - Highlight your technical proficiencies
        - Emphasize your soft skills (communication, leadership)
        - Mention your portfolio/GitHub if relevant
        - Show how these skills make you a great fit</p>

        <p>[Closing Paragraph]
        - Express appreciation for their consideration
        - Include a strong call to action
        - Show enthusiasm for discussing the role further</p>

        **Sincerely,**<br>
        [Full Name]

        </div>

        Important Requirements:
        1. DO NOT include all information from my data
        2. Select and include ONLY the most relevant information for this specific role
        3. Keep the exact HTML structure and CSS
        4. Use ** for bold text and * for italic text
        5. Keep the tone confident, warm, and professional
        6. Make sure all selected information is accurate
        7. Keep the letter concise and impactful
        8. Avoid generic statements, be specific to this role
        9. Do not add extraneous style code or script tags

        Respond with ONLY the formatted cover letter in HTML, no explanations or additional text.
        """