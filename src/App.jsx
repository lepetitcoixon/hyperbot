import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import Positions from './components/Positions';
import Logs from './components/Logs';
import Settings from './components/Settings';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [botStatus, setBotStatus] = useState('LOADING_STATUS'); // 'LOADING_STATUS', 'RUNNING', 'STOPPED', 'ERROR_STATUS'
  const [botData, setBotData] = useState(null);
  const [error, setError] = useState(null);

  const fetchBotStatus = useCallback(async () => {
    setBotStatus('LOADING_STATUS');
    setError(null);
    try {
      const response = await fetch('/api/status');
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch bot status, server response not ok.' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setBotData(data);
      setBotStatus(data.bot_running ? 'RUNNING' : 'STOPPED');
    } catch (e) {
      console.error("Fetch bot status error:", e);
      setError(e.message || "Failed to fetch bot status. Is the API server running?");
      setBotStatus('ERROR_STATUS');
    }
  }, []);

  useEffect(() => {
    let intervalId = null;

    const initialFetch = async () => {
      await fetchBotStatus();
      // Only set interval if the initial fetch didn't result in an error status
      // or if we want to keep trying even if there was an error.
      // For now, let's assume we always want to keep trying.
      if (botStatus !== 'ERROR_STATUS' || error === null) { // Condition to start interval
        intervalId = setInterval(fetchBotStatus, 10000);
      }
    };

    initialFetch();

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [fetchBotStatus]); // Added fetchBotStatus to dependency array due to useCallback

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard botData={botData} botStatus={botStatus} error={error} />;
      case 'positions':
        return <Positions />; // Will be updated later
      case 'logs':
        return <Logs />; // Will be updated later
      case 'settings':
        return <Settings />; // Will be updated later
      default:
        return <Dashboard botData={botData} botStatus={botStatus} error={error} />;
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 flex">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        botStatus={botStatus}
        botData={botData}
        error={error}
      />
      <div className="flex-1 flex flex-col">
        <Header
          botStatus={botStatus}
          fetchBotStatus={fetchBotStatus}
          error={error}
        />
        <main className="flex-1 p-6 overflow-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;