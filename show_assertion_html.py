"""
Generate HTML visualization showing assertions matched to response segments.
"""

import json
import html
import argparse
import webbrowser
import os
from typing import List, Dict

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text)

def highlight_matches_in_response(response: str, matched_segments: List[str]) -> str:
    """
    Highlight matched segments in the response text.
    Returns HTML with highlighted spans.
    """
    if not matched_segments:
        return escape_html(response)
    
    result = response
    
    # Sort matches by length (longest first) to avoid partial overlaps
    sorted_matches = sorted(matched_segments, key=len, reverse=True)
    
    # Replace each match with a placeholder first to avoid double-replacement
    placeholders = {}
    for i, match in enumerate(sorted_matches):
        placeholder = f"__MATCH_{i}__"
        if match in result:
            placeholders[placeholder] = match
            result = result.replace(match, placeholder, 1)
    
    # Escape HTML in the remaining text
    result = escape_html(result)
    
    # Replace placeholders with highlighted versions
    for placeholder, match in placeholders.items():
        highlighted = f'<span class="highlight">{escape_html(match)}</span>'
        result = result.replace(escape_html(placeholder), highlighted)
    
    return result

def generate_html(data: List[Dict], output_path: str):
    """Generate HTML file showing assertions with matched segments."""
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Assertion Matches Visualization</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #0078d4;
            padding-bottom: 10px;
        }
        .meeting {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .meeting-header {
            background: #0078d4;
            color: white;
            margin: -20px -20px 20px -20px;
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
        }
        .meeting-header h2 {
            margin: 0;
            font-size: 18px;
        }
        .utterance {
            background: #e8f4ff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-left: 4px solid #0078d4;
        }
        .response {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            line-height: 1.6;
            white-space: pre-wrap;
            font-size: 14px;
        }
        .highlight {
            background: #ffeb3b;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 500;
        }
        .assertions-section {
            margin-top: 20px;
        }
        .assertions-section h3 {
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 8px;
        }
        .assertion {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 12px;
            margin-bottom: 12px;
        }
        .assertion-text {
            font-weight: 500;
            color: #333;
            margin-bottom: 8px;
        }
        .assertion-level {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
        }
        .level-critical {
            background: #ffcdd2;
            color: #c62828;
        }
        .level-expected {
            background: #fff3e0;
            color: #e65100;
        }
        .level-aspirational {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .matched-segments {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px dashed #ddd;
        }
        .matched-segments-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        .matched-segment {
            background: #fffde7;
            padding: 8px;
            margin: 5px 0;
            border-radius: 3px;
            font-size: 13px;
            border-left: 3px solid #ffc107;
        }
        .no-matches {
            color: #999;
            font-style: italic;
            font-size: 13px;
        }
        .stats {
            background: #e3f2fd;
            padding: 10px 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>🎯 Assertion Matches Visualization</h1>
"""
    
    total_assertions = 0
    total_with_matches = 0
    
    for idx, item in enumerate(data, 1):
        utterance = item.get('utterance', 'N/A')
        response = item.get('response', '')
        assertions = item.get('assertions', [])
        
        # Collect all matched segments for this meeting
        all_matches = []
        for a in assertions:
            all_matches.extend(a.get('matched_segments', []))
        
        # Count stats
        for a in assertions:
            total_assertions += 1
            if a.get('matched_segments'):
                total_with_matches += 1
        
        html_content += f"""
    <div class="meeting">
        <div class="meeting-header">
            <h2>Meeting {idx}</h2>
        </div>
        
        <div class="utterance">
            <strong>User Request:</strong><br>
            {escape_html(utterance[:200])}{'...' if len(utterance) > 200 else ''}
        </div>
        
        <div class="response">
            <strong>Response (with highlights):</strong><br><br>
            {highlight_matches_in_response(response, all_matches)}
        </div>
        
        <div class="assertions-section">
            <h3>Assertions ({len(assertions)})</h3>
"""
        
        for a in assertions:
            level = a.get('level', 'expected').lower()
            level_class = f"level-{level}"
            text = a.get('text', '')
            matches = a.get('matched_segments', [])
            
            html_content += f"""
            <div class="assertion">
                <span class="assertion-level {level_class}">{level.upper()}</span>
                <span class="assertion-text">{escape_html(text)}</span>
"""
            
            if matches:
                html_content += """
                <div class="matched-segments">
                    <div class="matched-segments-label">📍 Supporting segments found:</div>
"""
                for match in matches:
                    html_content += f"""
                    <div class="matched-segment">{escape_html(match)}</div>
"""
                html_content += """
                </div>
"""
            else:
                html_content += """
                <div class="matched-segments">
                    <span class="no-matches">No supporting segments found</span>
                </div>
"""
            
            html_content += """
            </div>
"""
        
        html_content += """
        </div>
    </div>
"""
    
    # Add summary stats at the top
    match_rate = (total_with_matches / total_assertions * 100) if total_assertions > 0 else 0
    stats_html = f"""
    <div class="stats">
        <strong>Summary:</strong> {len(data)} meetings, {total_assertions} assertions, 
        {total_with_matches} with matches ({match_rate:.1f}%)
    </div>
"""
    
    html_content = html_content.replace(
        '<h1>🎯 Assertion Matches Visualization</h1>',
        f'<h1>🎯 Assertion Matches Visualization</h1>\n{stats_html}'
    )
    
    html_content += """
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML generated: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Generate HTML visualization of assertion matches')
    parser.add_argument(
        '--input',
        default='docs/test_5_with_matches.jsonl',
        help='Input JSONL file with matched_segments'
    )
    parser.add_argument(
        '--output',
        default='docs/assertion_matches.html',
        help='Output HTML file path'
    )
    parser.add_argument(
        '--open',
        action='store_true',
        help='Open the HTML file in browser after generation'
    )
    
    args = parser.parse_args()
    
    # Load data
    data = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    
    print(f"Loaded {len(data)} items from {args.input}")
    
    # Generate HTML
    output_path = generate_html(data, args.output)
    
    # Open in browser if requested
    if args.open:
        webbrowser.open(f'file://{os.path.abspath(output_path)}')

if __name__ == "__main__":
    main()
