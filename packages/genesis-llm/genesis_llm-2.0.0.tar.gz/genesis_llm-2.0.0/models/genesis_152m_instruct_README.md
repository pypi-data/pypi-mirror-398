---
license: apache-2.0
language:
  - en
pipeline_tag: text-generation
tags:
  - pytorch
  - safetensors
  - text-generation
  - small-llm
  - custom-architecture
---

# Genesis-152M-Instruct

Genesis-152M-Instruct is a small instruction-tuned model based on a custom **Genesis** PyTorch architecture. The weights are provided as a single `.safetensors` file and are **not** directly compatible with `transformers` (there is no `config.json` / tokenizer files in this repo).

## What’s in this repo

- `genesis_152m_instruct.safetensors` (model weights)
- `README.md` (this model card)
- `LICENSE` (Apache-2.0 for the weights)

## Model summary

- Params: ~151.8M total (~122.8M non-embedding; benchmark wrapper report)
- Context length: 2048
- Tokenizer: GPT‑NeoX / Pythia base vocab + ChatML tokens (`<|im_start|>`, `<|im_end|>`)
- Architecture: hybrid attention (linear + full attention)

## How to run (recommended)

1) Install the code (PyPI):

```bash
python -m pip install -U genesis-llm
```

2) Download the weights from the Hub:

```bash
python -m pip install -U "huggingface-hub<1.0,>=0.34.0"
hf download guiferrarib/genesis-152m-instruct genesis_152m_instruct.safetensors --local-dir .
```

3) Start chat (loads the `.safetensors` you downloaded):

```bash
genesis --model ./genesis_152m_instruct.safetensors
```

## Benchmarks (English, full; MPS)

Run (example):

```bash
python benchmark/run_benchmark.py --full --chatml -c models/genesis_152m_instruct.safetensors
```

Notes:

- Device: MPS
- Loglikelihood: `20848/20848` (`~5.91 it/s`)

| Task | Metric | Value | Stderr |
|---|---:|---:|---:|
| all | acc_norm | 0.3710 | 0.0122 |
| all | acc | 0.4909 | 0.0141 |
| genesis:_average:0 | acc_norm | 0.4021 | 0.0144 |
| genesis:_average:25 | acc_norm | 0.3434 | 0.0114 |
| genesis:arc_challenge:25 | acc_norm | 0.2466 | 0.0126 |
| genesis:arc_easy:25 | acc_norm | 0.4402 | 0.0102 |
| genesis:boolq:0 | acc_norm | 0.5630 | 0.0087 |
| genesis:commonsenseqa:0 | acc_norm | 0.2916 | 0.0130 |
| genesis:hellaswag:10 | acc_norm | 0.3019 | 0.0046 |
| genesis:openbookqa:0 | acc_norm | 0.2860 | 0.0202 |
| genesis:sciq:0 | acc_norm | 0.4680 | 0.0158 |
| genesis:winogrande:5 | acc | 0.4909 | 0.0141 |

## Intended use

- Small local assistant for short tasks (rewriting, short Q&A, quick explanations).
- Prompt-format experiments (ChatML) and sampling strategy prototyping.

## Limitations

- Hallucinations and factual errors can happen.
- Weak multi-step reasoning and unreliable math.
- Instruction-following can be brittle for strict constraints (e.g. “answer with only a number”).

## License

- Weights: Apache License 2.0 (see `LICENSE` in this repo).
- Code: MIT in the upstream code repository (see `LICENSE` there).
