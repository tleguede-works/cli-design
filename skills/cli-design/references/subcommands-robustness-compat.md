# Subcommands, robustness, signals, and future-proofing

## Subcommands

Subcommands tame a complex tool, or fold closely related tools into one (RCS → Git). They share global flags, help, config and storage.

- **Be consistent across subcommands**: same flag names for the same concepts, same output formatting, same `--json` shape conventions.
- **Consistent multi-level naming**: for many objects × operations, use two levels, noun + verb (`docker container create`). Use the same verbs across objects (`create`/`list`/`delete` everywhere, not `create`/`ls`/`remove` by type). `noun verb` is more common than `verb noun`; either is fine if consistent.
- **No ambiguous or similar names**: `update` vs `upgrade` confuses everyone. Pick different words or disambiguate.

## Robustness

**Validate input early** and bail before doing anything harmful, with understandable errors.

**Responsive beats fast.** Print something within ~100ms. Before a network request, say what you're doing so it doesn't look hung.

**Show progress for long work.** A spinner or progress bar makes a program feel faster. If a bar may stall, add an ETA or an animated element so the user knows it's alive. Libraries: tqdm / rich (Python), schollz/progressbar, charmbracelet/bubbles (Go), node-progress, ora, cli-progress (Node), indicatif (Rust). Only animate on a TTY.

**Parallelism, thoughtfully.** Big usability win (`docker pull`'s per-layer bars), but interleaved output is easy to get wrong — use a library that supports multiple bars. If you hide logs behind progress bars on success, **print the logs on failure**, or debugging becomes impossible.

**Timeouts.** Network operations get a sensible default timeout and a way to configure it. Never hang forever.

**Recoverable.** After a transient failure (network dropped), up-arrow + enter should resume or safely redo the work — be idempotent.

**Crash-only.** Better than idempotent: avoid requiring cleanup, or defer cleanup to the next run, so the program can exit immediately on failure or interruption. The program must expect to start in a state where previous cleanup never ran.

**Expect misuse.** People will wrap it in scripts, run it on bad connections, run many instances concurrently (lock files, atomic writes via temp + rename), and run it on systems you didn't test (case-insensitive but case-preserving macOS filesystems, Windows paths, no color support).

## Signals and control characters

- **Ctrl-C (SIGINT): exit as soon as possible.** Print something immediately, before cleanup. Put a timeout on cleanup so it can't hang.
- **Second Ctrl-C during long cleanup: skip it.** Tell the user what a second Ctrl-C will do, especially if destructive. Docker Compose: `Gracefully stopping... (press Ctrl+C again to force)`.
- Exit with the conventional code for signal termination (128 + signal number, i.e. 130 for SIGINT) so calling scripts can tell.
- Handle SIGTERM similarly to SIGINT. Handle SIGPIPE/EPIPE quietly (`mycmd | head` must not print a broken-pipe traceback).

## Future-proofing

Subcommands, args, flags, config files, env vars and machine-readable output are all interfaces you're committing to keep working. Change them only with a long, documented deprecation. (SemVer only excuses so much: a major bump every month is meaningless.)

- **Keep changes additive.** Add a new flag instead of changing an old one's meaning — as long as the interface doesn't bloat.
- **Warn before a breaking change, in the tool.** When someone uses the deprecated flag, tell them it's changing, what to use instead today, and when. If you can detect they've migrated, stop warning — then the eventual change is a non-event.
- **Human-readable output may change.** Iteration requires it. Tell script authors to use `--plain` or `--json`, which are the stable contracts.
- **No catch-all subcommand.** If `mycmd echo hi` is treated as `mycmd run echo hi`, you can never add any subcommand without potentially breaking someone's script.
- **No arbitrary prefix abbreviations.** If `mycmd i` means `install` by prefix matching, you can never add another `i…` command. Explicit, stable aliases are fine.
- **No time bombs.** Will it still work in 20 years? Avoid hard dependencies on external servers for core behavior — especially your own, which is the server most likely to disappear. Never block on an analytics call.
