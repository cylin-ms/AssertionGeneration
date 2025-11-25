"""
Offline script to compute assertion matches using a larger LLM.
Supports two backends:
  - Ollama (local): Uses local Ollama server with Qwen model
  - JJ (cloud): Uses Microsoft Substrate API with GPT-5 or GPT-4o-mini

This processes the output file and adds "matched_segments" to each assertion.
"""

import json
import os
import re
import ctypes
from typing import List, Dict, Optional
import argparse
import requests

# Substrate API Configuration
SUBSTRATE_ENDPOINT = "https://fe-26.qas.bing.net/chat/completions"
SUBSTRATE_RESOURCE = "https://substrate.office.com"
CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"
TENANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"

# Supported JJ models (only GPT-5 available with this App ID)
JJ_MODELS = {
    "gpt5": "dev-gpt-5-chat-jj",
}

# Global token cache for JJ
_jj_token_cache = None
# Global model name for JJ
_jj_model_type = "dev-gpt-5-chat-jj"
# Delay between JJ API calls (seconds) to avoid rate limiting
_jj_delay = 2.0

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
    
    # Get console window handle for broker
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

def call_jj_api(prompt: str, temperature: float = 0.1, max_retries: int = 3) -> str:
    """Call Substrate JJ API with the given prompt. Includes retry logic for rate limiting."""
    import time
    
    token = get_substrate_token()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-ModelType": _jj_model_type,
    }
    
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1000,
    }
    
    for attempt in range(max_retries):
        response = requests.post(
            SUBSTRATE_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        elif response.status_code == 429:
            # Rate limited - wait and retry
            wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
            print(f"      Rate limited, waiting {wait_time}s...", end="")
            time.sleep(wait_time)
            print(" retrying")
        else:
            raise Exception(f"JJ API error {response.status_code}: {response.text[:200]}")
    
    raise Exception(f"JJ API rate limited after {max_retries} retries")

def init_jj_backend(delay: float = 2.0):
    """Initialize JJ backend by testing authentication."""
    global _jj_model_type, _jj_delay
    
    _jj_model_type = "dev-gpt-5-chat-jj"
    _jj_delay = delay
    
    print(f"Connecting to Substrate API (model: gpt5 -> {_jj_model_type}, delay: {delay}s)...")
    
    # Test authentication
    token = get_substrate_token()
    print(f"✓ Successfully authenticated with Substrate API")
    
    return "jj", _jj_model_type

def load_qwen_model():
    """
    Initialize connection to Ollama API.
    Returns a tuple of (None, model_name) for API-based usage.
    """
    print("Connecting to Ollama API...")
    model_name = "gpt-oss:20b"  # Default model, can be changed via --model argument
    
    # Test connection
    try:
        response = requests.post(
            'http://192.168.2.163:11434/api/generate',
            json={
                'model': model_name,
                'prompt': 'test',
                'stream': False
            },
            timeout=30
        )
        if response.status_code == 200:
            print(f"✓ Successfully connected to Ollama with model: {model_name}")
        else:
            print(f"Warning: Ollama returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not connect to Ollama at http://192.168.2.163:11434")
        print(f"Make sure Ollama is running: 'ollama serve'")
        print(f"And the model is pulled: 'ollama pull {model_name}'")
        raise
    
    return None, model_name

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences for matching."""
    # Split by periods, exclamation marks, question marks, or newlines
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

def score_sentences_batch_jj(assertion_text: str, sentences: List[str], start_idx: int) -> Dict[int, float]:
    """
    Score a batch of sentences for relevance to the assertion using GPT-5 JJ API.
    
    Returns:
        Dict mapping sentence index to score (0.0-1.0)
    """
    
    prompt = f"""Given an assertion, score how well each numbered passage supports it.

Assertion: "{assertion_text}"

Passages:
{chr(10).join(f"{start_idx + i + 1}. {sent}" for i, sent in enumerate(sentences))}

Return ONLY a JSON object with scores (0.0-1.0) for relevant passages (>= 0.3):
{{"scores": {{"1": 0.9, "5": 0.7}}}}"""

    try:
        response_text = call_jj_api(prompt, temperature=0.1)
        
        # Parse JSON response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            scores_data = json.loads(json_match.group(0))
            scores = scores_data.get("scores", {})
            
            # Convert string keys to int and return
            return {int(k) - 1: float(v) for k, v in scores.items()}
            
    except Exception as e:
        print(f"    Warning: JJ batch scoring failed: {e}")
    
    return {}

def score_sentences_batch_ollama(assertion_text: str, sentences: List[str], start_idx: int, model_name: str) -> Dict[int, float]:
    """
    Score a batch of sentences for relevance to the assertion using Ollama API.
    
    Returns:
        Dict mapping sentence index to score (0.0-1.0)
    """
    
    prompt = f"""Given an assertion, score how well each numbered passage supports it.

Assertion: "{assertion_text}"

Passages:
{chr(10).join(f"{start_idx + i + 1}. {sent}" for i, sent in enumerate(sentences))}

Return ONLY a JSON object with scores (0.0-1.0) for relevant passages (>= 0.3):
{{"scores": {{"1": 0.9, "5": 0.7}}}}"""

    try:
        response = requests.post(
            'http://192.168.2.163:11434/api/generate',
            json={
                'model': model_name,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,
                    'top_p': 0.95
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                scores_data = json.loads(json_match.group(0))
                scores = scores_data.get("scores", {})
                
                # Convert string keys to int and return
                return {int(k) - 1: float(v) for k, v in scores.items()}
        else:
            print(f"    Warning: API returned status {response.status_code}")
            
    except Exception as e:
        print(f"    Warning: Batch scoring failed: {e}")
    
    return {}

def find_assertion_matches(assertion_text: str, response_text: str, model, model_name: str, top_k: int = 3, use_jj: bool = False) -> List[str]:
    """
    Use LLM to find where in the response the assertion is supported.
    Supports both Ollama (local) and GPT-5 JJ (cloud) backends.
    Processes the entire response in batches to handle token limits.
    
    Args:
        assertion_text: Full assertion text
        response_text: Generated response text
        model: Unused (kept for API compatibility)
        model_name: Name of the model to use
        top_k: Number of top matches to return
        use_jj: If True, use GPT-5 JJ; otherwise use Ollama
    
    Returns:
        List of matched text segments from the response
    """
    
    # Split response into sentences
    sentences = split_into_sentences(response_text)
    
    if not sentences:
        return []
    
    print(f"    Processing {len(sentences)} sentences in batches...")
    
    # Process in batches to handle long responses
    batch_size = 25  # Process 25 sentences at a time
    all_scores = {}
    
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i + batch_size]
        print(f"      Batch {i//batch_size + 1}/{(len(sentences)-1)//batch_size + 1}", end="\r")
        
        # Use appropriate backend
        if use_jj:
            batch_scores = score_sentences_batch_jj(assertion_text, batch, i)
            # Add delay to avoid rate limiting
            if _jj_delay > 0 and i + batch_size < len(sentences):
                import time
                time.sleep(_jj_delay)
        else:
            batch_scores = score_sentences_batch_ollama(assertion_text, batch, i, model_name)
        
        # Merge scores with global indices
        for local_idx, score in batch_scores.items():
            global_idx = i + local_idx
            if 0 <= global_idx < len(sentences):
                all_scores[global_idx] = score
    
    print()  # New line after batch processing
    
    if not all_scores:
        return []
    
    # Sort by score and take top k
    scored_sentences = [(score, idx, sentences[idx]) for idx, score in all_scores.items()]
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    
    return [sent for _, _, sent in scored_sentences[:top_k]]

def process_output_file(input_path: str, output_path: str, model, model_name: str, use_jj: bool = False, limit: int = None):
    """
    Process the output JSONL file and add matched_segments to each assertion.
    
    Args:
        input_path: Path to input JSONL file
        output_path: Path to output JSONL file
        model: Unused (kept for API compatibility)
        model_name: Name of the model
        use_jj: If True, use GPT-5 JJ; otherwise use Ollama
        limit: Maximum number of items to process (None for all)
    """
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        return
    
    processed_items = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Check limit
            if limit and line_num > limit:
                print(f"\nReached limit of {limit} items, stopping.")
                break
                
            line = line.strip()
            if not line:
                continue
            
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse line {line_num}")
                continue
            
            print(f"\nProcessing item {line_num}: {item.get('utterance', 'N/A')[:50]}...")
            
            response_text = item.get('response', '')
            assertions = item.get('assertions', [])
            
            # Process each assertion
            for i, assertion in enumerate(assertions, 1):
                assertion_text = assertion.get('text', '')
                print(f"  Assertion {i}/{len(assertions)}: {assertion_text[:60]}...")
                
                # Find matches using selected backend
                matches = find_assertion_matches(assertion_text, response_text, model, model_name, use_jj=use_jj)
                
                # Store matches
                assertion['matched_segments'] = matches
                print(f"    Found {len(matches)} matches")
            
            processed_items.append(item)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in processed_items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Processing complete! Output written to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Compute assertion matches using LLM (Ollama or GPT-5 JJ)')
    parser.add_argument(
        '--input',
        default='docs/output_v2.jsonl',
        help='Input JSONL file path'
    )
    parser.add_argument(
        '--output',
        default='docs/output_v2_with_matches.jsonl',
        help='Output JSONL file path'
    )
    parser.add_argument(
        '--model',
        default='gpt-oss:20b',
        help='Ollama model name (default: gpt-oss:20b)'
    )
    parser.add_argument(
        '--use-jj',
        action='store_true',
        help='Use Substrate JJ API (GPT-5) instead of Ollama'
    )
    parser.add_argument(
        '--jj-delay',
        type=float,
        default=2.0,
        help='Delay in seconds between JJ API calls to avoid rate limiting (default: 2.0)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of meetings to process (default: all)'
    )
    
    args = parser.parse_args()
    
    if args.use_jj:
        print(f"🚀 Starting assertion match computation with JJ (GPT-5, delay={args.jj_delay}s)...")
    else:
        print("🚀 Starting assertion match computation with Ollama...")
    
    # Initialize backend
    try:
        if args.use_jj:
            model, model_name = init_jj_backend(delay=args.jj_delay)
        else:
            model, model_name = load_qwen_model()
            # Override with command line argument if provided
            if args.model != 'gpt-oss:20b':
                model_name = args.model
                print(f"Using model: {model_name}")
    except Exception as e:
        backend = "GPT-5 JJ" if args.use_jj else "Ollama"
        print(f"❌ Failed to connect to {backend}: {e}")
        return
    
    # Process file
    process_output_file(args.input, args.output, model, model_name, use_jj=args.use_jj, limit=args.limit)

if __name__ == "__main__":
    main()
