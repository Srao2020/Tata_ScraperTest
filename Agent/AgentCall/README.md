# AgentCall

This agent lives under `Agent` and sends one fixed prompt directly to Groq. It does not read any input files.

## Setup

Set your shared Groq key in [api_config.py](/Users/srao/Documents/GitHub/Tata_ScraperTest/api_config.py).

## Usage

Run the agent:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/AgentCall/agent.py
```

Save the exact prompt sent to Groq:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/AgentCall/agent.py --save-prompt
```

## Output

The agent writes:

- [final_output.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/AgentCall/outputs/final_output.md)

If `--save-prompt` is used, it also writes:

- `prompt.txt`
