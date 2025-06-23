import React, { useState, useCallback, useEffect } from 'react';
import SchematicViewer from './components/SchematicViewer';
import HierarchyNavigator from './components/HierarchyNavigator';
import './styles/App.css';

function App() {
  const [designData, setDesignData] = useState(null);
  const [logs, setLogs] = useState([]);
  const [currentView, setCurrentView] = useState(null);
  const [showLogs, setShowLogs] = useState(false);
  const [selectedNet, setSelectedNet] = useState(null);

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

  // 加载设计数据
  const loadDesignData = async () => {
    try {
      const response = await fetch('/gpio_demo_design.json');
      const data = await response.json();
      setDesignData(data);
      setCurrentView(data.design_metadata.top_module);
      addLog('success', 'Design loaded successfully');
    } catch (error) {
      addLog('error', `Failed to load design: ${error.message}`);
    }
  };

  // 处理层次导航
  const handleNavigateToModule = useCallback((moduleName) => {
    setCurrentView(moduleName);
    addLog('info', `Navigated to module: ${moduleName}`);
  }, [addLog]);

  // 处理信号选择
  const handleNetSelect = useCallback((netId) => {
    setSelectedNet(netId);
    if (netId) {
      addLog('info', `Selected signal: ${netId}`);
    }
  }, [addLog]);

  useEffect(() => {
    loadDesignData();
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔧 Verilog Schematic Viewer</h1>
        <div className="header-controls">
          <button onClick={loadDesignData} className="reload-btn">
            Reload Design
          </button>
          <button 
            onClick={() => setShowLogs(!showLogs)}
            className={`logs-toggle-btn ${showLogs ? 'active' : ''}`}
          >
            {showLogs ? 'Hide Logs' : 'Show Logs'} ({logs.length})
          </button>
        </div>
      </header>
      
      <div className="app-content">
        <div className="sidebar">
          {designData && (
            <HierarchyNavigator 
              designData={designData}
              currentView={currentView}
              onNavigate={handleNavigateToModule}
            />
          )}
          
          {showLogs && (
            <div className="logs-section">
              <div className="logs-header">
                <h3>System Logs</h3>
                <button onClick={clearLogs} className="clear-logs-btn">
                  Clear
                </button>
              </div>
              <div className="logs-content">
                {logs.slice(-30).map((log, index) => (
                  <div key={index} className={`log-entry log-${log.type}`}>
                    <span className="timestamp">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="message">{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="main-content">
          {designData && currentView ? (
            <SchematicViewer 
              designData={designData}
              currentModule={currentView}
              selectedNet={selectedNet}
              onNetSelect={handleNetSelect}
              onNavigate={handleNavigateToModule}
            />
          ) : (
            <div className="loading-screen">
              <div className="spinner"></div>
              <h2>Loading Design...</h2>
              <p>Parsing Verilog hierarchy and signal connections</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;