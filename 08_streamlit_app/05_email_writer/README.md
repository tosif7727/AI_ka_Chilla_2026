# ✉️ MailCraft — AI Email Writer

> Turn rough bullet points into polished, professional emails in seconds — powered by GPT-4o-mini.

---

## 🖼️ What It Does

MailCraft is a Streamlit web app that takes your quick notes and converts them into well-structured emails. Choose a tone, add names, hit **Generate** — done. You can also send the email directly from the app without opening any email client.

---

## ⚡ Quick Start

### 1. Clone the project

```bash
git clone https://github.com/tosif7727/mailcraft.git
cd mailcraft
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install streamlit langchain-openai langchain-core
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## 🗂️ Project Structure

```
mailcraft/
├── app.py                    # Main Streamlit UI
├── email_generator.py        # LangChain prompt + GPT logic
├── email_sender.py           # SMTP email delivery
├── .mailcraft_config.json    # Auto-created — saves your credentials locally
└── README.md
```

---

## 🔐 Saving Your Credentials

On first launch, open **⚙️ Settings** at the top of the app and fill in:

| Field | Description |
|---|---|
| OpenAI API Key | Your key from [platform.openai.com](https://platform.openai.com/api-keys) |
| Your name | Used as the email sign-off |
| Your email | The address emails are sent from |
| App password | See provider guide below |
| Email provider | Gmail, Outlook, Yahoo, or Auto |

Click **💾 Save credentials** — everything is written to `.mailcraft_config.json` on your machine. You never have to fill these in again.

### Daily usage after setup

1. Write your bullet-point notes
2. Enter the recipient's name and email
3. Pick a tone
4. Click **✨ Generate Email**
5. Click **🚀 Send** — that's it

---

## 🔑 Getting an App Password

Regular passwords won't work for SMTP sending. You need an **App Password**.

### Gmail
1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** (required)
3. Search for **"App Passwords"**
4. Select app: *Mail*, device: *Other* → name it "MailCraft"
5. Copy the 16-character password into the app

### Yahoo
1. Go to [login.yahoo.com/account/security](https://login.yahoo.com/account/security)
2. Click **Generate app password**
3. Copy and paste into the app

### Outlook / Hotmail
1. Your normal account password works
2. Make sure **SMTP AUTH** is enabled: [account settings → Mail → POP and IMAP](https://outlook.live.com/mail/options/mail/popImap)

---

## 🎨 Tone Options

| Tone | Best For |
|---|---|
| 💼 Professional | Business emails, client communication |
| 😊 Friendly | Colleagues, warm follow-ups |
| 👋 Casual | Team mates, informal updates |
| 🎩 Formal | Official correspondence, senior stakeholders |
| ⚡ Urgent | Time-sensitive requests |
| 🙏 Apologetic | Delays, mistakes, making amends |

---

## 🛡️ Security Notes

- `.mailcraft_config.json` stores credentials in **plain text** on your local machine
- **Do not commit this file to Git** — add it to your `.gitignore`:

```
.mailcraft_config.json
```

- Your credentials are never sent anywhere except directly to OpenAI's API and your email provider's SMTP server

---

## 🧩 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `langchain-openai` | GPT-4o-mini integration |
| `langchain-core` | Prompt templates |

---

## 👤 Credits

Built by **[Touseef Afridi](https://github.com/tosif7727)**
Mentored by **[Dr. Ammar Tufail](https://www.youtube.com/c/Codanics)** @ Codanics