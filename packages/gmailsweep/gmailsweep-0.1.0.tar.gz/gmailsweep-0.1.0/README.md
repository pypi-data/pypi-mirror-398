# GmailSweep 🧹

**Your personal automated janitor for Gmail.**

![Gmail Storage Warning](docs/storage_warning.png)
*(The warning that started it all)*

## 📖 The Story: Why I Built This

I had been using my Gmail account for over 6 years without ever cleaning it up. I had accumulated **21,000+ emails**, and recently, I got the  email from Google:

> **"Your Gmail storage is 97% full. You will stop getting messages if you do not upgrade."**

I was stuck with two options:
1.  **Pay** for Google One storage (Storage upgrade).
2.  **Clean up** the mess.

I chose to clean it up. But when I tried to filter by keywords or senders in Gmail, I hit a major roadblock: **Gmail only lets you delete 50 emails at a time.**

Clicking "Select All" > "Delete" > "Confirm" > "Wait" for 400 pages of emails was not an option.

**That's where GmailSweep comes in.** I realized I could leverage the **Gmail API** to bypass these UI limitations. I built this tool to analyze the inbox, filter by Year or Sender, and perform **bulk deletions** safely and efficiently. It worked for me, so I'm sharing it with the community.

## 🚀 Features

*   **Bulk Deletion**: Delete thousands of emails in seconds (bypassing the 50-limit).
*   **Deep Filtering**: Filter by **Sender**, **Keyword**, or **Date Range** (e.g., "All emails from 2018").
*   **Inbox Health Check**: See your Top 30 Senders to identify who is clogging your storage.
*   **Safety First**: Built-in safeguards to prevents deleting Starred or Important emails by default.
*   **Private**: Runs locally on your machine. Your data never leaves your computer.

## 🏗️ Architecture & Tech Stack

GmailSweep is a **local-execution** Python application that interfaces directly with the Google Gmail API. It avoids third-party servers entirely.

*   **Integration**: Uses OAuth 2.0 to authenticate directly with Google servers from your machine.
*   **Major Libraries**:
    *   `streamlit`: For the reactive web dashboard UI.
    *   `google-api-python-client`: Official library for Gmail API interaction.
    *   `pandas`: For high-performance data manipulation and analysis of email metadata.
    *   `google-auth-oauthlib`: Handles the secure OAuth flow.

## 🔐 Security & Privacy

This tool was developed with a "Paranoid Security" mindset and has undergone a self-audit.

*   **Local Only**: The app runs on `localhost`. Your credentials (`credentials.json`) and tokens (`token.json`) are stored physically on your laptop. **Do NOT deploy this app to a public server.**
*   **Full Access Scope**: The app requests `https://mail.google.com/` scope. This is necessary for the core feature (Permanently Deleting emails), but it grants full access. Treat your `token.json` file like a password.
*   **Verified**:
    *   Token storage is excluded from Git (`.gitignore`).
    *   No external analytics or tracking code.
    *   Input sanitization prevents basic injection attacks.
*   **Recommendations**:
    *   Always verify the URL in the browser during login (should be `accounts.google.com`).
    *   Delete `token.json` after you finish your cleanup session if sharing the computer.

## ⚡ Performance Benchmark

**Scenario**: Scanning **20,000 emails** in "Overview Mode" (No filters).
*   **Hardware**: Mac (16GB RAM)
*   **Network**: 137 Mbps Down / 28 Mbps Up
*   **Estimated Time**: ~10 - 15 Minutes

**Why so long?**
*   **Rate Limits**: Google restricts the Gmail API to ~250 units/second. To prevent your account from being temporarily locked, GmailSweep intentionally runs slower (safe mode) with sleep intervals between batches.
*   **Retry Logic**: If the app hits a rate limit (`429 Error`), it will automatically pause for 2 seconds and retry. This ensures the scan completes successfully without crashing, even if it takes a bit longer.

> **💡 Pro Tip**: To speed this up, use **Filters**!
> Scanning by **Year** (e.g., "2023") or **Sender** is significantly faster because the app processes fewer messages.

## 📚 Documentation

*   **[User Guide](docs/user_guide.md)**: Step-by-step instructions on how to set up credentials and use the tool.

## 🛠️ Quick Start

**Prerequisites:** Python 3.9+

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mjgit007/gmailsweep.git
    cd gmailsweep
    ```

2.  **Install the package:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    ```

3.  **Run the App:**
    ```bash
    gmailsweep
    ```
    *(This command works from any directory!)*

4.  **Connect:**
    *   The app will ask for your `credentials.json` on the first run.
    *   It securely saves them to `~/.gmailsweep/`, so you only need to do this once.
    *   See the **[User Guide](docs/user_guide.md)** for how to get your Google Cloud credentials.

4.  **Connect:** Upload your `credentials.json` (See User Guide) and start sweeping!

---
*"I automated myself out of a 15GB problem."*
