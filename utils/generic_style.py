generic_styles = """
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333333;
    max-width: 8.5in;
    margin: 0 auto;
    padding: 1in;
    background-color: #ffffff;
    font-size: 12pt;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: #2c3e50;
    margin-top: 1.5em;
    margin-bottom: 0.8em;
    line-height: 1.3;
    text-align: left; /* Ensure all headings are left-aligned */
}

h1 { font-size: 2.2em; }
h2 { font-size: 1.8em; border-bottom: 1px solid #dddddd; padding-bottom: 5px; }
h3 { font-size: 1.5em; }
h4 { font-size: 1.2em; }

/* Paragraphs */
p {
    margin-bottom: 1em;
    text-align: left; /* Ensure paragraphs are left-aligned */
    text-justify: inter-word;
}

/* Links */
a {
    color: #007bff;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* Lists */
ul, ol {
    padding-left: 25px;
    margin-bottom: 1em;
}

li {
    margin-bottom: 0.5em;
}

/* Code Blocks */
pre {
    background-color: #f4f4f4;
    padding: 15px;
    border-radius: 4px;
    overflow-x: auto;
    font-family: 'Courier New', Courier, monospace;
}

code {
    font-family: 'Courier New', Courier, monospace;
    background-color: #f4f4f4;
    padding: 2px 4px;
    border-radius: 2px;
}

pre code {
    padding: 0;
    background-color: transparent;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.5em;
}

th, td {
    border: 1px solid #dddddd;
    padding: 8px;
    text-align: left;
}

th {
    background-color: #f2f2f2;
    font-weight: bold;
}

/* Horizontal Rule */
hr {
    border: 0;
    height: 1px;
    background: #e0e0e0;
    margin: 2em 0;
}
""" 