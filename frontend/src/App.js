import React, { useState, useCallback, useEffect } from 'react';
import ChipVisualization from './components/ChipVisualization';
import FileUpload from './components/FileUpload';
import ProcessManager from './components/ProcessManager';
import HierarchyView from './components/HierarchyView';
import './styles/App.css';

function App() {
  const [designData, setDesignData] = useState(null);
  const [parsingStatus, setParsingStatus] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('visualization');
  const [moduleData, setModuleData] = useState(null);
  const [isBackendAvailable, setIsBackendAvailable] = useState(false);

  const handleFilesUploaded = useCallback((data) => {
    setDesignData(data);
    setParsingStatus('success');
    if (data.stdout) {
      addLog('success', data.stdout);
    }
  }, []);

  const handleParsingError = useCallback((error) => {
    setParsingStatus('error');
    addLog('error', error);
  }, []);

  const addLog = useCallback((type, message) => {
    setLogs(prev => [...prev, { 
      type, 
      message, 
      timestamp: new Date().toISOString() 
    }]);
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // 检查后端是否可用
  const checkBackend = async () => {
    try {
      const response = await fetch('/api/health'); // 假设有健康检查端点
      setIsBackendAvailable(response.ok);
    } catch {
      setIsBackendAvailable(false);
    }
  };

  // 加载测试数据
  const loadTestData = async () => {
    try {
      const response = await fetch('/gpio_demo_design.json');
      const data = await response.json();
      setModuleData(data);
    } catch (error) {
      console.error('Failed to load test data:', error);
    }
  };

  useEffect(() => {
    checkBackend().then(() => {
      if (!isBackendAvailable) {
        // 后端不可用时加载测试数据
        loadTestData();
      }
    });
  }, [isBackendAvailable]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Verilog Chip Visualizer</h1>
        <ProcessManager onLog={addLog} />
      </header>
      
      <div className="app-content">
        <div className="sidebar">
          <FileUpload 
            onFilesUploaded={handleFilesUploaded}
            onError={handleParsingError}
            onStatusChange={setParsingStatus}
          />
          
          {designData && (
            <div className="design-info">
              <h3>Design Information</h3>
              <div className="info-tabs">
                <button 
                  className={activeTab === 'visualization' ? 'active' : ''}
                  onClick={() => setActiveTab('visualization')}
                >
                  Visualization
                </button>
                <button 
                  className={activeTab === 'hierarchy' ? 'active' : ''}
                  onClick={() => setActiveTab('hierarchy')}
                >
                  Hierarchy
                </button>
              </div>
            </div>
          )}
          
          <div className="logs-section">
            <div className="logs-header">
              <h3>Logs</h3>
              <button onClick={clearLogs} className="clear-logs-btn">
                Clear
              </button>
            </div>
            <div className="logs">
              {logs.slice(-50).map((log, index) => (
                <div key={index} className={`log-entry log-${log.type}`}>
                  <span className="timestamp">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="message">{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="main-content">
          {parsingStatus === 'loading' && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Parsing Verilog files...</p>
            </div>
          )}
          
          {parsingStatus === 'error' && (
            <div className="error">
              <h2>❌ Failed to parse Verilog files</h2>
              <p>Check logs for details.</p>
            </div>
          )}
          
          {designData && activeTab === 'visualization' && (
            <ChipVisualization data={designData} />
          )}
          
          {designData && activeTab === 'hierarchy' && (
            <HierarchyView data={designData} />
          )}
          
          {!designData && parsingStatus === 'idle' && (
            <div className="welcome">
              <h2>🔧 Welcome to Verilog Chip Visualizer</h2>
              <p>Upload your Verilog/SystemVerilog files or load demo data to get started.</p>
              <div className="features">
                <div className="feature">
                  <h3>📁 File Upload</h3>
                  <p>Support for .v and .sv files</p>
                </div>
                <div className="feature">
                  <h3>🎯 Interactive Visualization</h3>
                  <p>Drag, zoom, and explore your design</p>
                </div>
                <div className="feature">
                  <h3>🌳 Hierarchy View</h3>
                  <p>Browse module hierarchy and connections</p>
                </div>
              </div>
            </div>
          )}

          {!isBackendAvailable && (
            <div className="test-data-banner">
              Using test data (backend not available)
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;