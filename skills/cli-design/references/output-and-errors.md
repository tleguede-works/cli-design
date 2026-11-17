# Output and errors

## Output

**Human-readable output is the default.** The simplest test for whether a human is reading a stream is whether it's a TTY. Every language has a check (`isatty`); see `snippets.md`.

**Machine-readable output where it doesn't hurt usability.** Text streams are the universal UNIX interface: a user should be able to pipe your output to `grep` and get what they expect. "Expect the output of every program to become the input to another, as yet unknown, program." (Doug McIlroy)

**`--plain`** when the human format breaks line-oriented tools — e.g. a table that wraps a cell across lines. `--plain` gives one record per line with no decoration, for `grep`/`awk`.

**`--json`** for structured output: pretty-ish formatted JSON on stdout, which works with `jq` and pipes to/from web services with `curl`. When `--json` is set, nothing else may go to stdout — messages still go to stderr. Keep the JSON schema stable; it's an interface.

**Brief output on success.** Silence on success is the old UNIX norm and suits scripts, but humans then think the command hung (`cp` on a big file). Err toward less, not nothing. Provide `-q`/`--quiet` to suppress non-essential output so scripts don't need `2>/dev/null`.

**Tell the user when state changes.** Explain what just happened so they can model the system, especially when the result isn't a direct mapping of what they asked. `git push` reports what it sent and the new remote state.

**Make current state easy to see.** If the tool manages state that isn't visible on the filesystem, provide a `status`-like view. `git status` shows state plus hints for changing it.

**Suggest next commands.** In multi-step workflows, print what to run next ("(use "git add <file>..." to update what will be committed)"). It teaches the tool.

**Crossing the program's boundary should be explicit.** Reading/writing files the user didn't pass (other than internal state like caches) and talking to remote servers should be visible or opt-in, not surprising.

**Density via structure.** Compact, scannable layouts like `ls -l` permissions let beginners ignore detail and experts read it at a glance.

**Color with intention.** Highlight what matters, red for errors. If everything is colored, nothing is. Disable color when:
- stdout or stderr isn't a TTY — check each separately; colored stderr is still useful when stdout is piped
- `NO_COLOR` is set and non-empty (any value)
- `TERM=dumb`
- `--no-color` is passed
- optionally an app-specific `MYAPP_NO_COLOR`
`FORCE_COLOR` may force color on regardless of detection. (See no-color.org.)

**No animations when not a TTY.** Otherwise progress bars become pages of garbage in CI logs.

**Symbols and emoji where they clarify** — to separate kinds of lines or draw attention (✅ done, ❌ critical warning). Easy to overdo; too many makes the tool look cluttered or toy-like.

**No developer-only output by default.** Internal details belong in `--verbose`/`--debug`. Ask newcomers to try the tool; they'll spot noise you can't see.

**stderr isn't a log file by default.** No `ERR`/`WARN` level labels, timestamps, or module names unless verbose.

**Pager for lots of text** (like `git diff`), only when stdout is a TTY (and stdin, for interactive control). Good default: `less -FIRX` — doesn't page if it fits one screen, case-insensitive search, passes color, leaves output on screen after quitting. Honor `$PAGER`. Libraries (e.g. pypager) can be more robust than spawning `less` yourself.

## Errors

The most common reason people read docs is to fix an error. Make errors the documentation.

**Catch expected errors and rewrite them for humans.** Treat it as a conversation guiding the user back on track:
> Can't write to file.txt. You might need to make it writable by running `chmod +w file.txt`.

Good error = what happened + why (if known) + what to do next. Include the offending value (path, flag, ID).

**Signal-to-noise matters.** Every irrelevant line delays the fix. Group many errors of the same type under one explanatory header instead of 50 near-identical lines.

**Put the most important information last**, where the eye lands when the output stops. Use red sparingly and deliberately.

**Unexpected errors**: provide debug info and a traceback, plus how to file a bug — but don't overwhelm. Consider writing the full debug log to a file and printing its path.

**Make bug reports effortless**: e.g. print a URL that pre-fills version, OS, and the error.

Exit with a non-zero code on every error path, after the message has been written to stderr.

Further reading: Google "Writing Helpful Error Messages"; Nielsen Norman Group "Error-Message Guidelines".
