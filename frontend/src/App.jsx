import React, { useState, useEffect } from 'react';
import { 
  PenTool, Sun, Moon, Wand2, ImageIcon, 
  Settings, CheckCircle2, Loader2, Sparkles, 
  Clock, User, ChevronRight, FileText, Download, AlertCircle
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function App() {
  const [theme, setTheme] = useState('light');
  const [topic, setTopic] = useState('');
  const [generateImage, setGenerateImage] = useState(true);
  const [status, setStatus] = useState('idle'); // idle, generating, results, error
  const [currentStep, setCurrentStep] = useState(0);
  const [resultData, setResultData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  
  const steps = [
    { id: 'INIT', label: 'Initializing agent & validating input' },
    { id: 'CHECK_LIBRARY', label: 'Semantic search over existing blogs' },
    { id: 'SEO_RESEARCH', label: 'External SEO & Competitor research' },
    { id: 'GENERATE', label: 'Generating SEO optimized blog content' },
    { id: 'GENERATE_IMAGE', label: 'Creating featured image via DALL-E 3' }
  ];

  // Theme toggle effect
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    
    setStatus('generating');
    setCurrentStep(0);
    setResultData(null);
    setErrorMessage('');
    
    // Simulate the agent states with delays so the user sees progress
    let step = 0;
    const maxSteps = generateImage ? 5 : 4;
    
    const interval = setInterval(() => {
      if (step < maxSteps - 1) {
        step++;
        setCurrentStep(step);
      }
    }, 4000); // 4s per step simulated

    try {
      const response = await fetch('http://localhost:8000/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: topic,
          generate_image: generateImage
        })
      });

      const data = await response.json();
      clearInterval(interval);
      
      if (data.status === 'success') {
        setCurrentStep(maxSteps - 1);
        setResultData(data.data);
        setTimeout(() => setStatus('results'), 500);
      } else {
        setStatus('error');
        setErrorMessage(data.message || 'An error occurred during generation.');
      }
    } catch (error) {
      clearInterval(interval);
      setStatus('error');
      setErrorMessage('Failed to connect to the backend server. Make sure it is running on port 8000.');
    }
  };

  // Function to download markdown
  const downloadMarkdown = () => {
    if (!resultData || !resultData.blog_post) return;
    
    const content = resultData.blog_post.content;
    const element = document.createElement("a");
    const file = new Blob([content], {type: 'text/markdown'});
    element.href = URL.createObjectURL(file);
    element.download = `${resultData.blog_post.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="header">
        <div className="container header-content">
          <div className="logo">
            <div className="logo-icon">
              <PenTool size={20} />
            </div>
            <span>AutoBlog<span className="text-gradient">AI</span></span>
          </div>
          
          <button onClick={toggleTheme} className="theme-toggle" aria-label="Toggle theme">
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="container">
          
          {(status === 'idle' || status === 'error') && (
            <div className="hero">
              <h1>Create <span className="text-gradient">Professional Blogs</span> in Seconds</h1>
              <p>Our autonomous AI agent handles SEO research, semantic search, writing, and image generation. Just provide a topic.</p>
            </div>
          )}

          <div className={`generator-layout ${status === 'results' ? 'with-results' : ''}`}>
            
            {/* Input Form Column */}
            <div className="generator-column">
              <div className="card glass-card generator-form-card">
                <form onSubmit={handleGenerate}>
                  <div className="input-group">
                    <label className="input-label" htmlFor="topic">What should the blog be about?</label>
                    <input 
                      id="topic"
                      type="text" 
                      className="input-field" 
                      placeholder="e.g., How to Build a RAG Pipeline in Python..."
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      disabled={status === 'generating'}
                      required
                    />
                  </div>
                  
                  <div className="advanced-options">
                    <label className="checkbox-wrapper">
                      <input 
                        type="checkbox" 
                        checked={generateImage}
                        onChange={(e) => setGenerateImage(e.target.checked)}
                        disabled={status === 'generating'}
                      />
                      <span className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <ImageIcon size={18} className="text-primary" />
                        Generate Featured Image
                      </span>
                    </label>
                  </div>
                  
                  <button 
                    type="submit" 
                    className="btn btn-primary" 
                    style={{ width: '100%', marginTop: '2rem' }}
                    disabled={status === 'generating' || !topic.trim()}
                  >
                    {status === 'generating' ? (
                      <>
                        <Loader2 size={20} className="loader" />
                        Agent Working...
                      </>
                    ) : (
                      <>
                        <Wand2 size={20} />
                        Generate Blog
                      </>
                    )}
                  </button>
                </form>
                
                {/* Error Message */}
                {status === 'error' && (
                  <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: 'var(--danger-color)', color: 'white', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <AlertCircle size={20} />
                    <span>{errorMessage}</span>
                  </div>
                )}

                {/* Status Progress */}
                {status === 'generating' && (
                  <div className="status-container">
                    <h3 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: 600 }}>Agent Status Logs</h3>
                    
                    {steps.slice(0, generateImage ? 5 : 4).map((step, idx) => {
                      const isActive = idx === currentStep;
                      const isCompleted = idx < currentStep;
                      
                      return (
                        <div key={step.id} className={`status-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
                          <div className="step-icon">
                            {isCompleted ? (
                              <CheckCircle2 size={18} />
                            ) : isActive ? (
                              <Loader2 size={18} className="loader" style={{ color: 'var(--primary-color)' }} />
                            ) : (
                              <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: '2px solid var(--border-color)' }} />
                            )}
                          </div>
                          <span>{step.label}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Results Column */}
            {status === 'results' && resultData && (
              <div className="results-container">
                <div className="results-header">
                  <h2>Generated Content</h2>
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-outline" onClick={() => setStatus('idle')}>
                      Create New
                    </button>
                    <button className="btn btn-primary" onClick={downloadMarkdown}>
                      <Download size={18} />
                      Download Markdown
                    </button>
                  </div>
                </div>
                
                <div className="results-card">
                  {(resultData.featured_image?.image_url || resultData.featured_image?.image_path) && (
                    <img 
                      src={resultData.featured_image.image_url || resultData.featured_image.image_path} 
                      alt="Featured AI Generated Image" 
                      className="blog-image"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1200&auto=format&fit=crop";
                      }}
                    />
                  )}
                  
                  <div className="blog-content">
                    <div className="blog-meta">
                      <div className="meta-item">
                        <Clock size={16} />
                        <span>{Math.ceil(resultData.blog_post.word_count / 200)} min read</span>
                      </div>
                      <div className="meta-item">
                        <User size={16} />
                        <span>AutoBlog Agent</span>
                      </div>
                      <div className="meta-item">
                        <Sparkles size={16} style={{ color: 'var(--warning-color)' }} />
                        <span>{resultData.blog_post.source === 'existing_blog' ? 'Using Internal Library' : 'SEO Optimized'}</span>
                      </div>
                    </div>
                    
                    <h1 style={{ fontSize: '2.8rem', lineHeight: '1.2', marginBottom: '1.5rem', fontFamily: 'Outfit, sans-serif', letterSpacing: '-0.01em' }}>
                      {resultData.blog_post.title}
                    </h1>
                    
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {resultData.blog_post.content.replace(/^#\s+[^\n]+\n+/, '')}
                      </ReactMarkdown>
                    </div>
                    
                  </div>
                </div>
                
                {/* Agent Logs Output */}
                <div style={{ marginTop: '2rem' }} className="card generator-form-card">
                  <h3 style={{ marginBottom: '1rem' }}>Agent Execution Logs</h3>
                  <div style={{ backgroundColor: 'var(--bg-color-alt)', padding: '1rem', borderRadius: 'var(--radius-md)', fontFamily: 'monospace', fontSize: '0.9rem', color: 'var(--text-color-muted)' }}>
                    {resultData.execution_log.map((log, i) => (
                      <div key={i} style={{ marginBottom: '0.5rem' }}>&gt; {log}</div>
                    ))}
                  </div>
                </div>
                
              </div>
            )}
            
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>© 2026 Blog Generation Agent UI. For demonstration purposes.</p>
        </div>
      </footer>
    </div>
  );
}
