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
    setError(null); // Clear previous error before new fetch
    // setBotStatus('LOADING_STATUS'); // Already set before calling if needed, or handled by caller
    try {
      const response = await fetch('/api/status');
      if (!response.ok) {
        let errorDetail = `Failed to fetch bot status. Server responded with ${response.status}.`;
        try {
          const errorText = await response.text();
          console.error('API Error Response Text (fetchBotStatus):', errorText); // Log raw error text
          // Try to parse as JSON for FastAPI detail
          const errorJson = JSON.parse(errorText);
          if (errorJson && errorJson.detail) {
            // If detail is an object (like Pydantic validation error), stringify it
            const detailMessage = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
            errorDetail = `API Error (${response.status}): ${detailMessage}`;
          } else {
            // Fallback if not FastAPI-like JSON or no detail field
            errorDetail = `API Error (${response.status}): ${response.statusText}. Response: ${errorText.substring(0, 150)}${errorText.length > 150 ? '...' : ''}`;
          }
        } catch (e) {
          // Parsing errorText failed, or it wasn't JSON
          console.error('Could not parse error response text (fetchBotStatus):', e);
          // errorDetail is already set to a generic message, we can append if needed or leave as is
          errorDetail = `API Error (${response.status}): ${response.statusText}. Failed to parse server's error message.`;
        }
        console.error('API Error (fetchBotStatus):', { status: response.status, statusText: response.statusText, url: response.url });
        setError(errorDetail);
        setBotStatus('ERROR_STATUS');
        setBotData(null); // Clear potentially stale data
        return; // Important to stop further processing
      }
      const data = await response.json();
      setBotData(data);
      // Only change status if data is successfully fetched and parsed
      setBotStatus(data.bot_running ? 'RUNNING' : 'STOPPED');
      // setError(null); // Cleared at the beginning of the try block or here on success
    } catch (err) {
      // This catch block handles network errors or errors from parsing response.json() if `data = await response.json()` fails
      console.error('Network or other error fetching bot status (fetchBotStatus):', err);
      let detailedErrMessage = `Network Error: ${err.message || 'Could not connect to API server.'}`;
      if (err.name === "TypeError" && err.message.includes("fetch")) {
        detailedErrMessage = "Network request failed. This might be a CORS issue or the server is down.";
      }
      setError(detailedErrMessage);
      setBotStatus('ERROR_STATUS');
      setBotData(null); // Clear potentially stale data
    }
  }, []);

  useEffect(() => {
    let intervalId = null;

    const wrappedFetchBotStatus = async () => {
      // Set loading status before each call, not just the first one in useCallback
      // However, fetchBotStatus itself doesn't set LOADING_STATUS, App.jsx does before calling it.
      // For interval, we might want to show a subtle loading state or none if preferred.
      // For now, fetchBotStatus itself doesn't change botStatus to LOADING_STATUS to avoid flickering if called rapidly.
      // The initial call from initialFetch handles the LOADING_STATUS.
      await fetchBotStatus();
    };

    const initialFetch = async () => {
      setBotStatus('LOADING_STATUS'); // Set loading for the very first fetch
      await wrappedFetchBotStatus();

      // Start interval only if the initial fetch was not a catastrophic error
      // or if we decide to always poll. Current logic from before was:
      // if (botStatus !== 'ERROR_STATUS' || error === null)
      // For robustness, let's always try to set the interval. If server is down, it will keep trying.
      intervalId = setInterval(wrappedFetchBotStatus, 10000);
    };

    initialFetch();

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [fetchBotStatus]); // fetchBotStatus is stable due to useCallback

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