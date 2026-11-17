# Arguments, flags and interactivity

Terminology: **args** are positional (`cp foo bar` — order matters). **Flags** are named: `-r` or `--recursive`, optionally with a value (`--file foo.txt` or `--file=foo.txt`); their order normally doesn't matter.

## Use a parsing library

It handles flags, help, errors and often spelling suggestions correctly. Some good ones:

| Language | Libraries |
|---|---|
| Multi-platform | docopt |
| Bash | argbash (or `getopts` for tiny scripts) |
| Go | Cobra, urfave/cli |
| Haskell | optparse-applicative |
| Java | picocli |
| Julia | ArgParse.jl, Comonicon.jl |
| Kotlin | clikt |
| Node | oclif (also commander, yargs) |
| Deno | `@std/cli` parseArgs |
| Perl | Getopt::Long |
| PHP | symfony/console, CLImate |
| Python | argparse, Click, Typer |
| Ruby | TTY toolkit |
| Rust | clap |
| Swift | swift-argument-parser |

## Designing args and flags

**Prefer flags to args.** More typing, but clearer, and much easier to extend later without ambiguity or breaking changes.

**Full-length versions of all flags** (`-h` and `--help`). Long forms make scripts self-documenting.

**One-letter flags only for common options**, especially at top level with subcommands. Don't burn the short-flag namespace on rare options.

**Multiple args are fine for the same kind of thing**: `rm a.txt b.txt c.txt`, which also makes globbing work.

**Two or more args meaning different things is a smell.** Exception: a very common primary action where brevity is worth memorizing (`cp <src> <dest>`).

**Use standard flag names:**

| Flag | Meaning |
|---|---|
| `-a`, `--all` | All (ps, fetchmail) |
| `-d`, `--debug` | Debug output |
| `-f`, `--force` | Force; also skips confirmation for destructive actions in scripts |
| `--json` | JSON output |
| `-h`, `--help` | Help — only help |
| `-n`, `--dry-run` | Describe what would change without changing it (rsync, git add) |
| `--no-input` | Disable all prompts |
| `-o`, `--output` | Output file (sort, gcc) |
| `-p`, `--port` | Port (psql, ssh) |
| `-q`, `--quiet` | Less output |
| `-u`, `--user` | User (ps, ssh) |
| `--version` | Version |
| `-v` | Ambiguous (verbose vs version). Consider `-d`/`--verbose` for verbosity and `-v` for version, or leave `-v` unused |

**Make the default right for most users.** Most people never find or alias the flag. If `ls` were designed today it would probably default to `ls -lhF`.

**`-` means stdin/stdout** wherever a file path is accepted: `curl … | tar xvf -`.

**Optional flag values: use a sentinel word like `none`** (`ssh -F none`), never a blank value, which makes it ambiguous whether the next token is the flag's value or an argument.

**Order independence.** `mycmd --foo=1 sub` and `mycmd sub --foo=1` should both work where the parser allows. Users hit up-arrow and append flags at the end; "unknown flag" for a flag that exists elsewhere is baffling. (In Cobra use persistent flags; in Click consider passing parent options via context or repeating them.)

**Never read secrets directly from flags.** `--password hunter2` leaks into `ps` and shell history, and pushes people toward env vars (also leaky). Accept `--password-file <path>`, stdin, or a credential helper/keychain. `--password "$(< file)"` has the same leak; avoid it.

## Prompts and interactivity

**Prompt for missing input** — but only as a convenience.

**Never *require* a prompt.** Every prompted value must also be passable as a flag/arg. If stdin isn't a TTY, don't prompt; fail with an error naming the flag to pass.

**Only prompt or show interactive UI when stdin is a TTY.** That reliably distinguishes interactive use from pipes and scripts.

**`--no-input`** disables every prompt explicitly. If required input is then missing, fail and say which flag supplies it.

**Passwords: turn off echo** (Python `getpass`, Go `golang.org/x/term.ReadPassword`, Node `read` with `silent`, Rust `rpassword`).

**Let the user escape.** Make clear how to quit. Ctrl-C must work even while blocked on network I/O. If you wrap something where Ctrl-C can't quit (ssh, tmux, telnet), document the escape (ssh's `~.`).

## Confirming dangerous actions

Convention: prompt for `y`/`yes` when interactive; require `-f`/`--force` (or `--yes`) when not. Scale to the danger:

- **Mild** — small local change like deleting one file. Prompt optional; if the command is literally named `delete`, probably skip it.
- **Moderate** — deleting a directory, deleting a remote resource, bulk changes that can't easily be undone. Usually prompt. Offer `--dry-run`.
- **Severe** — deleting something complex like a whole remote app or server. Make it hard to confirm by accident: require typing the resource's name. Allow `--confirm=<name>` so it remains scriptable.

Watch for non-obvious destruction: changing a count in a config from 10 to 1 that implicitly deletes 9 things is severe and should be hard to do by accident.
