#  Blog Generation Agent

A full-stack AI-powered blog generation system that uses modern LLM APIs to generate high-quality blog content based on user input.

---

##  Features

-  AI-powered blog generation  
-  Web search integration for context-aware content  
-  Embedding-based retrieval using FAISS  
-  Fast backend using FastAPI  
-  Modern frontend built with Vite + React  
-  API documentation with Swagger UI  

---

##  Project Structure

blog_generation_agent/ │ ├── backend/ │   ├── server.py          # FastAPI backend │   ├── requirements.txt   # Python dependencies │   └── .env               # Environment variables │ ├── frontend/ │   ├── src/               # React source code │   ├── package.json       # Node dependencies │   └── vite.config.js     # Vite config │ └── README.md

---

##  Tech Stack

### Backend:
- Python
- FastAPI
- FAISS
- OpenAI / Anthropic APIs

### Frontend:
- React
- Vite
- JavaScript

---

##  Prerequisites

Make sure you have installed:

- Python 3.10+
- Node.js (v18 or v20 recommended)
- npm

---

##  Backend Setup

### 1. Navigate to project
bash cd blog_generation_agent 

### 2. Create virtual environment
bash python3 -m venv .venv 

### 3. Activate environment
bash source .venv/bin/activate 

### 4. Install dependencies
bash pip install -r requirements.txt 

### 5. Setup environment variables
bash cp .env.example .env 

Fill in required API keys inside .env.

---

###  Run backend server

bash python server.py or 
python3 server.py  

Backend will run on:
http://127.0.0.1:8000

API Docs:
http://127.0.0.1:8000/docs

---

##  Frontend Setup

### 1. Navigate to frontend
bash cd frontend 

### 2. Install dependencies
bash npm install 

### 3. Run development server
bash npm run dev 

Frontend will run on:
http://localhost:5173

---

##  Connecting Frontend & Backend

Ensure API calls in frontend point to:

http://127.0.0.1:8000

---

##  Common Issues & Fixes

### 1. FastAPI not found
bash pip install fastapi uvicorn 

---

### 2. Vite permission error
bash chmod +x node_modules/.bin/vite 

---

### 3. Node version issues
Use Node v18 or v20 (avoid v24)

---

### 4. CORS error
Add this in backend:

python from fastapi.middleware.cors import CORSMiddleware  app.add_middleware(     CORSMiddleware,     allow_origins=["*"],     allow_credentials=True,     allow_methods=["*"],     allow_headers=["*"], ) 

---

##  How It Works

1. User inputs a topic from frontend  
2. Frontend sends request to backend API  
3. Backend:
   - Fetches context (via search APIs)
   - Uses embeddings + FAISS
   - Calls LLM (OpenAI / Anthropic)
4. Generated blog is returned to frontend  
5. Displayed to user  

---

Future Improvements

- User authentication  
- Blog saving & history  
- Deployment (Render / Vercel)  
- Better UI/UX  

---

Author

Shruti Bhoria  

If you like this project

Give it a star on Git