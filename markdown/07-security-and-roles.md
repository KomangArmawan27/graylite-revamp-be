# 07. Security, auth and roles

## Role model [confirmed unless tagged]

- A role is a name from `System.[User.Level].user_group` (about 25: Director, Finance, General, HRD, Marketing, Marketing Manager, Accounting, Accounting Manager, Purchasing, Purchasing Manager, Warehouse, Warehouse2, Depo, Opname, Invoicing, Stock, E-COmmerce, Marketing Retail, Admin Brand, and others).
- A user's roles are the comma-separated names in `User.Management.user_level` (one for most users, up to 19 for others).
- A **role list** is a comma-separated string of exact role names, or `All`. It appears in three places:

| Where | Meaning |
|---|---|
| `Form.Headers.hdr_level` | **Visible**: who may see and open the screen |
| `Form.Headers.doc_header` on a **browser** | **Add/Remove**: who gets the Add and Remove buttons |
| `Form.Commands.cmd_privilege` | Who sees the toolbar command |

### Matching rule (`app/shared/roles.py`)

```python
def allowed(role_list: str | None, user_roles: list[str]) -> bool:
    """Exact-name match. 'All' allows everyone. Empty or None means denied."""
    if not role_list or not role_list.strip():
        return False
    wanted = {t.strip().casefold() for t in role_list.split(",") if t.strip()}
    if "all" in wanted:
        return True
    have = {r.strip().casefold() for r in user_roles}
    return bool(wanted & have)
```

Rules:

1. **Exact names only. Never substring matching.** `Accounting` is a substring of `Accounting Manager`, `Marketing` of `Marketing Manager`, `Warehouse` of `Warehouse2`. The old front end uses `.search()` in places and may match substrings; do **not** copy that until it is verified and decided.
2. Trim spaces and compare case-insensitively.
3. **Empty or null means denied** (fail closed) until the old app's meaning is confirmed **[unknown]**. 151 browsers have a null `doc_header` and 184 commands have a null `cmd_privilege`.
4. `None` (an option in the portal) is never used in data and means denied if it appears.
5. `Acc_Mgr` (11 uses) is not in the role list and is probably a legacy alias of `Accounting Manager`. Do not map it silently; the linter flags it.
6. `General` is just a role. A user without it does not get it automatically (the user "Tax" has no `General`).

### Where roles are enforced

Every endpoint, on the server:

- Screen **Visible** (`hdr_level`): meta, rows, read, save, delete, pickers used by that screen, and commands.
- Browser **Add/Remove** (`doc_header`): `canAdd`/`canRemove` in meta, and `POST` (create) and `DELETE` rejection with 403.
- **Command privilege** (`cmd_privilege`): which commands are listed and which may be run (`/v1/commands/{id}/run` re-checks).
- Menu: only entries whose target screen is Visible.

## Session values

Built at login from the user row and signed into the token. The client can never supply them.

| Name | Source |
|---|---|
| `_USERID` | `user_id` |
| `_USERLOGIN` | `user_login` |
| `_USERLEVEL` | the role list as a string (kept for compatibility) |
| `_CCID` | `cc_id` (cost center); whether it scopes data is **[unknown]** |
| other `_*` | defined by the server only (`div_id`, `ware_id`, `branch_id`) |

## Login flow (`app/modules/auth`)

1. Find the user by `user_login` (case-insensitive). Constant-time failure path: do not reveal whether the login or the password was wrong.
2. Reject if `is_active` is not 1.
3. Verify the password (see below).
4. If `is_login1device` is 1: create a new session id, store it in `login_session`, and reject older tokens that carry a different `sid`. **[likely behavior; verify]**
5. Update `user_lastlogin`. Update `user_lastactive` at most once a minute.
6. Return a short-lived access token (30 min) and a refresh token (14 days).
7. Check whether the old app enforces a password expiry using `user_passlastupdate` **[unknown]**.

**Rate limiting:** per login name and per IP (for example 5 failures in 10 minutes, then a lockout window), with an audit log line per failure.

**Tokens:** JWT signed **RS256** (private key signs, any service verifies with the public key). Claims: `sub`, `login`, `roles`, `ccId`, `divId`, `wareId`, `sid`, `exp`. Refresh tokens are single-use and rotated.

## Password hashes

`user_password` is a 20-byte value that looks like unsalted **SHA-1**. The exact method (plain `HASHBYTES('SHA1', password)`, a prefix, a salt, a different input encoding) is **[unknown]**. Find the old login code (stored procedure or PHP) before implementing verification. Do not guess.

Migration plan, so the old and new apps keep working side by side:

1. Keep the old column untouched.
2. Add a new place for a strong hash (a new column or a new table; a schema addition must be approved by the owner): **argon2id**.
3. On each successful login against the old hash, compute and store the argon2id hash. Prefer the new hash when it exists.
4. Retire the old hash only when the old app is gone.

**Never** log, return or echo `user_password`, `old_password`, `new_password`, `token_no` or `login_session`.

## SQL safety rules (non-negotiable)

1. Values are always bound parameters. The param engine is the only place that turns `::Name::` into `?`.
2. SQL text comes only from config rows or from code in `repository.py`. No endpoint accepts SQL from a client.
3. Identifiers (tables, columns) are accepted only if they exist in the catalog or config, then quoted with `[ ]`.
4. **Two database logins** (settings in `docs/09`):
   - **Read-only** (`DB_USER`) for meta, browser rows, pickers, reads and combo queries: `SELECT` and `VIEW DEFINITION` only.
   - **Read-write** (`DB_WRITE_USER`) only for the save engine and the command runner: `INSERT`, `UPDATE`, `DELETE` on base tables and `EXECUTE` on command procedures.

   The old project used one login with explicit table grants (`sql/001_permissions.sql`). If `DB_WRITE_USER` is empty the API falls back to the default login, which is acceptable only in development. Production splits them.

   The audit found no `INSERT`/`UPDATE`/`DELETE`/`EXEC`/`DROP` in any `hdr_expr`, so data endpoints work with the read-only login.

   The generic engine can write to any `hdr_basetable` (179 forms, 152 grids), so per-table grants by hand do not scale. Use `scripts/gen_grants.py` to generate a reviewed `sql/002_generated_grants.sql` from the config (base tables and command procedures) and run it manually. The API never runs `GRANT` or any DDL.
5. Commands (`cmd_controlexpr`) are the only config text allowed to `EXEC`. They run on the read-write login, with only the whitelisted variables bound, after the role check and confirmation rules.
6. Never execute text returned by a procedure (`docs/04` section 5).
7. Query timeout (`QUERY_TIMEOUT_SEC`) and row cap (`ROW_CAP`) on every config query.
8. `ENABLE_WRITES` defaults to false: saves, deletes and writing commands are rejected unless it is explicitly turned on (staging only until `docs/08` Q16 is settled).
9. Test rows in config (for example `select 'alert(1)'`) are treated like any other command output: parsed, whitelisted, dropped if unknown.

## Other hardening

- CORS: explicit origins from `.env` (the Flutter mobile app needs none; Flutter Web does).
- HTTPS only in production; `Strict-Transport-Security` header.
- Validate and limit request body size (for example 2 MB; larger for file fields later).
- Return generic errors to clients; keep SQL error text and stack traces in the server log, tagged with the request id.
- Audit log: who ran which save, which command and which screen, with the record id (not field values).
- Secrets only in `.env` or the platform secret store, never in git. Rotate any credential that was ever pasted into a chat or ticket.
