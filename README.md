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

### With `npx skills`

The quickest way — installs the skill into any supported agent (Claude Code, Codex, Cursor, Copilot, Gemini CLI…):

```bash
npx skills add tleguede-works/cli-design
```

Add `-g` to install it for every project (user-level) instead of just the current one:

```bash
npx skills add tleguede-works/cli-design -g
```

To keep it up to date afterwards:

```bash
npx skills update cli-design
```

### As a Claude Code plugin

Clone the repo and point your plugin configuration at it:

```bash
git clone https://github.com/tleguede-works/cli-design.git
```

The plugin manifest is `.claude-plugin/plugin.json` and exposes the single skill `cli-design`.

### Manually

Copy `skills/cli-design/` into your agent's skills directory (for example `~/.claude/skills/` for Claude Code), keeping `SKILL.md` at the root of the copied folder.

## Layout

```
LICENSE                             # CC BY-SA 4.0
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

## Credits

This skill is a derivative work. Credit belongs to:

- **Command Line Interface Guidelines (clig.dev)** — Aanand Prasad, Ben Firshman, Carl Tashian and Eva Parish. The guidance here is adapted from the [Command Line Interface Guidelines](https://clig.dev/), licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The licence text is preserved at `skills/cli-design/LICENSE-clig-CC-BY-SA-4.0.txt`.
- **Claude (Anthropic)** — the skill's structure, workflow, review checklist, reference files and `audit_cli.py` were written with Claude, Anthropic's AI assistant, working alongside the author.

Maintained by [@tleguede-works](https://github.com/tleguede-works).

## License

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) — see [`LICENSE`](LICENSE).

You are free to share and adapt this material, provided you give appropriate credit, link to the licence, indicate whether changes were made, and license your contributions under the same terms. As a derivative of clig.dev, this skill must stay under CC BY-SA 4.0.
