import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('news-reels') // 'news-reels' or 'custom'
  const [newsReels, setNewsReels] = useState([])
  const [loadingNews, setLoadingNews] = useState(false)
  const [generatingReels, setGeneratingReels] = useState(false)
  const [jobIds, setJobIds] = useState([])
  const [jobs, setJobs] = useState({})
  const [currentReelIndex, setCurrentReelIndex] = useState(0)
  const reelsContainerRef = useRef(null)
  const videoRefs = useRef([])
  
  // Custom reel state
  const [newsSummary, setNewsSummary] = useState('')
  const [numScenes, setNumScenes] = useState(8)
  const [loading, setLoading] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [error, setError] = useState(null)

  // Category selection
  const [category, setCategory] = useState('general')
  const [country, setCountry] = useState('in')
  const [maxArticles, setMaxArticles] = useState(5)

  // Fetch existing news reels on mount
  useEffect(() => {
    fetchNewsReels()
  }, [])

  const fetchNewsReels = async () => {
    try {
      const response = await axios.get('/api/news_reels')
      if (response.data.success) {
        setNewsReels(response.data.reels)
      }
    } catch (err) {
      console.error('Error fetching news reels:', err)
    }
  }

  const handleGenerateNewsReels = async () => {
    setGeneratingReels(true)
    setError(null)

    try {
      const response = await axios.post('/api/auto_generate_news_reels', {
        category,
        country,
        max_articles: parseInt(maxArticles),
        num_scenes: 8
      })

      if (response.data.success) {
        setJobIds(response.data.job_ids)
        console.log('Started generating', response.data.job_ids.length, 'news reels')
      }
    } catch (err) {
      console.error('Error generating news reels:', err)
      setError(err.response?.data?.error || err.message || 'Failed to generate news reels')
      setGeneratingReels(false)
    }
  }

  // Poll job statuses for news reels
  useEffect(() => {
    if (!generatingReels || jobIds.length === 0) return

    const pollInterval = setInterval(async () => {
      try {
        const jobStatuses = {}
        let allCompleted = true

        for (const jid of jobIds) {
          const response = await axios.get(`/api/job_status/${jid}`)
          jobStatuses[jid] = response.data

          if (response.data.status !== 'completed' && response.data.status !== 'failed') {
            allCompleted = false
          }
        }

        setJobs(jobStatuses)

        // Fetch news reels every poll to show completed ones immediately
        fetchNewsReels()

        if (allCompleted) {
          setGeneratingReels(false)
          clearInterval(pollInterval)
        }
      } catch (err) {
        console.error('Error polling job statuses:', err)
      }
    }, 3000)

    return () => clearInterval(pollInterval)
  }, [jobIds, generatingReels])

  // Handle scroll snap and auto-play
  useEffect(() => {
    if (!reelsContainerRef.current || newsReels.length === 0) return

    const handleScroll = () => {
      const container = reelsContainerRef.current
      if (!container) return
      
      const scrollTop = container.scrollTop
      const reelHeight = container.clientHeight
      const newIndex = Math.round(scrollTop / reelHeight)

      if (newIndex !== currentReelIndex && newIndex >= 0 && newIndex < newsReels.length) {
        setCurrentReelIndex(newIndex)
        
        // Pause all videos
        videoRefs.current.forEach((video, idx) => {
          if (video && idx !== newIndex) {
            video.pause()
            video.currentTime = 0
          }
        })
        
        // Play current video with sound
        const currentVideo = videoRefs.current[newIndex]
        if (currentVideo) {
          currentVideo.muted = false
          currentVideo.play().catch(err => {
            // If auto-play with sound fails, try muted
            currentVideo.muted = true
            currentVideo.play().catch(e => console.log('Auto-play prevented:', e))
          })
        }
      }
    }

    const container = reelsContainerRef.current
    container.addEventListener('scroll', handleScroll, { passive: true })
    
    // Play first video on mount
    setTimeout(() => {
      if (videoRefs.current[0]) {
        videoRefs.current[0].muted = false
        videoRefs.current[0].play().catch(err => {
          videoRefs.current[0].muted = true
          videoRefs.current[0].play().catch(e => console.log('Auto-play prevented:', e))
        })
      }
    }, 100)

    return () => {
      if (container) {
        container.removeEventListener('scroll', handleScroll)
      }
    }
  }, [newsReels, currentReelIndex])

  // Custom reel generation
  const handleGenerate = async () => {
    if (!newsSummary.trim()) {
      setError('Please enter a news summary')
      return
    }

    setLoading(true)
    setError(null)
    setJobStatus(null)

    try {
      const response = await axios.post('/api/generate_reel', {
        news_summary: newsSummary,
        num_scenes: parseInt(numScenes)
      })

      setJobId(response.data.job_id)
    } catch (err) {
      console.error('Error starting job:', err)
      setError(err.response?.data?.error || err.message || 'Failed to start generation')
      setLoading(false)
    }
  }

  // Poll custom job status
  useEffect(() => {
    if (!jobId || !loading) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/job_status/${jobId}`)
        const status = response.data

        setJobStatus(status)

        if (status.status === 'completed') {
          setLoading(false)
          clearInterval(pollInterval)
        } else if (status.status === 'failed') {
          setLoading(false)
          setError(status.error || 'Generation failed')
          clearInterval(pollInterval)
        }
      } catch (err) {
        console.error('Error polling status:', err)
        setError('Failed to get job status')
        setLoading(false)
        clearInterval(pollInterval)
      }
    }, 3000)

    return () => clearInterval(pollInterval)
  }, [jobId, loading])

  const handleReset = () => {
    setJobId(null)
    setJobStatus(null)
    setError(null)
    setLoading(false)
    setNewsSummary('')
  }

  return (
    <div className="App">
      <header>
        <h1>🎬 Vishwas Netra</h1>
        <p>AI-powered video reels from verified news sources</p>
      </header>

      <nav className="tabs">
        <button 
          className={`tab ${activeTab === 'news-reels' ? 'active' : ''}`}
          onClick={() => setActiveTab('news-reels')}
        >
          📰 News Reels
        </button>
        <button 
          className={`tab ${activeTab === 'custom' ? 'active' : ''}`}
          onClick={() => setActiveTab('custom')}
        >
          ✏️ Custom Reel
        </button>
      </nav>

      <main>
        {activeTab === 'news-reels' && (
          <div className="news-reels-section">
            <div className="news-controls">
              <h2>Generate News Reels</h2>
              <div className="control-grid">
                <div className="form-group">
                  <label>Category</label>
                  <select value={category} onChange={(e) => setCategory(e.target.value)}>
                    <option value="general">General</option>
                    <option value="business">Business</option>
                    <option value="technology">Technology</option>
                    <option value="entertainment">Entertainment</option>
                    <option value="sports">Sports</option>
                    <option value="science">Science</option>
                    <option value="health">Health</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Country</label>
                  <select value={country} onChange={(e) => setCountry(e.target.value)}>
                    <option value="us">United States</option>
                    <option value="in">India</option>
                    <option value="gb">United Kingdom</option>
                    <option value="ca">Canada</option>
                    <option value="au">Australia</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Articles</label>
                  <select value={maxArticles} onChange={(e) => setMaxArticles(e.target.value)}>
                    <option value="3">3 articles</option>
                    <option value="5">5 articles</option>
                    <option value="8">8 articles</option>
                    <option value="10">10 articles</option>
                  </select>
                </div>
              </div>

              <button 
                onClick={handleGenerateNewsReels} 
                className="generate-news-btn"
                disabled={generatingReels}
              >
                {generatingReels ? '⏳ Generating...' : '🚀 Generate News Reels'}
              </button>
            </div>

            {generatingReels && (
              <div className="generation-progress">
                <h3>🎬 Generating Reels...</h3>
                <div className="jobs-grid">
                  {jobIds.map(jid => {
                    const job = jobs[jid]
                    return (
                      <div key={jid} className="job-card">
                        <div className="job-title">{job?.article_title || 'Loading...'}</div>
                        <div className="job-source">{job?.article_source || ''}</div>
                        <div className="progress-bar">
                          <div 
                            className="progress-fill" 
                            style={{ width: `${job?.progress || 0}%` }}
                          ></div>
                        </div>
                        <div className="job-status">{job?.current_step || 'Initializing...'}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            <div className="reels-gallery">
              {newsReels.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">�</div>
                  <h3>No Reels Yet</h3>
                  <p>Generate news reels to start scrolling!</p>
                </div>
              ) : (
                <div 
                  className="instagram-reels-container" 
                  ref={reelsContainerRef}
                >
                  {newsReels.map((reel, index) => (
                    <div key={index} className="instagram-reel-card">
                      <div className="reel-header">
                        <div className="reel-header-left">
                          <div className="profile-pic">📰</div>
                          <div className="header-info">
                            <div className="username">{reel.source || 'News'}</div>
                            <div className="location">{reel.category || 'Breaking News'}</div>
                          </div>
                        </div>
                        <button className="more-btn">⋯</button>
                      </div>

                      <div className="reel-video-wrapper">
                        <video 
                          ref={el => videoRefs.current[index] = el}
                          className="instagram-reel-video"
                          playsInline
                          loop
                          preload="metadata"
                          onClick={(e) => {
                            if (e.target.paused) {
                              e.target.play();
                              e.target.muted = false;
                            } else {
                              e.target.pause();
                            }
                          }}
                        >
                          <source src={reel.video_url} type="video/mp4" />
                        </video>
                        
                        <div className="reel-overlay">
                          <div className="reel-actions-sidebar">
                            <div className="action-btn-wrapper">
                              <button className="action-btn">❤️</button>
                              <span className="action-count">125K</span>
                            </div>
                            <div className="action-btn-wrapper">
                              <button className="action-btn">💬</button>
                              <span className="action-count">1.2K</span>
                            </div>
                            <div className="action-btn-wrapper">
                              <button className="action-btn">📤</button>
                            </div>
                            <div className="action-btn-wrapper">
                              <button 
                                className="action-btn"
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  const link = document.createElement('a');
                                  link.href = reel.video_url;
                                  link.download = `reel_${index + 1}.mp4`;
                                  link.click();
                                }}
                              >
                                ⬇️
                              </button>
                            </div>
                            {reel.url && (
                              <div className="action-btn-wrapper">
                                <button 
                                  className="action-btn"
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    window.open(reel.url, '_blank', 'noopener,noreferrer');
                                  }}
                                >
                                  🔗
                                </button>
                              </div>
                            )}
                          </div>

                          <div className="reel-info-bottom">
                            <div className="reel-caption">
                              <span className="username">{reel.source || 'News'}</span>
                              <span className="caption-text">{reel.title}</span>
                            </div>
                            {reel.summary && (
                              <div className="reel-summary">
                                {reel.summary.length > 120 ? reel.summary.substring(0, 120) + '...' : reel.summary}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'custom' && (
          <div className="custom-reel-section">
            {!loading && !jobStatus?.video_url && (
              <div className="input-section">
                <div className="form-group">
                  <label htmlFor="news-summary">News Summary</label>
                  <textarea
                    id="news-summary"
                    placeholder="Enter your news summary here..."
                    value={newsSummary}
                    onChange={(e) => setNewsSummary(e.target.value)}
                    rows="8"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="num-scenes">Number of Scenes</label>
                  <select
                    id="num-scenes"
                    value={numScenes}
                    onChange={(e) => setNumScenes(e.target.value)}
                  >
                    <option value="4">4 scenes</option>
                    <option value="5">5 scenes</option>
                    <option value="6">6 scenes</option>
                    <option value="7">7 scenes</option>
                    <option value="8">8 scenes</option>
                    <option value="10">10 scenes</option>
                  </select>
                </div>

                <button 
                  onClick={handleGenerate} 
                  className="generate-btn"
                  disabled={loading}
                >
                  Generate Custom Reel
                </button>
              </div>
            )}

            {loading && (
              <div className="loading-section">
                <div className="spinner"></div>
                <h2>Generating Your Reel...</h2>
                {jobStatus && (
                  <>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${jobStatus.progress}%` }}
                      ></div>
                    </div>
                    <p className="status-text">{jobStatus.current_step}</p>
                    <p className="progress-text">{jobStatus.progress}%</p>
                  </>
                )}
              </div>
            )}

            {error && (
              <div className="error-section">
                <h2>❌ Error</h2>
                <p>{error}</p>
                <button onClick={handleReset} className="reset-btn">
                  Try Again
                </button>
              </div>
            )}

            {jobStatus?.video_url && (
              <div className="result-section">
                <h2>✅ Reel Generated Successfully!</h2>
                
                <div className="video-container">
                  <video controls className="reel-video">
                    <source src={jobStatus.video_url} type="video/mp4" />
                  </video>
                </div>

                {jobStatus.scenes && (
                  <div className="scenes-info">
                    <h3>Scene Breakdown ({jobStatus.scenes.length} scenes)</h3>
                    <div className="scenes-list">
                      {jobStatus.scenes.map((scene, index) => (
                        <div key={index} className="scene-card">
                          <div className="scene-number">Scene {scene.scene_number}</div>
                          <div className="scene-narration">{scene.narration}</div>
                          <div className="scene-duration">{scene.duration}s</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="actions">
                  <a 
                    href={jobStatus.video_url} 
                    download={`reel_${jobId}.mp4`}
                    className="download-btn"
                  >
                    Download Video
                  </a>
                  <button onClick={handleReset} className="new-btn">
                    Create New Reel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <footer>
        <p>Powered by Google Vertex AI • Gemini 2.0 Flash • Imagen 3.0 • Cloud TTS</p>
      </footer>
    </div>
  )
}

export default App
