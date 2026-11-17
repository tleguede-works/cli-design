# Help text and documentation

Help text gives an immediate sense of what the tool is and how to do the common things. Documentation is the full detail: what it's for, what it isn't for, and how to do everything.

## Help

**Extensive help on request.** `-h` and `--help` show help, for the top-level command and every subcommand. Ignore all other flags/args when `-h` is present, so a user can append `-h` to any half-typed command. `-h` means help and nothing else.

For git-like tools, all of these should work:
```
myapp help
myapp help subcommand
myapp subcommand --help
myapp subcommand -h
```

**Concise help by default.** If `myapp` (or `myapp sub`) needs arguments and gets none, print short help instead of an error. Skip this if the program is interactive by default (e.g. `npm init`). Concise help contains only:
- what the program does (one or two lines)
- one or two example invocations
- flag descriptions, unless there are many
- "Run `myapp --help` for more."

`jq` with no args is a good model: description, usage, a tiny example, then "For a listing of options, use jq --help."

**Lead with examples.** Users reach for examples before anything else. Put them early, especially the common complex cases; show real output if it's short. A series of examples can tell a story from simple to advanced. If there are many examples, move them to a cheat-sheet subcommand or web page instead of bloating `--help`. Integrations with other tools may deserve a full tutorial.

**Most common flags and commands first.** Lots of flags is fine; order them by use. Git groups commands by task ("start a working area", "work on the current change", ...) rather than alphabetically.

**Format for scanning.** Bold section headings (USAGE, OPTIONS, EXAMPLES, COMMANDS) help — but emit them terminal-independently, and emit no escape codes when help is piped (e.g. into a pager or file). Example layout:

```
list your apps

USAGE
  $ heroku apps

OPTIONS
  -A, --all          include apps in all teams
  -s, --space=space  filter by space
  --json             output in json format

EXAMPLES
  $ heroku apps

COMMANDS
  apps:create   creates a new app
  apps:destroy  permanently destroy an app
```

**Support path.** Put a website or issue-tracker link in top-level help.

**Link to web docs** from help, deep-linking to the subcommand's page/anchor when there is one.

**Suggest corrections.** If the input is wrong and you can guess the intent, say so: `brew update jq` → suggests `brew upgrade jq`; `heroku pss` → "Did you mean ps? [y/n]". You can offer to run the suggestion, but be wary of silently running it:
- invalid input might be a logic error or a mangled shell variable, not a typo, and guessing can be dangerous when the command modifies state;
- if you accept the wrong form, users never learn the right one, and you've committed to supporting that syntax forever. If you choose to, do it intentionally and document both.

**Don't hang waiting for piped input.** If the command expects stdin to be piped and stdin is an interactive terminal, print help (or a stderr hint like "reading from stdin… (Ctrl-D to end)") instead of sitting silently like `cat`.

## Documentation

- **Web docs**: searchable, linkable, the most inclusive format.
- **Terminal docs**: fast, offline, and match the installed version. Make them reachable from the tool itself (`myapp help <topic>`), since not everyone knows `man` and it's not on every platform. `npm help ls` ≡ `man npm-ls`.
- **Consider man pages**: many users try `man mycmd` first. Tools like ronn can generate man pages and web docs from one source. Many parser libraries (clap, Cobra, Click via extensions) can generate man pages too.
