"""
GPT-5 Assertion Evaluation Script with Span Highlighting

This script evaluates assertions against the generated response using GPT-5 JJ.
For each assertion, it:
1. Determines if the assertion is supported (passed/failed)
2. Finds the supporting text spans in the response
3. Assigns confidence scores to each span (for color intensity)
4. Provides reasoning for the evaluation

Features:
- Batch processing with rate limiting (10 meetings per batch)
- Resume from last successful meeting
- Individual meeting processing for JIT annotation
- Progress tracking and checkpoint saving

Usage:
    # Process all remaining meetings (resume from checkpoint)
    python evaluate_assertions_gpt5.py
    
    # Process specific meeting by index (0-based)
    python evaluate_assertions_gpt5.py --meeting 5
    
    # Process specific meeting by INPUT meeting number (1-based, as shown in UI)
    python evaluate_assertions_gpt5.py --meeting-num 7
    
    # Force reprocess all meetings
    python evaluate_assertions_gpt5.py --force
    
    # Process a specific range
    python evaluate_assertions_gpt5.py --start 0 --end 20
"""

import json
import os
import re
import time
import ctypes
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# File paths
INPUT_FILE = os.path.join("docs", "LOD_1121.WithUserUrl.jsonl")
OUTPUT_FILE = os.path.join("docs", "11_25_output.jsonl")
SCORES_FILE = os.path.join("docs", "assertion_scores.json")
CHECKPOINT_FILE = os.path.join("docs", ".gpt5_checkpoint.json")

# Rate limiting
BATCH_SIZE = 10
DELAY_BETWEEN_MEETINGS = 3  # seconds
DELAY_BETWEEN_BATCHES = 10  # seconds
DELAY_BETWEEN_ASSERTIONS = 1  # seconds

# Substrate API Configuration
SUBSTRATE_ENDPOINT = "https://fe-26.qas.bing.net/chat/completions"
SUBSTRATE_RESOURCE = "https://substrate.office.com"
CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"
TENANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"
JJ_MODEL = "dev-gpt-5-chat-jj"

# Global token cache
_jj_token_cache = None


# ═══════════════════════════════════════════════════════════════════════════════
# Authentication
# ═══════════════════════════════════════════════════════════════════════════════

def get_substrate_token():
    """Get authentication token for Substrate API using MSAL broker."""
    global _jj_token_cache
    
    if _jj_token_cache:
        return _jj_token_cache
    
    try:
        import msal
    except ImportError:
        print("Error: msal[broker] not installed. Run: pip install msal[broker]")
        raise
    
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        enable_broker_on_windows=True,
    )
    
    scopes = [f"{SUBSTRATE_RESOURCE}/.default"]
    
    # Try silent auth first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result and "access_token" in result:
            _jj_token_cache = result["access_token"]
            return _jj_token_cache
    
    # Fall back to interactive
    print("Authenticating with Microsoft (browser may open)...")
    
    kernel32 = ctypes.windll.kernel32
    hwnd = kernel32.GetConsoleWindow()
    
    result = app.acquire_token_interactive(
        scopes,
        parent_window_handle=hwnd,
    )
    
    if "access_token" in result:
        _jj_token_cache = result["access_token"]
        return _jj_token_cache
    else:
        raise Exception(f"Authentication failed: {result.get('error_description', result)}")


def call_gpt5_api(prompt: str, temperature: float = 0.1, max_tokens: int = 2000, max_retries: int = 3) -> str:
    """Call Substrate GPT-5 JJ API with retry logic."""
    import requests
    
    token = get_substrate_token()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-ModelType": JJ_MODEL,
    }
    
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    for attempt in range(max_retries):
        response = requests.post(
            SUBSTRATE_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        elif response.status_code == 429:
            wait_time = (attempt + 1) * 10
            print(f"      Rate limited, waiting {wait_time}s...", end="", flush=True)
            time.sleep(wait_time)
            print(" retrying")
        else:
            raise Exception(f"GPT-5 API error {response.status_code}: {response.text[:200]}")
    
    raise Exception(f"GPT-5 API rate limited after {max_retries} retries")


# ═══════════════════════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════════════════════

def load_input_data() -> List[Dict]:
    """Load INPUT data (LOD with context)."""
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def load_output_data() -> List[Dict]:
    """Load OUTPUT data (assertions and responses)."""
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def load_scores() -> Dict:
    """Load existing scores file or create empty structure."""
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "timestamp": None,
        "num_samples": 0,
        "overall_stats": {
            "total_assertions": 0,
            "passed_assertions": 0,
            "pass_rate": 0.0
        },
        "meetings": []
    }


def save_scores(scores: Dict):
    """Save scores to file."""
    scores["timestamp"] = datetime.now().isoformat()
    with open(SCORES_FILE, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=2)


def load_checkpoint() -> Dict:
    """Load processing checkpoint."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"last_processed_index": -1, "processed_utterances": []}


def save_checkpoint(checkpoint: Dict):
    """Save processing checkpoint."""
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# Core Evaluation Logic
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_assertion(assertion: Dict, response_text: str) -> Dict:
    """
    Evaluate a single assertion against the response using GPT-5.
    
    Returns:
        Dict with:
        - assertion_text: The assertion text
        - level: critical/expected/aspirational
        - passed: bool
        - explanation: GPT-5's reasoning
        - source_id: Original source ID if present
        - supporting_spans: List of {text, confidence, start_index, end_index, section}
    """
    assertion_text = assertion.get('text', '')
    level = assertion.get('level', 'expected')
    
    # Get source ID from justification (new format) or reasoning (old format)
    justification = assertion.get('justification', assertion.get('reasoning', {}))
    source_id = justification.get('sourceID', justification.get('source', ''))
    
    # Prompt for GPT-5 evaluation
    prompt = f"""You are evaluating whether a response correctly satisfies an assertion.

ASSERTION:
"{assertion_text}"

RESPONSE TO EVALUATE:
{response_text}

Analyze the response and determine:
1. Does the response satisfy this assertion? (true/false)
2. What parts of the response support or contradict the assertion?
3. Which section/header of the response contains each piece of evidence?
4. How confident is the support for each relevant part?

Return your analysis as JSON in this exact format:
{{
    "passed": true or false,
    "explanation": "Brief explanation of your evaluation",
    "supporting_spans": [
        {{
            "text": "exact quote from the response that supports/contradicts the assertion",
            "section": "The section header or title where this text appears (e.g., 'Context & Assumptions', 'Quick Timeline Overview', 'Task Details')",
            "confidence": 0.0 to 1.0 (how strongly this span supports the assertion),
            "supports": true or false (true if supports, false if contradicts)
        }}
    ]
}}

Important:
- Extract 1-5 most relevant text spans from the response
- Use EXACT quotes from the response (copy-paste the text)
- Include the section/header name where each quote appears (look for markdown headers like ##, ###, or labeled sections)
- Confidence should be 0.0-1.0 where 1.0 means very strong support
- If the assertion is NOT satisfied, still identify any partial/contradicting evidence
- Keep explanations concise but informative

Return ONLY the JSON object, no other text."""

    try:
        response = call_gpt5_api(prompt, temperature=0.1, max_tokens=2000)
        
        # Parse JSON response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            result = json.loads(json_match.group(0))
            
            # Find actual positions of spans in the response
            spans_with_positions = []
            for span in result.get('supporting_spans', []):
                span_text = span.get('text', '')
                section = span.get('section', '')
                # Try to find the span in the response
                start_idx = response_text.find(span_text)
                if start_idx == -1:
                    # Try case-insensitive search
                    lower_response = response_text.lower()
                    lower_span = span_text.lower()
                    start_idx = lower_response.find(lower_span)
                
                spans_with_positions.append({
                    "text": span_text,
                    "section": section,
                    "confidence": float(span.get('confidence', 0.5)),
                    "supports": span.get('supports', True),
                    "start_index": start_idx if start_idx >= 0 else None,
                    "end_index": start_idx + len(span_text) if start_idx >= 0 else None
                })
            
            return {
                "assertion_text": assertion_text,
                "level": level,
                "passed": result.get('passed', False),
                "explanation": result.get('explanation', ''),
                "source_id": source_id,
                "supporting_spans": spans_with_positions
            }
    except Exception as e:
        print(f"      Error evaluating assertion: {e}")
    
    # Return failed evaluation on error
    return {
        "assertion_text": assertion_text,
        "level": level,
        "passed": False,
        "explanation": f"Evaluation failed: {str(e) if 'e' in dir() else 'Unknown error'}",
        "source_id": source_id,
        "supporting_spans": []
    }


def evaluate_meeting(output_item: Dict, meeting_index: int) -> Dict:
    """
    Evaluate all assertions for a single meeting.
    
    Returns:
        Dict with meeting evaluation results
    """
    utterance = output_item.get('utterance', '')
    response_text = output_item.get('response', '')
    assertions = output_item.get('assertions', [])
    
    print(f"  Processing meeting #{meeting_index + 1}: {utterance[:50]}...")
    print(f"    {len(assertions)} assertions to evaluate")
    
    assertion_results = []
    passed_count = 0
    results_by_level = {
        'critical': {'total': 0, 'passed': 0},
        'expected': {'total': 0, 'passed': 0},
        'aspirational': {'total': 0, 'passed': 0}
    }
    
    for i, assertion in enumerate(assertions):
        print(f"    [{i+1}/{len(assertions)}] Evaluating...", end="\r")
        
        result = evaluate_assertion(assertion, response_text)
        assertion_results.append(result)
        
        # Update stats
        level = result.get('level', 'expected')
        if level not in results_by_level:
            level = 'expected'
        
        results_by_level[level]['total'] += 1
        if result.get('passed', False):
            passed_count += 1
            results_by_level[level]['passed'] += 1
        
        # Rate limiting between assertions
        if i < len(assertions) - 1:
            time.sleep(DELAY_BETWEEN_ASSERTIONS)
    
    # Calculate pass rates
    for level in results_by_level:
        total = results_by_level[level]['total']
        passed = results_by_level[level]['passed']
        results_by_level[level]['pass_rate'] = passed / total if total > 0 else 0.0
        results_by_level[level]['failed'] = total - passed
    
    total_assertions = len(assertions)
    pass_rate = passed_count / total_assertions if total_assertions > 0 else 0.0
    
    print(f"    ✓ {passed_count}/{total_assertions} passed ({pass_rate:.1%})      ")
    
    return {
        "utterance": utterance,
        "total_assertions": total_assertions,
        "passed_assertions": passed_count,
        "pass_rate": pass_rate,
        "results_by_level": results_by_level,
        "assertion_results": assertion_results
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main Processing
# ═══════════════════════════════════════════════════════════════════════════════

def process_meetings(start_index: int = 0, end_index: int = None, force: bool = False,
                     batch_size: int = 10, meeting_delay: float = 3.0, batch_delay: float = 10.0):
    """
    Process meetings in batches with rate limiting.
    
    Args:
        start_index: First meeting index to process (0-based)
        end_index: Last meeting index to process (exclusive, None = all)
        force: If True, reprocess all meetings regardless of checkpoint
        batch_size: Number of meetings per batch
        meeting_delay: Seconds to wait between meetings
        batch_delay: Seconds to wait between batches
    """
    print("=" * 70)
    print("GPT-5 Assertion Evaluation")
    print("=" * 70)
    
    # Load data
    print("\nLoading data...")
    output_data = load_output_data()
    scores = load_scores()
    checkpoint = load_checkpoint() if not force else {"last_processed_index": -1, "processed_utterances": []}
    
    # Build set of already processed utterances for quick lookup
    processed_utterances = set(checkpoint.get('processed_utterances', []))
    existing_meetings = {m['utterance']: m for m in scores.get('meetings', [])}
    
    # Determine range to process
    if end_index is None:
        end_index = len(output_data)
    
    # Find meetings that need processing
    meetings_to_process = []
    for i in range(start_index, min(end_index, len(output_data))):
        utterance = output_data[i].get('utterance', '')
        if force or utterance not in processed_utterances:
            meetings_to_process.append((i, output_data[i]))
    
    if not meetings_to_process:
        print("\n✓ All meetings already processed!")
        return
    
    print(f"\nMeetings to process: {len(meetings_to_process)}")
    print(f"Batch size: {batch_size}, Delay between meetings: {meeting_delay}s")
    print(f"Delay between batches: {batch_delay}s")
    
    # Authenticate first
    print("\nAuthenticating...")
    get_substrate_token()
    print("✓ Authentication successful")
    
    # Process in batches
    total_batches = (len(meetings_to_process) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(meetings_to_process))
        batch = meetings_to_process[batch_start:batch_end]
        
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num + 1}/{total_batches}")
        print(f"{'='*70}")
        
        for idx, (meeting_index, output_item) in enumerate(batch):
            utterance = output_item.get('utterance', '')
            
            try:
                result = evaluate_meeting(output_item, meeting_index)
                
                # Update or add to existing meetings
                if utterance in existing_meetings:
                    # Update existing
                    for i, m in enumerate(scores['meetings']):
                        if m['utterance'] == utterance:
                            scores['meetings'][i] = result
                            break
                else:
                    # Add new
                    scores['meetings'].append(result)
                    existing_meetings[utterance] = result
                
                # Update checkpoint
                processed_utterances.add(utterance)
                checkpoint['last_processed_index'] = meeting_index
                checkpoint['processed_utterances'] = list(processed_utterances)
                
                # Save progress after each meeting
                save_checkpoint(checkpoint)
                
                # Recalculate overall stats
                total_assertions = sum(m['total_assertions'] for m in scores['meetings'])
                passed_assertions = sum(m['passed_assertions'] for m in scores['meetings'])
                scores['num_samples'] = len(scores['meetings'])
                scores['overall_stats'] = {
                    'total_assertions': total_assertions,
                    'passed_assertions': passed_assertions,
                    'pass_rate': passed_assertions / total_assertions if total_assertions > 0 else 0.0
                }
                save_scores(scores)
                
            except Exception as e:
                print(f"    ✗ Error processing meeting {meeting_index + 1}: {e}")
                continue
            
            # Delay between meetings (except last in batch)
            if idx < len(batch) - 1:
                print(f"    Waiting {meeting_delay}s before next meeting...")
                time.sleep(meeting_delay)
        
        # Delay between batches (except last batch)
        if batch_num < total_batches - 1:
            print(f"\nBatch complete. Waiting {batch_delay}s before next batch...")
            time.sleep(batch_delay)
    
    # Final summary
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Total meetings processed: {scores['num_samples']}")
    print(f"Total assertions: {scores['overall_stats']['total_assertions']}")
    print(f"Passed assertions: {scores['overall_stats']['passed_assertions']}")
    print(f"Overall pass rate: {scores['overall_stats']['pass_rate']:.1%}")


def process_single_meeting(meeting_index: int = None, input_meeting_num: int = None):
    """
    Process a single meeting by index or INPUT meeting number.
    
    Args:
        meeting_index: 0-based index in OUTPUT data
        input_meeting_num: 1-based meeting number as shown in UI (from INPUT data)
    """
    print("=" * 70)
    print("GPT-5 Single Meeting Evaluation")
    print("=" * 70)
    
    # Load data
    output_data = load_output_data()
    scores = load_scores()
    
    # If input_meeting_num provided, find corresponding output index
    if input_meeting_num is not None:
        input_data = load_input_data()
        if input_meeting_num < 1 or input_meeting_num > len(input_data):
            print(f"Error: Invalid meeting number {input_meeting_num}. Valid range: 1-{len(input_data)}")
            return
        
        # Get utterance from input and find in output
        input_item = input_data[input_meeting_num - 1]
        target_utterance = input_item.get('UTTERANCE', {}).get('text', '')
        
        meeting_index = None
        for i, output_item in enumerate(output_data):
            if output_item.get('utterance', '') == target_utterance:
                meeting_index = i
                break
        
        if meeting_index is None:
            print(f"Error: Could not find output for INPUT meeting #{input_meeting_num}")
            return
        
        print(f"\nINPUT meeting #{input_meeting_num} → OUTPUT index {meeting_index}")
    
    if meeting_index is None:
        print("Error: Must specify --meeting or --meeting-num")
        return
    
    if meeting_index < 0 or meeting_index >= len(output_data):
        print(f"Error: Invalid meeting index {meeting_index}. Valid range: 0-{len(output_data)-1}")
        return
    
    output_item = output_data[meeting_index]
    
    # Authenticate
    print("\nAuthenticating...")
    get_substrate_token()
    print("✓ Authentication successful\n")
    
    # Process the meeting
    result = evaluate_meeting(output_item, meeting_index)
    
    # Update scores
    utterance = output_item.get('utterance', '')
    existing_meetings = {m['utterance']: i for i, m in enumerate(scores.get('meetings', []))}
    
    if utterance in existing_meetings:
        scores['meetings'][existing_meetings[utterance]] = result
    else:
        scores['meetings'].append(result)
    
    # Recalculate overall stats
    total_assertions = sum(m['total_assertions'] for m in scores['meetings'])
    passed_assertions = sum(m['passed_assertions'] for m in scores['meetings'])
    scores['num_samples'] = len(scores['meetings'])
    scores['overall_stats'] = {
        'total_assertions': total_assertions,
        'passed_assertions': passed_assertions,
        'pass_rate': passed_assertions / total_assertions if total_assertions > 0 else 0.0
    }
    
    save_scores(scores)
    
    # Also update checkpoint
    checkpoint = load_checkpoint()
    if utterance not in checkpoint.get('processed_utterances', []):
        checkpoint['processed_utterances'] = checkpoint.get('processed_utterances', []) + [utterance]
        save_checkpoint(checkpoint)
    
    print("\n✓ Saved to", SCORES_FILE)


# ═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate assertions using GPT-5 JJ with span highlighting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Process all remaining meetings (resume from checkpoint)
    python evaluate_assertions_gpt5.py
    
    # Process specific meeting by OUTPUT index (0-based)
    python evaluate_assertions_gpt5.py --meeting 5
    
    # Process specific meeting by INPUT number (1-based, as shown in UI)
    python evaluate_assertions_gpt5.py --meeting-num 7
    
    # Force reprocess all meetings
    python evaluate_assertions_gpt5.py --force
    
    # Process a specific range of OUTPUT indices
    python evaluate_assertions_gpt5.py --start 0 --end 20
        """
    )
    
    parser.add_argument('--meeting', type=int, help='Process single meeting by OUTPUT index (0-based)')
    parser.add_argument('--meeting-num', type=int, help='Process single meeting by INPUT number (1-based, as shown in Mira UI)')
    parser.add_argument('--start', type=int, default=0, help='Start index for batch processing (0-based)')
    parser.add_argument('--end', type=int, help='End index for batch processing (exclusive)')
    parser.add_argument('--force', action='store_true', help='Force reprocess all meetings')
    parser.add_argument('--batch-size', type=int, default=10, help='Meetings per batch (default: 10)')
    parser.add_argument('--meeting-delay', type=float, default=3.0, help='Seconds between meetings (default: 3)')
    parser.add_argument('--batch-delay', type=float, default=10.0, help='Seconds between batches (default: 10)')
    
    args = parser.parse_args()
    
    # Single meeting mode
    if args.meeting is not None or args.meeting_num is not None:
        process_single_meeting(
            meeting_index=args.meeting,
            input_meeting_num=args.meeting_num
        )
    else:
        # Batch processing mode
        process_meetings(
            start_index=args.start,
            end_index=args.end,
            force=args.force,
            batch_size=args.batch_size,
            meeting_delay=args.meeting_delay,
            batch_delay=args.batch_delay
        )


if __name__ == "__main__":
    main()
