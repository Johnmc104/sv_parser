import React, { useState, useCallback } from 'react';
import axios from 'axios';

function FileUpload({ onFilesUploaded, onError, onStatusChange }) {
  const [files, setFiles] = useState([]);
  const [topModule, setTopModule] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleFileChange = useCallback((event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
  }, []);

  const handleUpload = useCallback(async () => {
    if (files.length === 0) {
      onError('Please select at least one Verilog file');
      return;
    }

    setUploading(true);
    onStatusChange('loading');

    const formData = new FormData();
    files.forEach(file => {
      formData.append('verilog_files', file);
    });
    
    if (topModule) {
      formData.append('top_module', topModule);
    }

    try {
      const response = await axios.post(
        'http://localhost:5000/api/parse-verilog', 
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      if (response.data.success) {
        onFilesUploaded(response.data);
      } else {
        onError(response.data.error || 'Unknown error occurred');
      }
    } catch (error) {
      onError(error.response?.data?.error || error.message);
    } finally {
      setUploading(false);
    }
  }, [files, topModule, onFilesUploaded, onError, onStatusChange]);

  const loadDemoData = useCallback(async () => {
    setUploading(true);
    onStatusChange('loading');

    try {
      // 加载本地demo数据
      const response = await fetch('/gpio_demo_design.json');
      const demoData = await response.json();
      
      // 转换为前端期望的格式
      const formattedData = {
        success: true,
        data: demoData.data || demoData,
        flowData: demoData.data?.flow_data || demoData.flow_data,
        designInfo: demoData.data?.design_info || demoData.design_info,
        hierarchy: demoData.data?.hierarchy || demoData.hierarchy,
        stats: demoData.data?.stats || demoData.stats,
        validation: demoData.data?.validation || demoData.validation,
        stdout: 'Demo data loaded successfully'
      };
      
      onFilesUploaded(formattedData);
    } catch (error) {
      onError(`Failed to load demo data: ${error.message}`);
    } finally {
      setUploading(false);
    }
  }, [onFilesUploaded, onError, onStatusChange]);

  return (
    <div className="file-upload">
      <h3>Upload Verilog Files</h3>
      
      <div className="upload-section">
        <input
          type="file"
          multiple
          accept=".v,.sv"
          onChange={handleFileChange}
          disabled={uploading}
        />
        
        <div className="top-module-input">
          <label htmlFor="top-module">Top Module (optional):</label>
          <input
            id="top-module"
            type="text"
            value={topModule}
            onChange={(e) => setTopModule(e.target.value)}
            placeholder="Enter top module name"
            disabled={uploading}
          />
        </div>
        
        <button 
          onClick={handleUpload} 
          disabled={uploading || files.length === 0}
          className="upload-btn"
        >
          {uploading ? 'Parsing...' : 'Parse & Visualize'}
        </button>

        <button 
          onClick={loadDemoData} 
          disabled={uploading}
          className="demo-btn"
        >
          {uploading ? 'Loading...' : 'Load Demo Data'}
        </button>
      </div>
      
      {files.length > 0 && (
        <div className="selected-files">
          <h4>Selected Files:</h4>
          <ul>
            {files.map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default FileUpload;