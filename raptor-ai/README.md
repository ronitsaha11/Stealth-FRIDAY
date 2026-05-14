<p align="center">
  <img src="extension/icons/raptor128.png" alt="Raptor AI" width="120" />
</p>

<h1 align="center">Raptor AI</h1>

<p align="center">
  <strong>Autonomous Local-First AI Operating Layer for macOS</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#workflows">Workflows</a> •
  <a href="#setup">Setup</a> •
  <a href="#usage">Usage</a> •
  <a href="#project-structure">Structure</a> •
  <a href="docs/diagrams.md">All Diagrams</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square&logo=apple" alt="macOS" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/AI-Local--First-orange?style=flat-square" alt="Local AI" />
  <img src="https://img.shields.io/badge/voice-activated-purple?style=flat-square&logo=audiomack" alt="Voice Activated" />
  <img src="https://img.shields.io/badge/learning-adaptive-red?style=flat-square&logo=tensorflow" alt="Adaptive Learning" />
</p>

---

## Overview

**Raptor AI** is an autonomous, voice-activated AI assistant that operates as a personal **AI operating layer** — not just a chatbot. It runs entirely on your local machine, proactively monitors system health, network activity, and external intelligence sources, and adapts its behavior based on your preferences over time.

Unlike conventional assistants that wait passively for commands, Raptor **thinks ahead**: it detects anomalies, alerts intelligently, automates OS-level tasks, and explains every decision it makes.

---

## Features

| Category | Capabilities |
| :--- | :--- |
| **🎙️ Voice Interface** | Wake-word activation ("Hey Raptor"), local STT via Faster-Whisper, natural TTS |
| **🖥️ System Monitoring** | Real-time CPU, RAM, disk, and battery tracking with anomaly detection |
| **🌐 Network Intelligence** | Local network device scanning, new device alerts, IP change detection |
| **📡 External Intelligence** | Weather forecasts, breaking news, live sports scores (cricket, football) |
| **💬 OS Automation** | Send WhatsApp messages, read Apple Mail, manage files via osascript |
| **🌍 Browser Intelligence** | Google search, page summarization via Chrome extension bridge |
| **🧠 Adaptive Learning** | Priority engine adjusts alert frequency based on your engagement |
| **🔍 Explainability** | Ask "Why did you alert me?" — Raptor explains with confidence scores and history |
| **📊 Real-Time Dashboard** | Next.js frontend with live WebSocket state visualization |

---

## Architecture

Raptor AI employs a **six-layer architecture** with clear separation of concerns.

> 📐 **[View all 13 diagrams →](docs/diagrams.md)** for the complete visual reference.

### High-Level System Architecture

*The end-to-end flow from user voice input through planning, execution, learning, and spoken response.*

```mermaid
graph TD
    subgraph Perception["🎙️ Perception Layer"]
        WL["Wake Listener<br/><i>OpenWakeWord ONNX</i>"]
        STT["Speech-to-Text<br/><i>Faster-Whisper int8</i>"]
    end

    subgraph Orchestration["🧠 Orchestration Core"]
        Agent["Agent FSM<br/><i>IDLE → LISTEN → PROCESS → SPEAK</i>"]
        Planner["Intent Planner<br/><i>Regex + LLM Fallback</i>"]
        Intel["Intelligence Layer<br/><i>Context & Thresholds</i>"]
    end

    subgraph Execution["⚙️ Execution & Automation"]
        Exec["Action Executor"]
        TR["Tool Registry"]
        OS["OS Automation<br/><i>osascript / psutil</i>"]
        Browser["Browser Bridge<br/><i>WebSocket ↔ Chrome</i>"]
    end

    subgraph Daemons["🔄 Background Daemons"]
        Monitor["Proactive Monitor<br/><i>System · Network · External</i>"]
    end

    subgraph Learning["📚 Learning & Memory"]
        PE["Priority Engine"]
        LE["Learning Engine"]
        UP[("User Profile")]
        Log[("Interaction Log")]
    end

    subgraph Presentation["📊 Presentation Layer"]
        TTS["Local TTS<br/><i>pyttsx3</i>"]
        WS["WebSocket Bridge"]
        Dash["Next.js Dashboard"]
    end

    WL -- "Wake Word Detected" --> Agent
    STT -- "Transcription" --> Agent
    Agent -- "Raw Intent" --> Planner
    Planner -- "Parsed Task" --> Exec
    Exec -- "Resolve" --> TR
    TR -- "Execute" --> OS
    TR -- "Execute" --> Browser
    Exec -- "Result" --> Intel
    Intel -- "Synthesized Response" --> Agent
    Monitor -- "Anomalies & Events" --> Intel
    Intel -- "Check Priority" --> PE
    PE -- "Fetch Profile" --> UP
    Agent -- "State Updates" --> WS
    WS -- "Real-time Data" --> Dash
    Agent -- "Speak" --> TTS
    Agent -- "User Feedback" --> LE
    LE -- "Adjust Priorities" --> UP
    LE -- "Record Event" --> Log
```

### Module Dependency Graph

*How the actual Python modules depend on and communicate with each other.*

```mermaid
graph TD
    agent["agent.py<br/><i>Central Orchestrator</i>"]
    planner["planner.py<br/><i>Intent Router</i>"]
    executor["executor.py<br/><i>Action Runner</i>"]
    intel["intelligence.py<br/><i>Analysis Engine</i>"]
    monitor["monitor.py<br/><i>Background Daemon</i>"]
    le["learning_engine.py<br/><i>Adaptive Learner</i>"]
    lc["learning_controls.py<br/><i>Explainability</i>"]
    pe["priority_engine.py<br/><i>Priority Scorer</i>"]
    wake["wake_listener.py<br/><i>Wake Word</i>"]
    audio["local_audio.py<br/><i>STT / TTS</i>"]
    bb["browser_bridge.py<br/><i>Chrome Bridge</i>"]
    ws["ws_bridge.py<br/><i>Dashboard WS</i>"]

    subgraph Tools["core/tools/"]
        sys_t["system.py"]
        auto_t["automation.py"]
        browser_t["browser.py"]
        email_t["email.py"]
        rt_t["realtime.py"]
        web_t["web.py"]
        os_t["os.py"]
    end

    subgraph Monitors["core/external_monitors/"]
        news["news_monitor.py"]
        sports["sports_monitor.py"]
        weather["weather_monitor.py"]
    end

    subgraph Data["Persistent Storage"]
        up[("user_profile.json")]
        il[("interaction_log.json")]
    end

    wake --> agent
    audio --> agent
    agent --> planner
    agent --> executor
    agent --> ws
    planner --> executor
    executor --> Tools
    executor --> intel
    browser_t --> bb
    monitor --> Monitors
    monitor --> intel
    intel --> pe
    pe --> up
    agent --> le
    agent --> lc
    le --> up
    le --> il
    lc --> up
```

### Agent State Machine

*The four primary states with all valid transitions and operational notes.*

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> LISTENING : Wake Word Detected
    LISTENING --> PROCESSING : Speech Captured
    PROCESSING --> SPEAKING : Response Ready
    SPEAKING --> IDLE : Utterance Complete

    IDLE --> PROCESSING : Proactive Alert Triggered
    PROCESSING --> IDLE : Alert Suppressed by Priority Engine

    SPEAKING --> LISTENING : Follow-up Detected

    note right of IDLE
        Agent is dormant.
        Wake Listener active.
        Monitor daemons running.
    end note

    note right of LISTENING
        Audio capture active.
        Faster-Whisper on standby.
        Max speech duration enforced.
    end note

    note right of PROCESSING
        Planner routes intent.
        Executor runs tools.
        Intelligence analyzes output.
    end note

    note right of SPEAKING
        TTS in subprocess.
        WS bridge updates dashboard.
        Follow-up detection active.
    end note
```

---

## Workflows

### Voice Command Execution

*The complete reactive pipeline from wake word to spoken response with WebSocket state broadcasts.*

```mermaid
sequenceDiagram
    participant User
    participant Wake as 🎙️ Wake Listener
    participant STT as 🗣️ Local STT
    participant Core as 🧠 Agent Core
    participant Plan as 📋 Planner
    participant Exec as ⚙️ Executor
    participant Tool as 🔧 Tool Registry
    participant Intel as 📊 Intelligence
    participant TTS as 🔊 TTS Engine
    participant WS as 📡 WS Bridge

    User->>Wake: "Hey Raptor"
    Wake-->>Core: Wake Word Detected (confidence > 0.5)
    Core->>WS: State → LISTENING
    Core->>TTS: Play Chime
    Core->>STT: Start Audio Capture
    User->>STT: "What is my CPU usage?"
    STT-->>Core: Transcription Complete
    Core->>WS: State → PROCESSING
    Core->>Plan: Parse Intent
    Plan->>Plan: Regex Match → get_system_info
    Plan-->>Exec: {tool: "get_system_info", args: {}}
    Exec->>Tool: Run get_system_info()
    Tool-->>Exec: {cpu: "45%", ram: "60%", battery: "78%"}
    Exec->>Intel: Analyze Result
    Intel-->>Core: Synthesized: "CPU at 45 percent"
    Core->>WS: State → SPEAKING
    Core->>TTS: "Your CPU is at 45 percent."
    TTS-->>Core: Utterance Complete
    Core->>WS: State → IDLE
```

### Proactive Monitoring & Alerting

*How background daemons detect events, evaluate priority, and adapt from user responses.*

```mermaid
sequenceDiagram
    participant Mon as 🔍 Monitor Daemon
    participant Intel as 📊 Intelligence
    participant PE as ⚖️ Priority Engine
    participant UP as 💾 User Profile
    participant Agent as 🧠 Agent Core
    participant User as 👤 User
    participant LE as 📚 Learning Engine

    Mon->>Mon: Polling Cycle (every 60s)
    Mon->>Mon: Detect CPU Spike (95%)
    Mon->>Intel: Report Anomaly (cpu_spike, 95%)
    Intel->>PE: Evaluate Event Priority
    PE->>UP: Fetch cpu_spike config
    UP-->>PE: {priority: HIGH, ignore_rate: 0.2}
    PE-->>Intel: ALLOW (priority >= threshold)
    Intel->>Agent: Inject Alert

    Agent->>User: "⚠️ CPU critically high at 95%."
    User->>Agent: "Ignore it."
    Agent->>LE: Log (cpu_spike, IGNORED)
    LE->>LE: Recalculate ignore_rate → 0.4
    LE->>UP: Update cpu_spike priority

    Note over LE,UP: After 5+ events with ignore_rate > 0.6,<br/>priority auto-downgrades to MEDIUM.
```

### Tool Execution Pipeline

*The safety-first execution model with destructive tool confirmation and intelligence synthesis.*

```mermaid
flowchart TD
    A["Planner Output<br/>{tool, args}"] --> B{"Tool Exists in<br/>TOOL_REGISTRY?"}
    B -- "No" --> C["Return Error:<br/>Unknown Tool"]
    B -- "Yes" --> D{"Is Tool Marked<br/>Destructive?"}
    D -- "No" --> F["Execute Tool Function"]
    D -- "Yes" --> E{"User Voice<br/>Confirmation?"}
    E -- "Denied" --> G["Abort Execution"]
    E -- "Confirmed" --> F
    F --> H{"Execution<br/>Successful?"}
    H -- "Error" --> I["Return Error Response"]
    H -- "Success" --> J["Raw Result"]
    J --> K["Intelligence Layer<br/>Analyze & Contextualize"]
    K --> L["Synthesized Response<br/>Ready for TTS"]

    style A fill:#4F46E5,color:#fff
    style L fill:#059669,color:#fff
    style C fill:#DC2626,color:#fff
    style G fill:#DC2626,color:#fff
    style I fill:#DC2626,color:#fff
```

### Learning & Adaptation

*The closed-loop learning cycle that shapes future alert behavior.*

```mermaid
flowchart LR
    A["User Response<br/>Accept / Ignore"] --> B["Log Event"]
    B --> C["Update Stats<br/>accept_count, ignore_count"]
    C --> D["Calculate<br/>ignore_rate"]
    D --> E{"ignore_rate<br/>> 0.6?"}
    E -- "Yes" --> F["Downgrade Priority<br/>HIGH → MEDIUM → LOW"]
    E -- "No" --> G["Maintain Priority"]
    F --> H["Update User Profile"]
    G --> H
    H --> I["Future Alerts Use<br/>Updated Priority"]

    style A fill:#4F46E5,color:#fff
    style F fill:#F59E0B,color:#000
    style I fill:#059669,color:#fff
```

### Explainability & User Override

*How users query decisions and enforce manual overrides.*

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant Agent as 🧠 Agent Core
    participant LC as 🔍 Learning Controls
    participant UP as 💾 User Profile

    rect rgb(30, 58, 138)
        Note over User,UP: "Why" Query
        User->>Agent: "Why don't I get cricket updates?"
        Agent->>LC: detect_learning_intent()
        LC->>UP: Fetch cricket event data
        UP-->>LC: {priority: LOW, ignore_rate: 0.75, total: 4, ignored: 3}
        LC-->>Agent: "You ignored 3 of 4 alerts. Priority auto-reduced."
        Agent->>User: Speak Explanation
    end

    rect rgb(5, 90, 50)
        Note over User,UP: "Always" Override
        User->>Agent: "Always notify me about cricket."
        Agent->>LC: detect_learning_intent()
        LC->>UP: Set cricket.override = ALWAYS
        LC-->>Agent: Override Confirmed
        Agent->>User: "Cricket alerts set to ALWAYS."
    end
```

### Priority Decision Tree

*How the priority engine decides whether to alert or suppress.*

```mermaid
flowchart TD
    A["Event Detected"] --> B{"Protected<br/>Event?"}
    B -- "Yes" --> C["ALWAYS ALERT"]
    B -- "No" --> D{"User Override?"}
    D -- "ALWAYS" --> C
    D -- "NEVER" --> E["SUPPRESS"]
    D -- "None" --> F{"Learned<br/>Priority?"}
    F -- "HIGH" --> G["ALERT USER"]
    F -- "MEDIUM" --> H{"Cooldown<br/>Expired?"}
    H -- "Yes" --> G
    H -- "No" --> I["DEFER"]
    F -- "LOW" --> J{"Critical<br/>Threshold?"}
    J -- "Yes" --> G
    J -- "No" --> E

    style C fill:#059669,color:#fff
    style E fill:#6B7280,color:#fff
    style G fill:#2563EB,color:#fff
    style I fill:#F59E0B,color:#000
```

### Browser Intelligence

*WebSocket relay chain from user command through Chrome extension and back.*

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant Agent as 🧠 Agent
    participant BT as 🌐 Browser Tool
    participant BB as 🔌 Browser Bridge
    participant Ext as 🧩 Chrome Extension
    participant Page as 📄 Web Page

    User->>Agent: "Search for latest AI news"
    Agent->>BT: browser_search("latest AI news")
    BT->>BB: send_command("open_tab", url)
    BB->>BB: Check RESTRICTED_DOMAINS
    Note over BB: ✅ google.com allowed
    BB->>Ext: WebSocket: open_tab
    Ext->>Page: Navigate to Google
    Page-->>Ext: Page Loaded
    BT->>BB: send_command("get_text")
    BB->>Ext: WebSocket: extract_text
    Ext->>Page: Read DOM
    Page-->>Ext: Text Content
    Ext-->>BB: Raw Text
    BB-->>BT: Page Content
    BT->>BT: Summarize via LLM
    BT-->>Agent: Summary Ready
    Agent->>User: "Here's what I found..."
```

---

## Setup

### Prerequisites

- **macOS** 12+ (Monterey or later)
- **Python** 3.11+
- **Microphone** access (for voice input)
- **Groq API Key** (free tier available at [console.groq.com](https://console.groq.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/Rexy-5097/raptor-ai.git
cd raptor-ai

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Running

```bash
# Start the agent (recommended — includes watchdog)
python raptor_launcher.py

# Or run the agent directly
python agent.py
```

---

## Usage

### Voice Commands

| Say This | Raptor Does |
| :--- | :--- |
| *"Hey Raptor, what's my system status?"* | Reports CPU, RAM, disk, battery |
| *"Send a WhatsApp to John saying I'll be late"* | Opens WhatsApp, finds contact, sends message |
| *"What's the weather today?"* | Fetches local weather forecast |
| *"Search for latest AI news"* | Opens browser, searches, summarizes results |
| *"Read my emails"* | Reads and summarizes unread Apple Mail |
| *"Play some music"* | Opens YouTube and plays music |

### Learning Controls

| Say This | Effect |
| :--- | :--- |
| *"Always notify me about cricket"* | Sets cricket alerts to ALWAYS priority |
| *"Never alert me about weather"* | Suppresses weather notifications |
| *"Why did you alert me about CPU?"* | Explains confidence, history, and rule used |
| *"Reset my preferences"* | Clears all learned behavior |

---

## Project Structure

```
raptor-ai/
├── agent.py                    # Main agent FSM — central orchestrator
├── raptor_launcher.py          # Watchdog launcher with singleton locking
├── server.py                   # MCP server entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── LICENSE                     # MIT License
│
├── core/                       # Core engine modules
│   ├── planner.py              # Intent routing (regex + LLM fallback)
│   ├── executor.py             # Tool execution with safety checks
│   ├── intelligence.py         # Context analysis & threshold evaluation
│   ├── monitor.py              # Proactive background monitoring daemon
│   ├── priority_engine.py      # Dynamic event priority scoring
│   ├── learning_engine.py      # Adaptive behavior from user feedback
│   ├── learning_controls.py    # Explainability & user overrides
│   ├── local_audio.py          # Audio capture & Faster-Whisper STT
│   ├── wake_listener.py        # Wake word detection (OpenWakeWord)
│   ├── browser_bridge.py       # WebSocket bridge to Chrome extension
│   ├── ws_bridge.py            # Frontend dashboard WebSocket bridge
│   ├── health_check.py         # System health utilities
│   ├── config.py               # Global configuration
│   ├── validate_raptor.py      # Startup validation checks
│   │
│   ├── tools/                  # Tool registry modules
│   │   ├── automation.py       # macOS UI automation (WhatsApp, etc.)
│   │   ├── browser.py          # Browser search & summarization
│   │   ├── email.py            # Apple Mail integration
│   │   ├── realtime.py         # Real-time data tools
│   │   ├── system.py           # System info tools
│   │   ├── os.py               # OS-level file operations
│   │   ├── web.py              # Web scraping & API tools
│   │   └── time_tools.py       # Date/time utilities
│   │
│   ├── external_monitors/      # External intelligence sources
│   │   ├── news_monitor.py     # Breaking news polling
│   │   ├── sports_monitor.py   # Live sports score tracking
│   │   └── weather_monitor.py  # Weather forecast monitoring
│   │
│   ├── prompts/                # LLM prompt templates
│   └── resources/              # Static data resources
│
├── extension/                  # Chrome extension for browser bridge
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   └── icons/
│
├── dashboard/                  # Next.js real-time dashboard (separate setup)
├── scripts/                    # Launch & utility scripts
├── tests/                      # Test suite
├── docs/                       # Documentation & diagrams
│   └── diagrams.md             # 📐 Complete diagram reference (13 diagrams)
├── logs/                       # Runtime logs (gitignored)
└── config/                     # Additional configuration files
```

---

## Security & Permissions

Raptor AI requires the following macOS permissions:

| Permission | Purpose |
| :--- | :--- |
| **Microphone** | Voice input capture |
| **Accessibility** | UI automation for WhatsApp, Mail |
| **Full Disk Access** | File management operations |
| **Network** | Local network scanning, API calls |

### Safety Mechanisms

- **Destructive Action Confirmation:** Tools flagged as `destructive` require explicit voice confirmation before execution
- **Protected Events:** Critical alerts (low battery, new network device) cannot be fully suppressed by the learning engine
- **Restricted Domains:** Browser automation is blocked on sensitive sites (banking, login pages)

---

## Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| Wake Word | OpenWakeWord (ONNX) | Local, CPU-efficient, no TF dependency |
| Speech-to-Text | Faster-Whisper (int8) | Real-time local transcription, 100% private |
| Text-to-Speech | pyttsx3 | OS-native, process-isolated |
| LLM Reasoning | Groq (Llama-3.1-8b) | Near-instant inference via LPU |
| System Interface | osascript + psutil | Deep macOS integration |
| Dashboard | Next.js + WebSockets | Real-time state visualization |
| Backend | Python + FastAPI + aiohttp | Async event-driven architecture |

---

## Future Scope

- 🌐 **Browser Intelligence v2** — Full DOM manipulation, form filling, autonomous navigation
- 🔗 **Chained Workflows** — Multi-step task execution across tools
- 👁️ **Visual Perception** — Local vision models for screen awareness
- 🤖 **Multi-Agent** — Coordinated Raptor instances across devices
- 📱 **Cross-Platform** — Linux and mobile support

---

## Author

**[Rexy-5097](https://github.com/Rexy-5097)**

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
