# Assertion Matching System

This system uses a two-phase approach to match assertion evidence in generated responses:

## Architecture

### Phase 1: Offline Pre-computation (Using gpt-oss:20b)
- **Script**: `compute_assertion_matches.py`
- **Model**: gpt-oss:20b (or similar)
- **Purpose**: Use a more powerful LLM to analyze full assertions and find supporting evidence in responses
- **Output**: Enhanced JSONL file with `matched_segments` added to each assertion

### Phase 2: Visualization (Streamlit)
- **Script**: `visualize_output.py`  
- **Purpose**: Display pre-computed matches with color-coded highlighting
- **Approach**: No runtime LLM inference; simply reads and displays stored matches

## Why This Approach?

1. **Better Accuracy**: Large LLMs (7B+ params) understand context better than lightweight models (30M params)
2. **Better Prompting**: We can craft detailed prompts asking the LLM to find evidence for the full assertion text
3. **Easy Setup**: Ollama provides simple local LLM hosting on Mac/Linux/Windows
4. **Flexibility**: Can easily swap models (qwen, llama, mistral, etc.) without changing code
5. **Performance**: UI remains fast since no inference happens at runtime

## Usage

### Step 1: Set up Ollama on Mac

```bash
# Install Ollama (if not already installed)
brew install ollama

# Start Ollama service
ollama serve

# In another terminal, pull the model
ollama pull gpt-oss:20b
```

### Step 2: Run Offline Matching

```bash
# Install Python dependencies
pip install requests

# Run the matching script (connects to Ollama on 192.168.2.163:11434)
python compute_assertion_matches.py --input docs/output_v2.jsonl --output docs/output_v2_with_matches.jsonl

# Optional: Use a different model
python compute_assertion_matches.py --model llama3.2:latest
```

### Step 3: Visualize Results

```bash
streamlit run visualize_output.py
```

The visualization now reads from `output_v2_with_matches.jsonl` and displays the pre-computed evidence.

## Data Format

### Input (output_v2.jsonl)
```json
{
  "utterance": "Help me make a workback plan...",
  "response": "Here is a comprehensive workback plan...",
  "assertions": [
    {
      "text": "The response identifies Shakia as the organizer.",
      "level": "critical",
      "reasoning": {...}
    }
  ]
}
```

### Output (output_v2_with_matches.jsonl)
```json
{
  "utterance": "Help me make a workback plan...",
  "response": "Here is a comprehensive workback plan...",
  "assertions": [
    {
      "text": "The response identifies Shakia as the organizer.",
      "level": "critical",
      "reasoning": {...},
      "matched_segments": [
        "Shakia Gencarelli (You, Senior Software Engineer) as the facilitator",
        "Organizer: Shakia",
        "Owner: Shakia Gencarelli"
      ]
    }
  ]
}
```

## Customization

### Using a Different Ollama Model

```bash
# List available models
ollama list

# Pull a different model
ollama pull llama3.2

# Use it in the script
python compute_assertion_matches.py --model llama3.2:latest
```

### Using Remote Ollama Instance

Edit the script to point to a different host:

```python
# In compute_assertion_matches.py, change:
response = requests.post(
    'http://your-mac-ip:11434/api/generate',  # Point to Mac IP
    # ...
)
```

### Adjusting Number of Matches

```python
python compute_assertion_matches.py --input docs/output_v2.jsonl --output docs/output_v2_with_matches.jsonl --top-k 5
```

(You'll need to add this argument to the script)

## Highlighting Colors

The visualizer uses fading colors to indicate match strength:
- **Rank 1**: Strong Yellow (opacity 1.0)
- **Rank 2**: Medium Yellow (opacity 0.6)  
- **Rank 3**: Light Yellow (opacity 0.3)

## Troubleshooting

### "Could not connect to Ollama"
Make sure Ollama is running: `ollama serve`

### "Model not found"
Pull the model first: `ollama pull qwen3:30b`

### Poor match quality
- Try a different model: `--model llama3.2:latest`
- Adjust the prompt in `score_sentences_batch()`
- Increase batch size if responses are very long

### Slow processing
- Use a faster/smaller model: `ollama pull qwen2.5:7b` or `qwen2.5:3b`
- Reduce batch size in the script (currently 25 sentences)

## Future Enhancements

- [ ] Support for API-based LLMs (GPT-4, Claude)
- [ ] Batch processing for large files
- [ ] Confidence scores for matches
- [ ] Interactive re-matching in the UI
