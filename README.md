# Team Nexus: AI Conversational Loan Agent

### EY Techathon 6.0 (BFSI Track)

**Team Nexus** presents an AI-driven conversational chatbot designed to automate the end-to-end personal loan origination process for Non-Banking Financial Companies (NBFCs). This solution replaces manual sales processes with an intelligent 24/7 agent to increase conversion rates and operational efficiency.

-----

## 1\. The Challenge

  * **Problem:** The existing manual process for upselling personal loans is inefficient, costly, and creates operational bottlenecks, slowing growth.
  * **Solution:** A conversational AI built on a **Supervisor-Worker Multi-Agent Architecture**. A central **Supervisor Agent** intelligently routes the conversation flow to specialized, distinct **Worker Agents** (Sales, KYC, Underwriting) that independently manage specific parts of the customer journey.

-----

## 2\. Live Demo

End-users and judges can access the fully deployed chatbot here without running any code.

**🔴 Live Demo URL:** `[INSERT YOUR RENDER URL HERE]`

*Note: The live demo is hosted on Render. Please allow a moment for the cold-start of the backend services if the bot does not reply immediately.*

-----

## 3\. System Architecture

This is a true multi-agent system where distinct personas handle different tasks, orchestrated by a supervisor.

### A. Backend: The "Brain" (Orchestrator)

  * Built with **Python + Flask**, hosting a **LangGraph** state machine designed on the **Supervisor-Worker** pattern.
  * An **LLM (Gemini)** acts as the **Supervisor Agent**. Its sole job is to analyze conversation history and decide which specialized **Worker Agent** should handle the next step. It does not use tools itself.

### B. Worker Agents (Distinct Personas)

The Supervisor delegates control to these specialized agents, each with its own unique system prompt and allowed set of tools:

1.  **Sales Agent:** A charismatic agent that greets users, checks history, and discusses loan amounts and interest rates.
2.  **KYC Agent:** A strict verification officer dedicated solely to verifying user identity using the CRM tool.
3.  **Underwriting Agent:** A risk assessment expert that calculates eligibility, enforces logic rules (e.g., salary slip checks for high amounts), and generates sanction letters.

### C. Mocked Bank Infrastructure

To simulate a real banking environment, three independent Flask microservices run separately:

  * **Mock CRM Server (Port 5001):** Responds to KYC validation requests.
  * **Mock Credit Bureau (Port 5002):** Provides dummy credit scores (650-850).
  * **Mock Offer Mart (Port 5003):** Provides pre-approved loan limits.

-----

## 4\. 📁 Project Structure & File Details

Here is a breakdown of the updated repository structure.

```text
nexus_project/
├── backend/                        # Server-side code (Python/Flask)
│   ├── mock_services/              # Independent microservices simulating bank APIs
│   │   ├── crm.py                  # Mock CRM (Port 5001)
│   │   ├── credit_bureau.py        # Mock Credit Bureau (Port 5002)
│   │   └── offer_mart.py           # Mock Offer Mart (Port 5003)
│   │
│   ├── orchestrator/               # The main application "brain" (Port 5000)
│   │   ├── agents/                 # AI & Business Logic
│   │   │   ├── master.py           # Defines the Supervisor Agent and distinct Worker Agents (Sales, KYC, Underwriting) and their routing logic.
│   │   │   └── tools.py            # The specific Python functions callable by the Worker Agents.
│   │   │
│   │   ├── services/               # Supporting utility services
│   │   │   ├── db_service.py       # Database Manager for SQLite operations.
│   │   │   └── pdf_service.py      # PDF Generator using ReportLab.
│   │   │
│   │   ├── static/
│   │   │   └── pdfs/               # Generated PDF sanction letters are saved here.
│   │   │
│   │   └── app.py                  # Main Flask Entry Point handles /chat API.
│   │
│   └── requirements.txt            # Python dependencies (now includes honcho, pydantic).
│
├── frontend/                       # Client-side code (Web Browser)
│   ├── index.html                  # The main HTML page for the chat interface.
│   ├── style.css                   # Styling for the chat UI with markdown support.
│   └── script.js                   # Handles user input, calls backend, renders responses.
├── .env.example                    # Template for environment variables.
└── Procfile                        # Configuration for running all 4 services with one command using Honcho.
```

-----

## 5\. 🔄 System Data Flow

The following diagram illustrates the flow of data in the new multi-agent architecture.

<img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/410e94ab-2b7d-4544-ac3d-b053223a805f" />


-----

## 6\. Key Features

  * **True Multi-Agent System:** A Supervisor Agent intelligently routes tasks to distinct, specialized Worker Agents based on conversation context.
  * **Emotional Intelligence:** The chatbot detects user sentiment and adapts its tone for a more human-like interaction.
  * **Explainable AI (XAI):** Provides transparent reasons for loan approvals or rejections.
  * **End-to-End Automation:** Automated pipeline from initial chat to final PDF sanction letter generation.
  * **RBI-Compliant Design:** Secure, tamper-proof audit trail via SQLite logs.

-----

## 7\. Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript | Responsive web chat interface with Markdown rendering. |
| **Backend** | Python, Flask, Flask-CORS | Manages the main orchestration service API. |
| **AI Agents** | LangChain (LangGraph), Gemini API | Implements the Supervisor-Worker multi-agent architecture. |
| **Process Mgmt** | **Honcho** | Manages running multiple backend services with a single command. |
| **Database** | SQLite (Local/Embedded) | Securely stores user data and loan logs. |
| **PDF Gen** | ReportLab | Automatic generation of sanction letters. |
| **Deployment** | Render | Hosting the live application. |

-----

## 8\. 👨‍💻 For Developers: How to Run Locally

Follow these steps to clone the repository and run the entire system with a single command.

### Prerequisites

  * Python 3.10+
  * Git
  * A Google Gemini API Key (Get one here: [Google AI Studio](https://aistudio.google.com/))

### Step 1: Clone the Repository

```bash
git clone https://github.com/HR-coding/AI-Conversational-Loan-Agent.git
cd AI-Conversational-Loan-Agent
```

### Step 2: Environment Configuration

Create a `.env` file in the **project root directory** (next to the `Procfile`).

```bash
# Create a file named .env in the root folder and add:
GOOGLE_API_KEY="AIzaSy...[YOUR_ACTUAL_API_KEY]"
API_BASE_URL="http://localhost:5000"
```

### Step 3: Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 4: Run the System (Single Command)

We use **Honcho** to start the Orchestrator and all 3 Mock Services simultaneously, as defined in the `Procfile`.

Run this command from the **project root**:

```bash
honcho start
```

*You will see colorful logs for all four services starting up.*

### Step 5: Launch Frontend

1.  Navigate to the `frontend` folder.
2.  Open `index.html` directly in your browser.
3.  Start chatting\!

-----
