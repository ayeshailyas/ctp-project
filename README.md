# 🌍 Research Flow

<div align="center">

![Project Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=for-the-badge&logo=typescript)
![Tailwind](https://img.shields.io/badge/Tailwind-CSS-38B2AC?style=for-the-badge&logo=tailwind-css)
![OpenAlex](https://img.shields.io/badge/Data-OpenAlex-purple?style=for-the-badge)

**Explore the scientific output of nations through an immersive, interactive 3D experience.**

![View Website](https://research-flow-ctp.vercel.app/)

</div>

---

## 📖 About The Project

**Research Flow** is a cinematic data visualization platform that bridges the gap between raw bibliometric data and accessible insights. Powered by the **OpenAlex API** and **Google Gemini AI**, it allows researchers, policy-makers, and curious minds to explore what countries are researching, how they compare globally, and which papers are leading the charge.

The application features a seamless transition from a "Cinematic Intro" to a fully interactive dashboard, utilizing GPU-accelerated transitions and memoized 3D rendering for high performance.

### ✨ Key Features

* **🌐 Interactive 3D Globe:** Custom-built using `react-globe.gl` with per-polygon country highlighting and smooth zoom transitions.
* **📊 Dual-Mode Visualization:**
    * **Volume Mode:** See raw output quantities (e.g., "China produces the most Engineering papers").
    * **Specialization Mode (RCA):** Discover "Hidden Gems"—fields where a country punches above its weight (Relative Comparative Advantage).
* **🤖 AI Research Analyst:** A context-aware chatbot powered by **Gemini 2.5 Flash**. It knows exactly which country you are looking at and provides economic and historical context behind the data.
* **📑 Top Papers Extension:** A sliding "sidecar" panel that fetches the top 10 most-cited papers for any selected subfield, complete with DOI links.
* **📈 Historical Trends:** Interactive line charts showing the growth or decline of specific research topics over the last 20 years.

---

## 🛠️ Tech Stack

### Frontend
| Technology | Description |
| :--- | :--- |
| **Next.js 14** | App Router framework for React. |
| **React Globe GL** | WebGL-powered 3D globe visualization. |
| **Tailwind CSS** | Utility-first styling with custom glassmorphism effects. |
| **Recharts** | Composable charting library for trends and bars. |
| **Lucide React** | Beautiful, consistent iconography. |

### Backend & Data Pipeline
| Technology | Description |
| :--- | :--- |
| **Python / Pandas** | Data extraction, processing, and RCA score calculation. |
| **OpenAlex API** | The source of truth for global bibliographic data. |
| **Google Gemini** | LLM integration for the "Research Analyst" chatbot. |

---

## 🚀 Getting Started

Follow these steps to set up the project locally.

### Prerequisites
* Node.js (v18+)
* Python 3.8+ (for data pipeline)
* API Keys for Google Gemini

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/global-research-trends.git](https://github.com/yourusername/global-research-trends.git)
    cd global-research-trends
    ```

2.  **Install Frontend Dependencies**
    ```bash
    npm install
    # or
    yarn install
    ```

3.  **Set up Environment Variables**
    Create a `.env.local` file in the root directory:
    ```env
    GEMINI_API_KEY=your_google_gemini_key_here
    OPENALEX_EMAIL=your_email@example.com (Optional, for faster API rate limits)
    ```

4.  **Run the Development Server**
    ```bash
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000) to view the app.

---

## 🐍 Data Pipeline (Python)

This project relies on a pre-generated JSON dataset to ensure instant load times on the frontend. The data is fetched via Python scripts included in the repository.

**Location:** `/src/data/` (or root, depending on your structure)

1.  **Install Python Requirements:**
    ```bash
    pip install pyalex pandas python-dotenv
    ```

2.  **Fetch Raw Data (Top Works & Trends):**
    This script hits the OpenAlex API to get the top subfields, yearly trends, and top 10 papers per field.
    ```bash
    python save_data_csv.py
    ```

3.  **Process & Calculate Scores:**
    This script calculates the "Specialization Score" (RCA) and combines everything into one optimized JSON file.
    ```bash
    python convert_to_json.py
    ```
    *Output:* `src/data/generated-data.json`

---
