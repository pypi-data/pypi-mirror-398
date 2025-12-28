# ==========================================================
# CrystalAI v0.7 — Stabilized & Corrected Engine
# ----------------------------------------------------------

import os
import ast
import difflib
import requests
import json
from typing import Optional, Dict, Any


# ==========================================================
# Response Wrapper
# ==========================================================
class CrystalAIResponse:
    def __init__(self, text: str, meta: Optional[Dict[str, Any]] = None):
        self.text = text
        self.meta = meta or {}

    def __str__(self):
        return self.text


# ==========================================================
# MAIN ENGINE
# ==========================================================
class AI:
    DEFAULT_MODEL = "llama-3.1-70b-versatile"
    DEFAULT_PERSONALITY = (
        "You are CrystalWindow AI. You help users with Python code, "
        "debugging, error analysis, documentation, and file analysis. "
        "Be friendly, technical, clear, and precise."
    )

    PLACEHOLDER_KEY = "NO_KEY_PROVIDED"

    # ------------------------------------------------------
    def __init__(self, key=None, model=None):

        # --- KEY VALIDATION ---
        # If no key passed try common environment variables (makes key optional)
        if not key:
            key = (
                os.environ.get("CRYSTALAI_API_KEY")
                or os.environ.get("GROQ_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("API_KEY")
            )
            if key:
                key = str(key).strip()

        if not key or len(str(key).strip()) == 0:
            print("[CrystalAI] No API key provided → using offline mode.")
            self.key = None  # forces offline fallback
            self.force_local = True
        else:
            self.key = key
            self.force_local = False

        # --- MODEL VALIDATION ---
        # If model is omitted (None) use default silently; only warn if an invalid model is explicitly passed
        if model is None:
            self.model = self.DEFAULT_MODEL
        elif not isinstance(model, str) or len(model) < 3:
            print("[CrystalAI] Unknown model → using default.")
            self.model = self.DEFAULT_MODEL
        else:
            self.model = model

        self.personality = self.DEFAULT_PERSONALITY
        self.memory = []
        self.use_memory = True
        self.library_context = ""

    # ==========================================================
    # PERSONALITY
    # ==========================================================
    def set_personality(self, txt):
        if not isinstance(txt, str) or len(txt.strip()) < 10:
            print("[CrystalAI] Personality too short → reverting to default.")
            self.personality = self.DEFAULT_PERSONALITY
            return

        if len(txt) > 3000:
            print("[CrystalAI] Personality too long → using default.")
            self.personality = self.DEFAULT_PERSONALITY
            return

        self.personality = txt.strip()

    # ==========================================================
    # LIBRARY INGESTION
    # ==========================================================
    def index_library(self, folder):
        """
        Load all Python files as context for smarter answers.
        """
        if not os.path.exists(folder):
            print("[CrystalAI] Library folder not found.")
            return

        collected = []
        for root, _, files in os.walk(folder):
            for f in files:
                if f.endswith(".py"):
                    try:
                        p = os.path.join(root, f)
                        with open(p, "r", encoding="utf8") as fp:
                            collected.append(
                                f"# FILE: {p}\n{fp.read()}\n\n"
                            )
                    except:
                        pass

        self.library_context = "\n".join(collected)[:120_000]   # trimmed

    # ==========================================================
    # FILE READER
    # ==========================================================
    def _read_file(self, path):
        if not path:
            return None
        if not os.path.exists(path):
            return f"[CrystalAI] file not found: {path}"
        try:
            with open(path, "r", encoding="utf8") as f:
                return f.read()
        except:
            return "[CrystalAI] could not read file."

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================
    def _build_prompt(self, user_text, file_data):
        final = (
            f"[SYSTEM]\n{self.personality}\n\n"
            f"[USER]\n{user_text}\n\n"
        )

        if self.use_memory and self.memory:
            final += "[MEMORY]\n"
            for m in self.memory[-6:]:
                final += f"User: {m['user']}\nAI: {m['ai']}\n"
            final += "\n"

        if self.library_context:
            final += f"[LIBRARY]\n{self.library_context}\n\n"

        if file_data and not file_data.startswith("[CrystalAI]"):
            final += f"[FILE]\n{file_data}\n\n"

        return final[:190_000]   # safety limit

    def _save_memory(self, user, ai):
        self.memory.append({"user": user, "ai": ai})
        if len(self.memory) > 60:
            self.memory.pop(0)

    # ==========================================================
    # LOCAL FALLBACK AI
    # ==========================================================
    def _local_ai(self, user_text, file_data):
        """
        Much cleaner, more reliable fallback engine.
        """

        # --- AST SECTION ---
        if file_data and not file_data.startswith("[CrystalAI]"):
            try:
                ast.parse(file_data)
                return (
                    "[LocalAI] File parsed successfully — no syntax errors.\n"
                    "Ask for refactoring, explanation, or improvements."
                )
            except SyntaxError as se:
                snippet = self._snippet(file_data, se.lineno)
                return (
                    "[LocalAI] SyntaxError found:\n"
                    f"• {se.msg}\n"
                    f"• Line {se.lineno}\n\n"
                    f"{snippet}"
                )

        # --- GENERIC HELP ---
        lower = user_text.lower()
        if "python" in lower or "fix" in lower or "error" in lower:
            return (
                "[LocalAI] Offline mode: I can help with general Python logic.\n"
                "If you provide a file, I can analyze it using AST."
            )

        return "[LocalAI] Offline mode active — limited responses available."

    # ==========================================================
    # MAIN "ASK" FUNCTION
    # ==========================================================
    def ask(self, text, file=None):
        file_data = self._read_file(file)
        prompt = self._build_prompt(text, file_data)

        # If no API key → offline only
        if self.force_local:
            resp = self._local_ai(text, file_data)
            self._save_memory(text, resp)
            return CrystalAIResponse(resp)

        # Online mode
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.personality},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }

            r = requests.post(url, json=payload, headers=headers, timeout=8)
            data = r.json()

            if "error" in data:
                raise RuntimeError(data["error"])

            resp = data["choices"][0]["message"]["content"]

        except Exception:
            resp = self._local_ai(text, file_data)

        self._save_memory(text, resp)
        return CrystalAIResponse(resp)

    # ==========================================================
    # TERMINAL HELPER
    # ==========================================================
    def ask_t(self, text, file=None):
        return self.ask(f"[TERMINAL] {text}", file)

    # ==========================================================
    # AUTO FIX CODE
    # ==========================================================
    def fix_code(self, file_path):
        orig = self._read_file(file_path)

        if not orig or orig.startswith("[CrystalAI]"):
            return CrystalAIResponse(orig or "[CrystalAI] file missing")

        try:
            ast.parse(orig)
            return CrystalAIResponse("[AI] No syntax errors found.")
        except SyntaxError as se:
            fixed, notes = self._simple_fix(orig, se)
            diff = self._make_diff(orig, fixed)
            msg = "[AI] Auto-fix result:\n" + "\n".join(notes) + "\n\n" + diff
            return CrystalAIResponse(msg, {"diff": diff, "notes": notes})

    # ==========================================================
    # SIMPLE AUTO-FIX ENGINE
    # ==========================================================
    def _simple_fix(self, src, err):
        notes = []
        lines = src.splitlines()
        msg = getattr(err, "msg", "")
        lineno = err.lineno or 0

        if "expected" in msg and ":" in msg:
            if 1 <= lineno <= len(lines):
                l = lines[lineno - 1].rstrip()
                if not l.endswith(":"):
                    lines[lineno - 1] = l + ":"
                    notes.append("[fix] added missing ':'")
                    candidate = "\n".join(lines)
                    try:
                        ast.parse(candidate)
                        return candidate, notes
                    except:
                        pass

        notes.append("[info] auto-fix could not fix the error")
        return src, notes

    # ==========================================================
    # DIFF HELPER
    # ==========================================================
    def _make_diff(self, old, new):
        return "\n".join(
            difflib.unified_diff(
                old.splitlines(), new.splitlines(),
                fromfile="old", tofile="new", lineterm=""
            )
        )

    # ==========================================================
    # SNIPPET HELPER
    # ==========================================================
    def _snippet(self, src, lineno, ctx=2):
        lines = src.splitlines()
        start = max(0, lineno - ctx - 1)
        end = min(len(lines), lineno + ctx)
        out = []
        for i in range(start, end):
            mark = "->" if (i + 1) == lineno else "  "
            out.append(f"{mark} {i+1:4}: {lines[i]}")
        return "\n".join(out)

# ==========================================================
# END OF ENGINE
# ==========================================================
