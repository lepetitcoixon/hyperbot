import React, { useState } from 'react';
import { Power, PowerOff, AlertTriangle, Loader2 } from 'lucide-react';

const Header = ({ botStatus, fetchBotStatus, error: globalError }) => {
  const [isToggling, setIsToggling] = useState(false);
  const [toggleError, setToggleError] = useState(null);

  const handleBotToggle = async () => {
    setIsToggling(true);
    setToggleError(null);
    const endpoint = botStatus === 'STOPPED' ? '/api/start' : '/api/stop';

    try {
      const response = await fetch(endpoint, { method: 'POST' });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: "Operation failed, server response not ok."}));
        throw new Error(errorData.message || `Failed to ${botStatus === 'STOPPED' ? 'start' : 'stop'} bot.`);
      }
      // Success, fetch global status to update UI
    } catch (e) {
      console.error("Toggle bot error:", e);
      setToggleError(e.message);
      // Optionally clear toggleError after a few seconds
      setTimeout(() => setToggleError(null), 5000);
    } finally {
      await fetchBotStatus(); // Refresh global status regardless of toggle success/failure
      setIsToggling(false);
    }
  };

  let statusText;
  let statusColorClass;

  switch (botStatus) {
    case 'RUNNING':
      statusText = 'Running';
      statusColorClass = 'text-success-400';
      break;
    case 'STOPPED':
      statusText = 'Stopped';
      statusColorClass = 'text-danger-400';
      break;
    case 'LOADING_STATUS':
      statusText = 'Loading...';
      statusColorClass = 'text-warning-400';
      break;
    case 'ERROR_STATUS':
      statusText = 'Error';
      statusColorClass = 'text-danger-500';
      break;
    default:
      statusText = 'Unknown';
      statusColorClass = 'text-dark-400';
  }

  const buttonDisabled = isToggling || botStatus === 'LOADING_STATUS' || botStatus === 'ERROR_STATUS';
  let buttonText = "Start Bot";
  let ButtonIcon = Power;

  if (isToggling) {
    buttonText = "Loading...";
    ButtonIcon = Loader2; // Using Loader2 for spinning animation possibility
  } else if (botStatus === 'RUNNING') {
    buttonText = "Stop Bot";
    ButtonIcon = PowerOff;
  } else if (botStatus === 'STOPPED') {
    buttonText = "Start Bot";
    ButtonIcon = Power;
  } else if (botStatus === 'ERROR_STATUS' || botStatus === 'LOADING_STATUS') {
     // Determine button text if needed when disabled, or rely on generic "Start Bot"
     buttonText = botStatus === 'ERROR_STATUS' ? "Start Bot" : "Loading Status...";
  }


  return (
    <header className="bg-dark-900/30 backdrop-blur-sm border-b border-dark-700/50 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trading Dashboard</h1>
          <p className="text-dark-400">Monitor your bot's performance and manage trades</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <div className="flex items-center gap-2">
              <span className="text-sm text-dark-400">Bot Status:</span>
              <span className={`font-semibold ${statusColorClass}`}>
                {statusText}
              </span>
            </div>
            {globalError && botStatus === 'ERROR_STATUS' && (
              <div className="text-xs text-danger-400 mt-1 flex items-center gap-1">
                <AlertTriangle size={14} /> {globalError}
              </div>
            )}
            {toggleError && (
               <div className="text-xs text-danger-400 mt-1 flex items-center gap-1">
                 <AlertTriangle size={14} /> Toggle failed: {toggleError}
               </div>
            )}
          </div>
          
          <button
            onClick={handleBotToggle}
            disabled={buttonDisabled}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 hover:scale-105
              ${isToggling ? 'bg-gray-500 text-gray-300 cursor-not-allowed' : ''}
              ${!isToggling && botStatus === 'RUNNING' ? 'bg-danger-600 hover:bg-danger-700 text-white' : ''}
              ${!isToggling && botStatus === 'STOPPED' ? 'bg-success-600 hover:bg-success-700 text-white' : ''}
              ${!isToggling && (botStatus === 'LOADING_STATUS' || botStatus === 'ERROR_STATUS') ? 'bg-gray-500 text-gray-300 cursor-not-allowed' : ''}
            `}
          >
            <ButtonIcon className={`w-4 h-4 ${isToggling ? 'animate-spin' : ''}`} />
            {buttonText}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;