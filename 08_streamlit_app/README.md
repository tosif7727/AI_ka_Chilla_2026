# ✉️ Professional Email Writer

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Transform your bullet points into polished, professional emails in seconds using AI**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Project Structure](#-project-structure)

</div>

---

## ✨ Features

- **🎨 6 Tone Options**: Professional, Friendly, Casual, Formal, Urgent, and Apologetic
- **🤖 AI-Powered**: Leverages OpenAI's GPT-4o-mini via LangChain for high-quality email generation
- **👤 Personalization**: Optional recipient and sender name customization
- **⚡ Instant Generation**: Get professional emails in seconds
- **📥 Export Options**: Download as text file or copy to clipboard
- **🎭 Clean UI**: Modern gradient design with responsive layout
- **🔒 Secure**: API key handled securely via environment variables or user input

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit |
| **AI Framework** | LangChain |
| **LLM** | OpenAI GPT-4o-mini |
| **Language** | Python 3.8+ |
| **Styling** | Custom CSS |

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Step 1: Clone the Repository

```bash
git clone https://github.com/tosif7727/professional-email-writer.git
cd professional-email-writer
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**

```
streamlit>=1.28.0
langchain-openai>=0.0.5
langchain-core>=0.1.0
python-dotenv>=1.0.0
```

---

## 🚀 Usage

### Method 1: Run with API Key in Sidebar *(Recommended for beginners)*

```bash
streamlit run app.py
```

Then enter your OpenAI API key in the sidebar when prompted.

### Method 2: Run with Environment Variable

```bash
# macOS/Linux
export OPENAI_API_KEY="your-api-key-here"

# Windows
set OPENAI_API_KEY=your-api-key-here

streamlit run app.py
```

### How to Use

1. **Enter your notes** — Write bullet points or brief notes about what you want to say
2. **Select tone** — Choose from 6 tones: Professional, Friendly, Casual, Formal, Urgent, or Apologetic
3. **Add names** *(Optional)* — Enter recipient and sender names for personalization
4. **Generate** — Click "Generate Professional Email"
5. **Export** — Download as `.txt` file or copy to clipboard

---

## 📁 Project Structure

```
professional-email-writer/
│
├── app.py                  # Streamlit UI application
├── email_generator.py      # LangChain logic and email generation
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
```

| File | Purpose |
|------|---------|
| `app.py` | Streamlit frontend with UI components, session state management, and styling |
| `email_generator.py` | Core LangChain logic: LLM initialization, prompt templates, and email generation |
| `requirements.txt` | List of Python package dependencies |

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory *(optional)*:

```env
OPENAI_API_KEY=your-api-key-here
```

> **Note:** If not set in the environment, the app will prompt for the API key in the sidebar.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Instructor:** Dr. Ammar Tufail — Transforming students into AI Engineers at [Codanics](https://codanics.com/)
- **Framework:** Built with [Streamlit](https://streamlit.io/) and [LangChain](https://langchain.com/)
- **AI Model:** Powered by [OpenAI GPT-4o-mini](https://openai.com/)

---

## 📧 Contact

- **LinkedIn:** [Touseef Afridi](https://linkedin.com/in/touseef-afridi)
- **GitHub:** [@tosif7727](https://github.com/tosif7727)

<div align="center">

Crafted with ❤️ by **Touseef Afridi**  
Proud Student of **Codanics**

</div>
