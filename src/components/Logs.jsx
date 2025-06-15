import React, { useState } from 'react';
import { Search, Filter, Download, AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';

const Logs = () => {
  const [filter, setFilter] = useState('all');
  
  const logs = [
    {
      id: 1,
      timestamp: '2024-01-15 14:32:15',
      level: 'info',
      message: 'Bot started successfully with optimized BTC strategy',
      details: 'Capital: $32,858.24, Leverage: 5x'
    },
    {
      id: 2,
      timestamp: '2024-01-15 14:33:42',
      level: 'success',
      message: 'LONG position opened for BTC/USDT',
      details: 'Entry: $56,800, Size: 0.5 BTC, Capital: $2,840'
    },
    {
      id: 3,
      timestamp: '2024-01-15 14:45:18',
      level: 'info',
      message: 'RSI analysis: 32.4 (in range 15-35 for LONG)',
      details: 'BB Width: 0.045, Price touched lower band'
    },
    {
      id: 4,
      timestamp: '2024-01-15 15:12:33',
      level: 'warning',
      message: 'Position approaching stop loss level',
      details: 'BTC/USDT LONG, Current: $56,200, SL: $56,090'
    },
    {
      id: 5,
      timestamp: '2024-01-15 15:28:07',
      level: 'success',
      message: 'Take profit triggered for ETH/USDT SHORT',
      details: 'Exit: $2,451, P&L: +$60.90 (+1.17%)'
    },
    {
      id: 6,
      timestamp: '2024-01-15 15:45:22',
      level: 'error',
      message: 'Failed to place order: insufficient balance',
      details: 'Attempted BNB/USDT LONG, Required: $1,200, Available: $890'
    },
    {
      id: 7,
      timestamp: '2024-01-15 16:02:11',
      level: 'info',
      message: 'Market analysis completed for 5m timeframe',
      details: 'Processed 100 candles, Generated 0 signals'
    },
    {
      id: 8,
      timestamp: '2024-01-15 16:15:44',
      level: 'success',
      message: 'Trailing stop updated for SOL/USDT',
      details: 'New level: $195.80, Distance: 1.5%'
    }
  ];

  const getLogIcon = (level) => {
    switch (level) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-success-400" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-400" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-danger-400" />;
      default:
        return <Info className="w-4 h-4 text-primary-400" />;
    }
  };

  const getLogColor = (level) => {
    switch (level) {
      case 'success':
        return 'border-l-success-400 bg-success-900/10';
      case 'warning':
        return 'border-l-yellow-400 bg-yellow-900/10';
      case 'error':
        return 'border-l-danger-400 bg-danger-900/10';
      default:
        return 'border-l-primary-400 bg-primary-900/10';
    }
  };

  const filteredLogs = filter === 'all' ? logs : logs.filter(log => log.level === filter);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Bot Logs</h2>
        <div className="flex items-center gap-4">
          <button className="btn-primary flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export Logs
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4 mb-4">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400" />
            <input
              type="text"
              placeholder="Search logs..."
              className="w-full bg-dark-700/50 border border-dark-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-dark-400 focus:outline-none focus:border-primary-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-dark-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
            >
              <option value="all">All Levels</option>
              <option value="info">Info</option>
              <option value="success">Success</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-primary-400 rounded-full"></div>
            <span className="text-dark-400">Info ({logs.filter(l => l.level === 'info').length})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-success-400 rounded-full"></div>
            <span className="text-dark-400">Success ({logs.filter(l => l.level === 'success').length})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
            <span className="text-dark-400">Warning ({logs.filter(l => l.level === 'warning').length})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-danger-400 rounded-full"></div>
            <span className="text-dark-400">Error ({logs.filter(l => l.level === 'error').length})</span>
          </div>
        </div>
      </div>

      {/* Logs List */}
      <div className="space-y-3">
        {filteredLogs.map((log) => (
          <div key={log.id} className={`card border-l-4 ${getLogColor(log.level)} hover:bg-dark-800/70 transition-all duration-200`}>
            <div className="flex items-start gap-3">
              {getLogIcon(log.level)}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <div className="font-medium text-white">{log.message}</div>
                  <div className="text-sm text-dark-400">{log.timestamp}</div>
                </div>
                <div className="text-sm text-dark-400">{log.details}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredLogs.length === 0 && (
        <div className="card text-center py-12">
          <div className="text-dark-400 mb-2">No logs found</div>
          <div className="text-sm text-dark-500">Try adjusting your filter criteria</div>
        </div>
      )}
    </div>
  );
};

export default Logs;