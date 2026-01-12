import markdown
from xhtml2pdf import pisa
import io

def markdown_to_pdf(markdown_file, pdf_file):
    """Convert markdown file to PDF with styling"""

    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])

    # Add CSS styling
    css_content = """
    @page {
        size: A4;
        margin: 2cm;
    }

    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        font-size: 11pt;
    }

    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        font-size: 24pt;
        margin-top: 20px;
    }

    h2 {
        color: #34495e;
        border-bottom: 2px solid #95a5a6;
        padding-bottom: 8px;
        font-size: 18pt;
        margin-top: 20px;
        page-break-before: auto;
    }

    h3, h4 {
        color: #555;
        font-size: 14pt;
        margin-top: 15px;
    }

    table {
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
    }

    th {
        background-color: #3498db;
        color: white;
        padding: 10px;
        text-align: left;
        font-weight: bold;
    }

    td {
        border: 1px solid #ddd;
        padding: 8px;
    }

    tr:nth-child(even) {
        background-color: #f9f9f9;
    }

    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 9pt;
    }

    pre {
        background-color: #f4f4f4;
        padding: 10px;
        border-left: 3px solid #3498db;
        overflow-x: auto;
    }

    ul, ol {
        margin-left: 20px;
    }

    li {
        margin: 5px 0;
    }

    strong {
        color: #2c3e50;
    }

    hr {
        border: none;
        border-top: 2px solid #ecf0f1;
        margin: 20px 0;
    }

    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 15px;
        margin-left: 0;
        color: #555;
        font-style: italic;
    }
    """

    # Create full HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>AI Platform Analytics Report</title>
        <style>
            {css_content}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert HTML to PDF
    with open(pdf_file, 'wb') as output:
        pisa_status = pisa.CreatePDF(
            full_html.encode('utf-8'),
            dest=output
        )

    if pisa_status.err:
        print(f"[ERROR] PDF generation failed")
        return False
    else:
        print(f"[SUCCESS] PDF generated: {pdf_file}")
        return True

if __name__ == "__main__":
    markdown_file = "AI_Platform_Analytics_Report.md"
    pdf_file = "AI_Platform_Analytics_Report.pdf"

    markdown_to_pdf(markdown_file, pdf_file)
