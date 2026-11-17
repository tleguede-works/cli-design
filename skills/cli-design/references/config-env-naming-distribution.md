# Configuration, environment variables, naming, distribution, analytics

## Configuration

Choose the mechanism by how specific, stable and complex the setting is:

| Kind of setting | Examples | Use |
|---|---|---|
| Varies per invocation | debug level, dry run, safe mode | **Flags** (env vars maybe) |
| Mostly stable, varies per user/machine or project | non-default paths, color preference, HTTP proxy | **Flags + env vars** (users set them in shell profile or `.env`); a config file only if it gets complex |
| Stable within a project for everyone | build targets, service definitions (`Makefile`, `package.json`, `docker-compose.yml`) | **A command-specific, version-controlled project file** |

**Precedence (highest wins):**
1. Flags
2. Environment variables of the running shell
3. Project-level config (e.g. `.env`, `./.myapp.toml`)
4. User-level config (`~/.config/myapp/config.toml`)
5. System-wide config (`/etc/myapp/...`)

Implement this as one merge step so every setting follows the same order, and make the effective config inspectable (e.g. `myapp config show` with the source of each value) if there are many settings.

**Follow the XDG Base Directory spec.** Config in `$XDG_CONFIG_HOME/myapp/` (default `~/.config/myapp/`), cache in `$XDG_CACHE_HOME` (`~/.cache`), data in `$XDG_DATA_HOME` (`~/.local/share`), state in `$XDG_STATE_HOME` (`~/.local/state`). Don't litter `~` with dotfiles. On macOS/Windows, either use XDG anyway (common for dev tools) or the platform dirs (libraries: `platformdirs` (Python), `dirs` (Rust), `os.UserConfigDir` (Go), `env-paths` (Node)).

**Modifying another program's config requires consent.** Ask, and say exactly what you'll change. Prefer adding a new file (`/etc/cron.d/myapp`) over appending to a shared one (`/etc/crontab`). If you must edit a shared file, delimit your additions with a dated comment.

## Environment variables

**For behavior that varies with the context** (terminal session, machine, project checkout). They may duplicate flags/config or be distinct.

- **Names**: uppercase letters, digits, underscores only, not starting with a digit. Prefix with your app name (`MYAPP_TOKEN_FILE`, `MYAPP_NO_COLOR`).
- **Single-line values** — multi-line values make `env` output unusable.
- **Don't commandeer widely used names** (check the POSIX list: `PATH`, `HOME`, `USER`, `LANG`, …).
- **Honor general-purpose vars:**
  - `NO_COLOR` / `FORCE_COLOR` — disable / force color
  - `DEBUG` — more verbose output
  - `EDITOR` (and `VISUAL`) — for editing a file or multi-line input
  - `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY` — for network access (your HTTP library may already do this)
  - `SHELL` — to open the user's interactive shell (to *run a script*, use a specific interpreter like `/bin/sh`)
  - `TERM`, `TERMINFO`, `TERMCAP` — before emitting terminal-specific escape sequences
  - `TMPDIR` — for temp files
  - `HOME` — to locate config
  - `PAGER` — for paging output
  - `LINES`, `COLUMNS` — for size-dependent output like tables
- **Read `.env` where appropriate** for values tied to a working directory (dotenv libraries exist for most languages).
- **Don't use `.env` as a config file substitute.** It's usually not in version control (no history), only has strings, gets disorganized, invites encoding bugs, and often holds credentials that deserve better storage.
- **Don't read secrets from env vars.** Exported vars reach every child process and leak into logs; `curl -H "Authorization: Bearer $TOKEN"` exposes them in process listings (curl's `-H @file` avoids this); `docker inspect` and `systemctl show` reveal them. Accept secrets via credential files, pipes/stdin, `AF_UNIX` sockets, secret managers, or other IPC.

## Naming the command

- **A simple, memorable word**, not so generic it collides (ImageMagick and Windows both shipped `convert`).
- **Lowercase, dashes only if necessary.** `curl` yes, `DownloadURL` no.
- **Short, but not too short** — 2-letter names belong to ubiquitous utilities (`cd`, `ls`, `ps`).
- **Easy to type.** Docker Compose was first `plum` — an awkward one-handed hop — then `fig`, which flows. Say it and type it a few times before committing.

Further reading: "The Poetics of CLI Command Names" (Smallstep).

## Distribution

- **Ship a single binary if possible.** For interpreted languages consider PyInstaller, Nuitka, `deno compile`, Node SEA/pkg, etc. Otherwise use the platform's native package manager (Homebrew, apt, winget, …) so nothing is scattered on disk unremovably. Tread lightly on the user's machine.
- Exception: language-specific tools (a linter for language X) can assume that language's runtime and package manager (`pipx`, `npm -g`, `cargo install`).
- **Easy to uninstall**, with instructions right below install instructions — people often want to uninstall right after installing.

## Analytics / telemetry

CLI users expect to control their environment; background network activity is a surprise.

- **No usage or crash reporting without consent.** Users will find out and be angry. Document what's collected, why, how it's anonymized, and retention.
- **Prefer opt-in.** If opt-out, announce it clearly on first run and on the website, and make it trivial to disable (a config setting plus an env var such as `MYAPP_TELEMETRY=0`; also respect `DO_NOT_TRACK=1`, a common convention).
- Telemetry must never block or slow the command, and must fail silently offline.
- Examples: Angular (opt-in, detailed), Homebrew (documented FAQ), Next.js (opt-out, documented).

**Alternatives to analytics:** instrument your web docs (what people read and search for), instrument downloads (rough usage and OS mix), and talk to users — ask in docs and repos for feedback and draw out context.
