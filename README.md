# 🧠 Taji-Tiny Assistance

A lightweight, private, and fully local AI research assistant. 

Taji-Tiny is built for speed and privacy. It runs entirely on your own machine using **Ollama** and the **Qwen 2.5 3B** model, features a sleek **PySide6** desktop interface, and includes a built-in web research engine that can search the internet, read webpages, and synthesize cited answers without sending your data to the cloud.

---

## ✨ Features

- **100% Local & Private**: No API keys, no cloud dependencies. Everything runs on your hardware.
- **Sleek Desktop UI**: A modern, responsive PySide6 interface with Dark and Light modes.
- **Deep Research Engine**: 
  - Searches the web using DuckDuckGo (`ddgs`).
  - Automatically fetches and extracts readable text from the top sources.
  - Synthesizes a grounded answer with `[1], [2]` citations.
- **Strict Identity Constraints**: The system prompt is optimized for 3B models to ensure it identifies strictly as Taji-Tiny and avoids hallucinating base model origins (like Alibaba/Qwen).
- **Markdown Support**: Renders bold text, code blocks, lists, and links directly in the chat UI.

---

## 🛠️ Tech Stack

- **UI Framework**: [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python)
- **Local LLM Engine**: [Ollama](https://ollama.com/)
- **Model**: [Qwen 2.5 3B](https://ollama.com/library/qwen2.5) (Lightweight & fast)
- **Web Search**: [ddgs](https://pypi.org/project/ddgs/) (DuckDuckGo Search)
- **Web Scraping**: BeautifulSoup4 & lxml

---

## 🚀 Prerequisites

Before you begin, ensure you have the following installed:
1. **[Python 3.10+](https://www.python.org/downloads/)**
2. **[Ollama](https://ollama.com/download)** (Make sure the Ollama service is running in the background)

---

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/taji-tiny.git
   cd taji-tiny
   ```

2. **Download the Local Model:**
   Open your terminal and pull the Qwen 2.5 3B model via Ollama:
   ```bash
   ollama pull qwen2.5:3b
   ```

3. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎮 Usage

Start the application from the root directory:

```bash
python app.py
```

### How to use:
- **Chat Tab**: Type a message and press `Enter` to chat with the local model.
- **Research Tab**: Type a question (e.g., *"What happened in the 2026 Israel elections?"*) and click **Start Deep Research**. The app will search the web, read the articles, and generate a cited answer.
- **Copy to Chat**: After a research task finishes, click **Copy answer to chat** to save the result and its sources into your main chat history.

---

## 📂 Project Structure

```text
Taji-Tiny/
├── app.py                  # Entry point
├── requirements.txt        # Python dependencies
├── taji/
│   ├── config.py           # Global settings (temperature, max context, etc.)
│   ├── llm/
│   │   ├── client.py       # Ollama API wrapper
│   │   └── prompts.py      # System prompts optimized for 3B models
│   ├── research/
│   │   ├── engine.py       # Research orchestration logic
│   │   ├── fetch.py        # Web scraping & text extraction
│   │   └── search.py       # DuckDuckGo web search
│   └── ui/
│       ├── main_window.py  # Main PySide6 application window
│       ├── chat.py         # Chat bubbles and streaming logic
│       ├── markdown.py     # Custom Markdown-to-HTML renderer
│       ├── research.py     # Sources sidebar panel
│       └── theme.py        # QSS Stylesheet and theme palettes
```

---

## 📄 License

This project is licensed under the MIT License.
