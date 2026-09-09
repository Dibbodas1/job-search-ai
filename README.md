# 🚀 AI-Powered Multi-Source Job Search & CV Intelligence Engine

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Vite-6.0+-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Google%20Gemini-AI%20Powered-8E75B2?style=for-the-badge&logo=google&logoColor=white" alt="Gemini AI" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

An end-to-end intelligent job aggregation and resume matching application. Upload your CV (PDF) to let **Google Gemini AI** analyze your skill profile, extract experience metrics, automatically query multiple global job boards (LinkedIn, Remotive, Jobicy, RemoteOK, Arbeitnow), and compute deep personalized fit scores with pros, cons, and resume gap analysis.

---

## 📑 Table of Contents

- [Features](#-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Supported Job Platforms](#-supported-job-platforms)
- [Project Structure](#-project-structure)
- [Quick Start & Local Setup](#-quick-start--local-setup)
  - [Prerequisites](#prerequisites)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
- [Environment Variables](#-environment-variables)
- [Hosting & Deployment Guide](#-hosting--deployment-guide)
  - [Deploy Backend to Render](#option-a-deploy-backend-to-render)
  - [Deploy Backend to Railway](#option-b-deploy-backend-to-railway)
  - [Deploy Frontend to Vercel](#option-c-deploy-frontend-to-vercel)
  - [Deploy Frontend to Netlify](#option-d-deploy-frontend-to-netlify)
- [API Endpoints Reference](#-api-endpoints-reference)
- [Exporting to Excel](#-exporting-to-excel)
- [License](#-license)

---

## ✨ Features

- 📄 **Intelligent CV Parsing**: Upload your resume PDF and let Google Gemini AI extract technical skills, job titles, years of experience, and a structured candidate summary.
- 🎯 **Automated Search Query Generation**: Dynamically derives targeted search keywords based on your unique skill stack.
- 🌐 **Multi-Board Aggregation**: Concurrently scrapes and queries multiple job platforms with intelligent rate limiting and deduplication.
- 🤖 **Deep AI Match & Fit Scoring**: Gemini AI scores candidate fit (0–100%), highlighting strengths, matching skills, and potential missing requirements for each job listing.
- ⚡ **Real-Time Progress Feedback**: Live visual search progress indicators across all active scrapers.
- 📊 **Rich Filtering & Sorting**: Filter by workplace type (Remote, Hybrid, On-site), experience level (Junior, Mid, Senior, Lead), source portal, and sort by match percentage or post date.
- 📥 **One-Click Excel Export**: Download filtered job results as a clean, styled `.xlsx` workbook.
- 🎨 **Modern Dark Glassmorphism UI**: Built with React and Vite featuring responsive card layouts, intuitive badges, and smooth modal overlays.

---

## 🏗 Architecture & Tech Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    React 18 + Vite Frontend                 │
│         (CV Upload, Search Controls, Dashboard, Modal)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST
┌──────────────────────────────▼──────────────────────────────┐
│                      Flask API Backend                      │
│                    (server.py + CORS)                       │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│   ┌──────────────────────────▼──────────────────────────┐   │
│   │           Google Gemini AI (OpenAI API spec)        │   │
│   │     - CV extraction & resume skill profiling        │   │
│   │     - Search query generation & fit scoring         │   │
│   └─────────────────────────────────────────────────────┘   │
│                              │                              │
│   ┌──────────────────────────▼──────────────────────────┐   │
│   │           Multi-Source Scraping Engine              │   │
│   │   LinkedIn (Guest/Playwright) | Remotive | Jobicy   │   │
│   │         RemoteOK | Arbeitnow | Apify (optional)     │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

- **Backend**: Python 3.10+, Flask, Flask-CORS, PyPDF2, OpenAI SDK (Gemini client), BeautifulSoup4, Requests, OpenPyXL, Gunicorn, Playwright / Crawlee.
- **Frontend**: React 18, Vite 6, Native CSS with glassmorphism design tokens.
- **AI Engine**: Google Gemini API (`models/gemini-2.0-flash` / `gemini-1.5-flash`).

---

## 🌐 Supported Job Platforms

| Platform | Type | Coverage | Features |
| :--- | :--- | :--- | :--- |
| **LinkedIn** | Public / Guest Scraping | Global | Location-aware, company details, direct apply |
| **Remotive** | Public REST API | Global Remote | Tech, Software Dev, DevOps, Product, QA |
| **Jobicy** | Public REST API | Global Remote | Remote engineering, design, marketing |
| **RemoteOK** | Public REST API | Worldwide | Salary tags, startup opportunities |
| **Arbeitnow** | Public REST API | Europe / Global | Visa sponsorship tags, tech roles |

---

## 📁 Project Structure

```text
├── cv/                      # Upload directory for resumes (ignored in git)
├── frontend/                # React + Vite client
│   ├── public/              # Static assets
│   ├── src/
│   │   ├── components/
│   │   │   ├── CVUpload.jsx          # Resume uploader & AI parsing card
│   │   │   ├── Hero.jsx              # App header & branding
│   │   │   ├── Icons.jsx             # SVG icon set
│   │   │   ├── JobModal.jsx          # Job detail modal & AI fit feedback
│   │   │   ├── ResultsDashboard.jsx  # Job grid, filters, sorting & export
│   │   │   ├── SearchPanel.jsx       # Custom search inputs & source toggles
│   │   │   └── SearchProgress.jsx    # Real-time scraping status bar
│   │   ├── App.jsx                   # Main orchestrator component
│   │   ├── index.css                 # Glassmorphic dark styling system
│   │   └── main.jsx                  # React DOM entrypoint
│   ├── index.html
│   ├── package.json
│   └── vite.config.js                # Vite config with backend proxy
├── .env.example             # Template for required environment secrets
├── .gitignore               # Comprehensive ignores (secrets, logs, node_modules)
├── Procfile                 # Production WSGI process file for cloud hosts
├── requirements.txt         # Python dependencies
├── scrape_jobs.py           # Scraping logic, normalization & deduplication
├── server.py                # Flask API server & Gemini AI integrations
└── README.md                # Project documentation
```

---

## ⚡ Quick Start & Local Setup

### Prerequisites

- **Python**: 3.10 or newer (`python --version`)
- **Node.js**: 18.0 or newer (`node --version` and `npm --version`)
- **Google Gemini API Key**: Obtain a free key from [Google AI Studio](https://aistudio.google.com/)

---

### 1. Backend Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Dibbodas1/<your-repo-name>.git
   cd <your-repo-name>
   ```

2. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and insert your Gemini API Key:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   ```

5. **Start the Flask backend server**:
   ```bash
   python server.py
   ```
   *The server will start on `http://localhost:5000`.*

---

### 2. Frontend Setup

1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install frontend dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   *Open your browser and navigate to `http://localhost:3000`.*

---

## 🔑 Environment Variables

| Variable | Required | Description | Default |
| :--- | :---: | :--- | :--- |
| `GEMINI_API_KEY` | **Yes** | Google Gemini API Key | - |
| `GOOGLE_API_KEY` | Optional | Fallback Gemini API Key | - |
| `GEMINI_BASE_URL` | Optional | Gemini OpenAI compatibility endpoint | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `APIFY_API_KEY` | Optional | Apify token for enhanced LinkedIn scraping | - |
| `PORT` | Optional | Flask server port | `5000` |

---

## 🚀 Hosting & Deployment Guide

### 🌟 Method 1: Unified Full-Stack on Render (Easiest — 1 Free URL for Both!)

Because we have configured a multi-stage `Dockerfile` and Flask static SPA serving, you can host the **entire full-stack app (React frontend + Flask backend)** on a single free Render Web Service!

1. Go to your [Render Dashboard](https://dashboard.render.com/) and click **New +** → **Web Service**.
2. Select **Build and deploy from a Git repository** and connect `Dibbodas1/job-search-ai`.
3. Choose **Docker** as the runtime (Render will automatically detect the root `Dockerfile`).
4. Set the **Instance Type** to **Free**.
5. Under **Environment Variables**, add:
   - `GEMINI_API_KEY`: *(Your Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/))*
   - `GEMINI_BASE_URL`: `https://generativelanguage.googleapis.com/v1beta/openai/`
6. Click **Deploy Web Service**.
7. Once deployed, Render will give you a public URL (e.g. `https://job-search-ai.onrender.com`). Both the React UI and Flask API will be running live together on that single URL!

---

### 🚀 Method 2: Decoupled Deployment (Frontend on Vercel + Backend on Render)

If you prefer deploying the frontend and backend on separate specialized platforms:

#### Step 1: Deploy Backend to [Render](https://render.com)
1. In [Render Dashboard](https://dashboard.render.com/), create a **New Web Service** connected to `job-search-ai`.
2. Select **Python 3** environment:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn server:app`
3. Add Environment Variable:
   - `GEMINI_API_KEY`: *(Your Google Gemini API Key)*
4. Deploy and copy your live backend URL (e.g. `https://job-search-backend.onrender.com`).

#### Step 2: Deploy Frontend to [Vercel](https://vercel.com)
1. Go to [Vercel](https://vercel.com) and click **Add New** → **Project**.
2. Import `Dibbodas1/job-search-ai`.
3. Configure the project:
   - **Root Directory**: Click Edit and select `frontend`
   - **Framework Preset**: `Vite`
4. Under **Environment Variables**, add:
   - `VITE_API_BASE`: `https://job-search-backend.onrender.com/api` *(replace with your actual Render backend URL)*
5. Click **Deploy**. Vercel will build and deploy your React app to a fast global CDN!

---

### 🚂 Method 3: Deploy to [Railway](https://railway.app)

1. Sign up on [Railway](https://railway.app) and click **New Project** → **Deploy from GitHub repo**.
2. Select `job-search-ai`. Railway will automatically build using the `Dockerfile` or `Procfile`.
3. Go to the **Variables** tab and add `GEMINI_API_KEY`.
4. Under **Settings** → **Networking**, click **Generate Domain**.

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Healthcheck and verification of Gemini API key presence |
| `POST` | `/api/analyze-cv` | Accepts `multipart/form-data` with `cv` (PDF), returns extracted profile & suggested keywords |
| `POST` | `/api/search` | Body: `{ query, location, sources, time_filter, job_type, limit }`. Scrapes jobs across platforms |
| `POST` | `/api/match-jobs` | Body: `{ jobs, cv_profile }`. Uses Gemini to compute AI match scores, pros, cons & skill gaps |
| `GET` | `/api/download-excel?session_id=<id>` | Generates and downloads an `.xlsx` report of search results |

---

## 📊 Exporting to Excel

When you perform a job search or match jobs against your CV, click **Export to Excel** in the top-right corner of the Results Dashboard. The generated spreadsheet includes:
- Job Title & Company Name
- Workplace Type (Remote / Hybrid / On-site) & Location
- Source Job Board & Direct Apply Link
- AI Match Score & Fit Summary
- Required vs. Matching Skills Breakdown
- Date Posted & Extraction Timestamp

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Feel free to fork, customize, and build upon it.
