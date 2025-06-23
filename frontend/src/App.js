import React, { useState, useCallback, useEffect } from 'react';
import SchematicViewer from './components/SchematicViewer';
import HierarchyNavigator from './components/HierarchyNavigator';

// 导入所有样式文件
import 'reactflow/dist/style.css'; // ReactFlow基础样式 - 必须放在最前面
import './styles/App.css';
import './styles/Header.css';
import './styles/HierarchyNavigator.css';
import './styles/SchematicViewer.css';
import './styles/ModuleSymbol.css';
import './styles/Logs.css';
import './styles/SignalWire.css';

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
      addLog('info', 'Loading design data...');
      const response = await fetch('/gpio_demo_design.json');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Loaded design data:', data);
      
      setDesignData(data);
      setCurrentView(data.design_metadata?.top_module || 'gpio_demo_top');
      addLog('success', 'Design loaded successfully');
    } catch (error) {
      console.error('Failed to load design:', error);
      addLog('error', `Failed to load design: ${error.message}`);
      
      // 创建一个最小的测试数据
      const testData = createTestData();
      setDesignData(testData);
      setCurrentView('test_module');
      addLog('info', 'Using test data instead');
    }
  };

  // 创建测试数据
  const createTestData = () => {
    return {
      design_metadata: {
        name: "test_design",
        top_module: "test_module"
      },
      module_library: {
        test_module: {
          module_type: "top_level",
          ports: [
            { name: "clk", direction: "input", width: 1, type: "clock" },
            { name: "rst_n", direction: "input", width: 1, type: "reset" },
            { name: "data_out", direction: "output", width: 8, type: "data" }
          ],
          internal_structure: {
            instances: [
              { name: "u_test1", module_type: "test_sub" },
              { name: "u_test2", module_type: "test_sub" }
            ]
          }
        },
        test_sub: {
          module_type: "utility",
          ports: [
            { name: "clk", direction: "input", width: 1, type: "clock" },
            { name: "data", direction: "output", width: 4, type: "data" }
          ]
        }
      },
      signal_netlist: {
        nets: {}
      }
    };
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
            🔄 Reload Design
          </button>
          <button 
            onClick={() => setShowLogs(!showLogs)}
            className={`logs-toggle-btn ${showLogs ? 'active' : ''}`}
          >
            {showLogs ? '📋 Hide Logs' : '📋 Show Logs'} ({logs.length})
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
                  🗑️ Clear
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