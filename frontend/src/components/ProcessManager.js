// filepath: frontend/src/components/ProcessManager.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ProcessManager({ onLog }) {
  const [backendStatus, setBackendStatus] = useState('unknown');
  const [lastCheck, setLastCheck] = useState(null);

  const checkBackendHealth = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/health', {
        timeout: 3000
      });
      
      if (response.data.status === 'ok') {
        setBackendStatus('running');
        onLog('success', 'Backend service is running');
      } else {
        setBackendStatus('error');
        onLog('warning', 'Backend service returned unexpected status');
      }
    } catch (error) {
      setBackendStatus('stopped');
      onLog('error', 'Backend service is not responding');
    }
    
    setLastCheck(new Date());
  };

  const startBackend = async () => {
    onLog('info', 'Starting backend service...');
    try {
      // 这里可以调用启动脚本或API
      // 暂时只是模拟
      setTimeout(() => {
        checkBackendHealth();
      }, 2000);
    } catch (error) {
      onLog('error', `Failed to start backend: ${error.message}`);
    }
  };

  const stopBackend = async () => {
    onLog('info', 'Stopping backend service...');
    try {
      // 这里可以调用停止脚本或API
      setBackendStatus('stopped');
      onLog('info', 'Backend service stopped');
    } catch (error) {
      onLog('error', `Failed to stop backend: ${error.message}`);
    }
  };

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 10000); // 每10秒检查一次
    
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    switch (backendStatus) {
      case 'running': return '#4CAF50';
      case 'stopped': return '#f44336';
      case 'error': return '#FF9800';
      default: return '#9E9E9E';
    }
  };

  return (
    <div className="process-manager">
      <div className="status-indicator">
        <div 
          className="status-dot" 
          style={{ backgroundColor: getStatusColor() }}
        ></div>
        <span className="status-text">
          Backend: {backendStatus}
        </span>
        
        {lastCheck && (
          <span className="last-check">
            (checked: {lastCheck.toLocaleTimeString()})
          </span>
        )}
      </div>
      
      <div className="control-buttons">
        <button 
          onClick={checkBackendHealth}
          className="check-btn"
        >
          Check
        </button>
        
        {backendStatus === 'stopped' && (
          <button 
            onClick={startBackend}
            className="start-btn"
          >
            Start Backend
          </button>
        )}
        
        {backendStatus === 'running' && (
          <button 
            onClick={stopBackend}
            className="stop-btn"
          >
            Stop Backend
          </button>
        )}
      </div>
    </div>
  );
}

export default ProcessManager;