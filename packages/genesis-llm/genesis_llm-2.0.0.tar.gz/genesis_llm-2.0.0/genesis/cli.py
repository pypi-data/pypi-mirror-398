import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from dataclasses import asdict
from typing import Dict, List, Optional

import torch
from safetensors import safe_open
from safetensors.torch import load_file

from . import Genesis, GenesisConfig, get_tokenizer


class GenesisChat:
    def __init__(self, model_path: str, device: Optional[str] = None):
        self.device = device or (
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )
        self.model = self._load_model(model_path)
        self.tokenizer = self._setup_tokenizer()
        self.history: List[Dict[str, str]] = []
        self.system_prompt = "You are a helpful assistant."

    def _load_model(self, path: str) -> Genesis:
        with safe_open(path, framework="pt", device="cpu") as f:
            metadata = f.metadata() or {}
            if "genesis_config_json" in metadata:
                config_dict = json.loads(metadata["genesis_config_json"])
                config = GenesisConfig(**config_dict)
            else:
                config = GenesisConfig.genesis_147m()

        state_dict = load_file(path, device=self.device)
        model = Genesis(config).to(self.device)

        if "lm_head.weight" not in state_dict and config.tie_word_embeddings:
            if "tok_emb.weight" in state_dict:
                state_dict["lm_head.weight"] = state_dict["tok_emb.weight"]

        model.load_state_dict(state_dict, strict=False)
        model.eval()
        return model

    def _setup_tokenizer(self):
        tokenizer = get_tokenizer("neox")
        if hasattr(tokenizer, "add_chat_tokens"):
            tokenizer.add_chat_tokens()
        return tokenizer

    def reset_history(self):
        self.history = []

    def build_prompt(self, query: str) -> str:
        prompt = f"<|im_start|>system\n{self.system_prompt}\n<|im_end|>\n"
        for msg in self.history:
            prompt += f"<|im_start|>{msg['role']}\n{msg['content']}\n<|im_end|>\n"
        prompt += f"<|im_start|>user\n{query}\n<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"
        return prompt

    def generate(
        self,
        query: str,
        max_new_tokens: int = 150,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.05,
    ) -> str:
        full_prompt = self.build_prompt(query)
        input_ids = self.tokenizer.encode(full_prompt)
        input_tensor = torch.tensor([input_ids], dtype=torch.long, device=self.device)

        if input_tensor.shape[1] > self.model.config.block_size - max_new_tokens:
            while input_tensor.shape[1] > self.model.config.block_size - max_new_tokens and len(self.history) > 0:
                self.history.pop(0)
                full_prompt = self.build_prompt(query)
                input_ids = self.tokenizer.encode(full_prompt)
                input_tensor = torch.tensor([input_ids], dtype=torch.long, device=self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                input_tensor,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                stop_tokens=[self.tokenizer.im_end_id] if getattr(self.tokenizer, "im_end_id", None) else None,
            )

        new_tokens = output_ids[0][input_tensor.shape[1] :]
        response = self.tokenizer.decode(new_tokens.tolist())
        response = response.replace("<|im_end|>", "").strip()

        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": response})
        return response


def _print_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _main_chat(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Chat with a Genesis checkpoint (.safetensors).")
    parser.add_argument("--model", type=str, required=True, help="Path to .safetensors checkpoint")
    parser.add_argument(
        "--system",
        type=str,
        default="You are a helpful assistant.",
        help="System prompt",
    )
    parser.add_argument("--device", type=str, default=None, help="cuda|mps|cpu (auto if omitted)")
    parser.add_argument("--max-new-tokens", type=int, default=150)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--repetition-penalty", type=float, default=1.05)
    parser.add_argument("--print-config", action="store_true")
    args = parser.parse_args(argv)

    chat = GenesisChat(args.model, device=args.device)
    chat.system_prompt = args.system

    if args.print_config:
        _print_json(asdict(chat.model.config))
        return 0

    while True:
        try:
            user_input = input("User: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"quit", "exit"}:
                break
            if user_input.lower() == "reset":
                chat.reset_history()
                continue

            response = chat.generate(
                user_input,
                max_new_tokens=args.max_new_tokens,
                temperature=args.temperature,
                top_k=args.top_k,
                top_p=args.top_p,
                repetition_penalty=args.repetition_penalty,
            )
            print(f"Assistant: {response}")
        except KeyboardInterrupt:
            break
    return 0


def _run(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def _main_publish_pypi(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Build and (optionally) upload to PyPI.")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--dist-dir", type=str, default="dist")
    parser.add_argument("--build-dir", type=str, default="build")
    parser.add_argument("--repository", type=str, default=None)
    args = parser.parse_args(argv)

    root = Path.cwd()
    dist_dir = root / args.dist_dir
    build_dir = root / args.build_dir

    if args.clean:
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        if build_dir.exists():
            shutil.rmtree(build_dir)

    _run([sys.executable, "-m", "pip", "install", "-U", "build", "twine"])
    _run([sys.executable, "-m", "build"])
    _run([sys.executable, "-m", "twine", "check", str(dist_dir / "*")])

    if args.upload:
        cmd = [sys.executable, "-m", "twine", "upload", str(dist_dir / "*")]
        if args.repository:
            cmd.extend(["--repository", args.repository])
        _run(cmd)
    else:
        print(f"Built artifacts in: {dist_dir}")
        print(f"To upload: {sys.executable} -m twine upload {dist_dir}/*")
    return 0


def _hf_cli_cmd() -> List[str]:
    return [sys.executable, "-m", "huggingface_hub.commands.huggingface_cli"]


def _main_publish_hf(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Upload files to Hugging Face Hub.")
    parser.add_argument("--repo", type=str, required=True, help="<user_or_org>/<repo_name>")
    parser.add_argument("--create-repo", action="store_true")
    parser.add_argument("--repo-type", type=str, default="model")
    parser.add_argument("--weights", type=str, default="models/genesis_152m_instruct.safetensors")
    parser.add_argument("--readme", type=str, default="models/genesis_152m_instruct_README.md")
    parser.add_argument("--license", type=str, default="MODEL_LICENSE")
    parser.add_argument("--weights-dst", type=str, default=None)
    parser.add_argument("--whoami", action="store_true")
    args = parser.parse_args(argv)

    _run([sys.executable, "-m", "pip", "install", "huggingface_hub>=0.34.0,<1.0"])
    hf = _hf_cli_cmd()

    if args.whoami:
        _run([*hf, "whoami"])
        return 0

    if args.create_repo:
        _run([*hf, "repo", "create", args.repo, "--type", args.repo_type])

    weights_src = Path(args.weights)
    weights_dst = args.weights_dst or weights_src.name
    _run([*hf, "upload", args.repo, str(weights_src), weights_dst, "--repo-type", args.repo_type])
    _run([*hf, "upload", args.repo, args.readme, "README.md", "--repo-type", args.repo_type])
    _run([*hf, "upload", args.repo, args.license, "LICENSE", "--repo-type", args.repo_type])
    return 0


def _main_publish(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="genesis publish")
    sub = parser.add_subparsers(dest="target", required=True)
    sub.add_parser("pypi")
    sub.add_parser("hf")
    args, rest = parser.parse_known_args(argv)

    if args.target == "pypi":
        return _main_publish_pypi(rest)
    if args.target == "hf":
        return _main_publish_hf(rest)
    return 2


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "publish":
        return _main_publish(argv[1:])
    if argv and argv[0] == "chat":
        return _main_chat(argv[1:])
    return _main_chat(argv)
