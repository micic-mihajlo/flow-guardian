# Flow Guardian - Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** January 16, 2026  
**Hackathon:** 8090 x Highline Beta: Build for Builders  
**Authors:** [Team Names]

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Vision](#3-product-vision)
4. [User Personas](#4-user-personas)
5. [User Stories](#5-user-stories)
6. [Functional Requirements](#6-functional-requirements)
7. [Technical Architecture](#7-technical-architecture)
8. [API Specifications](#8-api-specifications)
9. [Complete Setup Guide](#9-complete-setup-guide)
10. [Environment Configuration](#10-environment-configuration)
11. [Testing Procedures](#11-testing-procedures)
12. [Troubleshooting Guide](#12-troubleshooting-guide)
13. [Implementation Timeline](#13-implementation-timeline)
14. [Success Metrics](#14-success-metrics)
15. [Future Roadmap](#15-future-roadmap)

---

## 1. Executive Summary

### What is Flow Guardian?

Flow Guardian is a CLI tool that captures developer context before interruptions and restores it instantly when they return. It solves the "23 minutes to regain focus" problem by using fast LLM inference (Cerebras) combined with persistent semantic memory (Backboard.io).

### Key Value Proposition

- **Before:** Developer returns from meeting, spends 20+ minutes asking "what was I doing?"
- **After:** Developer runs `flow resume`, gets instant context restoration in <2 seconds

### Core Commands

| Command | Purpose |
|---------|---------|
| `flow init` | Set up Flow Guardian for a project |
| `flow capture` | Save current context before interruption |
| `flow resume` | Restore context after returning |
| `flow learn` | Store a personal learning/insight |
| `flow team` | Search team's shared knowledge |
| `flow status` | View current state |

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Inference | Cerebras Cloud (Llama 3.3 70B) | Fast context analysis (<1 sec) |
| Memory Layer | Backboard.io | Persistent semantic memory with auto-RAG |
| CLI Framework | Python + Typer + Rich | Beautiful terminal interface |
| Version Control | GitPython | Git state extraction |

---

## 2. Problem Statement

### The Context Switching Crisis

**Research Data:**
- 23 minutes to regain focus after an interruption (UC Irvine)
- 69% of developers lose 8+ hours/week to inefficiencies (Stack Overflow 2024)
- 62% cite context switching as their #1 frustration
- Average developer experiences 3-4 interruptions per day
- Cost: ~$6.9M/year for a 500-developer company

### The Pain Sequence

```
1. Developer is deep in flow state
   └── Holding 5 things in working memory
   └── Has a hypothesis about a bug
   └── Knows exactly what to try next

2. Interruption occurs
   └── Meeting / Slack ping / colleague question

3. Developer returns (30-60 mins later)
   └── "What file was I in?"
   └── "What was my theory?"
   └── "What did I try already?"
   └── Spends 20+ mins rebuilding context

4. Repeat 3-4x per day
   └── 60-90 minutes lost daily per developer
```

### Why Existing Tools Don't Solve This

| Tool | Limitation |
|------|------------|
| Note-taking apps | Manual effort, breaks flow |
| Git history | Shows what changed, not what you were thinking |
| IDE session restore | Opens files, but no cognitive context |
| AI assistants | No memory between sessions |

---

## 3. Product Vision

### Mission Statement

"Return developers to flow state in 30 seconds, not 23 minutes."

### Core Principles

1. **Zero-friction capture** — One command, <1 second
2. **Intelligent restoration** — Not just files, but context + changes
3. **Team knowledge compounding** — Learnings shared, not siloed
4. **CLI-first** — Developers live in terminals

### Success Vision

A developer runs `flow capture` before every interruption as naturally as `git commit`. When they return, `flow resume` becomes the first command they run—and they're productive in under a minute instead of 20+.

---

## 4. User Personas

### Primary: The Focused Developer

**Name:** Alex  
**Role:** Senior Backend Engineer  
**Context:** Works on complex distributed systems, often debugging issues that require holding multiple components in mind.

**Pain Points:**
- Gets pulled into meetings 3-4x daily
- Loses debugging context constantly
- Wastes time re-reading code to remember what they were doing
- Team members repeatedly ask the same questions

**Goals:**
- Minimize context rebuild time
- Share knowledge efficiently with team
- Stay in flow longer

### Secondary: The New Team Member

**Name:** Jordan  
**Role:** Junior Developer (3 months at company)  
**Context:** Still learning the codebase, frequently needs to ask questions.

**Pain Points:**
- Doesn't know who to ask about specific systems
- Repeats questions others have asked before
- Takes weeks to become productive on new areas

**Goals:**
- Find answers without interrupting senior devs
- Build knowledge faster
- Contribute to team knowledge base

---

## 5. User Stories

### Epic 1: Context Capture

| ID | User Story | Priority | Acceptance Criteria |
|----|------------|----------|---------------------|
| US-1.1 | As a developer, I want to capture my current context with one command so that I can quickly save my state before an interruption | P0 | `flow capture` completes in <2 seconds, stores context to Backboard |
| US-1.2 | As a developer, I want to specify why I'm being interrupted so that I have better context later | P1 | `flow capture -t meeting` stores trigger type |
| US-1.3 | As a developer, I want automatic git state capture so that I don't have to describe what I'm working on | P0 | Branch, modified files, recent commits captured automatically |

### Epic 2: Context Restoration

| ID | User Story | Priority | Acceptance Criteria |
|----|------------|----------|---------------------|
| US-2.1 | As a developer, I want to restore my context with one command so that I can immediately continue working | P0 | `flow resume` shows context panel in <2 seconds |
| US-2.2 | As a developer, I want to see what changed while I was away so that I don't miss important updates | P0 | Shows git changes since capture |
| US-2.3 | As a developer, I want a suggested next action so that I know exactly what to do first | P1 | AI generates recommended next step |

### Epic 3: Learning System

| ID | User Story | Priority | Acceptance Criteria |
|----|------------|----------|---------------------|
| US-3.1 | As a developer, I want to save learnings for personal recall so that I don't forget solutions | P1 | `flow learn "insight"` stores to personal memory |
| US-3.2 | As a developer, I want to share learnings with my team so that others benefit from my discoveries | P1 | `flow learn "insight" --team` stores to team memory |
| US-3.3 | As a developer, I want to search team knowledge so that I can find answers without asking | P1 | `flow team "query"` returns relevant learnings |

### Epic 4: Setup & Configuration

| ID | User Story | Priority | Acceptance Criteria |
|----|------------|----------|---------------------|
| US-4.1 | As a developer, I want easy initialization so that I can start using Flow Guardian quickly | P0 | `flow init` sets up everything with prompts |
| US-4.2 | As a developer, I want to see my current status so that I know if Flow Guardian is working | P2 | `flow status` shows config and last capture |

---

## 6. Functional Requirements

### FR-1: Context Capture System

**FR-1.1: Git State Extraction**
- Extract current branch name
- List modified files (staged and unstaged)
- Get last 5 commit messages
- Generate diff summary (truncated to 2000 chars)
- Capture HEAD commit SHA for change detection

**FR-1.2: Context Analysis**
- Send git state to Cerebras Llama 3.3 70B
- Generate structured JSON output:
  - `summary`: One sentence description of current work
  - `hypothesis`: Current theory/approach (nullable)
  - `next_steps`: List of likely next actions
  - `complexity`: simple | medium | complex
  - `key_files`: Most important files being worked on
- Complete analysis in <1 second

**FR-1.3: Memory Storage**
- Store captured context to Backboard.io personal assistant
- Include metadata: timestamp, trigger, branch, files
- Use `send_to_llm=False` for storage-only operations

### FR-2: Context Restoration System

**FR-2.1: Change Detection**
- Compare current git HEAD to captured HEAD
- List commits made since capture
- Identify if key files were modified by others

**FR-2.2: Context Recall**
- Query Backboard.io with `memory="auto"` for semantic recall
- Retrieve most recent context snapshot
- Combine with change detection results

**FR-2.3: Restoration Generation**
- Generate "welcome back" message via Cerebras
- Include: context summary, hypothesis, changes impact, suggested action
- Format as Rich panel in terminal

### FR-3: Learning System

**FR-3.1: Personal Learnings**
- Store text learnings with optional tags
- Enable semantic search via Backboard.io
- Learnings isolated to personal assistant

**FR-3.2: Team Learnings**
- Store learnings to shared team assistant
- Include author attribution
- Enable team-wide semantic search

### FR-4: Local State Management

**FR-4.1: Configuration Persistence**
- Store assistant IDs, thread IDs, username in `.flowguardian/config.json`
- Auto-create directory in project root (near `.git`)

**FR-4.2: Capture Persistence**
- Store last capture details in `.flowguardian/last_capture.json`
- Include timestamp, branch, files, summary, git HEAD SHA

---

## 7. Technical Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                FLOW GUARDIAN                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│    ┌──────────────────────────────────────────────────────────────────────────┐ │
│    │                           CLI LAYER (Typer)                               │ │
│    │  flow init | flow capture | flow resume | flow learn | flow team | status │ │
│    └────────────────────────────────┬─────────────────────────────────────────┘ │
│                                     │                                            │
│    ┌────────────────────────────────┼────────────────────────────────────────┐  │
│    │                                ▼                                         │  │
│    │  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │  │
│    │  │   Git       │    │    Cerebras     │    │     Backboard.io        │  │  │
│    │  │   Utils     │───▶│    Client       │───▶│     Client              │  │  │
│    │  │             │    │                 │    │                         │  │  │
│    │  │ • Branch    │    │ • Llama 3.3 70B │    │ • Personal Assistant    │  │  │
│    │  │ • Diff      │    │ • <1s inference │    │ • Team Assistant        │  │  │
│    │  │ • Commits   │    │ • JSON mode     │    │ • memory="auto" recall  │  │  │
│    │  │ • Changes   │    │                 │    │ • Semantic search       │  │  │
│    │  └─────────────┘    └─────────────────┘    └─────────────────────────┘  │  │
│    │                                                                          │  │
│    │                        CORE SERVICES LAYER                               │  │
│    └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│    ┌──────────────────────────────────────────────────────────────────────────┐ │
│    │                           LOCAL STATE                                     │ │
│    │                                                                           │ │
│    │    .flowguardian/                                                         │ │
│    │    ├── config.json        (assistant IDs, thread IDs, username)          │ │
│    │    └── last_capture.json  (timestamp, branch, summary, git HEAD)         │ │
│    │                                                                           │ │
│    └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│    ┌──────────────────────────────────────────────────────────────────────────┐ │
│    │                           UI LAYER (Rich)                                 │ │
│    │                                                                           │ │
│    │    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │ │
│    │    │ Capture Panel   │  │ Restore Panel   │  │ Team Panel      │        │ │
│    │    │ ✓ Context saved │  │ 🔄 Welcome back │  │ 💡 Team insight │        │ │
│    │    └─────────────────┘  └─────────────────┘  └─────────────────┘        │ │
│    │                                                                           │ │
│    └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Capture

```
User runs: flow capture -t meeting
              │
              ▼
┌─────────────────────────┐
│ 1. Extract Git State    │
│    • git.Repo()         │
│    • branch, diff, HEAD │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. Analyze with Cerebras│
│    • Llama 3.3 70B      │
│    • JSON response      │
│    • <1 second          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. Store to Backboard   │
│    • POST /messages     │
│    • send_to_llm=False  │
│    • metadata included  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. Save Local State     │
│    • last_capture.json  │
│    • timestamp, HEAD    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 5. Display Rich Panel   │
│    • ✓ Context Captured │
│    • Summary shown      │
└─────────────────────────┘
```

### Data Flow: Resume

```
User runs: flow resume
              │
              ▼
┌─────────────────────────┐
│ 1. Load Last Capture    │
│    • last_capture.json  │
│    • Get stored HEAD    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. Detect Git Changes   │
│    • Compare HEADs      │
│    • List new commits   │
│    • Check key files    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. Recall from Backboard│
│    • POST /messages     │
│    • memory="auto"      │
│    • Semantic retrieval │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. Generate Restoration │
│    • Cerebras Llama 3.3 │
│    • Context + changes  │
│    • Suggested action   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 5. Display Rich Panel   │
│    • 🔄 Flow Restored   │
│    • Changes highlighted│
│    • Next step shown    │
└─────────────────────────┘
```

---

## 8. API Specifications

### 8.1 Cerebras Cloud API

**Base URL:** `https://api.cerebras.ai/v1`

**Authentication:**
```
Authorization: Bearer {CEREBRAS_API_KEY}
```

**Chat Completions Endpoint:**
```
POST /chat/completions
```

**Request Body (Capture Analysis):**
```json
{
  "model": "llama-3.3-70b",
  "messages": [
    {
      "role": "user",
      "content": "Analyze this developer's current working context..."
    }
  ],
  "response_format": {
    "type": "json_object"
  },
  "max_tokens": 500,
  "temperature": 0.3
}
```

**Response:**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1705420800,
  "model": "llama-3.3-70b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"summary\": \"Debugging JWT token expiry...\", ...}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 450,
    "completion_tokens": 120,
    "total_tokens": 570
  }
}
```

**Rate Limits:**
- Default: 30 requests/minute
- With hackathon increase: 100+ requests/minute
- Request increase form: https://form.typeform.com/to/IpWtfYd1

### 8.2 Backboard.io API

**Base URL:** `https://app.backboard.io/api`

**Authentication:**
```
Authorization: Bearer {BACKBOARD_API_KEY}
Content-Type: application/json
```

#### Create Assistant

```
POST /assistants
```

**Request:**
```json
{
  "name": "flow-guardian-personal-raz",
  "llm_provider": "cerebras",
  "llm_model_name": "llama-3.3-70b",
  "tools": []
}
```

**Response:**
```json
{
  "id": "asst_abc123",
  "name": "flow-guardian-personal-raz",
  "created_at": "2026-01-16T17:00:00Z"
}
```

#### Create Thread

```
POST /assistants/{assistant_id}/threads
```

**Response:**
```json
{
  "id": "thread_xyz789",
  "assistant_id": "asst_abc123",
  "created_at": "2026-01-16T17:00:00Z"
}
```

#### Store Message (No LLM)

```
POST /threads/{thread_id}/messages
```

**Request:**
```json
{
  "content": "## Context Snapshot\n**Working on:** Debugging JWT...",
  "metadata": {
    "type": "context_snapshot",
    "timestamp": "2026-01-16T17:30:00Z",
    "trigger": "meeting",
    "branch": "fix/jwt-expiry",
    "files": ["src/auth.py", "tests/test_auth.py"]
  },
  "send_to_llm": false
}
```

#### Recall with Memory

```
POST /threads/{thread_id}/messages
```

**Request:**
```json
{
  "content": "What was I working on in my last context snapshot?",
  "memory": "auto",
  "send_to_llm": true
}
```

**Response:**
```json
{
  "id": "msg_def456",
  "content": "Based on your last context snapshot, you were debugging...",
  "created_at": "2026-01-16T18:00:00Z"
}
```

---

## 9. Complete Setup Guide

### Prerequisites

- Python 3.11 or higher
- Git installed and configured
- Terminal access
- Internet connection

### Step 1: Get API Keys

#### Cerebras API Key

1. Go to https://cloud.cerebras.ai
2. Sign up / Log in
3. Navigate to API Keys section
4. Click "Create new API key"
5. Copy the key (starts with `csk-...`)
6. **Important:** Fill out rate limit increase form for hackathon: https://form.typeform.com/to/IpWtfYd1

#### Backboard.io API Key

1. Go to https://backboard.io/hackathons/
2. Use promo code: `8090JAN`
3. Sign up / Log in
4. Navigate to Settings → API Keys
5. Create new API key
6. Copy the key

### Step 2: Create Project Directory

```bash
# Create project directory
mkdir flow-guardian
cd flow-guardian

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
cerebras-cloud-sdk>=1.0.0
httpx>=0.25.0
rich>=13.0.0
typer>=0.9.0
gitpython>=3.1.0
python-dotenv>=1.0.0
pydantic>=2.0.0
EOF

# Install
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Create .env file
cat > .env << 'EOF'
CEREBRAS_API_KEY=your-cerebras-key-here
BACKBOARD_API_KEY=your-backboard-key-here
BACKBOARD_BASE_URL=https://app.backboard.io/api
EOF

# Create .env.example (for git)
cat > .env.example << 'EOF'
CEREBRAS_API_KEY=csk-xxx
BACKBOARD_API_KEY=bb-xxx
BACKBOARD_BASE_URL=https://app.backboard.io/api
EOF

# Add .env to .gitignore
echo ".env" >> .gitignore
echo ".flowguardian/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "venv/" >> .gitignore
```

### Step 5: Create Project Structure

```bash
# Create directories
mkdir -p flow scripts

# Create __init__.py
touch flow/__init__.py
```

### Step 6: Implement Core Files

Create each file as specified in the Technical Architecture section. Start with:

1. `flow/state.py` - Local state management
2. `flow/cerebras_client.py` - Cerebras integration
3. `flow/backboard_client.py` - Backboard integration
4. `flow/git_utils.py` - Git operations
5. `flow/ui.py` - Rich terminal UI
6. `flow/capture.py` - Capture logic
7. `flow/restore.py` - Restore logic
8. `flow/cli.py` - CLI commands

### Step 7: Create Entry Point

```bash
# Create main entry point
cat > flow.py << 'EOF'
#!/usr/bin/env python
"""Flow Guardian - Return to flow state in 30 seconds."""
from dotenv import load_dotenv
load_dotenv()

from flow.cli import app

if __name__ == "__main__":
    app()
EOF

# Make executable
chmod +x flow.py
```

### Step 8: Initialize Git (for testing)

```bash
# Initialize git repo (needed for flow to work)
git init
git add .
git commit -m "Initial commit: Flow Guardian setup"

# Create a test branch
git checkout -b feature/test-flow
```

### Step 9: Run Initialization

```bash
# Initialize Flow Guardian
python flow.py init --user "your-username"

# You should see:
# Setting up Flow Guardian...
# ✓ Personal memory initialized
# Ready! Use 'flow capture' before interruptions.
```

---

## 10. Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CEREBRAS_API_KEY` | Cerebras Cloud API key | `csk-abc123...` |
| `BACKBOARD_API_KEY` | Backboard.io API key | `bb-xyz789...` |
| `BACKBOARD_BASE_URL` | Backboard API base URL | `https://app.backboard.io/api` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLOW_DEBUG` | Enable debug logging | `false` |
| `FLOW_TIMEOUT` | API timeout in seconds | `30` |

### Local Configuration Files

#### `.flowguardian/config.json`

```json
{
  "personal_assistant_id": "asst_abc123",
  "personal_thread_id": "thread_xyz789",
  "team_assistant_id": "asst_team456",
  "team_thread_id": "thread_team012",
  "username": "raz"
}
```

#### `.flowguardian/last_capture.json`

```json
{
  "timestamp": "2026-01-16T17:30:00Z",
  "branch": "fix/jwt-expiry",
  "files": ["src/auth.py", "tests/test_auth.py"],
  "summary": "Debugging JWT token expiry check",
  "git_head": "a1b2c3d4e5f6789..."
}
```

---

## 11. Testing Procedures

### Test 1: API Connectivity

#### Test Cerebras Connection

```python
# test_cerebras.py
import os
from dotenv import load_dotenv
load_dotenv()

from cerebras.cloud.sdk import Cerebras

def test_cerebras():
    client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))
    
    response = client.chat.completions.create(
        model="llama-3.3-70b",
        messages=[{"role": "user", "content": "Say 'Flow Guardian connected!' in 5 words or less"}],
        max_tokens=20
    )
    
    print("✓ Cerebras connected!")
    print(f"  Response: {response.choices[0].message.content}")

if __name__ == "__main__":
    test_cerebras()
```

Run:
```bash
python test_cerebras.py
# Expected: ✓ Cerebras connected!
```

#### Test Backboard Connection

```python
# test_backboard.py
import os
import httpx
from dotenv import load_dotenv
load_dotenv()

def test_backboard():
    base_url = os.environ.get("BACKBOARD_BASE_URL", "https://app.backboard.io/api")
    api_key = os.environ.get("BACKBOARD_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try to list assistants (should work even if empty)
    response = httpx.get(f"{base_url}/assistants", headers=headers)
    
    if response.status_code == 200:
        print("✓ Backboard connected!")
        assistants = response.json()
        print(f"  Found {len(assistants)} existing assistants")
    else:
        print(f"✗ Backboard connection failed: {response.status_code}")
        print(f"  Response: {response.text}")

if __name__ == "__main__":
    test_backboard()
```

Run:
```bash
python test_backboard.py
# Expected: ✓ Backboard connected!
```

### Test 2: End-to-End Flow

#### Test Capture

```bash
# Make sure you're in a git repository with some changes
echo "test change" >> test_file.txt
git add test_file.txt

# Run capture
python flow.py capture -t testing

# Expected output:
# ┌─────────────────────────────────────────────┐
# │          ✓ Context Captured                 │
# ├─────────────────────────────────────────────┤
# │ Working on   Adding test changes            │
# │ Key files    test_file.txt                  │
# │ Complexity   simple                         │
# │ Trigger      testing                        │
# └─────────────────────────────────────────────┘
```

#### Test Resume

```bash
# Simulate being away (make a commit)
git commit -m "Test commit while away"

# Run resume
python flow.py resume

# Expected output:
# ┌─────────────────────────────────────────────┐
# │          🔄 Flow Restored                   │
# ├─────────────────────────────────────────────┤
# │ You were     Adding test changes            │
# │ Changes      1 new commit since capture     │
# │ → Next step  Review the test commit         │
# └─────────────────────────────────────────────┘
```

### Test 3: Learning System

```bash
# Store a personal learning
python flow.py learn "Always use UTC for timestamps"

# Expected: ✓ Saved: Always use UTC for timestamps...

# Store a team learning (if team configured)
python flow.py learn "JWT tokens expire in UTC, not local time" --team --tags auth jwt

# Expected: ✓ Shared with team: JWT tokens expire...

# Recall personal learning
python flow.py recall "timestamps"

# Expected: Returns relevant learning about UTC timestamps

# Query team memory
python flow.py team "authentication timezone"

# Expected: Returns JWT insight with author attribution
```

### Test 4: Status Check

```bash
python flow.py status

# Expected output:
# ┌─────────────────────────────────────────────┐
# │          Flow Guardian Status               │
# ├─────────────────────────────────────────────┤
# │ User             raz                        │
# │ Personal memory  ✓ Connected                │
# │ Team memory      ✓ Connected                │
# │                                             │
# │ Last capture     2026-01-16T17:30:00        │
# │ Branch           fix/jwt-expiry             │
# │ Summary          Debugging JWT token...     │
# └─────────────────────────────────────────────┘
```

### Test 5: Performance Benchmarks

```bash
# Time the capture command
time python flow.py capture -t benchmark

# Target: < 2 seconds total
# - Git extraction: < 100ms
# - Cerebras analysis: < 800ms
# - Backboard storage: < 500ms
# - UI rendering: < 100ms

# Time the resume command
time python flow.py resume

# Target: < 3 seconds total
```

### Automated Test Script

```bash
# test_all.sh
#!/bin/bash
set -e

echo "=== Flow Guardian Test Suite ==="
echo ""

echo "1. Testing Cerebras connection..."
python test_cerebras.py

echo ""
echo "2. Testing Backboard connection..."
python test_backboard.py

echo ""
echo "3. Testing status command..."
python flow.py status

echo ""
echo "4. Testing capture..."
echo "test" >> .flowguardian_test
git add .flowguardian_test 2>/dev/null || true
python flow.py capture -t test

echo ""
echo "5. Testing resume..."
python flow.py resume

echo ""
echo "6. Testing learn..."
python flow.py learn "Test learning for automated tests"

echo ""
echo "7. Testing recall..."
python flow.py recall "test"

echo ""
echo "=== All tests passed! ==="

# Cleanup
rm -f .flowguardian_test
```

---

## 12. Troubleshooting Guide

### Common Issues

#### Issue: "CEREBRAS_API_KEY not set"

**Symptom:**
```
Error: CEREBRAS_API_KEY environment variable not set
```

**Solution:**
```bash
# Check if .env file exists
cat .env

# Make sure it contains:
CEREBRAS_API_KEY=csk-your-key-here

# Verify it's loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('CEREBRAS_API_KEY', 'NOT SET'))"
```

#### Issue: "Rate limit exceeded" (Cerebras)

**Symptom:**
```
Error 429: Rate limit exceeded
```

**Solution:**
1. Fill out rate limit increase form: https://form.typeform.com/to/IpWtfYd1
2. Wait 5-10 minutes for approval
3. Add retry logic with exponential backoff

#### Issue: "Not a git repository"

**Symptom:**
```
Error: Not a git repository (or any of the parent directories)
```

**Solution:**
```bash
# Initialize git in your project
git init
git add .
git commit -m "Initial commit"
```

#### Issue: "Assistant not found" (Backboard)

**Symptom:**
```
Error 404: Assistant not found
```

**Solution:**
```bash
# Re-initialize Flow Guardian
rm -rf .flowguardian
python flow.py init --user "your-username"
```

#### Issue: "Connection timeout"

**Symptom:**
```
httpx.ConnectTimeout: Connection timeout
```

**Solution:**
```python
# Increase timeout in API calls
async with httpx.AsyncClient(timeout=60.0) as client:
    ...
```

#### Issue: Rich panels not rendering correctly

**Symptom:**
- Garbled output
- Missing borders
- No colors

**Solution:**
```bash
# Check terminal supports colors
echo $TERM
# Should be: xterm-256color or similar

# Force Rich to use colors
export FORCE_COLOR=1

# Or in Python:
from rich.console import Console
console = Console(force_terminal=True)
```

### Debug Mode

Enable verbose logging:

```bash
export FLOW_DEBUG=true
python flow.py capture -t debug
```

Add debug output to your code:

```python
import os
DEBUG = os.environ.get("FLOW_DEBUG", "").lower() == "true"

def debug_log(message):
    if DEBUG:
        print(f"[DEBUG] {message}")
```

### Getting Help

1. **Cerebras issues:** Check https://docs.cerebras.ai or reach out on hackathon Discord
2. **Backboard issues:** They're a sponsor—reach out on Discord channel
3. **General issues:** Ask teammates first, then hackathon mentors

---

## 13. Implementation Timeline

### Phase 0: Setup (30 minutes)

- [ ] Clone/create repository
- [ ] Set up virtual environment
- [ ] Install dependencies
- [ ] Configure environment variables
- [ ] Test API connectivity

### Phase 1: Core Foundation (1.5 hours)

- [ ] `state.py` - Local state management
- [ ] `backboard_client.py` - API wrapper
- [ ] `git_utils.py` - Git operations
- [ ] Basic CLI skeleton

**Checkpoint:** Can create assistants and threads in Backboard

### Phase 2: Context Capture (2.5 hours)

- [ ] `cerebras_client.py` - Analysis prompts
- [ ] `capture.py` - Full capture logic
- [ ] `ui.py` - Capture panel
- [ ] `flow capture` command working

**Checkpoint:** `flow capture` saves context and displays panel

### Phase 3: Context Restoration (2.5 hours)

- [ ] Change detection in `git_utils.py`
- [ ] `restore.py` - Restoration logic
- [ ] Restore panel in `ui.py`
- [ ] `flow resume` command working

**Checkpoint:** Full capture → resume flow works end-to-end

### Phase 4: Learning System (2 hours)

- [ ] `flow learn` command
- [ ] `flow learn --team` command
- [ ] `flow recall` command
- [ ] `flow team` command
- [ ] `flow status` command

**Checkpoint:** All commands functional

### Phase 5: Polish & Demo (2.5 hours)

- [ ] Error handling for edge cases
- [ ] Beautiful Rich panels
- [ ] Demo script rehearsal (3x minimum)
- [ ] Backup recording
- [ ] README completion

**Checkpoint:** Ready to present

---

## 14. Success Metrics

### Hackathon Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Capture latency | < 2 seconds | Time from command to panel display |
| Resume latency | < 3 seconds | Time from command to panel display |
| Demo completion | 100% | All demo steps work without errors |
| Sponsor integration | Genuine | Both Cerebras and Backboard are core, not checkbox |

### Product Success Metrics (Post-Hackathon)

| Metric | Target | Description |
|--------|--------|-------------|
| Time to flow restoration | < 60 seconds | vs. 23 minutes baseline |
| Daily captures per user | 3-5 | Indicates habit formation |
| Team learnings created | 10+/week | Knowledge compounding |
| User retention (week 2) | > 50% | Continued usage |

---

## 15. Future Roadmap

### Version 1.1 (Post-Hackathon)

- [ ] VS Code extension for automatic file tracking
- [ ] Slack integration for team change notifications
- [ ] Calendar integration for automatic pre-meeting captures
- [ ] Web dashboard for viewing history

### Version 1.2

- [ ] GitHub/GitLab integration for PR context
- [ ] Automatic capture on branch switch
- [ ] AI-suggested capture triggers
- [ ] Team analytics dashboard

### Version 2.0

- [ ] Multi-repo support
- [ ] Project-level context (not just file-level)
- [ ] Integration with project management tools (Jira, Linear)
- [ ] Mobile companion app for on-the-go recalls

---

## Appendix A: Complete File Listings

### A.1 `flow/state.py`

```python
"""Local state persistence between CLI invocations."""
import json
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class FlowConfig(BaseModel):
    personal_assistant_id: str
    personal_thread_id: str
    team_assistant_id: Optional[str] = None
    team_thread_id: Optional[str] = None
    username: str

class LastCapture(BaseModel):
    timestamp: str
    branch: str
    files: list[str]
    summary: str
    git_head: str

def get_flow_dir() -> Path:
    """Get or create .flowguardian directory in project root."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            flow_dir = parent / ".flowguardian"
            flow_dir.mkdir(exist_ok=True)
            return flow_dir
    flow_dir = cwd / ".flowguardian"
    flow_dir.mkdir(exist_ok=True)
    return flow_dir

def load_config() -> Optional[FlowConfig]:
    config_path = get_flow_dir() / "config.json"
    if config_path.exists():
        return FlowConfig.model_validate_json(config_path.read_text())
    return None

def save_config(config: FlowConfig):
    config_path = get_flow_dir() / "config.json"
    config_path.write_text(config.model_dump_json(indent=2))

def load_last_capture() -> Optional[LastCapture]:
    capture_path = get_flow_dir() / "last_capture.json"
    if capture_path.exists():
        return LastCapture.model_validate_json(capture_path.read_text())
    return None

def save_last_capture(capture: LastCapture):
    capture_path = get_flow_dir() / "last_capture.json"
    capture_path.write_text(capture.model_dump_json(indent=2))
```

### A.2 `flow/cerebras_client.py`

```python
"""Direct Cerebras integration for fast inference."""
import os
import json
from cerebras.cloud.sdk import Cerebras
from pydantic import BaseModel

client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))

class CapturedContext(BaseModel):
    summary: str
    hypothesis: Optional[str] = None
    next_steps: list[str]
    complexity: str
    key_files: list[str]

CAPTURE_PROMPT = """Analyze this developer's current working context and extract key information.

Git State:
- Branch: {branch}
- Modified files: {modified_files}
- Recent commits: {recent_commits}
- Uncommitted changes: {diff_summary}

Respond in JSON format:
{{
    "summary": "One sentence: what they're working on",
    "hypothesis": "Their current theory/approach (null if unclear)",
    "next_steps": ["Likely next action 1", "Likely next action 2"],
    "complexity": "simple|medium|complex",
    "key_files": ["most_important_file.py"]
}}

Be concise and actionable."""

def analyze_context(
    branch: str,
    modified_files: list[str],
    recent_commits: list[str],
    diff_summary: str
) -> CapturedContext:
    """Analyze current context using Cerebras."""
    
    prompt = CAPTURE_PROMPT.format(
        branch=branch,
        modified_files=", ".join(modified_files) or "None",
        recent_commits="\n".join(recent_commits[-5:]) or "None",
        diff_summary=diff_summary[:2000]
    )
    
    response = client.chat.completions.create(
        model="llama-3.3-70b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=500,
        temperature=0.3
    )
    
    result = response.choices[0].message.content
    return CapturedContext.model_validate_json(result)

RESTORE_PROMPT = """Generate a welcome-back message for a developer.

Their last context:
{context}

What changed while away:
{changes}

Respond in JSON:
{{
    "context_summary": "What you were doing (1 sentence)",
    "hypothesis": "Your working theory (null if none)",
    "changes_impact": "How changes affect your work",
    "suggested_action": "Recommended next step"
}}

Be direct. No fluff."""

def generate_restoration(context: dict, changes: str) -> dict:
    """Generate restoration message."""
    
    prompt = RESTORE_PROMPT.format(
        context=json.dumps(context, indent=2),
        changes=changes or "No changes detected"
    )
    
    response = client.chat.completions.create(
        model="llama-3.3-70b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=300,
        temperature=0.3
    )
    
    return json.loads(response.choices[0].message.content)
```

### A.3 `flow/backboard_client.py`

```python
"""Backboard.io client for persistent memory."""
import os
import httpx
from datetime import datetime
from typing import Optional

BASE_URL = os.environ.get("BACKBOARD_BASE_URL", "https://app.backboard.io/api")
API_KEY = os.environ.get("BACKBOARD_API_KEY")

def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

async def create_assistant(name: str) -> str:
    """Create a Backboard assistant."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/assistants",
            headers=_headers(),
            json={
                "name": name,
                "llm_provider": "cerebras",
                "llm_model_name": "llama-3.3-70b",
                "tools": []
            }
        )
        resp.raise_for_status()
        return resp.json()["id"]

async def create_thread(assistant_id: str) -> str:
    """Create a thread within an assistant."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/assistants/{assistant_id}/threads",
            headers=_headers()
        )
        resp.raise_for_status()
        return resp.json()["id"]

async def store_context_snapshot(thread_id: str, context: dict):
    """Store context snapshot without LLM call."""
    content = f"""## Context Snapshot
**Working on:** {context.get('summary', 'unknown')}
**Hypothesis:** {context.get('hypothesis', 'none')}
**Files:** {', '.join(context.get('key_files', []))}
**Branch:** {context.get('branch', 'unknown')}
**Next steps:** {', '.join(context.get('next_steps', []))}"""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": content,
                "metadata": {
                    "type": "context_snapshot",
                    "timestamp": datetime.now().isoformat(),
                    **context
                },
                "send_to_llm": False
            }
        )
        resp.raise_for_status()
        return resp.json()

async def store_learning(thread_id: str, learning: str, tags: list = None):
    """Store a learning for future recall."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": f"**Learning:** {learning}",
                "metadata": {
                    "type": "learning",
                    "timestamp": datetime.now().isoformat(),
                    "tags": tags or []
                },
                "send_to_llm": False
            }
        )
        resp.raise_for_status()
        return resp.json()

async def recall_context(thread_id: str, query: str) -> str:
    """Query memory with semantic recall."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": query,
                "memory": "auto",
                "send_to_llm": True
            }
        )
        resp.raise_for_status()
        return resp.json().get("content", "")

async def store_team_learning(thread_id: str, learning: str, author: str, tags: list = None):
    """Store learning to team memory."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": f"**Team Learning** (from {author}): {learning}",
                "metadata": {
                    "type": "team_learning",
                    "author": author,
                    "timestamp": datetime.now().isoformat(),
                    "tags": tags or []
                },
                "send_to_llm": False
            }
        )
        resp.raise_for_status()
        return resp.json()

async def query_team_memory(thread_id: str, query: str) -> str:
    """Search team's shared learnings."""
    return await recall_context(
        thread_id, 
        f"Search team learnings for: {query}\n\nSummarize relevant learnings with authors."
    )

async def recall_personal(thread_id: str, query: str) -> str:
    """Search personal learnings."""
    return await recall_context(thread_id, f"Search my learnings for: {query}")
```

### A.4 `flow/git_utils.py`

```python
"""Git operations for context capture."""
from git import Repo
from git.exc import InvalidGitRepositoryError
from pathlib import Path
from typing import Optional

def get_repo() -> Optional[Repo]:
    """Get git repo for current directory."""
    try:
        return Repo(Path.cwd(), search_parent_directories=True)
    except InvalidGitRepositoryError:
        return None

def get_git_state(repo: Repo) -> dict:
    """Extract current git state."""
    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = "detached HEAD"
    
    modified = [item.a_path for item in repo.index.diff(None)]
    staged = [item.a_path for item in repo.index.diff("HEAD")]
    
    recent_commits = []
    for commit in list(repo.iter_commits(max_count=5)):
        recent_commits.append(f"{commit.hexsha[:7]} - {commit.message.strip()[:50]}")
    
    try:
        diff = repo.git.diff("--stat")
    except:
        diff = ""
    
    return {
        "branch": branch,
        "head": repo.head.commit.hexsha,
        "modified_files": modified + staged,
        "recent_commits": recent_commits,
        "diff_summary": diff[:1000]
    }

def get_changes_since(repo: Repo, since_sha: str) -> str:
    """Get summary of changes since a commit."""
    try:
        commits = list(repo.iter_commits(f"{since_sha}..HEAD"))
        if not commits:
            return "No new commits"
        
        changes = []
        for commit in commits[:10]:
            author = commit.author.name
            msg = commit.message.strip().split("\n")[0][:60]
            changes.append(f"• {author}: {msg}")
        
        return "\n".join(changes)
    except:
        return "Unable to determine changes"
```

### A.5 `flow/ui.py`

```python
"""Rich terminal UI for Flow Guardian."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

FLOW_GREEN = "#50C878"
FLOW_BLUE = "#4A90D9"
FLOW_RED = "#FF6B6B"

def capture_panel(context: dict, trigger: str):
    """Display capture confirmation."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style="bold cyan", justify="right")
    content.add_column()
    
    content.add_row("Working on", context.get("summary", "Unknown"))
    if context.get("hypothesis"):
        content.add_row("Hypothesis", context["hypothesis"])
    content.add_row("Key files", ", ".join(context.get("key_files", [])[:3]))
    content.add_row("Complexity", context.get("complexity", "unknown"))
    content.add_row("Trigger", trigger)
    
    panel = Panel(
        content,
        title="[bold green]✓ Context Captured[/bold green]",
        subtitle="[dim]Use 'flow resume' when you return[/dim]",
        border_style=FLOW_GREEN,
        box=box.ROUNDED
    )
    console.print(panel)

def restore_panel(restoration: dict, capture_time: str):
    """Display restoration panel."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style="bold cyan", justify="right", width=15)
    content.add_column()
    
    content.add_row("You were", restoration.get("context_summary", "Unknown"))
    
    if restoration.get("hypothesis"):
        content.add_row("Your theory", restoration["hypothesis"])
    
    changes = restoration.get("changes_impact", "No relevant changes")
    if changes and changes != "No relevant changes":
        content.add_row(
            Text("⚠ Changes", style="bold yellow"),
            Text(changes, style="yellow")
        )
    else:
        content.add_row("Changes", Text("No relevant changes", style="dim"))
    
    content.add_row(
        Text("→ Next step", style="bold green"),
        Text(restoration.get("suggested_action", "Continue"), style="green")
    )
    
    panel = Panel(
        content,
        title=f"[bold blue]🔄 Flow Restored[/bold blue]",
        subtitle=f"[dim]Away since {capture_time}[/dim]",
        border_style=FLOW_BLUE,
        box=box.ROUNDED
    )
    console.print()
    console.print(panel)

def error_panel(message: str, hint: str = None):
    """Display error."""
    content = Text(message, style="red")
    if hint:
        content.append(f"\n\n💡 {hint}", style="dim")
    
    panel = Panel(content, title="[bold red]Error[/bold red]", border_style=FLOW_RED, box=box.ROUNDED)
    console.print(panel)

def status_panel(config: dict, last_capture: dict = None):
    """Display status."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style="bold", justify="right")
    content.add_column()
    
    content.add_row("User", config.get("username", "Unknown"))
    content.add_row("Personal memory", "✓ Connected" if config.get("personal_assistant_id") else "✗ Not set")
    content.add_row("Team memory", "✓ Connected" if config.get("team_assistant_id") else "○ Optional")
    
    if last_capture:
        content.add_row("", "")
        content.add_row("Last capture", last_capture.get("timestamp", "Unknown")[:19])
        content.add_row("Branch", last_capture.get("branch", "Unknown"))
        content.add_row("Summary", last_capture.get("summary", "Unknown")[:50])
    
    panel = Panel(content, title="[bold]Flow Guardian Status[/bold]", border_style="blue", box=box.ROUNDED)
    console.print(panel)

def team_panel(result: str, query: str):
    """Display team search result."""
    panel = Panel(
        f"[cyan]{result}[/cyan]",
        title=f"[bold magenta]Team Knowledge: '{query}'[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED
    )
    console.print(panel)
```

---

## Appendix B: Demo Checklist

### Pre-Demo Setup

- [ ] Terminal font size increased (18pt+)
- [ ] VS Code theme is readable on projector
- [ ] `.env` file has valid API keys
- [ ] `flow init` already run
- [ ] Test file with a "bug" ready (e.g., `auth.py`)
- [ ] Git has some staged changes
- [ ] Screen recording backup ready

### Demo Commands Sequence

```bash
# 1. Show the problem (files open, working)
# [Narrate what you're doing]

# 2. Capture
flow capture -t meeting

# 3. Simulate being away (optional: make a commit)
git commit -m "Sarah's fix for auth.py"

# 4. Resume
flow resume

# 5. Team learning
flow learn "JWT tokens use UTC, not local time" --team --tags auth jwt

# 6. Team search
flow team "timezone issues authentication"
```

### Emergency Fallbacks

1. **API fails:** Have pre-recorded video of successful demo
2. **Git issues:** Use a pre-prepared demo directory
3. **Backboard down:** Show Cerebras-only capture with local storage
4. **Time running out:** Skip team features, focus on capture/resume

---

*End of PRD*