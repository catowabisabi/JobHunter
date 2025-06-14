# save_pdf.py
import os
import pdfkit
import markdown2


# Configure PDFKit
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')

class SavePDFExporter:
    def __init__(self, pdfkit_config=PDFKIT_CONFIG):
        self.pdfkit_config = pdfkit_config

    def convert_markdown_to_html(self, markdown_content, extra_css=None):
        """Convert markdown content to HTML with proper styling and layout."""
        html_content = markdown2.markdown(
            markdown_content,
            extras=[
                "tables",
                "break-on-newline",
                "fenced-code-blocks",
                "html-classes",
                "div",
                "style"
            ]
        )
        html_css = f"""
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .main-container {{ display: flex; flex-wrap: wrap; }}
            .left-column-content {{ width: 35%; padding-right: 2em; box-sizing: border-box; }}
            .right-column-content {{ width: 65%; box-sizing: border-box; }}
            h1, h2, h3, h4, h5, h6 {{ color: #2c3e50; margin-top: 1em; margin-bottom: 0.5em; }}
            h1 {{ font-size: 2em; }}
            h2 {{ font-size: 1.5em; }}
            h3 {{ font-size: 1.17em; }}
            h4 {{ font-size: 1em; }}
            h5 {{ font-size: 0.83em; }}
            h6 {{ font-size: 0.67em; }}
            strong {{ font-weight: bold; }}
            em {{ font-style: italic; }}
            p {{ margin-bottom: 1em; }}
            ul {{ list-style-type: disc; margin-left: 20px; margin-bottom: 1em; }}
            ul li {{ margin-bottom: 0.5em; }}
            a {{ color: #3498db; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            hr {{ border: 0; height: 1px; background: #ccc; margin: 1em 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 1em; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
        """
        if extra_css:
            html_css += f"<style>{extra_css}</style>"
        final_html = f"""
        <html>
        <head>
            <meta charset=\"UTF-8\">
            {html_css}
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        return final_html

    def save_pdf(self, markdown_content, output_pdf="output_cv_dashboard.pdf", extra_css=None):
        html_content = self.convert_markdown_to_html(markdown_content, extra_css=extra_css)
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_pdf)
        pdfkit.from_string(html_content, output_path, configuration=self.pdfkit_config)
        print(f"PDF saved to: {output_path}")
        return output_path

    def save_debug_html_with_markdown_rendered(self, markdown_content, output_filename="debug_rendered_markdown.html", extra_css=None):
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        html_content = self.convert_markdown_to_html(markdown_content, extra_css=extra_css)
        debug_html_path = os.path.join(output_dir, output_filename)
        with open(debug_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Debug HTML with rendered Markdown saved to: {debug_html_path}")
        return debug_html_path

    def save_pdf_from_html_file(self, html_file_path, output_pdf="output_cv_dashboard.pdf"):
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_pdf)
        pdfkit.from_file(html_file_path, output_path, configuration=self.pdfkit_config)
        print(f"PDF saved to: {output_path}")
        return output_path

if __name__ == '__main__':
    exporter = SavePDFExporter()

    # 指定你已經生成好的 HTML 路徑
    html_file_path = 'output/output_cv_dashboard.html'
    exporter.save_pdf_from_html_file(html_file_path)