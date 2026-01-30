# n8n Setup & Handoff Guide

This guide explains how to set up the automated event alert workflow using **n8n**. This is the recommended path for flexible, visual orchestration of the ingestion ecosystem.

## 1. Prerequisites
- **n8n Instance**: You can use n8n Desktop, a self-hosted Docker instance, or n8n Cloud.
- **Python Environment**: The machine running n8n (or accessible to it) must have the project's virtual environment set up and the scrapers functional.

---

## 2. Importing the Workflow
1.  Open your n8n instance.
2.  Create a new workflow.
3.  Copy the contents of `docs/n8n_workflow.json` from this project.
4.  Paste it directly into the n8n canvas.

---

## 3. Configuration Steps

### Step A: Terminal Path
The "Execute Command" node in n8n needs to know the absolute path to your Python environment.
- **Node**: `Run Python Collectors`
- **Command**: `C:\Users\ANDREY\OneDrive\Escritorio\event-driven-alerts\venv\Scripts\python.exe -m src.demo_ingestion`
- *Note: Adjust this path if moving the project to a different machine.*

### Step B: Google/Gmail Integration Options

There are two primary ways to connect the client's Google account to the notification system:

#### Option 1: SMTP with "App Passwords" (Easiest)
This is compatible with both the Python script (`main.py`) and n8n's **Email Send** node.
1.  **Preparation**: Ensure **2-Step Verification** is enabled on the Google account.
2.  **Generate Password**: 
    - Go to [Google App Passwords](https://myaccount.google.com/apppasswords).
    - Give it a name (e.g., "Event Alerts Script").
    - Copy the **16-character code**.
3.  **Credential Setup**:
    - **SMTP_USER**: `client@gmail.com`
    - **SMTP_PASSWORD**: `[The 16-character code]`
    - **SMTP_SERVER**: `smtp.gmail.com`
    - **SMTP_PORT**: `587`

#### Option 2: Direct Gmail Node (Professional)
n8n has a dedicated **Gmail Node** that uses OAuth2. This is more secure but requires creating a project in the **Google Cloud Console**.
1.  Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable the **Gmail API**.
3.  Configure the **OAuth Consent Screen** (Internal).
4.  Create **OAuth2 Client ID** credentials.
5.  In n8n, add a **Gmail Node** and use the "Google Auth" credential type, pasting the Client ID and Secret.

> [!TIP]
> **Recommendation**: For the initial handoff, use **Option 1 (SMTP)**. It takes 2 minutes to set up and works immediately with our current `n8n_workflow.json`.

### Step C: Schedule
- The **Schedule Trigger** is set to run every **Monday at 8:00 AM**.
- You can change this by double-clicking the node and selecting a different interval (Daily, Hourly, etc.).

---

## 4. Verification
1.  Click **Execute Workflow** at the bottom of the n8n screen.
2.  Monitor the "Run Python Collectors" node. It should stay active for about 1-2 minutes while the SeleniumBase and Playwright scrapers run.
3.  Confirmation: You should receive an email with the formatted summary and the CSV attachment.

---

## 5. Maintenance
- **Credentials**: If you change your email password, update the SMTP credentials in n8n.
- **Project Location**: If the project folder is moved, update the path in the "Execute Command" node.
- **Scraper Errors**: n8n will show a red node if the Python script fails. Check the `stderr` output in n8n for debugging.
