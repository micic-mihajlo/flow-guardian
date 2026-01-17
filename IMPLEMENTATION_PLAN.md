# Implementation Plan

> Flow Guardian — "Claude forgets. Flow Guardian remembers."

**Last Updated:** 2026-01-17
**Status:** 🚧 **Phase 2: Seamless Context System**

---

## Current State Summary

| File | Status | Lines of Code |
|------|--------|---------------|
| `flow.py` | ✅ **Fully Implemented** | 622 |
| `capture.py` | ✅ **Fully Implemented** | 238 |
| `restore.py` | ✅ **Fully Implemented** | 378 |
| `backboard_client.py` | ✅ **Fully Implemented** | 404 |
| `setup_assistants.py` | ✅ **Fully Implemented** | 153 |
| `memory.py` | ✅ **Fully Implemented** | 388 |
| `cerebras_client.py` | ✅ **Fully Implemented** | 213 |
| `git_utils.py` | ✅ **Fully Implemented** | 55 |
| **TOTAL** | **All core modules complete** | **2,451** |

**Specifications:** 10 complete spec files in `specs/` directory
**Dependencies:** Fully specified in `requirements.txt`
**Reference implementation:** `backboard_client.py` code provided in `docs/HACKATHON_PLAN.md` (lines 154-318)

**Phase 1 (MVP) complete. Now implementing Phase 2: Seamless Context System.**

---

## Phase 2: Seamless Context System (CURRENT)

> Automatic context injection. When you open Claude Code, it just knows.

### P0: Handoff System

- [ ] Create `handoff.py` module
  - [ ] `find_project_root(cwd)` — find project root via .flow-guardian/, .git/, pyproject.toml
  - [ ] `get_handoff_path(project_root)` — path to `.flow-guardian/handoff.yaml`
  - [ ] `load_handoff(project_root)` — load YAML, return None if missing
  - [ ] `save_handoff(data, project_root)` — save with validation
  - [ ] `update_handoff(updates, project_root)` — merge updates
- [ ] Update `flow save` to write handoff.yaml
- [ ] Update daemon to update handoff.yaml on extraction
- Spec: `specs/11_HANDOFF_SYSTEM.md`

### P0: TLDR System

- [ ] Create `tldr.py` module
  - [ ] `summarize_context(content, level, max_tokens)` — Cerebras summarization
  - [ ] `summarize_handoff(handoff, level)` — handoff to TLDR string
  - [ ] `summarize_recall(results, level)` — recall results to TLDR
  - [ ] `estimate_tokens(text)` — rough token count
- [ ] Implement levels: L0 (paths), L1 (descriptions), L2 (logic), L3 (full)
- [ ] Fallback when Cerebras unavailable
- Spec: `specs/12_TLDR_SYSTEM.md`

### P0: Inject Command

- [ ] Create `inject.py` module
  - [ ] `generate_injection(level, quiet)` → formatted context string
  - [ ] `save_current_state()` → save to handoff.yaml
  - [ ] `format_injection(handoff, memory, quiet)` → output string
- [ ] Add `flow inject` command to CLI
  - [ ] `--quiet/-q` — plain output for hooks
  - [ ] `--level/-l` — TLDR depth (default: L1)
  - [ ] `--save-state` — save state mode for PreCompact
- [ ] Integrate with Backboard semantic recall
- Spec: `specs/13_HOOKS_INTEGRATION.md`

### P1: Claude Code Hooks

- [ ] Create `.claude/hooks/flow-inject.sh` — SessionStart hook
- [ ] Create `.claude/hooks/flow-precompact.sh` — PreCompact hook
- [ ] Generate `.claude/settings.json` hook configuration
- Spec: `specs/13_HOOKS_INTEGRATION.md`

### P1: Setup Command

- [ ] Add `flow setup` command
  - [ ] Create `.flow-guardian/` directory
  - [ ] Create `.flow-guardian/handoff.yaml`
  - [ ] Create `.flow-guardian/config.yaml`
  - [ ] Create `.claude/hooks/` with scripts
  - [ ] Update `.claude/settings.json`
  - [ ] `--global/-g` for user-level hooks
  - [ ] `--check/-c` for status check
  - [ ] `--force/-f` to overwrite
- [ ] Verify environment (API keys)
- Spec: `specs/15_SETUP_COMMAND.md`

### P2: Semantic Recall Optimization

- [ ] Context-aware queries (project name, branch, focus)
- [ ] Result categorization (learnings, decisions, context)
- [ ] Local fallback via memory.py
- Spec: `specs/14_SEMANTIC_RECALL.md`

### P2: Testing & Polish

- [ ] Tests for handoff.py
- [ ] Tests for tldr.py
- [ ] Tests for inject.py
- [ ] Tests for setup command
- [ ] End-to-end test: save → close → reopen → context restored

---

## Stack

- **Cerebras** — Fast LLM inference (Llama 3.3 70B)
- **Backboard.io** — Persistent memory with semantic recall
- **Rich** — CLI output
- **Click** — CLI framework
- **Local JSON** — Offline fallback

---

## Priority 1: Core Infrastructure (MUST HAVE — P0) ✅ COMPLETE

### 1.1 Create `cerebras_client.py` — LLM Inference ✅
- [x] Import and configure Cerebras Cloud SDK
- [x] Implement `analyze_session_context(branch, files, diff_summary, user_message)` → returns dict with summary, hypothesis, next_steps, decisions, learnings
- [x] Implement `generate_restoration_message(context, changes)` → returns welcome-back string
- [x] Implement `complete(prompt, system, json_mode, max_tokens)` → generic completion
- [x] Define error classes: `CerebrasError`, `CerebrasAuthError`, `CerebrasRateLimitError`
- [x] Handle rate limiting with graceful fallback
- Spec: `specs/09_CEREBRAS_CLIENT.md`

### 1.2 Create `memory.py` — Local Storage Fallback ✅
- [x] Initialize storage directory `~/.flow-guardian/`
- [x] Implement `init_storage()` — create directories and index files
- [x] Implement `save_session(session)` → returns session_id
- [x] Implement `load_session(session_id)` → returns dict or None
- [x] Implement `get_latest_session()` → returns dict or None
- [x] Implement `list_sessions(limit, branch)` → returns list of session summaries
- [x] Implement `save_learning(learning)` → returns learning_id
- [x] Implement `search_learnings(query, tags)` → returns list (keyword-based fallback)
- [x] Implement `get_config()` / `set_config(key, value)`
- [x] Atomic file writes (write to temp, then rename)
- [x] Handle concurrent access, data validation, auto-create directories
- Spec: `specs/07_MEMORY_MODULE.md`

### 1.3 Implement `backboard_client.py` — Backboard.io API ✅
- [x] Configure httpx async client with connection pooling
- [x] Implement `_headers()` helper for auth
- [x] Implement `create_assistant(name, llm_provider)` → returns assistant_id
- [x] Implement `create_thread(assistant_id)` → returns thread_id
- [x] Implement `health_check()` → returns bool
- [x] Implement `store_message(thread_id, content, metadata)` with `send_to_llm=False`
- [x] Implement `store_session(thread_id, session)` — store context snapshot
- [x] Implement `store_learning(thread_id, text, tags, author)` — store learning
- [x] Implement `recall(thread_id, query)` with `memory="auto"`, `send_to_llm=True`
- [x] Implement `get_restoration_context(thread_id, changes_summary)`
- [x] Implement `store_team_learning(team_thread_id, learning, author, tags)`
- [x] Implement `query_team_memory(team_thread_id, query)`
- [x] Define error classes: `BackboardError`, `BackboardAuthError`, `BackboardConnectionError`, `BackboardRateLimitError`
- [x] Retry logic: max 3 attempts on 5xx, exponential backoff (1s, 2s, 4s), no retry on 4xx
- [x] 30-second timeout
- [x] Never log API keys
- Spec: `specs/08_BACKBOARD_CLIENT.md`
- Reference: `docs/HACKATHON_PLAN.md` lines 154-318

### 1.4 Implement `setup_assistants.py` — One-Time Setup ✅
- [x] Create personal assistant ("flow-guardian-personal")
- [x] Create personal thread
- [x] Create team assistant ("flow-guardian-team")
- [x] Create team thread
- [x] Print output for .env configuration (assistant/thread IDs)
- [x] Handle errors gracefully (API key missing, connection issues)

---

## Priority 2: Core Commands — Save & Resume (MUST HAVE — P0) ✅ COMPLETE

### 2.1 Implement `capture.py` — Context Capture ✅
- [x] `capture_git_state()` → returns branch, uncommitted files, recent commits, last commit message
- [x] `get_diff_summary()` → summarize uncommitted changes
- [x] `analyze_context(git_state, user_message)` → call Cerebras to extract structured context
- [x] Handle non-git repos gracefully
- Spec: `specs/01_SAVE_COMMAND.md`

### 2.2 Implement `restore.py` — Context Restoration ✅
- [x] `get_changes_since(checkpoint_timestamp)` → git commits, file changes since checkpoint
- [x] `calculate_time_elapsed(timestamp)` → human-readable duration
- [x] `generate_restoration_message(session, changes)` → call Cerebras for welcome-back message
- [x] `detect_conflicts(session)` → highlight if current state conflicts with checkpoint
- Spec: `specs/02_RESUME_COMMAND.md`

### 2.3 Implement `flow.py` CLI — Core Commands ✅
- [x] Set up Click CLI framework with `flow` as main command group
- [x] Add Rich console for formatted output
- [x] Load environment variables with python-dotenv
- [x] **`flow save`** command:
  - [x] Flags: `--message/-m`, `--tag/-t` (repeatable), `--quiet/-q`
  - [x] Capture git state via `capture.py`
  - [x] Analyze with Cerebras
  - [x] Store to Backboard.io (primary) with local fallback
  - [x] Display Rich confirmation panel
  - [x] Performance target: <3 seconds
  - Spec: `specs/01_SAVE_COMMAND.md`
- [x] **`flow resume`** command:
  - [x] Flags: `--session/-s`, `--pick/-p` (interactive), `--raw`, `--copy`
  - [x] Load checkpoint (latest by default, or by ID, or via picker)
  - [x] Detect changes since checkpoint
  - [x] Generate welcome-back message via Cerebras
  - [x] Display Rich "Welcome Back" panel
  - [x] Support clipboard copy (--copy)
  - [x] Performance target: <2 seconds
  - Spec: `specs/02_RESUME_COMMAND.md`

---

## Priority 3: Learning Commands (SHOULD HAVE — P1) ✅ COMPLETE

### 3.1 `flow learn` Command ✅
- [x] Accept learning text as argument: `flow learn "insight text"`
- [x] Flags: `--tag/-t` (repeatable), `--team` (share with team)
- [x] Store to Backboard.io personal thread (or team thread if --team)
- [x] Local fallback storage via memory.py
- [x] Display confirmation with learning echoed back, tags, scope (personal/team)
- [x] Performance target: <1 second
- Spec: `specs/03_LEARN_COMMAND.md`

### 3.2 `flow recall` Command ✅
- [x] Accept natural language query: `flow recall "query"`
- [x] Flags: `--tag/-t`, `--since`, `--limit` (default: 10)
- [x] Use Backboard.io semantic search with `memory="auto"`
- [x] Display results ranked by relevance with timestamps, tags, snippets
- [x] Local fallback: keyword search via memory.py
- [x] Performance target: <2 seconds
- Spec: `specs/04_RECALL_COMMAND.md`

### 3.3 `flow team` Command ✅
- [x] Search team-shared learnings: `flow team "query"`
- [x] Flags: `--tag/-t`, `--since`, `--limit`
- [x] Show author attribution for each result
- [x] Use team's Backboard.io assistant
- [x] Display team knowledge panel
- Spec: `specs/05_TEAM_COMMAND.md`

---

## Priority 4: Utility Commands (NICE TO HAVE — P2) ✅ COMPLETE

### 4.1 `flow status` Command ✅
- [x] Show current Flow Guardian state
- [x] Display: last save time, active session, branch, working context
- [x] Memory stats: sessions count, learnings count (personal/team)
- [x] Storage status (Backboard.io connected or local-only)
- Spec: `specs/06_STATUS_HISTORY_COMMANDS.md`

### 4.2 `flow history` Command ✅
- [x] Show past sessions and checkpoints
- [x] Flags: `-n <number>` (limit), `--all`, `--branch <name>`
- [x] Display: timestamp, branch, summary, session ID
- [x] Show how to resume specific sessions
- Spec: `specs/06_STATUS_HISTORY_COMMANDS.md`

---

## Priority 5: Polish & Error Handling (P2) ✅ COMPLETE

- [x] Comprehensive error handling across all modules — Custom exception hierarchies in all API clients
- [x] Graceful degradation when Backboard.io unavailable — Local fallback storage used automatically
- [x] Graceful degradation when Cerebras unavailable — Fallback messages generated in capture.py and restore.py
- [x] Beautiful Rich output panels for all commands — Color-coded panels for save, resume, learn, recall, team, status, history
- [x] Edge case handling: non-git repos, empty repos, API failures — Verified working in non-git directories
- [ ] Demo script preparation — Optional polish item
- [x] **Test infrastructure** — 139 passing tests covering all core modules

---

## Files Structure

```
flow-guardian/
├── flow.py              # ✅ CLI entry (Click + Rich) - 622 lines
├── capture.py           # ✅ Git state extraction + Cerebras analysis - 240 lines
├── restore.py           # ✅ Change detection + restoration - 380 lines
├── memory.py            # ✅ Local storage fallback - 388 lines
├── cerebras_client.py   # ✅ Cerebras LLM client - 213 lines
├── backboard_client.py  # ✅ Backboard.io API client - 404 lines
├── setup_assistants.py  # ✅ One-time Backboard.io setup - 153 lines
├── git_utils.py         # ✅ Shared git utilities - 53 lines
├── src/lib/             # Shared utilities (currently empty)
├── specs/               # Feature PRDs (10 files, complete)
├── docs/                # HACKATHON_PLAN.md with reference code
├── tests/               # ✅ Test suite - 139 passing tests
│   ├── __init__.py
│   ├── test_memory.py
│   ├── test_capture.py
│   ├── test_restore.py
│   ├── test_cerebras_client.py
│   ├── test_backboard_client.py
│   ├── test_flow_cli.py
│   ├── test_setup_assistants.py
│   └── test_git_utils.py
└── pytest.ini           # ✅ Pytest configuration
```

---

## Implementation Order (Critical Path) ✅ ALL COMPLETE

1. ✅ **`cerebras_client.py`** — Required by capture.py and restore.py
2. ✅ **`memory.py`** — Required for local fallback (always needed)
3. ✅ **`backboard_client.py`** — Required for cloud storage
4. ✅ **`capture.py`** — Depends on cerebras_client
5. ✅ **`restore.py`** — Depends on cerebras_client
6. ✅ **`flow.py` (save + resume)** — Depends on all above
7. ✅ **`setup_assistants.py`** — Depends on backboard_client
8. ✅ **`flow.py` (learn + recall + team)** — Depends on backboard_client
9. ✅ **`flow.py` (status + history)** — Depends on memory.py

---

## Hackathon MVP Priority ✅ ALL IMPLEMENTED

**MUST work for demo:**
- ✅ `flow save` — Capture context before interruption
- ✅ `flow resume` — Restore context after returning

**WOW factor for judges:**
- ✅ `flow learn --team` — Store team insight
- ✅ `flow team` — Search team knowledge

**Bonus features (also completed):**
- ✅ `flow status` — View current state and stats
- ✅ `flow history` — Browse past sessions
- ✅ `flow recall` — Search personal learnings

---

## Testing

**Test Suite:** 139 passing tests with pytest

| Module | Test File | Coverage |
|--------|-----------|----------|
| `git_utils.py` | `test_git_utils.py` | Git command execution, repo detection, branch retrieval |
| `memory.py` | `test_memory.py` | Storage, sessions, learnings, config |
| `capture.py` | `test_capture.py` | Git state capture, diff summary, context analysis |
| `restore.py` | `test_restore.py` | Change detection, restoration messages, conflicts |
| `cerebras_client.py` | `test_cerebras_client.py` | LLM inference, error handling, rate limiting |
| `backboard_client.py` | `test_backboard_client.py` | API calls, retry logic, error classes, create_assistant, create_thread |
| `flow.py` | `test_flow_cli.py` | All CLI commands (save, resume, learn, recall, team, status, history) |
| `setup_assistants.py` | `test_setup_assistants.py` | Personal and team assistant setup, error handling |

**Run tests:** `pytest` or `pytest -v` for verbose output
