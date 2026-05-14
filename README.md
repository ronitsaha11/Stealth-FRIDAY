<div align="center">

# 🦅 Stealth F.R.I.D.A.Y

### **Fully Responsive Intelligent Digital Autonomous Yielder**

> A locally-running, offline-first AI voice agent with real-time system monitoring,  
> browser intelligence, multi-tool execution, and a Next.js dashboard — all on your machine.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-F55036?style=for-the-badge)](https://groq.com)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Core Pipeline Flow](#-core-pipeline-flow)
- [Agent State Machine](#-agent-state-machine)
- [Tool Ecosystem](#-tool-ecosystem)
- [Proactive Monitor](#-proactive-monitor)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Launching](#-launching)
- [Capabilities](#-capabilities)
- [Tech Stack](#-tech-stack)

---

## 🧠 Overview

**Stealth F.R.I.D.A.Y** is a fully local, privacy-first AI voice assistant. Unlike cloud-dependent assistants, it runs entirely on your hardware — no persistent data leaves your machine.

It listens for a custom wake word (`"Hey Raptor"`), transcribes speech using **Faster-Whisper**, routes intent through a rule-based planner + LLM fallback (via **Groq / LLaMA 3.1**), executes tools, and responds with natural TTS — all in real-time.

A **Next.js dashboard** streams live agent state, last command, active module, and system health via **WebSocket**.

---

## 🏗 System Architecture

```mermaid
graph TB
    subgraph USER["👤 User Layer"]
        MIC["🎤 Microphone"]
        SPEAKER["🔊 Speaker"]
        DASH["🖥️ Next.js Dashboard\n(localhost:3000)"]
    end

    subgraph CORE["🧠 Voice Agent Core (Python)"]
        WW["Wake Word Listener\nOpenWakeWord · OWW"]
        STT["Speech-to-Text\nFaster-Whisper (local)"]
        PLAN["Planner\nIntent → Tool Router"]
        EXEC["Executor\nTool Dispatcher"]
        LLM["LLM Fallback\nGroq · LLaMA 3.1-8B"]
        TTS["Text-to-Speech\npyttsx3 (offline)"]
        MON["Proactive Monitor\nRaptorMonitor daemon"]
        WSB["WebSocket Bridge\nws://localhost:8765"]
        BB["Browser Bridge\nChrome Extension ↔ Agent"]
    end

    subgraph TOOLS["🔧 Tool Modules"]
        RT["realtime.py\nWeather · News · Sports · Stocks"]
        OS_T["os.py\nApps · Files · Shell"]
        EM["email.py\nGmail IMAP · Search · Read"]
        AUTO["automation.py\nSystem · Network · Browser"]
        WEB["web.py\nWeb Search · URLs"]
        TIME["time_tools.py\nTimers · Alarms"]
    end

    subgraph EXT["🌐 External"]
        GROQ["Groq API\nCloud LLM fallback"]
        GMAIL["Gmail IMAP"]
        WHATSAPP["WhatsApp Web\nBrowser Automation"]
        WEATHER_API["Open-Meteo / wttr.in"]
        NEWS_API["NewsData.io / RSS"]
        SPORTS_API["Cricbuzz · Football API"]
    end

    MIC -->|raw audio| WW
    WW -->|wake event| STT
    STT -->|transcript| PLAN
    PLAN -->|tool list| EXEC
    EXEC -->|results| TTS
    TTS --> SPEAKER
    PLAN -->|no match| LLM
    LLM -->|response| TTS
    MON -->|alerts| TTS
    MON -->|state| WSB
    EXEC -->|state updates| WSB
    WSB <-->|WebSocket| DASH
    BB <-->|page context| AUTO
    EXEC --> TOOLS
    RT --> WEATHER_API
    RT --> NEWS_API
    RT --> SPORTS_API
    EM --> GMAIL
    AUTO --> WHATSAPP
    LLM --> GROQ
```

---

## 🔄 Core Pipeline Flow

```mermaid
sequenceDiagram
    participant User
    participant WakeListener
    participant STT as Faster-Whisper STT
    participant Planner
    participant Executor
    participant LLM as Groq LLM
    participant TTS
    participant Dashboard

    User->>WakeListener: "Hey Raptor"
    WakeListener-->>STT: wake_event fired
    TTS-->>User: "Raptor online. What can I do for you?"

    loop Conversation Turn
        User->>STT: speaks command
        STT-->>Planner: transcript string

        alt Tool matched
            Planner-->>Executor: [{tool, args}]
            Note over Planner: Priority-ordered routing:<br/>weather → cricket → stocks<br/>→ email → OS → browser
            
            alt Sensitive tool (email/WhatsApp)
                Executor-->>TTS: "Are you sure?"
                TTS-->>User: confirmation prompt
                User->>STT: "yes / cancel"
            end

            Executor-->>TTS: result message
            Executor-->>Dashboard: state update via WebSocket

        else No tool matched
            Planner-->>LLM: raw query
            LLM-->>TTS: LLaMA 3.1 response
        end

        TTS-->>User: spoken response
    end

    User->>STT: "stop / sleep"
    STT-->>WakeListener: return to IDLE
```

---

## 🔁 Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> STARTUP

    STARTUP --> IDLE : STT model loaded\nWake listener active

    IDLE --> SPEAKING : Wake word detected\n"Hey Raptor"
    SPEAKING --> LISTENING : Greeting complete
    LISTENING --> PROCESSING : Voice input received
    PROCESSING --> SPEAKING : Plan executed / LLM replied

    SPEAKING --> LISTENING : Interrupted by wake event

    LISTENING --> IDLE : 15s silence timeout
    SPEAKING --> IDLE : Exit command heard\n("stop", "sleep", "goodbye")

    IDLE --> SPEAKING : Monitor alert fires\n(CPU spike / rain / news)
    SPEAKING --> LISTENING : Monitor awaits confirmation
    LISTENING --> PROCESSING : User confirms action
    PROCESSING --> IDLE : Action complete

    note right of IDLE
        Wake word listener active
        Background monitor running
        Dashboard connected via WS
    end note

    note right of PROCESSING
        Planner routes intent
        Executor dispatches tools
        LLM handles fallback
    end note
```

---

## 🔧 Tool Ecosystem

```mermaid
mindmap
  root((F.R.I.D.A.Y Tools))
    Real-Time Intelligence
      get_weather
      get_weather_forecast
      get_cricket_scores
      get_football_scores
      get_news
      get_stock_price
    Communication
      read_emails
      summarize_emails
      search_emails
      send_whatsapp_message
      send_file_via_whatsapp
    OS & Files
      open_app
      open_url
      open_file
      find_latest_file
      create_folder
      run_command
      search_files
    Browser Intelligence
      browser_get_page
      browser_summarize
      browser_search
      browser_click
      browser_type
    Automation Engine
      automation_system_info
      automation_network_scan
      automation_screenshot
    Time & Alerts
      set_timer
      set_alarm
      read_recent_notifications
    Media
      play_music
```

---

## 🛡️ Proactive Monitor

The `RaptorMonitor` daemon runs as a background thread with no interaction required — it watches your system and world events and proactively alerts you.

```mermaid
flowchart TD
    START([Monitor Daemon\nThread Start]) --> LOOP{Poll Loop\nevery tick}

    LOOP -->|every 10s| SYS[System Check\nCPU · RAM · Disk · Battery]
    LOOP -->|every 60s| NET[Network Scan\nHost Discovery Delta]
    LOOP -->|every 5min| WEA[Weather Check\nRain · Temp Spike]
    LOOP -->|every 2min| SPO[Sports Check\nCricket · Football]
    LOOP -->|every 3min| NEWS[News Check\nBreaking Headlines]

    SYS --> DET{Event\nDetected?}
    NET --> DET
    WEA --> DET
    SPO --> DET
    NEWS --> DET

    DET -->|No| LOOP
    DET -->|Yes| COOL{Cooldown\nExpired?\n30s per type}
    COOL -->|No| LOOP
    COOL -->|Yes| LEARN{Learning\nEngine:\nSuppressed?}
    LEARN -->|Yes| LOOP
    LEARN -->|No| PRIO{Priority\nEngine:\nApproved?}
    PRIO -->|No| LOOP
    PRIO -->|Yes| IDLE{Agent\nState = IDLE?}
    IDLE -->|No| DEFER[Defer Alert\nLog only]
    DEFER --> LOOP

    IDLE -->|Yes| ALERT[🔊 Speak Alert\n+ Suggestion]
    ALERT --> LISTEN[Listen for\nConfirmation\n10s timeout]
    LISTEN -->|"yes / confirm"| ACTION[Execute\nRemediation Action]
    LISTEN -->|"no / cancel"| CANCEL[Cancel\nLog interaction]
    LISTEN -->|timeout| DISCARD[Discard\nLog timeout]
    ACTION --> RESULT[🔊 Speak Result]
    RESULT --> LOOP
    CANCEL --> LOOP
    DISCARD --> LOOP

    subgraph EVENTS["Monitored Events"]
        E1[cpu_spike > 80%]
        E2[ram_spike > 85%]
        E3[disk_full > 90%]
        E4[low_battery < 15%]
        E5[new_device on network]
        E6[rain / heat forecast]
        E7[cricket / football goal]
        E8[breaking news]
    end
```

---

## 📁 Project Structure

```
Stealth F.R.I.D.A.Y/
│
├── 🚀 launch_raptor.bat          # Start backend agent (Windows)
├── 🚀 launch_frontend.bat        # Start Next.js dashboard (Windows)
│
├── voice_agent_core/             # 🧠 Core Python agent
│   ├── agent.py                  # Main LocalVoiceAgent class & run loop
│   ├── server.py                 # FastAPI REST server
│   ├── raptor_launcher.py        # Process management launcher
│   │
│   └── core/
│       ├── wake_listener.py      # OpenWakeWord integration
│       ├── local_audio.py        # STT (Faster-Whisper) + TTS (pyttsx3)
│       ├── planner.py            # Intent → tool routing (480+ rules)
│       ├── executor.py           # Tool dispatch + result handling
│       ├── intelligence.py       # Automation engine + context memory
│       ├── monitor.py            # Proactive background daemon
│       ├── health_check.py       # Startup system validation
│       ├── ws_bridge.py          # WebSocket server (port 8765)
│       ├── browser_bridge.py     # Chrome extension ↔ agent bridge
│       ├── learning_engine.py    # Interaction history & suppression
│       ├── priority_engine.py    # Alert priority scoring
│       │
│       ├── tools/
│       │   ├── realtime.py       # Weather, news, sports, stocks
│       │   ├── email.py          # Gmail IMAP tools
│       │   ├── automation.py     # System/network/browser automation
│       │   ├── os.py             # App launching, file ops, shell
│       │   ├── browser.py        # Browser control tools
│       │   ├── web.py            # Web search
│       │   └── time_tools.py     # Timers & alarms
│       │
│       └── external_monitors/
│           ├── weather_monitor.py
│           ├── news_monitor.py
│           └── sports_monitor.py
│
├── frontend/                     # 🖥️ Next.js Dashboard (TypeScript)
│   └── src/
│       ├── app/
│       │   ├── page.tsx          # Main dashboard page
│       │   └── api/
│       │       ├── raptor/       # Agent control endpoints
│       │       └── token/        # Auth token route
│       │
│       ├── components/
│       │   ├── RaptorVisualizer.tsx   # Animated state visualizer
│       │   ├── StateIndicator.tsx     # IDLE/LISTENING/PROCESSING badges
│       │   ├── ActiveAgent.tsx        # Live agent info panel
│       │   ├── CommandPanel.tsx       # Command history & wake button
│       │   └── ModuleDisplay.tsx      # Active tool module display
│       │
│       └── hooks/
│           └── useRaptorSocket.ts     # WebSocket ↔ React state hook
│
├── extension/                    # 🌐 Chrome Extension
│   ├── manifest.json
│   ├── background.js             # Service worker
│   └── content.js                # Page context injector
│
├── external_modules/
│   └── automation_script/        # Network scanning & system tools
│
└── raptor-ai/                    # 🗂️ Canonical source / reference build
```

---

## ⚙️ Installation

### Prerequisites

| Requirement | Version |
|------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| Git | Any |
| Windows | 10/11 |

### 1. Clone the repository

```bash
git clone https://github.com/ronitsaha11/Stealth-FRIDAY.git
cd Stealth-FRIDAY
```

### 2. Set up the Python environment

```bash
cd voice_agent_core

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# or if using pyproject.toml:
pip install -e .
```

### 3. Install frontend dependencies

```bash
cd ../frontend
npm install
```

### 4. Install Chrome Extension *(optional — for browser intelligence)*

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder

---

## 🔑 Configuration

Copy the example env file and fill in your API keys:

```bash
cp voice_agent_core/.env.example voice_agent_core/.env
```

```env
# Required for LLM fallback
GROQ_API_KEY=gsk_...

# Required for email tools
GOOGLE_API_KEY=AIza...
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Required for real-time data
OPENAI_API_KEY=sk-...        # optional, alternative LLM

# Optional external services
SARVAM_API_KEY=sk_...        # Indian language TTS
DEEPGRAM_API_KEY=...         # Alternative STT
SUPABASE_URL=https://...     # Ticketing system
SUPABASE_API_KEY=...
```

> **Note:** The agent runs fully offline for voice, OS tools, timers, and browser control. API keys are only needed for email, Groq LLM fallback, and live data (weather/sports/news).

---

## 🚀 Launching

### Windows (Recommended)

Run both scripts — each opens its own terminal window:

```bat
launch_raptor.bat       # Starts the Python voice agent
launch_frontend.bat     # Starts the Next.js dashboard on :3000
```

### Manual

```bash
# Terminal 1 – Backend
cd voice_agent_core
.venv\Scripts\activate
python agent.py

# Terminal 2 – Frontend
cd frontend
npm run dev
```

The dashboard will be available at **http://localhost:3000**  
The WebSocket bridge runs at **ws://localhost:8765**

---

## 💬 Capabilities

| Category | Example Commands |
|---------|-----------------|
| **Wake** | *"Hey Raptor"* |
| **Weather** | *"Weather in Mumbai"*, *"Forecast for Delhi this week"* |
| **Sports** | *"What's the IPL score?"*, *"Live football scores"* |
| **News** | *"What's happening in the world?"*, *"Latest headlines"* |
| **Stocks** | *"Bitcoin price"*, *"What's Tesla stock at?"* |
| **Email** | *"Read my emails"*, *"Summarize emails"*, *"Search emails from John"* |
| **WhatsApp** | *"Send hello to Mum on WhatsApp"*, *"Send my resume to Priya"* |
| **Apps** | *"Open Chrome"*, *"Launch VS Code"*, *"Open Task Manager"* |
| **Files** | *"Find my latest PDF"*, *"Create a folder named Projects"* |
| **Browser** | *"What is this page?"*, *"Summarize this page"*, *"Click Sign In"* |
| **Timer** | *"Set a timer for 10 minutes"*, *"Wake me at 7am"* |
| **Music** | *"Play some music"*, *"Play Blinding Lights"* |
| **Sleep** | *"Stop"*, *"Sleep"*, *"Goodbye"* |

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Wake Word** | OpenWakeWord (OWW) |
| **Speech-to-Text** | Faster-Whisper (local, offline) |
| **Text-to-Speech** | pyttsx3 (offline) |
| **LLM** | Groq · LLaMA 3.1-8B-Instant |
| **Email** | Gmail IMAP (imaplib) |
| **System Monitoring** | psutil (cross-platform) |
| **WebSocket** | websockets (Python) |
| **Frontend** | Next.js 15 · TypeScript · TailwindCSS |
| **Browser Extension** | Chrome MV3 |
| **Real-time Data** | Open-Meteo · wttr.in · NewsData.io |
| **Platform** | Windows 10/11 |

---

## 🔐 Privacy

- All STT/TTS runs **100% locally** — your voice never leaves your machine
- Wake word detection is **on-device** via OpenWakeWord
- API calls are made only for: Groq LLM fallback, Gmail (IMAP), and live data feeds
- `.env` files are excluded from version control via `.gitignore`

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

MIT © [Ronit Saha](https://github.com/ronitsaha11)

---

<div align="center">
  <sub>Built with ❤️ by Ronit Saha · Stealth F.R.I.D.A.Y runs on your machine, for your machine.</sub>
</div>
