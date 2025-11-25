"""
Score assertions against generated responses using GPT-5 JJ model.

This script:
1. Loads sample meetings with their responses and assertions
2. Calls GPT-5 JJ to evaluate if each assertion passes or fails
3. Computes pass rate statistics

Supports two providers:
- Substrate LLM API (primary): https://fe-26.qas.bing.net/chat/completions
- Azure OpenAI (fallback): Azure endpoint with gpt-5-chat deployment

Author: Chin-Yew Lin
"""

import json
import os
import time
import asyncio
import aiohttp
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============== CONFIGURATION ==============
# Substrate LLM API (Primary)
SUBSTRATE_ENDPOINT = "https://fe-26.qas.bing.net/chat/completions"
SUBSTRATE_MODEL = "dev-gpt-5-chat-jj"
# Use SilverFlow's proven auth settings (for Substrate, not specific to llmapi)
SUBSTRATE_RESOURCE = "https://substrate.office.com"
SUBSTRATE_CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"  # Office first-party app (from SilverFlow)
TENANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"

# Azure OpenAI (Fallback)
AZURE_ENDPOINT = "https://ozevr-m8rwmcjq-eastus2.cognitiveservices.azure.com/"
AZURE_DEPLOYMENT = "gpt-5-chat"
AZURE_API_VERSION = "2025-03-01-preview"

# Data paths
OUTPUT_FILE = os.path.join("docs", "11_25_output.jsonl")
RESULTS_FILE = os.path.join("docs", "assertion_scores.json")

# Number of samples to test
NUM_SAMPLES = 10
START_INDEX = 5  # Start from index 5 (skip first 5 used for training)


@dataclass
class AssertionResult:
    """Result of evaluating a single assertion."""
    assertion_text: str
    level: str  # critical, expected, aspirational
    passed: bool
    explanation: str
    source_id: Optional[str] = None


@dataclass
class MeetingScore:
    """Scoring results for a single meeting."""
    utterance: str
    total_assertions: int
    passed_assertions: int
    pass_rate: float
    results_by_level: Dict[str, Dict[str, int]]  # {level: {passed: N, failed: N}}
    assertion_results: List[AssertionResult]


def get_azure_token() -> str:
    """Get Azure AD token using Azure CLI credentials."""
    try:
        from azure.identity import AzureCliCredential
        credential = AzureCliCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        return token.token
    except Exception as e:
        print(f"Failed to get Azure token: {e}")
        print("Please run 'az login' first.")
        raise


def _login_hint() -> str:
    """Get login hint from username."""
    user = os.getenv("USERNAME") or os.getenv("USER") or None
    return f"{user}@microsoft.com" if user else None


def get_substrate_token() -> str:
    """
    Get Substrate token using MSAL with Windows Broker (WAM).
    Uses the same pattern as SilverFlow bizchat_search.py.
    """
    try:
        import msal
        
        authority = f"https://login.microsoftonline.com/{TENANT_ID}"
        scopes = [f"{SUBSTRATE_RESOURCE}/.default"]
        
        # Try to enable Windows Broker (WAM) for seamless SSO
        try:
            app = msal.PublicClientApplication(
                SUBSTRATE_CLIENT_ID,
                authority=authority,
                enable_broker_on_windows=True,
            )
            broker_enabled = True
            print("   Windows Broker (WAM) enabled")
        except Exception:
            app = msal.PublicClientApplication(
                SUBSTRATE_CLIENT_ID,
                authority=authority,
                enable_broker_on_windows=False,
            )
            broker_enabled = False
            print("   Falling back to non-broker auth")
        
        # Get login hint
        login_hint = _login_hint()
        print(f"   Login hint: {login_hint}")
        
        # Try to find a cached account
        account = None
        try:
            if login_hint:
                accounts = app.get_accounts(username=login_hint)
                if accounts:
                    account = accounts[0]
            if not account:
                accounts = app.get_accounts()
                if accounts:
                    account = accounts[0]
        except Exception:
            pass
        
        # Try silent acquisition first
        if account:
            print(f"   Found cached account: {account.get('username', 'unknown')}")
            cached = app.acquire_token_silent(scopes, account=account)
            if cached and "access_token" in cached:
                print("   Using cached token")
                return cached["access_token"]
        
        # Fall back to interactive auth with broker
        print("   Initiating interactive authentication...")
        kwargs = {"scopes": scopes, "login_hint": login_hint}
        if broker_enabled:
            kwargs["parent_window_handle"] = msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE
        
        result = app.acquire_token_interactive(**kwargs)
        
        if "access_token" in result:
            print("   ✓ Authentication successful")
            return result["access_token"]
        
        if "error" in result:
            raise Exception(f"Auth error: {result.get('error_description', result.get('error'))}")
        
        raise Exception("Failed to acquire Substrate token")
    except ImportError:
        raise Exception("MSAL library not installed. Run: pip install msal[broker]")
    except Exception as e:
        raise Exception(f"Substrate auth failed: {e}")


async def call_substrate_api(session: aiohttp.ClientSession, messages: List[Dict], token: str) -> Optional[str]:
    """Call Substrate LLM API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-ModelType": SUBSTRATE_MODEL,
    }
    
    payload = {
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 500,
    }
    
    try:
        async with session.post(SUBSTRATE_ENDPOINT, json=payload, headers=headers, timeout=60) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                error = await resp.text()
                print(f"Substrate API error {resp.status}: {error}")
                return None
    except Exception as e:
        print(f"Substrate API call failed: {e}")
        return None


async def call_azure_api(session: aiohttp.ClientSession, messages: List[Dict], token: str) -> Optional[str]:
    """Call Azure OpenAI API."""
    url = f"{AZURE_ENDPOINT}openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={AZURE_API_VERSION}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 500,
    }
    
    try:
        async with session.post(url, json=payload, headers=headers, timeout=60) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                error = await resp.text()
                print(f"Azure API error {resp.status}: {error}")
                return None
    except Exception as e:
        print(f"Azure API call failed: {e}")
        return None


async def evaluate_assertion(
    session: aiohttp.ClientSession,
    response_text: str,
    assertion: Dict,
    provider: str,
    token: str
) -> AssertionResult:
    """Evaluate a single assertion against the response."""
    
    assertion_text = assertion.get("text", "")
    level = assertion.get("level", "expected")
    justification = assertion.get("justification", {})
    reason = justification.get("reason", "")
    source_id = justification.get("sourceID", "")
    
    system_prompt = """You are an expert evaluator for AI-generated workback plans. You have deep expertise in:
• Project management and meeting preparation workflows
• Calendar scheduling, task dependencies, and timeline planning  
• Identifying actionable items, owners, deadlines, and deliverables
• Recognizing implicit vs explicit information in planning documents

## Your Evaluation Task:
Determine if a workback plan response SATISFIES a given assertion. Focus on SEMANTIC MEANING, not exact wording.

## Evaluation Criteria by Level:

🔴 **CRITICAL** (Must Pass):
- Information MUST be present and accurate
- Core requirements that define a valid workback plan
- Examples: correct meeting date/time, key participants mentioned, main tasks identified
- FAIL only if clearly missing or factually wrong

🟡 **EXPECTED** (Should Pass):
- Standard best practices that a good plan should include
- Examples: task owners assigned, reasonable timeline, relevant context referenced
- PASS if the concept is addressed, even with different wording or structure
- PASS if the intent is satisfied through equivalent content

🟢 **ASPIRATIONAL** (Nice to Have):
- Enhancements that elevate quality but aren't essential
- Examples: risk mitigation, follow-up suggestions, alternative approaches
- PASS if there's ANY reasonable attempt to address the concept
- PASS if related helpful content is provided instead

## Key Principle:
Evaluate INTENT and SUBSTANCE over exact phrasing. If the response achieves the goal of the assertion through different but equivalent means, it PASSES.

## Output Format (JSON only):
{"passed": true, "explanation": "Brief evidence from response"}
{"passed": false, "explanation": "What's specifically missing"}"""

    user_prompt = f"""## Workback Plan Response:

{response_text[:5000]}

---

## Assertion [{level.upper()}]:
"{assertion_text}"

## Context:
{reason if reason else "Standard quality check."}

---

Think step-by-step:
1. What is this assertion asking for?
2. Does the response contain this information (explicitly or implicitly)?
3. Given the {level.upper()} level, should this pass?

Output JSON only:"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Call the appropriate API
    if provider == "substrate":
        result = await call_substrate_api(session, messages, token)
    else:
        result = await call_azure_api(session, messages, token)
    
    # Parse the result
    if result:
        try:
            # Try to extract JSON from the response
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            
            parsed = json.loads(result.strip())
            return AssertionResult(
                assertion_text=assertion_text,
                level=level,
                passed=parsed.get("passed", False),
                explanation=parsed.get("explanation", ""),
                source_id=source_id
            )
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {result[:200]}...")
            return AssertionResult(
                assertion_text=assertion_text,
                level=level,
                passed=False,
                explanation=f"Failed to parse evaluation response: {str(e)}",
                source_id=source_id
            )
    else:
        return AssertionResult(
            assertion_text=assertion_text,
            level=level,
            passed=False,
            explanation="API call failed",
            source_id=source_id
        )


async def score_meeting(
    session: aiohttp.ClientSession,
    item: Dict,
    provider: str,
    token: str
) -> MeetingScore:
    """Score all assertions for a single meeting."""
    
    utterance = item.get("utterance", "")
    response = item.get("response", "")
    assertions = item.get("assertions", [])
    
    print(f"\n📊 Scoring meeting: {utterance[:60]}...")
    print(f"   {len(assertions)} assertions to evaluate")
    
    # Evaluate each assertion
    results = []
    for i, assertion in enumerate(assertions):
        print(f"   Evaluating assertion {i+1}/{len(assertions)}...", end=" ")
        result = await evaluate_assertion(session, response, assertion, provider, token)
        results.append(result)
        status = "✅" if result.passed else "❌"
        print(f"{status} [{result.level}]")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)
    
    # Calculate statistics
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    pass_rate = passed / total if total > 0 else 0.0
    
    # Results by level
    results_by_level = {}
    for level in ["critical", "expected", "aspirational"]:
        level_results = [r for r in results if r.level == level]
        level_passed = sum(1 for r in level_results if r.passed)
        results_by_level[level] = {
            "total": len(level_results),
            "passed": level_passed,
            "failed": len(level_results) - level_passed,
            "pass_rate": level_passed / len(level_results) if level_results else 0.0
        }
    
    return MeetingScore(
        utterance=utterance,
        total_assertions=total,
        passed_assertions=passed,
        pass_rate=pass_rate,
        results_by_level=results_by_level,
        assertion_results=results
    )


def load_samples(file_path: str, num_samples: int, start_index: int = 0) -> List[Dict]:
    """Load sample meetings from JSONL file."""
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.strip():
                if i < start_index:
                    continue  # Skip samples before start_index
                samples.append(json.loads(line))
                if len(samples) >= num_samples:
                    break
    return samples


def print_summary(scores: List[MeetingScore]):
    """Print a summary of all scores."""
    print("\n" + "="*80)
    print("📈 SCORING SUMMARY")
    print("="*80)
    
    total_assertions = sum(s.total_assertions for s in scores)
    total_passed = sum(s.passed_assertions for s in scores)
    overall_pass_rate = total_passed / total_assertions if total_assertions > 0 else 0.0
    
    print(f"\n🎯 Overall Pass Rate: {overall_pass_rate:.1%} ({total_passed}/{total_assertions})")
    
    # Aggregate by level
    level_stats = {"critical": {"total": 0, "passed": 0}, 
                   "expected": {"total": 0, "passed": 0}, 
                   "aspirational": {"total": 0, "passed": 0}}
    
    for score in scores:
        for level, stats in score.results_by_level.items():
            level_stats[level]["total"] += stats["total"]
            level_stats[level]["passed"] += stats["passed"]
    
    print("\n📊 Pass Rate by Assertion Level:")
    for level, stats in level_stats.items():
        rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0.0
        emoji = "🔴" if level == "critical" else ("🟡" if level == "expected" else "🟢")
        print(f"   {emoji} {level.capitalize():15} {rate:.1%} ({stats['passed']}/{stats['total']})")
    
    print("\n📋 Per-Meeting Results:")
    for i, score in enumerate(scores, 1):
        print(f"\n   Meeting {i}: {score.utterance[:50]}...")
        print(f"      Pass Rate: {score.pass_rate:.1%} ({score.passed_assertions}/{score.total_assertions})")
        
        # Show failed assertions
        failed = [r for r in score.assertion_results if not r.passed]
        if failed:
            print(f"      ❌ Failed Assertions ({len(failed)}):")
            for r in failed[:3]:  # Show first 3 failed
                print(f"         - [{r.level}] {r.assertion_text[:60]}...")


def save_results(scores: List[MeetingScore], output_file: str):
    """Save detailed results to JSON file."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "num_samples": len(scores),
        "overall_stats": {
            "total_assertions": sum(s.total_assertions for s in scores),
            "passed_assertions": sum(s.passed_assertions for s in scores),
            "pass_rate": sum(s.passed_assertions for s in scores) / sum(s.total_assertions for s in scores) if sum(s.total_assertions for s in scores) > 0 else 0.0
        },
        "meetings": []
    }
    
    for score in scores:
        meeting_data = {
            "utterance": score.utterance,
            "total_assertions": score.total_assertions,
            "passed_assertions": score.passed_assertions,
            "pass_rate": score.pass_rate,
            "results_by_level": score.results_by_level,
            "assertion_results": [
                {
                    "assertion_text": r.assertion_text,
                    "level": r.level,
                    "passed": r.passed,
                    "explanation": r.explanation,
                    "source_id": r.source_id
                }
                for r in score.assertion_results
            ]
        }
        results["meetings"].append(meeting_data)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {output_file}")


async def main():
    """Main entry point."""
    print("="*80)
    print("🔬 Assertion Scoring Script - GPT-5 JJ Evaluation")
    print("="*80)
    
    # Load samples
    print(f"\n📂 Loading {NUM_SAMPLES} samples from {OUTPUT_FILE} (starting at index {START_INDEX})...")
    samples = load_samples(OUTPUT_FILE, NUM_SAMPLES, START_INDEX)
    print(f"   Loaded {len(samples)} meetings (test set, indices {START_INDEX}-{START_INDEX + len(samples) - 1})")
    
    # Use Substrate LLM API with GPT-5 JJ
    provider = "substrate"
    token = None
    
    print("\n🔐 Authenticating with Substrate LLM API...")
    try:
        token = get_substrate_token()
        print("   ✅ Substrate token acquired")
    except Exception as e:
        print(f"   ❌ Auth failed: {e}")
        print("\nPlease ensure MSAL is installed: pip install msal")
        return
    
    print(f"\n🚀 Using provider: {provider.upper()} ({SUBSTRATE_MODEL})")
    
    # Score all samples
    scores = []
    async with aiohttp.ClientSession() as session:
        for i, sample in enumerate(samples, 1):
            print(f"\n{'='*40}")
            print(f"Sample {i}/{len(samples)}")
            score = await score_meeting(session, sample, provider, token)
            scores.append(score)
    
    # Print summary
    print_summary(scores)
    
    # Save detailed results
    save_results(scores, RESULTS_FILE)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
