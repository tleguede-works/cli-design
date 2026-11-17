# cli-design

A Claude Code plugin (skill) that turns the [Command Line Interface Guidelines](https://clig.dev/) into working practice: designing, building, reviewing and fixing command-line programs.

Most of a CLI's quality lives in defaults nobody notices until they're wrong — where output goes, which exit code comes back, what happens when there is no TTY. This skill puts those rules in front of the agent while the code is being written, not only when a review is requested.

## What it covers

- **Arguments and flags** — positional vs flags, standard names (`--force`, `--dry-run`, `--output`, `--json`, `--no-input`, `-` for stdin/stdout), parsing libraries, prompt design, secret handling
- **Help and docs** — `-h`/`--help` semantics, examples-first help, "did you mean…?" suggestions, man pages and web docs
- **Output and errors** — stdout vs stderr, `--json`/`--plain`, `-q`, color and `NO_COLOR`/`TERM=dumb` handling, pagers, state-change messages, human-readable errors
- **Subcommands and robustness** — command structure, early validation, timeouts, parallelism, Ctrl-C and signal handling, deprecation and backwards compatibility
- **Config, env and distribution** — XDG paths, precedence (flags > env > project > user > system), env var naming, install/uninstall, telemetry consent

## Install

As a Claude Code plugin, drop the directory into your plugins (or point your plugin manifest at this repo):

```bash
git clone https://github.com/tleguede-works/cli-design.git
```

The plugin manifest is `.claude-plugin/plugin.json` and exposes the single skill `cli-design`.

## Layout

```
.claude-plugin/plugin.json          # plugin manifest
skills/cli-design/
  SKILL.md                          # the skill: mindset, workflow, essentials, review checklist
  references/
    arguments-and-flags.md
    help-and-docs.md
    output-and-errors.md
    subcommands-robustness-compat.md
    config-env-naming-distribution.md
    snippets.md                     # TTY/color/exit-code/signal snippets: Python, Go, Node, Rust, Bash
  scripts/audit_cli.py              # external black-box audit of a real binary
  LICENSE-clig-CC-BY-SA-4.0.txt
```

## Auditing a CLI

`audit_cli.py` runs a command in a sandboxed way — help, version and bogus flags only; it never triggers real actions — and checks the mechanically verifiable rules: help on `-h`/`--help`, `--version`, unknown-flag handling and exit codes, the stdout/stderr split, no ANSI escapes when piped, `NO_COLOR` honored under a pseudo-TTY, and no hang on missing input.

```bash
python3 skills/cli-design/scripts/audit_cli.py -- mycmd           # top-level command
python3 skills/cli-design/scripts/audit_cli.py -- mycmd deploy    # a subcommand
python3 skills/cli-design/scripts/audit_cli.py --json -- python -m myapp
```

It exits non-zero if any check fails, so it can run in CI. It only covers what is observable from the outside — the review checklist in `SKILL.md` still needs someone to read the code.

## License

The skill's guidance is adapted from *Command Line Interface Guidelines* (https://clig.dev) by Aanand Prasad, Ben Firshman, Carl Tashian and Eva Parish, licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). This skill's text is shared under the same license — see `skills/cli-design/LICENSE-clig-CC-BY-SA-4.0.txt`.
