import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Settings, MessageSquare, Plus, 
  Send, Database, Bot, ShieldAlert, ArrowRight, Activity, 
  PanelLeft, AlertTriangle, GitCompare, BrainCircuit, Play,
  RefreshCw, X, Clock, Shield
} from 'lucide-react';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isQTableOpen, setIsQTableOpen] = useState(false);
  const [sessions, setSessions] = useState(() => {
    try {
      const stored = localStorage.getItem('sre_sessions');
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  });
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [activeTransparency, setActiveTransparency] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  const [totalSavings, setTotalSavings] = useState(0);
  const [totalCalls, setTotalCalls] = useState(0);
  const [loadingText, setLoadingText] = useState("");
  const [diffModal, setDiffModal] = useState(null);
  const [qTable, setQTable] = useState(null);
  const [pendingApproval, setPendingApproval] = useState(null);
  const [agentControl, setAgentControl] = useState('Ask Everytime');
  
  // Live status polling
  const [status, setStatus] = useState({ slm: 'Checking', llm: 'Checking' });
  
  // Model config modals
  const [activeModelPanel, setActiveModelPanel] = useState(null); // 'llm' | 'slm' | null
  const [llmConfig, setLlmConfig] = useState({ name: 'Gemini 2.5 Pro', apiKey: '', logs: [] });
  const [slmConfig, setSlmConfig] = useState({ name: 'Qwen 2.5 (Ollama)', apiKey: 'http://localhost:11434', logs: [] });
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-save active session
  useEffect(() => {
    if (!currentSessionId || messages.length === 0) return;
    setSessions(prev => {
      const updated = prev.map(s => s.id === currentSessionId ? { ...s, messages } : s);
      localStorage.setItem('sre_sessions', JSON.stringify(updated));
      return updated;
    });
  }, [messages, currentSessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => { scrollToBottom(); }, [messages, isProcessing, pendingApproval]);

  // Poll backend status every 10s and log connection events
  useEffect(() => {
    const checkStatus = () => {
      const ts = new Date().toLocaleTimeString();
      fetch('http://localhost:8000/api/status')
        .then(r => r.json())
        .then(d => {
          setStatus({ slm: d.slm_status, llm: d.llm_status });
          if (d.llm_status === 'Online') {
            setLlmConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-19), { ts, type: 'ok', msg: 'Health check passed' }] }));
          } else {
            setLlmConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-19), { ts, type: 'err', msg: 'Health check failed' }] }));
          }
          if (d.slm_status === 'Online') {
            setSlmConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-19), { ts, type: 'ok', msg: 'Health check passed' }] }));
          } else {
            setSlmConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-19), { ts, type: 'err', msg: 'Health check failed' }] }));
          }
        })
        .catch(() => {
          setStatus({ slm: 'Offline', llm: 'Offline' });
          setLlmConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-19), { ts, type: 'err', msg: 'Backend unreachable' }] }));
          setSlmConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-19), { ts, type: 'err', msg: 'Backend unreachable' }] }));
        });
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  // Loading micro-states
  useEffect(() => {
    let interval;
    if (isProcessing) {
      const states = [
        "OptimizationFunnel compressing context...",
        "Zero-Shot Classifier scoring severity...",
        "TokenBudgeter allocating spend...",
        "Q-Learning Engine selecting policy...",
        "Model Factory spooling execution...",
        "RiskAssessor scanning output..."
      ];
      let i = 0;
      setLoadingText(states[0]);
      interval = setInterval(() => { i = (i + 1) % states.length; setLoadingText(states[i]); }, 700);
    }
    return () => clearInterval(interval);
  }, [isProcessing]);

  // Fetch Q-Table
  const fetchQTable = useCallback(() => {
    fetch('http://localhost:8000/api/qtable')
      .then(r => r.json())
      .then(d => setQTable(d.q_table))
      .catch(() => setQTable({}));
  }, []);

  useEffect(() => { if (isQTableOpen) fetchQTable(); }, [isQTableOpen, fetchQTable]);



  const handleSend = async (e, isOutage = false) => {
    if (e && e.preventDefault) e.preventDefault();
    const currentInput = isOutage 
      ? "CRITICAL: Kubernetes Node 4 unresponsive. Pods Evicted. OOMKilled on redis-master-0. Memory threshold 95% exceeded. Cluster autoscaler failing." 
      : input;
    if (!currentInput.trim() || isProcessing) return;
    
    let sessionId = currentSessionId;
    if (!sessionId) {
      sessionId = Date.now().toString();
      setCurrentSessionId(sessionId);
      setSessions(prev => {
        const updated = [{
          id: sessionId,
          title: currentInput.slice(0, 40) + (currentInput.length > 40 ? '...' : ''),
          messages: [],
          timestamp: new Date().toISOString()
        }, ...prev];
        localStorage.setItem('sre_sessions', JSON.stringify(updated));
        return updated;
      });
    }
    
    setMessages(prev => [...prev, { role: 'user', content: currentInput }]);
    setInput('');
    setIsProcessing(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: currentInput, is_outage: isOutage })
      });
      const data = await response.json();
      
      if (agentControl === 'Ask Everytime' && !isOutage) {
        setPendingApproval(data);
        setIsProcessing(false);
        return;
      }
      commitMessage(data);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: "Backend unreachable. Run: uvicorn src.api:app --host 0.0.0.0 --port 8000" }]);
      setIsProcessing(false);
    }
  };

  const commitMessage = (data) => {
    setMessages(prev => [...prev, { 
      role: 'assistant', 
      content: data.response,
      transparency: data.transparency
    }]);
    setTotalSavings(prev => prev + (data.transparency.estimated_savings_usd || 0));
    setTotalCalls(prev => prev + 1);
    setIsProcessing(false);
    setPendingApproval(null);
  };

  const handleReward = async (transparency, reward) => {
    try {
      await fetch('http://localhost:8000/api/reward', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          severity: transparency.severity,
          complexity: transparency.complexity,
          model_target: transparency.model_target,
          reward: reward
        })
      });
      // Refresh immediately if modal is open, otherwise invalidate cache
      if (isQTableOpen) fetchQTable();
      else setQTable(null);
    } catch { /* silent */ }
  };

  const resetChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setTotalSavings(0);
    setTotalCalls(0);
    setPendingApproval(null);
    setActiveTransparency(null);
  };

  const loadSession = (sessionId) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSessionId(session.id);
      setMessages(session.messages || []);
      const savings = (session.messages || []).reduce((acc, msg) => {
        return acc + (msg.transparency?.estimated_savings_usd || 0);
      }, 0);
      const calls = (session.messages || []).filter(m => m.role === 'assistant').length;
      setTotalSavings(savings);
      setTotalCalls(calls);
      setPendingApproval(null);
      setActiveTransparency(null);
    }
  };

  const statusDot = (s) => s === 'Online' ? 'bg-green-500' : s === 'Offline' ? 'bg-red-500' : 'bg-yellow-400 animate-pulse';

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 overflow-hidden font-sans">
      
      {/* ========== SIDEBAR ========== */}
      <div className={`${isSidebarOpen ? 'w-64' : 'w-0'} bg-white border-r border-gray-200 flex-col justify-between hidden md:flex shadow-sm z-20 shrink-0 transition-all duration-300 overflow-hidden`}>
        <div className="w-64 flex flex-col h-full justify-between">
          <div>
            {/* New Chat */}
            <div className="px-4 mt-5">
              <button onClick={resetChat} className="flex items-center justify-center space-x-2 text-sm font-semibold bg-gray-900 hover:bg-black text-white w-full py-2.5 px-4 rounded-xl transition-all shadow-sm hover:shadow">
                <Plus size={16} />
                <span>New Chat</span>
              </button>
            </div>
            
            {/* Recent Incidents -- populated from actual chat */}
            <div className="mt-7 px-4">
              <div className="text-[11px] font-bold text-gray-400 mb-2 uppercase tracking-wider">Recent Incidents</div>
              {sessions.length === 0 ? (
                <p className="text-xs text-gray-400 px-3 py-2">No incidents yet</p>
              ) : (
                <div className="space-y-0.5 max-h-48 overflow-y-auto">
                  {sessions.map((session) => (
                    <button key={session.id} onClick={() => loadSession(session.id)} className={`flex items-center space-x-2.5 text-sm font-medium w-full py-2 px-3 rounded-lg transition-colors text-left group ${currentSessionId === session.id ? 'bg-gray-100 text-gray-900' : 'hover:bg-gray-50 text-gray-600'}`}>
                      <MessageSquare size={14} className={`shrink-0 ${currentSessionId === session.id ? 'text-gray-900' : 'text-gray-300 group-hover:text-gray-900'}`} />
                      <span className="truncate">{session.title}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Testing Tools */}
            <div className="mt-7 px-4">
              <div className="text-[11px] font-bold text-gray-400 mb-2 uppercase tracking-wider">Testing Tools</div>
              <button onClick={(e) => handleSend(e, true)} disabled={isProcessing} className="flex items-center space-x-2.5 text-sm font-bold w-full py-2 px-3 rounded-lg transition-colors text-left text-red-600 hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed group">
                <Play size={14} className="text-red-500 group-hover:text-red-700 shrink-0" />
                <span>Simulate Outage</span>
              </button>
            </div>
          </div>
          
          {/* Bottom actions */}
          <div className="p-4 border-t border-gray-100 space-y-0.5">
            <button onClick={() => { setIsQTableOpen(true); fetchQTable(); }} className="flex items-center space-x-2.5 text-sm font-medium hover:bg-gray-50 w-full py-2 px-3 rounded-lg transition-colors text-gray-600 group">
              <BrainCircuit size={16} className="text-gray-400 group-hover:text-gray-900" />
              <span>Q-Learning State</span>
            </button>
            <button onClick={() => setIsSettingsOpen(true)} className="flex items-center space-x-2.5 text-sm font-medium hover:bg-gray-50 w-full py-2 px-3 rounded-lg transition-colors text-gray-600 group">
              <Settings size={16} className="text-gray-400 group-hover:text-gray-600" />
              <span>Settings</span>
            </button>
          </div>
        </div>
      </div>

      {/* ========== MAIN ========== */}
      <div className="flex-1 flex flex-col relative transition-all duration-300">
        
        {/* Topbar */}
        <div className="h-14 flex items-center justify-between px-5 border-b border-gray-200/60 absolute top-0 w-full z-10 bg-white/80 backdrop-blur-md">
          <div className="flex items-center space-x-3">
            <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
              <PanelLeft size={18} />
            </button>
            {totalCalls > 0 && (
              <span className="text-[11px] text-gray-400 font-medium">{totalCalls} call{totalCalls !== 1 ? 's' : ''} processed</span>
            )}
          </div>
          
          <div className="flex items-center">
            {/* SLM Indicator */}
            <button 
              onClick={() => setActiveModelPanel('slm')}
              className="flex items-center px-3 py-1.5 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer group"
            >
              <div className="flex flex-col items-start leading-none text-left">
                <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Local SLM</span>
                <div className="flex items-center mt-1 space-x-1.5">
                  <div className={`w-2 h-2 rounded-full ${statusDot(status.slm)}`}></div>
                  <span className="text-[12px] font-medium text-gray-800">{slmConfig.name}</span>
                </div>
              </div>
            </button>
            
            <div className="h-6 w-px bg-gray-200 mx-2"></div>
            
            {/* LLM Indicator */}
            <button 
              onClick={() => setActiveModelPanel('llm')}
              className="flex items-center px-3 py-1.5 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer group"
            >
              <div className="flex flex-col items-start leading-none text-left">
                <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Cloud LLM</span>
                <div className="flex items-center mt-1 space-x-1.5">
                  <div className={`w-2 h-2 rounded-full ${statusDot(status.llm)}`}></div>
                  <span className="text-[12px] font-medium text-gray-800">{llmConfig.name}</span>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto pt-20 pb-36 px-4 md:px-10 scroll-smooth">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center -mt-8">
              <h1 className="text-2xl font-bold mb-2 text-gray-900 tracking-tight text-center max-w-2xl leading-snug">
                Self-Healing Token-Aware Multi-Agent Architecture
              </h1>
              <p className="text-gray-400 font-medium text-sm">for Cost-Effective SRE Automation</p>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6 pt-2">
              {messages.map((msg, idx) => (
                <div key={idx} id={`msg-${idx}`} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  
                  {/* Cost comparison badges */}
                  {msg.role === 'assistant' && msg.transparency && (
                    <div className="mb-1.5 flex items-center space-x-1.5 ml-1">
                      <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
                        msg.transparency.model_target === 'LOCAL_SLM' ? 'bg-green-50 text-gray-900 border-green-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200'
                      }`}>
                        {msg.transparency.model_target === 'LOCAL_SLM' ? 'SLM $0.00' : 'LLM ~$0.04'}
                      </span>
                      {msg.transparency.model_target === 'LOCAL_SLM' && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border bg-gray-50 text-gray-400 border-gray-200 line-through">LLM ~$0.04</span>
                      )}
                      {!msg.transparency.is_safe && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border bg-red-50 text-red-600 border-red-200 flex items-center"><ShieldAlert size={10} className="mr-0.5" /> Blocked</span>
                      )}
                    </div>
                  )}
                  
                  {/* Chat bubble */}
                  <div className={`px-5 py-3.5 rounded-2xl max-w-[85%] text-[14px] leading-relaxed shadow-sm ${
                    msg.role === 'user' ? 'bg-gray-800 text-white rounded-br-sm font-medium' : 'bg-white text-gray-800 rounded-bl-sm border border-gray-200'
                  }`}>
                    {msg.role === 'assistant' && msg.content.startsWith('#!') ? (
                       <div className="bg-gray-900 -mx-5 -my-3.5 p-4 rounded-2xl rounded-bl-sm">
                         <div className="flex items-center space-x-1.5 mb-2.5">
                           <div className="w-2 h-2 rounded-full bg-red-500"></div><div className="w-2 h-2 rounded-full bg-yellow-500"></div><div className="w-2 h-2 rounded-full bg-green-500"></div>
                           <span className="ml-2 text-[10px] text-gray-500 font-mono">remediation.sh</span>
                         </div>
                         <pre className="font-mono text-[13px] overflow-x-auto text-green-400 leading-relaxed"><code>{msg.content}</code></pre>
                       </div>
                    ) : msg.content}
                  </div>
                  
                  {/* Action row: View Trace + Reject/Approve if unsafe */}
                  {msg.role === 'assistant' && msg.transparency && (
                    <div className="mt-2 ml-1 flex items-center space-x-2">
                      <button onClick={() => setActiveTransparency(msg.transparency)} className="flex items-center space-x-1 text-[11px] text-gray-500 hover:text-gray-900 font-semibold transition-colors bg-white px-2.5 py-1 rounded-md border border-gray-200 hover:shadow-sm">
                        <Activity size={12} /> <span>View Trace</span>
                      </button>
                      {!msg.transparency.is_safe && (
                        <>
                          <button onClick={() => handleReward(msg.transparency, -20)} className="flex items-center space-x-1 text-[11px] text-red-600 font-bold bg-red-50 px-2.5 py-1 rounded-md border border-red-200 hover:bg-red-100 transition-colors">
                            <X size={12} /> <span>Reject</span>
                          </button>
                          <button onClick={() => handleReward(msg.transparency, 10)} className="flex items-center space-x-1 text-[11px] text-gray-900 font-bold bg-green-50 px-2.5 py-1 rounded-md border border-green-200 hover:bg-green-100 transition-colors">
                            <Shield size={12} /> <span>Force Approve</span>
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {/* Human-in-the-Loop Pause */}
              {pendingApproval && (
                <div className="flex flex-col items-start py-4">
                  <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 shadow-sm w-full max-w-md relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-orange-400 to-yellow-400 animate-pulse"></div>
                    <h3 className="text-orange-800 font-bold flex items-center text-sm mb-2">
                      <AlertTriangle size={15} className="mr-1.5" /> Routing Approval Required
                    </h3>
                    <p className="text-xs text-orange-700/80 mb-3 font-medium leading-relaxed">
                      Routing to <b>{pendingApproval.transparency.model_target === 'LOCAL_SLM' ? 'Local SLM' : 'Cloud LLM'}</b>
                      <br/><span className="text-orange-600/60">"{pendingApproval.transparency.routing_reason}"</span>
                    </p>
                    <div className="flex space-x-2">
                      <button onClick={() => commitMessage(pendingApproval)} className="flex-1 bg-gray-900 hover:bg-black text-white font-bold text-xs py-2 rounded-lg shadow-sm transition-colors">Approve</button>
                      <button onClick={() => {
                         const overridden = JSON.parse(JSON.stringify(pendingApproval));
                         overridden.transparency.model_target = overridden.transparency.model_target === 'LOCAL_SLM' ? 'CLOUD_LLM' : 'LOCAL_SLM';
                         overridden.transparency.routing_reason = 'Human override: switched model target.';
                         overridden.transparency.estimated_savings_usd = overridden.transparency.model_target === 'LOCAL_SLM' ? 0.14 : 0.00;
                         commitMessage(overridden);
                      }} className="flex-1 bg-white border border-orange-200 text-orange-700 font-bold text-xs py-2 rounded-lg hover:bg-orange-50 transition-colors">Override</button>
                      <button onClick={() => { setPendingApproval(null); setIsProcessing(false); }} className="px-3 bg-white border border-gray-200 text-gray-500 font-bold text-xs py-2 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
                    </div>
                  </div>
                </div>
              )}

              {/* Processing indicator */}
              {isProcessing && (
                <div className="flex items-start">
                  <div className="px-4 py-3 rounded-2xl bg-white text-gray-500 rounded-bl-sm border border-gray-200 shadow-sm flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-[11px] font-semibold animate-pulse">{loadingText}</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className={`absolute w-full px-4 md:px-10 transition-all duration-500 flex justify-center ${
          messages.length === 0 ? 'bottom-1/2 translate-y-20' : 'bottom-0 pb-6 pt-3 bg-gradient-to-t from-gray-50 via-gray-50/95 to-transparent'
        }`}>
          <form onSubmit={handleSend} className="w-full max-w-3xl relative flex items-center bg-white border border-gray-300 rounded-2xl shadow-lg focus-within:border-gray-500 focus-within:ring-4 focus-within:ring-gray-500/10 transition-all">
            <input
              ref={inputRef}
              type="text" value={input} onChange={(e) => setInput(e.target.value)}
              placeholder="Paste incident log or describe an infrastructure issue..."
              className="w-full bg-transparent text-gray-900 px-5 py-3.5 outline-none font-medium text-sm"
              disabled={isProcessing}
            />
            <button type="submit" disabled={!input.trim() || isProcessing} className="absolute right-2.5 p-2 bg-gray-900 hover:bg-black disabled:bg-gray-100 disabled:text-gray-400 rounded-xl text-white shadow-sm transition-colors">
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>

      {/* ========== SETTINGS MODAL ========== */}
      {isSettingsOpen && (
        <div className="fixed inset-0 bg-gray-900/30 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setIsSettingsOpen(false)}>
          <div className="bg-white border border-gray-200 w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-5" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center">
              <h2 className="text-base font-bold text-gray-900 flex items-center"><ShieldAlert size={16} className="mr-2 text-gray-500"/> Agent Control</h2>
              <button onClick={() => setIsSettingsOpen(false)} className="text-gray-400 hover:text-gray-700 p-1"><X size={18} /></button>
            </div>
            <p className="text-xs text-gray-500 leading-relaxed">Controls how the routing agent handles decisions. "Ask Everytime" pauses at Phase 2 and shows you the proposed route before executing.</p>
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl border border-gray-200">
              {['Full', 'Ask Everytime', 'Auto'].map((mode) => (
                <button key={mode} onClick={() => setAgentControl(mode)} className={`flex-1 text-sm py-2 rounded-lg transition-all ${agentControl === mode ? 'bg-white text-gray-900 font-bold shadow' : 'text-gray-500 font-medium hover:text-gray-700'}`}>
                  {mode}
                </button>
              ))}
            </div>
            <div className="text-[11px] text-gray-400 bg-gray-50 rounded-lg p-3 border border-gray-100">
              <b>Full:</b> No pipeline pause, execute end-to-end.<br/>
              <b>Ask Everytime:</b> Pause at routing, require human approval.<br/>
              <b>Auto:</b> Q-Learning agent decides autonomously.
            </div>
          </div>
        </div>
      )}

      {/* ========== Q-TABLE MODAL ========== */}
      {isQTableOpen && (
        <div className="fixed inset-0 bg-gray-900/30 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setIsQTableOpen(false)}>
          <div className="bg-white border border-gray-200 w-full max-w-3xl rounded-2xl shadow-2xl flex flex-col overflow-hidden max-h-[75vh]" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center shrink-0">
              <h2 className="font-bold text-gray-800 flex items-center text-sm"><BrainCircuit size={16} className="mr-2 text-gray-900"/> Q-Learning Heatmap</h2>
              <div className="flex items-center space-x-2">
                <button onClick={fetchQTable} className="text-gray-400 hover:text-gray-900 p-1" title="Refresh"><RefreshCw size={16} /></button>
                <button onClick={() => setIsQTableOpen(false)} className="text-gray-400 hover:text-gray-700 p-1"><X size={16} /></button>
              </div>
            </div>
            <div className="p-6 overflow-y-auto">
              {qTable && Object.keys(qTable).length > 0 ? (
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(qTable).map(([sev, complexities]) => (
                    <div key={sev} className="bg-gray-50 border border-gray-200 rounded-xl p-3">
                      <div className="text-[11px] font-bold text-gray-500 mb-1.5 uppercase relative group cursor-help w-max">
                        Severity {sev}
                        <div className="absolute hidden group-hover:block bottom-full left-0 mb-1 w-48 bg-gray-800 text-white text-[10px] p-2 rounded-lg z-50 font-normal shadow-lg normal-case tracking-normal">
                          {(() => {
                            const s = parseInt(sev);
                            if (s <= 2) return "Informational / Minor Alert";
                            if (s <= 4) return "Low Priority Warning";
                            if (s <= 7) return "Moderate System Degradation";
                            if (s <= 9) return "High Impact Outage";
                            return "Critical System Failure";
                          })()}
                        </div>
                      </div>
                      {Object.entries(complexities).map(([comp, values]) => {
                        const slmQ = values[0], llmQ = values[1];
                        const pref = slmQ >= llmQ ? 'slm' : 'llm';
                        return (
                          <div key={comp} className="flex justify-between items-center text-sm border-t border-gray-100 py-1 mt-0.5">
                            <span className="text-gray-500 text-xs">Complexity {comp}</span>
                            <div className="flex space-x-1.5 text-[11px]">
                              <span className={`px-1.5 py-0.5 rounded ${pref === 'slm' ? 'bg-green-100 text-gray-900 font-bold' : 'text-gray-400'}`}>SLM: {slmQ.toFixed(1)}</span>
                              <span className={`px-1.5 py-0.5 rounded ${pref === 'llm' ? 'bg-indigo-100 text-indigo-700 font-bold' : 'text-gray-400'}`}>LLM: {llmQ.toFixed(1)}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <BrainCircuit size={32} className="mx-auto text-gray-300 mb-3" />
                  <p className="text-sm text-gray-500 font-medium">Q-Table is empty (all zeros)</p>
                  <p className="text-xs text-gray-400 mt-1">Use Reject/Approve on risky scripts to train the agent</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========== DIFF MODAL ========== */}
      {diffModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4" onClick={() => setDiffModal(null)}>
          <div className="bg-white border border-gray-200 w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-3 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
              <h2 className="font-bold text-gray-800 flex items-center text-sm"><GitCompare size={16} className="mr-2 text-gray-900"/> Semantic Compression Diff</h2>
              <button onClick={() => setDiffModal(null)} className="text-gray-400 hover:text-gray-700 p-1"><X size={16} /></button>
            </div>
            <div className="flex min-h-[35vh] max-h-[55vh]">
              <div className="w-1/2 p-4 border-r border-gray-200 overflow-y-auto bg-red-50/20">
                <h4 className="text-[11px] font-bold text-red-600 mb-2 uppercase flex items-center justify-between">
                  <span>Original</span><span className="font-mono">{diffModal.original_chars} chars</span>
                </h4>
                <div className="text-[13px] text-gray-700 font-mono whitespace-pre-wrap leading-relaxed">{diffModal.original_prompt}</div>
              </div>
              <div className="w-1/2 p-4 overflow-y-auto bg-green-50/20">
                <h4 className="text-[11px] font-bold text-gray-900 mb-2 uppercase flex items-center justify-between">
                  <span>Compressed</span><span className="font-mono">{diffModal.compressed_chars} chars</span>
                </h4>
                <div className="text-[13px] text-gray-700 font-mono whitespace-pre-wrap leading-relaxed">{diffModal.compressed_prompt}</div>
              </div>
            </div>
            <div className="px-5 py-2.5 border-t border-gray-100 bg-gray-50 text-center">
              <span className="text-[11px] font-bold text-gray-900">{diffModal.reduction_percent}% context reduction</span>
              <span className="text-[11px] text-gray-400 mx-2">|</span>
              <span className="text-[11px] text-gray-500">{diffModal.original_chars - diffModal.compressed_chars} characters pruned</span>
            </div>
          </div>
        </div>
      )}

      {/* ========== TRANSPARENCY DRAWER ========== */}
      <div className={`fixed inset-y-0 right-0 w-[380px] bg-white border-l border-gray-200 shadow-2xl transform transition-transform duration-300 z-40 flex flex-col ${activeTransparency ? 'translate-x-0' : 'translate-x-full'}`}>
        {activeTransparency && (
          <>
            <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center shrink-0">
              <h2 className="text-sm font-bold text-gray-900 flex items-center"><Activity size={16} className="mr-2 text-gray-900" /> Transparency Trace</h2>
              <button onClick={() => setActiveTransparency(null)} className="text-gray-400 hover:bg-gray-100 p-1 rounded-lg"><X size={16} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-5 space-y-6 bg-gray-50/50">
              
              {/* Interactive Flowchart */}
              <div>
                <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-3">Pipeline Execution</h3>
                <div className="flex flex-col space-y-1.5 items-center text-[13px] font-semibold text-gray-700">
                  <div className="px-3 py-1.5 border border-gray-200 rounded-lg bg-white w-full text-center shadow-sm">Prompt Received</div>
                  <ArrowRight size={14} className="text-gray-300 rotate-90" />
                  <button onClick={() => setDiffModal(activeTransparency)} className="px-3 py-1.5 border border-blue-200 rounded-lg bg-blue-50 w-full text-center text-blue-700 shadow-sm hover:ring-2 hover:ring-blue-300 cursor-pointer transition-all">
                    Semantic Compression
                    <span className="block text-[10px] font-normal text-blue-500 mt-0.5">Click to view diff</span>
                  </button>
                  <ArrowRight size={14} className="text-gray-300 rotate-90" />
                  <div className="px-3 py-1.5 border border-purple-200 rounded-lg bg-purple-50 w-full text-center text-purple-700 shadow-sm relative group cursor-help">
                    Zero-Shot Router
                    <div className="absolute hidden group-hover:block top-full left-0 mt-1 w-full bg-gray-800 text-white text-[11px] p-2 rounded-lg z-50 font-normal shadow-lg">{activeTransparency.routing_reason}</div>
                  </div>
                  <ArrowRight size={14} className="text-gray-300 rotate-90" />
                  <div className="px-3 py-1.5 border border-green-200 rounded-lg bg-green-50 w-full text-center text-gray-900 shadow-sm">
                    {activeTransparency.model_target === 'LOCAL_SLM' ? 'Local SLM' : 'Cloud LLM'} Executed
                  </div>
                  <ArrowRight size={14} className="text-gray-300 rotate-90" />
                  <div className={`px-3 py-1.5 border rounded-lg w-full text-center shadow-sm relative group cursor-help ${activeTransparency.is_safe ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-red-200 bg-red-50 text-red-700'}`}>
                    Risk Assessor: {activeTransparency.is_safe ? 'Safe' : 'Blocked'}
                    {!activeTransparency.is_safe && (
                      <div className="absolute hidden group-hover:block bottom-full left-0 mb-1 w-full bg-gray-800 text-white text-[11px] p-2 rounded-lg z-50 font-normal shadow-lg">
                        Pattern matched: {activeTransparency.risk_reason}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Latency Waterfall -- real phase timings */}
              <div>
                <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Latency Waterfall</h3>
                <div className="bg-white rounded-xl border border-gray-200 p-3 shadow-sm space-y-2.5">
                  {(() => {
                    const tOpt = activeTransparency.t_optimize_ms || 0;
                    const tRoute = activeTransparency.t_route_ms || 0;
                    const tExec = activeTransparency.t_execute_ms || Math.max(0, activeTransparency.latency_ms - tOpt - tRoute);
                    const total = Math.max(tOpt + tRoute + tExec, 1);
                    return [
                      { label: "Compression", ms: tOpt, color: "bg-blue-400", pct: (tOpt / total * 100) },
                      { label: "Routing", ms: tRoute, color: "bg-purple-400", pct: (tRoute / total * 100) },
                      { label: "Execution", ms: tExec, color: "bg-green-500", pct: (tExec / total * 100) },
                    ].map(p => (
                      <div key={p.label}>
                        <div className="flex justify-between text-[10px] text-gray-500 mb-0.5">
                          <span className="flex items-center"><Clock size={10} className="mr-1" />{p.label}</span>
                          <span className="font-mono font-bold">{p.ms}ms</span>
                        </div>
                        <div className="overflow-hidden h-1 rounded bg-gray-100">
                          <div style={{ width: `${Math.max(p.pct, 2)}%` }} className={`h-full rounded ${p.color} transition-all duration-500`}></div>
                        </div>
                      </div>
                    ));
                  })()}
                  <div className="flex justify-between text-[10px] text-gray-600 pt-1 border-t border-gray-100 font-bold">
                    <span>Total</span><span className="font-mono">{activeTransparency.latency_ms}ms</span>
                  </div>
                </div>
              </div>

              {/* Metrics */}
              <div>
                <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Diagnostics</h3>
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm text-sm">
                  <button onClick={() => setDiffModal(activeTransparency)} className="w-full p-3 border-b border-gray-100 flex justify-between items-center hover:bg-gray-50 transition-colors">
                    <span className="font-medium text-gray-500">Context Reduction</span>
                    <span className="font-bold text-gray-900 underline decoration-green-200 decoration-2 underline-offset-2">{activeTransparency.reduction_percent}%</span>
                  </button>
                  <div className="p-3 border-b border-gray-100 flex justify-between items-center">
                    <span className="font-medium text-gray-500">Risk Score</span>
                    <span className={`font-bold ${activeTransparency.risk_score > 50 ? 'text-red-600' : 'text-gray-700'}`}>{activeTransparency.risk_score}/100</span>
                  </div>
                  <div className="p-3 border-b border-gray-100 flex justify-between items-center">
                    <span className="font-medium text-gray-500">Severity / Complexity</span>
                    <span className="font-bold text-gray-700">{activeTransparency.severity} / {activeTransparency.complexity}</span>
                  </div>
                  <div className="p-3 bg-green-50/50 flex justify-between items-center">
                    <span className="font-semibold text-gray-900">Cost Saved</span>
                    <span className="font-black text-gray-900">+${activeTransparency.estimated_savings_usd.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              
            </div>
          </>
        )}
      </div>
      {/* ========== MODEL CONFIG PANEL ========== */}
      {activeModelPanel && (() => {
        const isLLM = activeModelPanel === 'llm';
        const config = isLLM ? llmConfig : slmConfig;
        const setConfig = isLLM ? setLlmConfig : setSlmConfig;
        const modelStatus = isLLM ? status.llm : status.slm;
        return (
          <div className="fixed inset-0 bg-gray-900/30 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setActiveModelPanel(null)}>
            <div className="bg-white border border-gray-200 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]" onClick={e => e.stopPropagation()}>
              
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                <div className="flex items-center space-x-3">
                  <div>
                    <h2 className="font-bold text-gray-900 text-sm uppercase tracking-wider">{isLLM ? 'Cloud LLM' : 'Local SLM'} Configuration</h2>
                    <div className="flex items-center space-x-1.5 mt-1">
                      <div className={`w-1.5 h-1.5 rounded-full ${statusDot(modelStatus)}`}></div>
                      <span className="text-[10px] text-gray-500 font-medium">{modelStatus}</span>
                    </div>
                  </div>
                </div>
                <button onClick={() => setActiveModelPanel(null)} className="text-gray-400 hover:text-gray-900 p-1"><X size={16} /></button>
              </div>
              
              {/* Body */}
              <div className="p-6 space-y-5 overflow-y-auto">
                
                {/* Model Name */}
                <div>
                  <label className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5 block">Model Name</label>
                  <input 
                    type="text" 
                    value={config.name} 
                    onChange={e => setConfig(prev => ({ ...prev, name: e.target.value }))}
                    onBlur={() => {
                      fetch('http://localhost:8000/api/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ model_type: activeModelPanel, name: config.name })
                      }).catch(() => {});
                    }}
                    className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm text-gray-900 font-medium focus:border-gray-500 focus:ring-2 focus:ring-gray-500/20 outline-none transition-all"
                  />
                </div>
                
                {/* API Key / Endpoint */}
                <div>
                  <label className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1.5 block">
                    {isLLM ? 'API Key' : 'Endpoint URL'}
                  </label>
                  <div className="relative">
                    <input 
                      type={isLLM ? 'password' : 'text'}
                      value={config.apiKey} 
                      onChange={e => {
                        const val = e.target.value;
                        setConfig(prev => ({ ...prev, apiKey: val }));
                      }}
                      onBlur={() => {
                        // Save to backend when user finishes editing
                        const ts = new Date().toLocaleTimeString();
                        const payload = { model_type: activeModelPanel, name: config.name };
                        if (isLLM) payload.api_key = config.apiKey;
                        else payload.endpoint = config.apiKey;
                        fetch('http://localhost:8000/api/config', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify(payload)
                        }).then(() => {
                          setConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-29), { ts, type: 'info', msg: `${isLLM ? 'API key' : 'Endpoint'} saved to backend` }] }));
                        }).catch(() => {
                          setConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-29), { ts, type: 'err', msg: 'Failed to save config' }] }));
                        });
                      }}
                      placeholder={isLLM ? 'AIzaSy... or sk-...' : 'http://localhost:11434'}
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm text-gray-900 font-mono focus:border-gray-500 focus:ring-2 focus:ring-gray-500/20 outline-none transition-all pr-24"
                    />
                    <button 
                      onClick={async () => {
                        const ts = new Date().toLocaleTimeString();
                        setConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-29), { ts, type: 'info', msg: 'Testing connection...' }] }));
                        
                        // First save config to backend
                        const savePayload = { model_type: activeModelPanel, name: config.name };
                        if (isLLM) savePayload.api_key = config.apiKey;
                        else savePayload.endpoint = config.apiKey;
                        await fetch('http://localhost:8000/api/config', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify(savePayload)
                        }).catch(() => {});
                        
                        // Then test real connection
                        try {
                          const testPayload = { model_type: activeModelPanel };
                          if (isLLM) testPayload.api_key = config.apiKey;
                          else testPayload.endpoint = config.apiKey;
                          
                          const resp = await fetch('http://localhost:8000/api/test-connection', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(testPayload)
                          });
                          const result = await resp.json();
                          const ts2 = new Date().toLocaleTimeString();
                          setConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-29), { 
                            ts: ts2, 
                            type: result.status === 'online' ? 'ok' : 'err', 
                            msg: result.message 
                          }] }));
                        } catch {
                          const ts2 = new Date().toLocaleTimeString();
                          setConfig(prev => ({ ...prev, logs: [...prev.logs.slice(-29), { ts: ts2, type: 'err', msg: 'Backend unreachable' }] }));
                        }
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-[11px] font-bold text-gray-900 bg-gray-100 hover:bg-gray-200 border border-gray-200 px-3 py-1 rounded-lg transition-colors"
                    >
                      Test
                    </button>
                  </div>
                </div>
                
                {/* Connection Logs */}
                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Connection Logs</label>
                    <button 
                      onClick={() => setConfig(prev => ({ ...prev, logs: [] }))} 
                      className="text-[10px] text-gray-400 hover:text-red-500 font-medium transition-colors"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="bg-gray-900 rounded-xl p-3 h-44 overflow-y-auto font-mono text-[11px] leading-relaxed">
                    {config.logs.length === 0 ? (
                      <span className="text-gray-600">No logs yet. Connection events will appear here.</span>
                    ) : (
                      config.logs.map((log, i) => (
                        <div key={i} className="flex items-start space-x-2">
                          <span className="text-gray-600 shrink-0">{log.ts}</span>
                          <span className={
                            log.type === 'ok' ? 'text-green-400' : 
                            log.type === 'err' ? 'text-red-400' : 
                            'text-blue-400'
                          }>
                            {log.type === 'ok' ? '[OK]' : log.type === 'err' ? '[ERR]' : '[INFO]'}
                          </span>
                          <span className="text-gray-300">{log.msg}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

    </div>
  );
}
