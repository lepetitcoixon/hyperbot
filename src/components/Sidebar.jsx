import React from 'react';
import { BarChart3, Target, FileText, Settings, Bot } from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab, botStatus, balance }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'positions', label: 'Positions', icon: Target },
    { id: 'logs', label: 'Logs', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

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
        <div className={`status-indicator ${botStatus === 'RUNNING' ? 'status-running' : 'status-stopped'}`}>
          <div className={`w-2 h-2 rounded-full ${botStatus === 'RUNNING' ? 'bg-success-400 animate-pulse' : 'bg-danger-400'}`}></div>
          {botStatus}
        </div>
        <div className="mt-3 text-sm">
          <div className="text-dark-400">Balance</div>
          <div className="text-success-400 font-semibold">${balance.toLocaleString()}</div>
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