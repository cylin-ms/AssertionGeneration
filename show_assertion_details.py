"""
Generate detailed HTML showing each assertion with its matched segments.
"""

import json
import html as html_lib
import argparse
import webbrowser
import os

def escape(text):
    return html_lib.escape(str(text))

def generate_detailed_html(input_path: str, output_path: str, meeting_idx: int = 0):
    """Generate HTML showing each assertion with its supporting segments."""
    
    # Load data
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        if meeting_idx >= len(lines):
            print(f"Error: Meeting index {meeting_idx} out of range (only {len(lines)} meetings)")
            return
        data = json.loads(lines[meeting_idx])
    
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Assertion Match Details</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; border-bottom: 2px solid #0078d4; padding-bottom: 10px; }
        .section { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .section h2 { margin-top: 0; color: #0078d4; }
        .utterance { background: #e8f4ff; padding: 15px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #0078d4; white-space: pre-wrap; }
        .response { background: #f9f9f9; padding: 15px; border-radius: 5px; line-height: 1.6; white-space: pre-wrap; font-size: 13px; max-height: 400px; overflow-y: auto; }
        .assertion-card { background: white; border: 2px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        .assertion-card.has-matches { border-color: #4caf50; }
        .assertion-card.no-matches { border-color: #f44336; }
        .assertion-header { display: flex; align-items: center; margin-bottom: 10px; }
        .assertion-num { background: #0078d4; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 10px; flex-shrink: 0; }
        .assertion-level { padding: 3px 10px; border-radius: 3px; font-size: 12px; font-weight: 600; margin-left: auto; }
        .level-critical { background: #ffcdd2; color: #c62828; }
        .level-expected { background: #fff3e0; color: #e65100; }
        .level-aspirational { background: #e8f5e9; color: #2e7d32; }
        .assertion-text { font-weight: 500; color: #333; padding: 12px; background: #f5f5f5; border-radius: 5px; line-height: 1.5; }
        .matches-section { margin-top: 15px; }
        .matches-label { font-size: 14px; color: #666; margin-bottom: 8px; font-weight: 600; }
        .matches-label.found { color: #2e7d32; }
        .matches-label.not-found { color: #c62828; }
        .match-item { background: #fffde7; padding: 12px; margin: 8px 0; border-radius: 5px; border-left: 4px solid #ffc107; font-size: 13px; line-height: 1.5; }
        .match-num { background: #ffc107; color: #333; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-right: 8px; }
        .no-matches { color: #c62828; font-style: italic; padding: 10px; background: #ffebee; border-radius: 5px; }
        .summary { background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .summary-stat { display: inline-block; margin-right: 30px; }
        .summary-stat strong { color: #0078d4; }
    </style>
</head>
<body>
'''
    
    # Title
    html += f'    <h1>🎯 Assertion Match Details - Meeting {meeting_idx + 1}</h1>\n'
    
    # Summary stats
    total = len(data.get('assertions', []))
    with_matches = sum(1 for a in data.get('assertions', []) if a.get('matched_segments'))
    html += f'''
    <div class="summary">
        <span class="summary-stat"><strong>{total}</strong> assertions</span>
        <span class="summary-stat"><strong>{with_matches}</strong> with matches</span>
        <span class="summary-stat"><strong>{total - with_matches}</strong> without matches</span>
    </div>
'''
    
    # User request
    utterance = data.get('utterance', 'N/A')
    html += f'''
    <div class="section">
        <h2>📋 User Request</h2>
        <div class="utterance">{escape(utterance)}</div>
    </div>
'''
    
    # Response
    response = data.get('response', '')
    html += f'''
    <div class="section">
        <h2>💬 Full Response</h2>
        <div class="response">{escape(response)}</div>
    </div>
'''
    
    # Individual assertions
    html += '''
    <div class="section">
        <h2>✅ Assertions & Supporting Evidence</h2>
'''
    
    for i, assertion in enumerate(data.get('assertions', []), 1):
        level = assertion.get('level', 'expected').lower()
        level_class = f'level-{level}'
        text = assertion.get('text', '')
        matches = assertion.get('matched_segments', [])
        card_class = 'has-matches' if matches else 'no-matches'
        
        html += f'''
        <div class="assertion-card {card_class}">
            <div class="assertion-header">
                <div class="assertion-num">{i}</div>
                <span style="flex-grow: 1;"></span>
                <span class="assertion-level {level_class}">{level.upper()}</span>
            </div>
            <div class="assertion-text">{escape(text)}</div>
            <div class="matches-section">
'''
        
        if matches:
            html += f'                <div class="matches-label found">✓ {len(matches)} supporting segment(s) found:</div>\n'
            for j, match in enumerate(matches, 1):
                html += f'''                <div class="match-item">
                    <span class="match-num">#{j}</span>
                    {escape(match)}
                </div>
'''
        else:
            html += '''                <div class="matches-label not-found">✗ No supporting segments found</div>
                <div class="no-matches">The LLM could not find text in the response that directly supports this assertion.</div>
'''
        
        html += '''            </div>
        </div>
'''
    
    html += '''    </div>
</body>
</html>
'''
    
    # Write HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generated: {output_path}")
    
    # Print summary
    print(f"\nSummary: {total} assertions, {with_matches} with matches")
    for i, a in enumerate(data.get('assertions', []), 1):
        matches = a.get('matched_segments', [])
        status = f"✓ {len(matches)} matches" if matches else "✗ no matches"
        print(f"  {i}. [{a.get('level', 'expected').upper():12}] {status:12} - {a['text'][:55]}...")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Generate detailed HTML for assertion matches')
    parser.add_argument('--input', default='docs/test_1_with_matches.jsonl', help='Input JSONL file')
    parser.add_argument('--output', default='docs/assertion_details.html', help='Output HTML file')
    parser.add_argument('--meeting', type=int, default=0, help='Meeting index (0-based)')
    parser.add_argument('--open', action='store_true', help='Open in browser')
    
    args = parser.parse_args()
    
    output_path = generate_detailed_html(args.input, args.output, args.meeting)
    
    if args.open and output_path:
        webbrowser.open(f'file://{os.path.abspath(output_path)}')

if __name__ == "__main__":
    main()
