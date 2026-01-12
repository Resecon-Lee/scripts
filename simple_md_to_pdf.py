import markdown
import subprocess
import os

def markdown_to_pdf_via_html(markdown_file, pdf_file):
    """Convert markdown to PDF via HTML intermediate"""

    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Convert markdown to HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'nl2br']
    )

    # CSS for better formatting
    css = """
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
        }
        h2 {
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 25px;
        }
        h3, h4 {
            color: #555;
            margin-top: 20px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            box-shadow: 0 2px 3px rgba(0,0,0,0.1);
        }
        th {
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        td {
            border: 1px solid #ddd;
            padding: 10px;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background-color: #f4f4f4;
            padding: 15px;
            border-left: 4px solid #3498db;
            overflow-x: auto;
        }
        ul, ol {
            margin-left: 25px;
        }
        li {
            margin: 8px 0;
        }
        strong {
            color: #2c3e50;
            font-weight: 600;
        }
        hr {
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin-left: 0;
            color: #555;
            font-style: italic;
        }
    </style>
    """

    # Create full HTML
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI Platform Analytics Report</title>
    {css}
</head>
<body>
{html_content}
</body>
</html>"""

    # Save HTML file
    html_file = markdown_file.replace('.md', '.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"[INFO] HTML file created: {html_file}")

    # Try to use system tools to convert to PDF
    # Try wkhtmltopdf if available
    try:
        result = subprocess.run(
            ['wkhtmltopdf', '--enable-local-file-access', html_file, pdf_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"[SUCCESS] PDF generated using wkhtmltopdf: {pdf_file}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # If wkhtmltopdf fails, keep the HTML and suggest manual conversion
    print(f"[INFO] wkhtmltopdf not found. HTML file saved as: {html_file}")
    print(f"[INFO] You can:")
    print(f"       1. Open {html_file} in a browser and use 'Print to PDF'")
    print(f"       2. Install wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html")
    print(f"       3. Use an online converter")

    # Try using Chrome/Edge in headless mode if available
    browsers = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
    ]

    for browser in browsers:
        if os.path.exists(browser):
            try:
                print(f"[INFO] Trying to use {os.path.basename(browser)} for PDF conversion...")
                result = subprocess.run(
                    [browser, '--headless', '--disable-gpu', f'--print-to-pdf={pdf_file}',
                     f'file:///{os.path.abspath(html_file).replace(chr(92), "/")}'],
                    capture_output=True,
                    timeout=30
                )
                if os.path.exists(pdf_file):
                    print(f"[SUCCESS] PDF generated using {os.path.basename(browser)}: {pdf_file}")
                    return True
            except (subprocess.TimeoutExpired, Exception) as e:
                continue

    return False

if __name__ == "__main__":
    markdown_file = "AI_Platform_Analytics_Report.md"
    pdf_file = "AI_Platform_Analytics_Report.pdf"

    success = markdown_to_pdf_via_html(markdown_file, pdf_file)

    if not success:
        print("\n[ALTERNATIVE] Opening HTML file for manual PDF conversion...")
        html_file = markdown_file.replace('.md', '.html')
        os.system(f'start "" "{html_file}"')
