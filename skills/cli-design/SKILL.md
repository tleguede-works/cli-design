---
name: cli-design
description: Design, build, review and fix command-line programs (CLIs) using the Command Line Interface Guidelines (clig.dev). Covers argument and flag design, help text, stdout vs stderr, exit codes, --json/--plain output, color and TTY detection, NO_COLOR, error messages, prompts and --no-input, confirmations for destructive actions, subcommands, config files and env var precedence, secrets handling, Ctrl-C/signals, progress output, naming, distribution, telemetry and deprecation. Use this skill whenever the user is writing or changing any command-line tool, script with flags, or subcommand (argparse, Click, Typer, Cobra, clap, oclif, commander, picocli, yargs, bash getopts…), asks to "add a CLI" to a project, asks how flags/help/output/exit codes should work, or wants a CLI reviewed for UX or scriptability — even if they never say "guidelines" or "best practices".
---

# CLI design (based on clig.dev)

This skill turns the [Command Line Interface Guidelines](https://clig.dev/) into working practice. Use it while you write CLI code, not just when asked for a review: most of the value is in getting small defaults right (where output goes, what exit code is returned, what happens with no TTY) before anyone notices they're wrong.

## The mindset

A CLI has two audiences at once: a human typing at a terminal, and a script piping its output somewhere. Design for the human first, then make sure nothing you did for the human breaks the script. Almost every rule below falls out of that tension:

- **Human-first**: say what happened, suggest next steps, rewrite errors in plain language, show progress, lead help with examples.
- **Composable**: primary output on stdout, chatter on stderr, meaningful exit codes, stable `--json`/`--plain` output, no prompts or color or animation when there's no TTY.
- **Consistent**: use the flag names users already know (`-h`, `--force`, `--dry-run`, `-o`), and behave the same across subcommands.
- **Conversational**: users learn a CLI by trial and error. Each error message and each suggestion is part of that conversation.
- **Robust and respectful**: validate early, time out, survive Ctrl-C, don't phone home without consent, don't leak secrets.

The guidelines are defaults, not law. If a rule is wrong for this specific program, break it deliberately and say why.

## Workflow

**When building a new CLI or adding commands:**
1. Pick an argument-parsing library rather than hand-parsing `sys.argv` (see the list in `references/arguments-and-flags.md`). It gets help, errors, and typo suggestions right for free.
2. Sketch the interface first: command name, subcommands (noun-verb or verb-noun, but consistent), positional args vs flags, which actions are destructive. Show the user this sketch when the design is non-trivial — interfaces are hard to change later.
3. Implement with the **Essentials** below baked in from the first commit.
4. Read the relevant reference file(s) for the parts you're touching (table below).
5. Run `scripts/audit_cli.py` against the built command and fix what it flags.

**When reviewing or fixing an existing CLI:** go through the **Review checklist**, run `scripts/audit_cli.py`, and report findings ranked by impact (broken scripting and data loss first, polish last). Quote the specific code and propose concrete diffs, not just principles.

## Essentials (get these right every time)

These are the rules whose violation makes a CLI broken rather than merely unpolished.

1. **Exit codes**: `0` on success, non-zero on failure. Map distinct non-zero codes to the important failure modes if callers will care (e.g. `1` general error, `2` usage error is the common convention). Scripts depend on this; never print an error and exit 0.
2. **stdout is for output, stderr is for messages**. The thing the user asked for (data, results, machine-readable output) goes to stdout. Logs, progress, warnings, errors, prompts go to stderr. Otherwise `mycmd | jq` breaks.
3. **Help**: `-h` and `--help` show help and exit 0, wherever they appear in the command line (`mycmd sub --foo -h` still shows help for `sub`). Don't give `-h` any other meaning. If the command needs args and got none, show concise help (description, 1–2 examples, pointer to `--help`) rather than an error wall. Git-like tools also support `mycmd help <sub>`.
4. **TTY awareness**: check whether stdin/stdout/stderr are terminals.
   - No color, spinners or progress animation when the stream isn't a TTY. Check stdout and stderr separately.
   - Disable color also when `NO_COLOR` is set and non-empty, `TERM=dumb`, or `--no-color` is passed. Honor `FORCE_COLOR` if you support forcing.
   - Never *require* a prompt: if stdin isn't a TTY (or `--no-input` is passed), don't prompt — fail with a message naming the flag that supplies the value.
5. **Errors for humans**: catch expected errors and say what went wrong and how to fix it ("Can't write to out.txt: permission denied. Try `chmod +w out.txt`."). No raw stack traces for expected failures; keep tracebacks for genuinely unexpected errors, ideally behind `--debug`/`--verbose` or in a log file, with a pointer to where to report bugs.
6. **Dangerous actions need confirmation**: prompt (`y/yes`) when interactive; require `--force` (or `--yes`) when not. For severe actions (deleting a whole app/server), make the user type the resource name, with `--confirm=<name>` for scripts. Offer `--dry-run`/`-n` for bulk or hard-to-undo changes.
7. **Secrets never via flags or env vars**: flag values leak into `ps` and shell history; env vars leak into logs, child processes, `docker inspect`. Accept secrets via `--password-file`, stdin, or a credential store; prompt with echo off.
8. **Full-length flags**: every short flag has a long form (`-o`/`--output`). Reserve single letters for the commonly used ones.
9. **Say something within ~100ms**, and show progress for anything slow. A silent CLI looks hung. Print before network calls. Put timeouts on network operations.
10. **Ctrl-C works**: exit promptly on SIGINT, say something immediately, bound any cleanup with a timeout; a second Ctrl-C skips cleanup.

## Reference files — read the one(s) you need

| Working on… | Read |
|---|---|
| Help text, usage, examples, man pages, web docs, "did you mean" | `references/help-and-docs.md` |
| Output format, `--json`/`--plain`, `-q`, color, emoji, pagers, state-change messages, error messages | `references/output-and-errors.md` |
| Args vs flags, standard flag names, defaults, `-` for stdin/stdout, prompts, `--no-input`, confirmations, secrets, parsing libraries | `references/arguments-and-flags.md` |
| Subcommand structure, robustness (validation, progress, timeouts, parallelism, crash-only), signals/Ctrl-C, deprecation and backwards compatibility | `references/subcommands-robustness-compat.md` |
| Config files, XDG, precedence, environment variables, `.env`, naming the command, distribution/install/uninstall, analytics/telemetry | `references/config-env-naming-distribution.md` |
| Language-specific snippets (TTY detection, color, exit codes, signal handling) in Python, Go, Node, Rust, Bash | `references/snippets.md` |

## Review checklist

Use this when reviewing a CLI, or as a final pass before calling your own CLI done. Mark each as ✅ / ⚠️ / ❌ in the review.

**Basics**
- [ ] Uses an argument-parsing library
- [ ] Exit 0 on success, non-zero on every failure path (check `except` blocks and early returns)
- [ ] Primary output → stdout; logs/errors/progress/prompts → stderr

**Help & docs**
- [ ] `-h`/`--help` anywhere → help, exit 0; `-h` not overloaded
- [ ] No-args (when args are required) → concise help, not a stack trace
- [ ] Help leads with examples; common flags first; includes docs/issue URL
- [ ] Typos get a "did you mean…?" suggestion (not silent auto-correction of state-changing commands)
- [ ] Expects piped stdin but stdin is a TTY → prints help/hint instead of hanging

**Output**
- [ ] Human-readable by default; `--json` for structured output; `--plain` if the human format breaks line-per-record
- [ ] State changes are reported briefly; `-q`/`--quiet` silences non-essential output
- [ ] Color only on TTYs; respects `NO_COLOR`, `TERM=dumb`, `--no-color`
- [ ] No animations/progress bars when not a TTY
- [ ] No developer-only noise or log-level prefixes by default
- [ ] Long output uses a pager only when interactive (`less -FIRX`)

**Errors**
- [ ] Expected errors rewritten with cause + fix; most important info last
- [ ] Repeated similar errors grouped
- [ ] Unexpected errors: debug info available, bug-report path given

**Args, flags & interactivity**
- [ ] Every short flag has a long form; standard names used (`--force`, `--dry-run`, `--output`, `--quiet`, `--verbose`, `--json`, `--version`, `--no-input`)
- [ ] Flags preferred over multiple positional args of different meaning
- [ ] `-` accepted for stdin/stdout where a file is taken
- [ ] Prompts only on TTY; `--no-input` disables them; every prompted value also has a flag
- [ ] Destructive actions confirmed (or `--force`), severity-appropriate
- [ ] Secrets not accepted via flags or env vars; password prompts don't echo
- [ ] Flags work before and after subcommands where possible

**Subcommands, robustness, compat**
- [ ] Consistent flags/output/verbs across subcommands; no confusing pairs like update/upgrade
- [ ] No catch-all default subcommand; no implicit prefix abbreviations
- [ ] Input validated early; network timeouts with sane defaults
- [ ] Re-running after failure resumes or is safe (idempotent / crash-only)
- [ ] Ctrl-C exits quickly; cleanup is bounded
- [ ] Breaking changes are additive or preceded by in-tool deprecation warnings

**Config, env, distribution**
- [ ] Precedence: flags > env vars > project config > user config > system config
- [ ] Config under XDG paths (`$XDG_CONFIG_HOME`, default `~/.config/<app>`)
- [ ] Env var names `UPPER_SNAKE`, prefixed with the app name; standard vars honored (`NO_COLOR`, `DEBUG`, `EDITOR`, `PAGER`, `HTTP(S)_PROXY`, `TMPDIR`, `HOME`)
- [ ] Doesn't edit other programs' config without consent
- [ ] Name is short, lowercase, easy to type, not a generic collision
- [ ] Simple install (single binary or native package) and documented uninstall
- [ ] No telemetry without explicit, documented consent

## Auditing a real binary

`scripts/audit_cli.py` runs the command in a sandboxed way (help/version/bogus-flag only — it never runs real actions) and checks the mechanically verifiable rules: help on `-h`/`--help`, `--version`, unknown-flag handling and exit codes, stdout/stderr split, no ANSI escapes when piped, `NO_COLOR` honored under a pseudo-TTY, no hang on missing input.

```bash
python3 scripts/audit_cli.py -- mycmd              # top-level command
python3 scripts/audit_cli.py -- mycmd deploy       # a subcommand
python3 scripts/audit_cli.py --json -- python -m myapp
```

It exits non-zero if any check fails, so it can sit in CI. It only covers what can be checked from the outside; the checklist above still needs a read of the code.

## When writing the review/report

Lead with the issues that break scripts or risk data (exit codes, stdout pollution, prompts without TTY, unconfirmed destructive actions, secrets in flags), then UX issues (help, errors, output), then polish. For each: what's wrong, where (file:line), why it matters for users, and the fix as code.

## Attribution

Guidance adapted from *Command Line Interface Guidelines* (https://clig.dev) by Aanand Prasad, Ben Firshman, Carl Tashian and Eva Parish, licensed under CC BY-SA 4.0 (see `LICENSE-clig-CC-BY-SA-4.0.txt`). This skill's text is shared under the same license.
