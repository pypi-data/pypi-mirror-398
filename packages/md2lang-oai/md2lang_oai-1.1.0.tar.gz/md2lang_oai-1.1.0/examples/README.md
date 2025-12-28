# Example with local model

Enable large context with (or set max-tokens to 4K):
```bash
ollama create qwen2.5-large -f ./Modelfile
```

```bash
export OPENAI_API_KEY=test   
input="./dnd_sample.md"                          
output="${input%.md}-es.md"
uvx md2lang-oai --to es-ES \
  --model qwen2.5-large \
  --base-url http://localhost:11434/v1 \
  --max-tokens 10000 \
  --timeout 600 \
  --input "$input" \
  --instructions-file ./dnd_instructions.txt \
  --output "$output"
```

# Example using openAI

However, OpenAI GPT-4 outperforms any local model I could test, including Llama3, Qwen, and Aya8.

```bash
export OPENAI_API_KEY=your-api-key 
uvx md2lang-oai --to es-ES \
  --max-tokens 4000 \
  --timeout 600 \
  --input ./dnd_sample.md \
  --instructions-file ./dnd_instructions.txt
```
