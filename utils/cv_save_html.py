import os
import markdown2
import re # Import the re module for regular expressions

# Separated CSS as a string
from cv_style import cv_styles

class CVHtmlExporter:
    def __init__(self, css_styles):
        self.css_styles = css_styles

    def parse_education_section(self, education_content):
        """
        Parse education section and structure it with proper HTML classes
        """
        # Split by university entries (looking for lines that start with **)
        entries = re.split(r'\n(?=\*\*)', education_content.strip())
        
        structured_html = ""
        for entry in entries:
            if not entry.strip():
                continue
            
            # Split into lines first to separate main content and bullet points
            lines = entry.strip().split('\n')
            if len(lines) < 3:
                continue
            
            # 處理 university name，只取逗號前的內容，並處理 markdown bold
            university_line_raw = lines[0].strip()
            # 取 **之間的內容
            match = re.match(r'\*\*(.*?)\*\*', university_line_raw)
            if match:
                university_name = match.group(1).strip()
            else:
                # fallback: 取逗號前
                university_name = university_line_raw.split(',')[0].replace('**','').strip()
            # program name
            program_line = lines[1].strip() if len(lines) > 1 else ""
            # dates
            dates_line = lines[2].strip() if len(lines) > 2 else ""
            
            # Extract and convert bullet points separately
            bullet_points = []
            bullet_content = '\n'.join(lines[3:])
            if bullet_content.strip():
                bullet_html = markdown2.markdown(bullet_content)
                for line in bullet_html.split('\n'):
                    if '<li>' in line:
                        point = line.replace('<li>', '').replace('</li>', '').strip()
                        bullet_points.append(point)
        
            # Create structured HTML for education entry
            structured_html += f'''
            <div class="education-entry">
                <p class="university-city">{university_name}</p>
                <p class="program">{program_line}</p>
                <p class="dates"><em>{dates_line}</em></p>
            '''
            
            if bullet_points:
                structured_html += "<ul>\n"
                for point in bullet_points:
                    structured_html += f"                <li>{point}</li>\n"
                structured_html += "            </ul>\n"
            
            structured_html += "        </div>\n"
        
        return structured_html


    def parse_experience_section(self, experience_content):
        """
        Parse experience section and structure it with proper HTML classes
        """
        # Split by company entries (looking for lines that start with **)
        entries = re.split(r'\n(?=\*\*)', experience_content.strip())
        
        structured_html = ""
        for entry in entries:
            if not entry.strip():
                continue
            
            lines = entry.strip().split('\n')
            if len(lines) < 3:
                continue
        
            # First line should be company and city
            company_line = lines[0]
            # Second line should be position
            position_line = lines[1].strip('*').strip() if len(lines) > 1 else ""
            # Third line should be dates
            dates_line = lines[2] if len(lines) > 2 else ""
            
            # Extract bullet points
            bullet_points = []
            for line in lines[3:]:
                if line.strip().startswith('-'):
                    bullet_points.append(line.strip()[1:].strip())
        
            # Create structured HTML for experience entry
            structured_html += f'''
            <div class="experience-entry">
                <p class="position">{position_line}</p>
                <p class="company-city">{company_line}</p>
                <p class="dates"><em>{dates_line}</em></p>
            '''
            
            if bullet_points:
                structured_html += "            <ul>\n"
                for point in bullet_points:
                    structured_html += f"                <li>{point}</li>\n"
                structured_html += "            </ul>\n"
            
            structured_html += "        </div>\n"
        
        return structured_html


    def save_html(self, markdown_content, output_filename="output_cv_dashboard.html"):
        """
        Converts markdown content to HTML, handling embedded HTML divs properly,
        applies necessary layout and styling from a separate CSS string,
        and saves the result to an HTML file for inspection.
        """
        
        # Split the original markdown content into header and body sections based on the first '---'
        header_separator = "---"
        header_end_index = markdown_content.find(header_separator)

        # Extract the header markdown
        md_before_main_div_section = markdown_content[:header_end_index].strip()
        
        # Extract the section containing the two columns (starts after the first '---')
        md_columns_section_with_html = markdown_content[header_end_index + len(header_separator):].strip()

        # Convert the header section to HTML
        html_pre_main = markdown2.markdown(
            md_before_main_div_section,
            extras=["tables", "break-on-newline", "fenced-code-blocks", "html-classes"]
        )

        # Use regex to robustly extract content within the specific column divs
        left_col_pattern = re.compile(r'<div style="width: 35%;[^>]*>([\s\S]*?)</div>')
        right_col_pattern = re.compile(r'<div style="width: 65%;[^>]*>([\s\S]*?)</div>')

        left_match = left_col_pattern.search(md_columns_section_with_html)
        right_match = right_col_pattern.search(md_columns_section_with_html)

        left_col_markdown_content = ""
        right_col_markdown_content = ""

        if left_match:
            left_col_markdown_content = left_match.group(1).strip()
        else:
            print("Warning: Could not find left column content using regex.")

        if right_match:
            right_col_markdown_content = right_match.group(1).strip()
        else:
            print("Warning: Could not find right column content using regex.")

        # Parse left column (Education and Skills)
        left_sections = left_col_markdown_content.split('## ')
        html_left_col = ""
        
        for section in left_sections:
            if not section.strip():
                continue
            
            if section.startswith('Education'):
                education_content = section.replace('Education', '').strip()
                # Split by the skills section
                if '## Skills' in education_content:
                    education_content = education_content.split('## Skills')[0].strip()
                
                html_left_col += "<h2>Education</h2>\n"
                html_left_col += self.parse_education_section(education_content)
                
            elif section.startswith('Skills'):
                skills_content = section.replace('Skills', '').strip()
                html_left_col += "<hr>\n<h2>Skills</h2>\n"
                
                # Convert skills section normally
                skills_html = markdown2.markdown(
                    skills_content,
                    extras=["tables", "break-on-newline", "fenced-code-blocks", "html-classes"]
                )
                html_left_col += skills_html

        # Parse right column (Professional Summary and Experience)
        right_sections = right_col_markdown_content.split('## ')
        html_right_col = ""
        
        for section in right_sections:
            if not section.strip():
                continue
            
            if section.startswith('Professional Summary'):
                summary_content = section.replace('Professional Summary', '').strip()
                html_right_col += "<h2>Professional Summary</h2>\n"
                
                # Convert summary normally
                summary_html = markdown2.markdown(
                    summary_content.split('---')[0].strip(),
                    extras=["tables", "break-on-newline", "fenced-code-blocks", "html-classes"]
                )
                html_right_col += summary_html
                html_right_col += "<hr>\n"
                
            elif section.startswith('Professional Experience'):
                experience_content = section.replace('Professional Experience', '').strip()
                html_right_col += "<h2>Professional Experience</h2>\n"
                html_right_col += self.parse_experience_section(experience_content)

        # Step 3: Reconstruct the final HTML body content
        reconstructed_html_body_content = f"""
        {html_pre_main}
        <div class="main-container">
            <div class="left-column-content">
                {html_left_col}
            </div>
            <div class="right-column-content">
                {html_right_col}
            </div>
        </div>
        """

        # Wrap the body content with a complete HTML structure and inject CSS
        final_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard CV</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
            <style>
                {self.css_styles}
            </style>
        </head>
        <body>
            {reconstructed_html_body_content}
        </body>
        </html>
        """

        # 4. Save the final HTML to a file
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, output_filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_html)

        return file_path

# Example of how to use this class
if __name__ == '__main__':
    # 使用 cv_md 作為輸入
    from test_string import cv_md
    exporter = CVHtmlExporter(cv_styles)
    html_file = exporter.save_html(cv_md)
    print(f"HTML file saved successfully to: {html_file}")
    print(f"Please open '{html_file}' in your web browser to check the Markdown rendering and layout.")
    print("Also, consider opening the file in a text editor to verify that Markdown syntax (like #, **, -) has been converted into corresponding HTML tags (like <h1>, <strong>, <ul><li>).")