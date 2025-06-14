cv_styles = """
/* General Body Styling */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.5;
    color: #333;
    max-width: 900px;
    margin: 0 auto;
    padding: 30px;
    background-color: #f8f9fa;
}

/* Header Section (Name, Title, Contact) */
h1 {
    font-size: 2.8em;
    color: #2c3e50;
    margin-bottom: 0.2em;
    text-align: center;
}

body > p:first-of-type {
    font-size: 1.2em;
    color: #555;
    margin-top: 0;
    margin-bottom: 1em;
    text-align: center;
}

body > p:nth-of-type(2) {
    font-size: 0.95em;
    color: #777;
    margin-top: -0.5em;
    margin-bottom: 2em;
    text-align: center;
}

a {
    color: #007bff;
    text-decoration: none;
    transition: color 0.3s ease;
}

a:hover {
    color: #0056b3;
    text-decoration: underline;
}

hr {
    border: 0;
    height: 1px;
    background: #e0e0e0;
    margin: 2em 0;
}

/* Main Layout (Flexbox Dashboard Columns) */
.main-container {
    display: flex;
    flex-wrap: nowrap;
    gap: 20px;
    margin-top: 0;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    background-color: #fff;
    padding: 20px;
    border-radius: 8px;
    align-items: flex-start;
}

.left-column-content, .right-column-content {
    padding: 15px;
    box-sizing: border-box;
    float: none !important;
    line-height: 1.6;
}

.left-column-content {
    width: 35%;
    border-right: 1px solid #eee;
}

.right-column-content {
    width: 65%;
}

/* Responsive adjustments for smaller screens */
@media (max-width: 768px) {
    .left-column-content, .right-column-content {
        width: 100%;
        border-right: none;
        padding-right: 0;
    }
}

/* Section Headings - Unified style for all sections */
h2 {
    font-size: 1.8em;
    color: #34495e;
    border-bottom: 2px solid #007bff;
    padding-bottom: 5px;
    margin-top: 1.5em;
    margin-bottom: 0.8em;
    text-align: left;
}

h2:first-of-type {
    margin-top: 0;
}

/* Skills 標題特別樣式 */
.left-column-content h2 {
    font-size: 2.2em; /* 技能標題更大一點 */
    margin-bottom: 0.4em; /* 進一步縮短與技能內容的距離 */
}

/* Content Styling */
p {
    margin-bottom: 1em;
    text-align: justify;
    text-justify: inter-word;
}

strong {
    font-weight: 700;
    color: #444;
}

em {
    font-style: italic;
    color: #666;
}

/* Education Section Styling */
.left-column-content > p {
    margin-bottom: 0.2em;
}

/* University name styling - 不用左右對齊，城市放在名字後面同一行 */
.left-column-content strong {
    display: inline; /* 改為inline，這樣城市可以跟在後面 */
    font-size: 1.1em;
    color: #2c3e50;
    font-weight: 700;
}

/* Program name 加粗 */
.left-column-content p:nth-child(even):not(:has(strong)):not(:has(em)) {
    font-weight: 700; /* Program name 加粗 */
    color: #2c3e50;
}

/* 確保城市和大學名稱在同一行 */
.education-entry {
    margin-bottom: 1.2em;
}

.education-entry .university-city {
    font-size: 1.1em;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 0.2em;
    text-align: left;
}

.education-entry .program {
    font-size: 0.9em;
    font-weight: 600;
    color: #2c3e50;
    margin: 0.2em 0;
    text-align: left;
}

.education-entry .dates {
    font-style: italic;
    color: #666;
    font-size: 0.9em;
    margin: 0.2em 0;
}

/* 日期斜體 */
.left-column-content em,
.right-column-content em {
    font-style: italic;
    color: #666;
    font-size: 0.95em;
}

/* Experience Section Styling */
.experience-entry {
    margin-bottom: 1.5em;
}

.experience-entry .position {
    font-size: 1.3em;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 0.2em;
    display: block;
}

.experience-entry .company-city {
    font-size: 1em;
    font-weight: 600;
    color: #444;
    margin-bottom: 0.2em;
}

.experience-entry .dates {
    font-style: italic;
    color: #666;
    font-size: 0.95em;
    margin-bottom: 0.8em;
}

/* 工作描述列表的特殊樣式 */
.experience-entry ul {
    margin-left: 0;
    padding-left: 20px; /* 整個列表內進 */
}

.experience-entry li {
    text-align: left;
    padding-left: 10px; /* 內容進一步縮進 */
    margin-bottom: 0.6em;
    list-style-position: outside; /* 確保bullet在外面 */
    line-height: 1.6;
}

/* 確保多行文字對齊文字而不是對齊點 */
.experience-entry li::marker {
    color: #666;
}

/* 多行文字的縮進對齊 */
.experience-entry li {
    text-indent: 0;
    hanging-indent: 0;
}

/* Skills Section */
.skills-section {
    margin-top: 1.5em;
}

.skills-section h3 {
    color: #2c3e50;
    font-size: 1.2em;
    margin-bottom: 0.5em;
}

.skills-section ul {
    margin-bottom: 1.2em;
}

"""