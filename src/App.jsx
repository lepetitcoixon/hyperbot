import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import Positions from './components/Positions';
import Logs from './components/Logs';
import Settings from './components/Settings';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [botStatus, setBotStatus] = useState('RUNNING');
  const [botData, setBotData] = useState({
    totalPnL: 2858.24,
    activePositions: 8,
    winRate: 73.2,
    dailyVolume: 45237,
    balance: 32858.24
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setBotData(prev => ({
        ...prev,
        totalPnL: prev.totalPnL + (Math.random() - 0.5) * 10,
        dailyVolume: prev.dailyVolume + Math.random() * 100
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleBotToggle = () => {
    setBotStatus(prev => prev === 'RUNNING' ? 'STOPPED' : 'RUNNING');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard botData={botData} />;
      case 'positions':
        return <Positions />;
      case 'logs':
        return <Logs />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard botData={botData} />;
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 flex">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} botStatus={botStatus} balance={botData.balance} />
      <div className="flex-1 flex flex-col">
        <Header botStatus={botStatus} onBotToggle={handleBotToggle} />
        <main className="flex-1 p-6 overflow-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;