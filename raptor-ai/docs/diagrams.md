# Raptor AI — System Diagrams & Workflows

> Complete visual reference for understanding Raptor AI's architecture, data flows, and decision-making processes.  
> All diagrams use [Mermaid.js](https://mermaid.js.org/) and render natively on GitHub.

---

## Table of Contents

- [Architecture](#architecture)
  - [High-Level System Architecture](#1-high-level-system-architecture)
  - [Component Interaction Map](#2-component-interaction-map)
  - [Module Dependency Graph](#3-module-dependency-graph)
- [State Machine](#state-machine)
  - [Agent FSM](#4-agent-state-machine)
- [Workflows](#workflows)
  - [Voice Command Execution](#5-voice-command-execution-workflow)
  - [Proactive Monitoring & Alerting](#6-proactive-monitoring--alerting-workflow)
  - [Tool Execution Pipeline](#7-tool-execution-pipeline)
- [Learning System](#learning-system)
  - [Learning & Adaptation Flow](#8-learning--adaptation-flow)
  - [Explainability & User Override](#9-explainability--user-override-flow)
  - [Priority Decision Tree](#10-priority-decision-tree)
- [Advanced Flows](#advanced-flows)
  - [Browser Intelligence Flow](#11-browser-intelligence-flow)
  - [Multi-Tool Chaining Flow](#12-multi-tool-chaining-flow)
  - [System Boot Sequence](#13-system-boot-sequence)

---

## Architecture

### 1. High-Level System Architecture

The core architecture showing all six layers and how data flows from perception to presentation.

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

> Shows all six architectural layers and how user voice input flows through planning, execution, and learning before producing a response.

---

### 2. Component Interaction Map

How input sources flow through processing into action domains and output channels.

```mermaid
graph LR
    subgraph Input["Input Sources"]
        Voice["🎤 Voice"]
        Sensors["📡 System Sensors"]
        APIs["🌐 External APIs"]
    end

    subgraph Processing["Processing Pipeline"]
        ASR["Speech Recognition"]
        NLU["Language Understanding"]
        TaskRouter["Task Router"]
    end

    subgraph Actions["Action Domains"]
        SysTool["System Tools"]
        AutoTool["Automation Tools"]
        BrowseTool["Browser Tools"]
        ExtTool["External Data"]
    end

    subgraph Output["Output Channels"]
        Speech["🔊 Voice"]
        Dashboard["📊 Dashboard"]
        OSAction["💻 OS Actions"]
    end

    Voice --> ASR --> NLU --> TaskRouter
    Sensors --> TaskRouter
    APIs --> TaskRouter
    TaskRouter --> SysTool --> OSAction
    TaskRouter --> AutoTool --> OSAction
    TaskRouter --> BrowseTool --> OSAction
    TaskRouter --> ExtTool --> Speech
    SysTool --> Dashboard
    AutoTool --> Speech
    BrowseTool --> Speech
    ExtTool --> Dashboard
```

> Maps the three input sources (voice, sensors, APIs) through processing to four action domains and three output channels.

---

### 3. Module Dependency Graph

How the actual Python modules depend on and communicate with each other.

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

> Shows the actual file-level dependencies. The `agent.py` module sits at the center, delegating to planner, executor, and learning systems.

---

## State Machine

### 4. Agent State Machine

The four primary states of the Agent FSM with all valid transitions.

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

> The agent cycles through IDLE → LISTENING → PROCESSING → SPEAKING. Two special transitions exist: proactive alerts bypass LISTENING, and follow-ups loop from SPEAKING back to LISTENING.

---

## Workflows

### 5. Voice Command Execution Workflow

The complete end-to-end reactive pipeline from wake word to spoken response.

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

> Full reactive pipeline with WebSocket state broadcasts at each transition. Total latency is under 2 seconds for a fully local pipeline.

---

### 6. Proactive Monitoring & Alerting Workflow

How background daemons detect events, evaluate priority, and adaptively learn from user responses.

```mermaid
sequenceDiagram
    participant Mon as 🔍 Monitor Daemon
    participant News as 📰 News Monitor
    participant Sports as 🏏 Sports Monitor
    participant Weather as 🌦️ Weather Monitor
    participant Intel as 📊 Intelligence
    participant PE as ⚖️ Priority Engine
    participant UP as 💾 User Profile
    participant Agent as 🧠 Agent Core
    participant User as 👤 User
    participant LE as 📚 Learning Engine

    Mon->>Mon: Polling Cycle (every 60s)
    Mon->>News: Check Breaking News
    Mon->>Sports: Check Live Scores
    Mon->>Weather: Check Severe Alerts
    Mon->>Mon: Check CPU, RAM, Battery, Disk

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

    Note over LE,UP: If ignore_rate > 0.6 after 5+ events,<br/>priority auto-downgrades to MEDIUM
```

> Demonstrates the full proactive cycle: polling → detection → priority evaluation → user interaction → adaptive learning. The monitor runs independently of voice commands.

---

### 7. Tool Execution Pipeline

Detailed view of how the executor resolves and runs a tool safely.

```mermaid
flowchart TD
    A["Planner Output<br/>{tool, args}"] --> B{"Tool Exists in<br/>TOOL_REGISTRY?"}
    B -- "No" --> C["Return Error:<br/>Unknown Tool"]
    B -- "Yes" --> D{"Is Tool Marked<br/>Destructive?"}
    D -- "No" --> F["Execute Tool Function"]
    D -- "Yes" --> E{"User Voice<br/>Confirmation?"}
    E -- "Denied" --> G["Abort Execution<br/>Log: user_denied"]
    E -- "Confirmed" --> F
    F --> H{"Execution<br/>Successful?"}
    H -- "Error" --> I["Return Error Response<br/>Log: tool_error"]
    H -- "Success" --> J["Raw Result"]
    J --> K["Intelligence Layer<br/>Analyze & Contextualize"]
    K --> L["Synthesized Response<br/>Ready for TTS"]

    style A fill:#4F46E5,color:#fff
    style L fill:#059669,color:#fff
    style C fill:#DC2626,color:#fff
    style G fill:#DC2626,color:#fff
    style I fill:#DC2626,color:#fff
```

> Shows the safety-first execution model. Destructive tools require explicit voice confirmation. All results pass through the intelligence layer for contextual analysis before being spoken.

---

## Learning System

### 8. Learning & Adaptation Flow

How user interactions shape future alert behavior over time.

```mermaid
flowchart LR
    A["User Interaction<br/>Accept / Ignore / Override"] --> B["Learning Engine<br/>Log Event"]
    B --> C["Update Stats<br/>accept_count, ignore_count"]
    C --> D["Calculate<br/>ignore_rate"]
    D --> E{"ignore_rate<br/>> 0.6?"}
    E -- "Yes" --> F["Downgrade Priority<br/>HIGH → MEDIUM → LOW"]
    E -- "No" --> G["Maintain Current<br/>Priority Level"]
    F --> H["Update User Profile<br/>user_profile.json"]
    G --> H
    H --> I["Future Alerts<br/>Use Updated Priority"]

    style A fill:#4F46E5,color:#fff
    style F fill:#F59E0B,color:#000
    style I fill:#059669,color:#fff
```

> The learning engine is a feedback loop: every user response is logged, statistics are recalculated, and priority levels automatically adjust. Over time, Raptor learns what matters to you.

---

### 9. Explainability & User Override Flow

How users query the system for transparency and enforce manual overrides.

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant Agent as 🧠 Agent Core
    participant LC as 🔍 Learning Controls
    participant UP as 💾 User Profile

    rect rgb(30, 58, 138)
        Note over User,UP: Query: "Why" Flow
        User->>Agent: "Why don't I get cricket updates?"
        Agent->>LC: detect_learning_intent()
        LC->>UP: Fetch cricket event data
        UP-->>LC: {priority: LOW, ignore_rate: 0.75, total: 4, ignored: 3}
        LC->>LC: Build Explanation String
        LC-->>Agent: "You ignored 3 of 4 cricket alerts.<br/>Priority was auto-reduced to LOW."
        Agent->>User: Speak Explanation
    end

    rect rgb(5, 90, 50)
        Note over User,UP: Override: "Always" Flow
        User->>Agent: "Always notify me about cricket."
        Agent->>LC: detect_learning_intent()
        LC->>LC: Parse → ALWAYS override
        LC->>UP: Set cricket.override = ALWAYS
        LC-->>Agent: Override Confirmed
        Agent->>User: "Done. Cricket alerts set to ALWAYS."
    end

    rect rgb(120, 20, 20)
        Note over User,UP: Override: "Reset" Flow
        User->>Agent: "Reset my preferences."
        Agent->>LC: detect_learning_intent()
        LC->>UP: Clear all learned priorities
        UP-->>LC: Profile Reset
        LC-->>Agent: Reset Confirmed
        Agent->>User: "All preferences have been reset."
    end
```

> Three interaction patterns: querying why an alert was suppressed, setting a manual override, and resetting all learned behavior. All use natural language via `learning_controls.py`.

---

### 10. Priority Decision Tree

How the priority engine decides whether to alert the user for a given event.

```mermaid
flowchart TD
    A["Event Detected<br/>(e.g. cpu_spike, cricket_score)"] --> B{"Is Event Type<br/>PROTECTED?"}
    B -- "Yes (low_battery,<br/>new_device)" --> C["ALWAYS ALERT<br/>Cannot be suppressed"]
    B -- "No" --> D{"User Override<br/>Exists?"}
    D -- "ALWAYS" --> C
    D -- "NEVER" --> E["SUPPRESS ALERT<br/>Log silently"]
    D -- "No Override" --> F{"Check Learned<br/>Priority Level"}
    F -- "HIGH" --> G["ALERT USER"]
    F -- "MEDIUM" --> H{"Last Alert<br/>> 30 min ago?"}
    H -- "Yes" --> G
    H -- "No" --> I["DEFER<br/>Queue for later"]
    F -- "LOW" --> J{"Critical<br/>Threshold?"}
    J -- "Yes (>95%)" --> G
    J -- "No" --> E

    style C fill:#059669,color:#fff
    style E fill:#6B7280,color:#fff
    style G fill:#2563EB,color:#fff
    style I fill:#F59E0B,color:#000
```

> Decision tree showing how protected events, user overrides, learned priorities, and cooldown timers interact to produce the final alert/suppress decision.

---

## Advanced Flows

### 11. Browser Intelligence Flow

How Raptor communicates with the Chrome extension to perform autonomous web operations.

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant Agent as 🧠 Agent
    participant Plan as 📋 Planner
    participant BT as 🌐 Browser Tool
    participant BB as 🔌 Browser Bridge
    participant Ext as 🧩 Chrome Extension
    participant Page as 📄 Web Page

    User->>Agent: "Search for latest AI news"
    Agent->>Plan: Parse Intent
    Plan-->>Agent: {tool: "browser_search", query: "latest AI news"}
    Agent->>BT: Execute browser_search()
    BT->>BB: send_command("open_tab", url)

    BB->>BB: Check RESTRICTED_DOMAINS
    Note over BB: ✅ google.com is allowed

    BB->>Ext: WebSocket: open_tab
    Ext->>Page: Navigate to Google
    Page-->>Ext: Page Loaded
    Ext-->>BB: DOM Content Ready

    BT->>BB: send_command("get_text")
    BB->>Ext: WebSocket: extract_text
    Ext->>Page: Read DOM Text
    Page-->>Ext: Raw HTML Text
    Ext-->>BB: Text Content

    BB-->>BT: Page Text (truncated)
    BT->>BT: Summarize via LLM
    BT-->>Agent: Summary Ready
    Agent->>User: "Here's what I found about AI news..."
```

> Shows the complete WebSocket relay chain from user command through the browser bridge to the Chrome extension and back. The restricted domains check prevents automation on sensitive sites.

---

### 12. Multi-Tool Chaining Flow

How future chained workflows will execute multiple tools in sequence.

```mermaid
flowchart TD
    A["User: 'Summarize this tab,<br/>find related news,<br/>send to John via WhatsApp'"] --> B["Planner: Decompose<br/>into 3 sub-tasks"]

    B --> C["Step 1<br/>browser_get_page_text()"]
    C --> D["Result: Page Content"]
    D --> E["Step 2<br/>browser_search(related news)"]
    E --> F["Result: News Summary"]
    F --> G["Step 3<br/>send_whatsapp(John, combined)"]

    G --> H{"Destructive<br/>Tool Check"}
    H -- "Confirm" --> I["WhatsApp Sent ✅"]
    H -- "Deny" --> J["Aborted at Step 3"]

    D --> K["Context Accumulator<br/>Passes data between steps"]
    F --> K
    K --> G

    style A fill:#4F46E5,color:#fff
    style I fill:#059669,color:#fff
    style J fill:#DC2626,color:#fff
    style K fill:#7C3AED,color:#fff
```

> Future capability: the planner decomposes complex natural language into ordered sub-tasks. A context accumulator passes results between steps. Destructive tools still require confirmation.

---

### 13. System Boot Sequence

What happens when `raptor_launcher.py` starts the agent.

```mermaid
sequenceDiagram
    participant Launch as 🚀 Launcher
    participant Lock as 🔒 Lock Check
    participant Agent as 🧠 Agent
    participant Wake as 🎙️ Wake Listener
    participant Mon as 🔍 Monitor
    participant WS as 📡 WS Bridge
    participant Val as ✅ Validator

    Launch->>Lock: Check PID Lock File
    alt Lock Exists & Process Alive
        Lock-->>Launch: ❌ Already Running
        Launch->>Launch: Exit (Singleton Guard)
    else No Lock or Stale
        Lock-->>Launch: ✅ Proceed
        Launch->>Lock: Write PID Lock
    end

    Launch->>Val: Run Startup Validation
    Val->>Val: Check Microphone
    Val->>Val: Check Dependencies
    Val->>Val: Check .env Config
    Val-->>Launch: All Checks Passed

    Launch->>Agent: Initialize Agent Core
    Agent->>Wake: Start Wake Listener Thread
    Agent->>Mon: Start Monitor Daemon Thread
    Agent->>WS: Start WebSocket Bridge

    Note over Agent,WS: System Ready<br/>State: IDLE
    Wake->>Wake: Listening for "Hey Raptor"...
    Mon->>Mon: Polling system/network/external...
```

> Shows the watchdog boot sequence: singleton locking prevents duplicate processes, validation checks dependencies, then all subsystems start in parallel threads.

---

*📐 Generated for Raptor AI — see the [main README](../README.md) for setup and usage.*
