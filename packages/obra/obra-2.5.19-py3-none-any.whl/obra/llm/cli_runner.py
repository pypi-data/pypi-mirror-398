"""CLI-backed LLM invocation helpers for Obra.

Hybrid handlers (derive/examine/revise/execute) should be able to run using
provider CLIs (claude/codex/gemini) without requiring API keys.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path


def _prepare_prompt(prompt: str, provider: str, thinking_level: str) -> str:
    if provider == "anthropic" and thinking_level == "maximum":
        return f"ultrathink: {prompt}"
    return prompt


def invoke_llm_via_cli(
    *,
    prompt: str,
    cwd: Path,
    provider: str,
    model: str,
    thinking_level: str,
    on_stream: Callable[[str], None] | None = None,
    output_schema: Path | None = None,
    timeout_s: int = 600,
) -> str:
    """Invoke an LLM via its provider CLI and return stdout as the model response."""
    from obra.config import build_llm_args, get_llm_cli

    prepared_prompt = _prepare_prompt(prompt, provider, thinking_level)
    cli_command = get_llm_cli(provider)

    # build_llm_args expects a resolved config dict
    cli_args = build_llm_args({"provider": provider, "model": model, "thinking_level": thinking_level})

    # Special-case Codex: for "text-only" orchestration prompts, keep it read-only and capture the
    # final message cleanly via --output-last-message.
    if provider == "openai" and cli_command == "codex":
        # Avoid the "workspace-write" behavior of --full-auto for orchestration prompts.
        # Use stdin to avoid arg-length limits.
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as f:
            output_path = f.name

        cmd = [
            cli_command,
            "exec",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--output-last-message",
            output_path,
        ]
        if output_schema:
            cmd.extend(["--output-schema", str(output_schema)])
        if model and model not in ("default", "auto"):
            cmd.extend(["--model", model])

        try:
            subprocess.run(
                cmd + ["-"],
                cwd=cwd,
                input=prepared_prompt,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
            return Path(output_path).read_text(encoding="utf-8")
        finally:
            try:
                Path(output_path).unlink(missing_ok=True)
            except Exception:
                pass

    # ISSUE-SAAS-030 FIX: Use stdin for Claude CLI to avoid command-line length limits.
    # On Windows, command-line args are limited to ~8K-32K chars. Long prompts get truncated,
    # causing the LLM to see JSON instructions but not the objective.
    # Claude CLI supports stdin: echo "prompt" | claude --print ...
    if provider == "anthropic" and cli_args and cli_args[0] == "--print":
        # Remove --print from cli_args, we'll add it back without the prompt as arg
        remaining_args = cli_args[1:]
        cmd = [cli_command, "--print"] + remaining_args
        use_stdin = True
    else:
        # Default: flags first, then prompt as positional argument
        cmd = [cli_command] + cli_args + [prepared_prompt]
        use_stdin = False

    if not on_stream:
        result = subprocess.run(
            cmd,
            check=False, cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",  # Explicit UTF-8 to avoid Windows cp1252 issues
            timeout=timeout_s,
            input=prepared_prompt if use_stdin else None,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "Unknown CLI error")[:500])
        return result.stdout

    # Streaming path
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdin=subprocess.PIPE if use_stdin else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",  # Explicit UTF-8 to avoid Windows cp1252 issues
    )
    # If using stdin, write prompt and close stdin to signal EOF
    if use_stdin and proc.stdin:
        proc.stdin.write(prepared_prompt)
        proc.stdin.close()

    assert proc.stdout is not None
    chunks: list[str] = []
    try:
        for line in proc.stdout:
            chunks.append(line)
            on_stream(line)
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise RuntimeError(f"LLM CLI timed out after {timeout_s}s")

    if proc.returncode != 0:
        stderr = (proc.stderr.read() if proc.stderr else "")  # type: ignore[union-attr]
        raise RuntimeError((stderr or "Unknown CLI error")[:500])

    return "".join(chunks)
