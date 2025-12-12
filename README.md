# Team Nexus: AI Conversational Loan Agent

### EY Techathon 6.0 (BFSI Track)

**Team Nexus** presents an AI-driven conversational chatbot designed to automate the end-to-end personal loan origination process for Non-Banking Financial Companies (NBFCs). This solution replaces manual sales processes with an intelligent 24/7 AI agent system to increase conversion rates and operational efficiency.

Built with **LangGraph + Groq (Llama 3.1)** for fast, reliable multi-agent orchestration.

-----

## 1\. The Challenge

  * **Problem:** The existing manual process for upselling personal loans is inefficient, costly, and creates operational bottlenecks, slowing growth.
  * **Solution:** A conversational AI built on a **Master-Worker Multi-Agent Architecture**. A central **Master Agent (Supervisor)** with reasoning capabilities intelligently routes the conversation flow to specialized **Worker Agents** (Sales, KYC, Underwriting) that independently manage specific parts of the customer journey with their own tools and expertise.

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
  * Uses **Groq API (Llama 3.1)** as the **LLM engine** for fast, efficient AI responses with high rate limits.
  * The **Master Agent (Supervisor)** analyzes conversation history with reasoning and intelligently routes to specialized **Worker Agents**. It does not use tools itself.

### B. Worker Agents (Distinct Personas)

The Master Agent delegates control to these specialized agents, each with its own unique system prompt and allowed set of tools:

1.  **Sales Agent:** An enthusiastic, persuasive agent that warmly greets users, builds rapport, checks history, discusses loan needs, amounts, tenure options, and interest rates. Convinces customers about loan benefits.
2.  **KYC Agent:** A professional verification officer dedicated solely to verifying user identity (PAN number) using the CRM tool. Handles all KYC verification tasks.
3.  **Underwriting Agent:** A risk assessment expert that:
    * Fetches credit scores from mock credit bureau
    * Evaluates eligibility based on pre-approved limits
    * Handles three scenarios:
      - **Instant Approval**: Amount ≤ pre-approved limit
      - **Conditional Approval**: Amount ≤ 2× limit (requires salary slip, EMI must be ≤ 50% of salary)
      - **Rejection**: Amount > 2× limit OR credit score < 700
    * Generates PDF sanction letters for approved loans

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

  * **True Multi-Agent System:** A Master Agent (Supervisor) with reasoning capabilities intelligently routes tasks to distinct, specialized Worker Agents based on conversation context.
  * **Conversational & Persuasive:** Sales agent mimics human sales executives with warm greetings, rapport building, and persuasive techniques.
  * **Smart Tool Execution:** Agents seamlessly call tools (CRM, Credit Bureau, Offer Mart) and formulate natural responses based on results.
  * **Robust Workflow:** Fixed architecture prevents infinite loops with proper tool execution flow (Agent → Tools → Agent with results → Response).
  * **Explainable AI (XAI):** Provides transparent reasons for loan approvals or rejections, including credit score analysis and EMI calculations.
  * **End-to-End Automation:** Automated pipeline from initial chat to final PDF sanction letter generation with download links.
  * **RBI-Compliant Design:** Secure, tamper-proof audit trail via SQLite logs tracking all loan applications and decisions.
  * **State Management:** Tracks KYC verification status, loan amounts, and underwriting progress across the conversation.

-----

## 7\. Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript | Responsive web chat interface with Markdown rendering. |
| **Backend** | Python, Flask, Flask-CORS | Manages the main orchestration service API. |
| **AI Agents** | LangChain (LangGraph), Groq API (Llama 3.1) | Implements the Supervisor-Worker multi-agent architecture with fast, efficient LLM responses. |
| **Database** | SQLite (Local/Embedded) | Securely stores user data and loan logs. |
| **PDF Gen** | ReportLab | Automatic generation of sanction letters. |
| **Mock Services** | Flask microservices | CRM (Port 5001), Credit Bureau (Port 5002), Offer Mart (Port 5003). |

-----

## 8\. 👨‍💻 For Developers: How to Run Locally

Follow these steps to clone the repository and run the entire system with a single command.

### Prerequisites

  * Python 3.9+
  * Git
  * A Groq API Key (Get one free here: [Groq Console](https://console.groq.com/))

### Step 1: Clone the Repository

```bash
git clone https://github.com/HR-coding/AI-Conversational-Loan-Agent.git
cd AI-Conversational-Loan-Agent
```

### Step 2: Environment Configuration

Create `.env` files in both the **project root** and **backend/** directories:

**Root .env file:**
```bash
GROQ_API_KEY="gsk_...[YOUR_ACTUAL_GROQ_API_KEY]"
API_BASE_URL="http://localhost:5000"
```

**backend/.env file:**
```bash
GROQ_API_KEY="gsk_...[YOUR_ACTUAL_GROQ_API_KEY]"
API_BASE_URL="http://localhost:5000"
```

### Step 3: Install Dependencies

```bash
pip install -r backend/requirements.txt
```

Key packages include:
- `langchain-groq` - Groq LLM integration
- `langgraph` - Multi-agent orchestration
- `flask` & `flask-cors` - Backend API
- `reportlab` - PDF generation

### Step 4: Start Mock Services

Open **3 separate terminals** and run each mock service:

```bash
# Terminal 1 - CRM Service
cd backend/mock_services
python crm.py

# Terminal 2 - Credit Bureau
cd backend/mock_services
python credit_bureau.py

# Terminal 3 - Offer Mart
cd backend/mock_services
python offer_mart.py
```

### Step 5: Start Main Backend

Open a **4th terminal**:

```bash
cd backend/orchestrator
python app.py
```

Backend will start on `http://127.0.0.1:5000`

### Step 6: Launch Frontend

Open `frontend/index.html` directly in your browser or double-click the file.

The chat interface will connect to `http://localhost:5000/chat` automatically.

### Step 7: Start Chatting!

Try these sample conversations:
1. "Hi, I need a loan for my business"
2. Provide PAN number when asked (e.g., "ABCDE1234F")
3. System will evaluate eligibility and generate sanction letter if approved

-----
