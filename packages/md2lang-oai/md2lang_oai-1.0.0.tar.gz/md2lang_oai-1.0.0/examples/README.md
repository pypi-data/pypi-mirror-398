# Example with local model qwen2.5:7b

```bash
ollama create qwen2.5-large -f ./Modelfile

export OPENAI_API_KEY=test                             
input='/Users/carloscasalar/wks/rol/d&d5/Confrontación en candlekeep/DD4_ConfrontationCandlekeep_Download.md'
output="${input%.md}-es.md"
uv run md2lang-oai --to es-ES \
  --model qwen2.5-large \
  --base-url http://localhost:11434/v1 \
  --max-tokens 10000 \
  --timeout 600 \
  --input "$input" \
  --output "$output"
```

