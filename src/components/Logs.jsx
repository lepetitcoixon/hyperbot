import React, { useState, useEffect, useCallback, useRef } from 'react';
import { RefreshCw, Play, Pause, ListFilter, FileText, AlertTriangle, Loader2 } from 'lucide-react';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [logFileName, setLogFileName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [numberOfLines, setNumberOfLines] = useState(100);
  const [inputNumberOfLines, setInputNumberOfLines] = useState(100);

  const logsContainerRef = useRef(null);

  const fetchLogs = useCallback(async (linesToFetch) => {
    setIsLoading(true);
    // Don't clear previous error immediately, only on success or new error
    // setError(null);
    try {
      const response = await fetch(`/api/logs?lines=${linesToFetch}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to fetch logs. Server response not ok." }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setLogs(data.lines || []);
      setLogFileName(data.log_file || 'N/A');
      setError(null); // Clear error on successful fetch
    } catch (e) {
      console.error("Fetch logs error:", e);
      setError(e.message || "Failed to fetch logs. Is the API server running?");
      // Keep previous logs on error, or clear them:
      // setLogs([]);
      // setLogFileName('');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs(numberOfLines); // Initial fetch

    let intervalId = null;
    if (autoRefreshEnabled) {
      intervalId = setInterval(() => {
        fetchLogs(numberOfLines);
      }, 7000); // Refresh every 7 seconds
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [fetchLogs, autoRefreshEnabled, numberOfLines]);

  // Scroll to bottom when logs update, if user hasn't scrolled up
  useEffect(() => {
    if (logsContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current;
      // Check if user is near the bottom before auto-scrolling
      if (scrollHeight - scrollTop <= clientHeight + 20) { // 20px tolerance
        logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
      }
    }
  }, [logs]);


  const handleRefresh = () => {
    setNumberOfLines(inputNumberOfLines); // Apply new number of lines
    fetchLogs(inputNumberOfLines);
  };

  const handleToggleAutoRefresh = () => {
    setAutoRefreshEnabled(prev => !prev);
  };

  return (
    <div className="space-y-6 animate-fade-in h-full flex flex-col">
      {/* Header and Controls */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-2xl font-bold text-white">Bot Logs</h2>
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <label htmlFor="linesInput" className="text-sm text-gray-300">Lines:</label>
              <input
                type="number"
                id="linesInput"
                value={inputNumberOfLines}
                onChange={(e) => setInputNumberOfLines(Math.max(1, parseInt(e.target.value, 10) || 1))}
                className="w-20 bg-dark-700 border border-dark-600 rounded-md px-2 py-1 text-white focus:outline-none focus:border-primary-500"
              />
            </div>
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="btn-secondary flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={handleToggleAutoRefresh}
              className={`btn-secondary flex items-center gap-2 ${autoRefreshEnabled ? 'bg-success-600 hover:bg-success-700' : 'bg-danger-600 hover:bg-danger-700'}`}
            >
              {autoRefreshEnabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              {autoRefreshEnabled ? 'Auto (ON)' : 'Auto (OFF)'}
            </button>
          </div>
        </div>
        {logFileName && <p className="text-xs text-gray-400 mt-2">Current log file: <FileText size={12} className="inline mr-1"/>{logFileName}</p>}
      </div>

      {/* Error Display */}
      {error && !isLoading && ( // Show error only if not currently loading (to avoid showing old error during refresh)
        <div className="card bg-danger-900/50 border border-danger-600 text-danger-300 p-3 animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} />
            <span className="font-medium">Error:</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Loading Indicator Full Block */}
      {isLoading && logs.length === 0 && (
         <div className="flex-grow flex items-center justify-center text-gray-400">
            <Loader2 size={32} className="animate-spin mr-3" />
            Loading logs...
        </div>
      )}

      {/* Log Display Area */}
      {!isLoading && logs.length === 0 && !error && (
        <div className="flex-grow flex items-center justify-center text-gray-400">
            No logs found or an error occurred.
        </div>
      )}

      {logs.length > 0 && (
        <div
          ref={logsContainerRef}
          className="flex-grow card bg-dark-900 text-gray-200 p-4 overflow-y-auto font-mono text-xs custom-scrollbar"
          style={{ maxHeight: 'calc(100vh - 250px)' }} // Adjust height as needed
        >
          {logs.map((line, index) => (
            <div key={index} className="whitespace-pre-wrap leading-relaxed py-0.5 hover:bg-dark-800/60 px-1 rounded-sm">
              {line}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Logs;