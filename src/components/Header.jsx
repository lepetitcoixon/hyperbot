import React from 'react';
import { Power, PowerOff } from 'lucide-react';

const Header = ({ botStatus, onBotToggle }) => {
  return (
    <header className="bg-dark-900/30 backdrop-blur-sm border-b border-dark-700/50 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trading Dashboard</h1>
          <p className="text-dark-400">Monitor your bot's performance and manage trades</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-dark-400">Bot Status:</span>
            <span className={`font-semibold ${botStatus === 'RUNNING' ? 'text-success-400' : 'text-danger-400'}`}>
              {botStatus}
            </span>
          </div>
          
          <button
            onClick={onBotToggle}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 hover:scale-105 ${
              botStatus === 'RUNNING' 
                ? 'bg-danger-600 hover:bg-danger-700 text-white' 
                : 'bg-success-600 hover:bg-success-700 text-white'
            }`}
          >
            {botStatus === 'RUNNING' ? (
              <>
                <PowerOff className="w-4 h-4" />
                Stop Bot
              </>
            ) : (
              <>
                <Power className="w-4 h-4" />
                Start Bot
              </>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;