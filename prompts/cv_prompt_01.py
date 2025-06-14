import json

def get_cv_prompt(job_details, cv_data) :
    return  f"""
        Analyze the job posting and my information, then create a modern two-column CV by selecting the most relevant information.

        Job Details:
        {json.dumps(job_details, indent=2)}

        My Information (select the most relevant parts for this specific role):
        {json.dumps(cv_data, indent=2, ensure_ascii=False)}

        Task:
        1. Analyze the job requirements and my experience
        2. Select the most relevant information for this specific role
        3. Create a targeted CV that highlights my best matching qualifications

        Decisions to make:
        - Which title best matches the role?
        - Which skills are most relevant?
        - Which work experiences best demonstrate my fit for the role?
        - Which education details are most important?
        - Should I include portfolio links? (for design/art/PM roles)
        - Should I include GitHub? (for IT roles)
        - Which achievements best match the job requirements?

        Format the CV using this exact template:

        # [Full Name]  
        **[Selected Most Relevant Job Title]**  
        [Phone] | [Email] | [Location] | [Selected Portfolio/GitHub if relevant]

        ---

        <div style="display: flex;">
        <div style="width: 35%; padding-right: 2em; float: left;">

        ## Education

        **[University Name]**, [Location]  
        [Degree Title]  
        [Start Date] – [End Date]  
        - [Education Bullet Point]

        (repeat for each relevant education)

        ---

        ## Skills

        **[Category Title]**  
        - [Selected Skill 1]  
        - [Selected Skill 2]  

        (repeat categories as needed)

        </div>
        <div style="width: 65%; float: left;">

        ## Professional Summary
        [Write a compelling summary focusing on the selected relevant qualifications]

        ---

        ## Professional Experience

        **[Company Name]**, [Location]  
        *[Job Title]*  
        [Start Date] – [End Date]  
        - [Selected Achievement 1]  
        - [Selected Achievement 2]  
        - [Selected Achievement 3]  

        (repeat for each relevant position)

        </div>
        </div>

        Important Requirements:
        1. DO NOT include all information from my data
        2. Select and include ONLY the most relevant information for this specific role
        3. Keep the exact HTML-like div structure for layout
        4. Focus on achievements and results that match the job requirements
        5. Use bullet points for better readability
        6. Make sure all selected information is accurate
        7. Do not use emoji or icons
        8. Do not include table borders
        9. Keep the formatting clean and professional

        Respond with ONLY the formatted CV in Markdown with inline HTML blocks, no explanations or additional text.
        """