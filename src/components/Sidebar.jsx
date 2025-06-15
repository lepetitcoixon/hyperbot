import React from 'react';
import { BarChart3, Target, FileText, Settings, Bot, AlertTriangle, Loader2 } from 'lucide-react'; // Added AlertTriangle, Loader2

const formatCurrency = (value, decimals = 2) => {
  const num = parseFloat(value);
  if (isNaN(num) || value === null || value === undefined) return "N/A";
  return `$${num.toFixed(decimals)}`;
};

const Sidebar = ({ activeTab, setActiveTab, botStatus, botData, error }) => { // Added botData, error. Removed balance.
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'positions', label: 'Positions', icon: Target },
    { id: 'logs', label: 'Logs', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  let statusTextDisplay;
  let statusColorClassDot;
  let StatusIcon = null;

  switch (botStatus) {
    case 'RUNNING':
      statusTextDisplay = 'Running';
      statusColorClassDot = 'bg-success-400 animate-pulse';
      break;
    case 'STOPPED':
      statusTextDisplay = 'Stopped';
      statusColorClassDot = 'bg-danger-400';
      break;
    case 'LOADING_STATUS':
      statusTextDisplay = 'Loading...';
      statusColorClassDot = 'bg-warning-400 animate-pulse';
      StatusIcon = <Loader2 size={14} className="inline-block animate-spin mr-1" />;
      break;
    case 'ERROR_STATUS':
      statusTextDisplay = 'Error';
      statusColorClassDot = 'bg-danger-700';
      StatusIcon = <AlertTriangle size={14} className="inline-block mr-1 text-danger-500" />;
      break;
    default:
      statusTextDisplay = 'Unknown';
      statusColorClassDot = 'bg-gray-500';
  }

  const displayBalance = botData?.account_summary?.total_capital;

  return (
    <div className="w-64 bg-dark-900/50 backdrop-blur-sm border-r border-dark-700/50 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-dark-700/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">TradeBotPro</h1>
            <p className="text-sm text-dark-400">Advanced Trading Bot</p>
          </div>
        </div>
      </div>

      {/* Bot Status */}
      <div className="p-4 border-b border-dark-700/50">
        <div className="text-sm text-dark-400 mb-2">Bot Status</div>
        <div className={`status-indicator flex items-center ${
            botStatus === 'RUNNING' ? 'text-success-300' :
            botStatus === 'STOPPED' ? 'text-danger-300' :
            botStatus === 'LOADING_STATUS' ? 'text-warning-300' :
            botStatus === 'ERROR_STATUS' ? 'text-danger-400' : 'text-gray-400'
          }`}>
          <div className={`w-2 h-2 rounded-full mr-2 ${statusColorClassDot}`}></div>
          {StatusIcon}{statusTextDisplay}
        </div>
         {botStatus === 'ERROR_STATUS' && error && (
          <p className="text-xs text-danger-400 mt-1 truncate" title={error}>Error: {error.substring(0,25)}{error.length > 25 ? '...' : ''}</p>
        )}
        <div className="mt-3 text-sm">
          <div className="text-dark-400">Balance</div>
          <div className={`font-semibold ${botStatus === 'ERROR_STATUS' ? 'text-gray-500' : 'text-success-400'}`}>
            {botStatus === 'LOADING_STATUS' ? 'Loading...' : formatCurrency(displayBalance)}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.id}
                className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </div>
            );
          })}
        </div>
      </nav>

      {/* Performance Indicator */}
      <div className="p-4 border-t border-dark-700/50">
        <div className="flex items-center gap-2 text-sm">
          <div className="w-2 h-2 bg-success-400 rounded-full animate-pulse"></div>
          <span className="text-dark-400">24h Performance</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;