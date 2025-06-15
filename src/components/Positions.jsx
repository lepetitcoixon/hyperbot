import React from 'react';
import { TrendingUp, TrendingDown, Clock, DollarSign } from 'lucide-react';

const Positions = () => {
  const positions = [
    {
      id: 1,
      symbol: 'BTC/USDT',
      type: 'LONG',
      size: '0.5',
      entryPrice: '56,800',
      currentPrice: '57,499',
      pnl: '+349.50',
      pnlPercent: '+1.23',
      duration: '2h 15m',
      positive: true
    },
    {
      id: 2,
      symbol: 'ETH/USDT',
      type: 'SHORT',
      size: '2.1',
      entryPrice: '2,480',
      currentPrice: '2,451',
      pnl: '+60.90',
      pnlPercent: '+1.17',
      duration: '45m',
      positive: true
    },
    {
      id: 3,
      symbol: 'SOL/USDT',
      type: 'LONG',
      size: '15.0',
      entryPrice: '195.20',
      currentPrice: '198.45',
      pnl: '+48.75',
      pnlPercent: '+1.66',
      duration: '1h 30m',
      positive: true
    },
    {
      id: 4,
      symbol: 'ADA/USDT',
      type: 'LONG',
      size: '1000',
      entryPrice: '1.28',
      currentPrice: '1.23',
      pnl: '-50.00',
      pnlPercent: '-3.91',
      duration: '3h 22m',
      positive: false
    }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Active Positions</h2>
        <div className="flex items-center gap-4">
          <div className="text-sm text-dark-400">
            Total: <span className="text-white font-medium">{positions.length} positions</span>
          </div>
          <button className="btn-primary">Close All</button>
        </div>
      </div>

      <div className="grid gap-4">
        {positions.map((position) => (
          <div key={position.id} className="card hover:bg-dark-800/70 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  {position.type === 'LONG' ? (
                    <TrendingUp className="w-5 h-5 text-success-400" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-danger-400" />
                  )}
                  <div>
                    <div className="font-semibold text-white">{position.symbol}</div>
                    <div className="text-sm text-dark-400">{position.type} • {position.size}</div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-8 text-sm">
                  <div>
                    <div className="text-dark-400">Entry Price</div>
                    <div className="text-white font-medium">${position.entryPrice}</div>
                  </div>
                  <div>
                    <div className="text-dark-400">Current Price</div>
                    <div className="text-white font-medium">${position.currentPrice}</div>
                  </div>
                  <div>
                    <div className="text-dark-400">Duration</div>
                    <div className="text-white font-medium flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {position.duration}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className={`text-lg font-bold ${position.positive ? 'profit-positive' : 'profit-negative'}`}>
                    {position.pnl}
                  </div>
                  <div className={`text-sm ${position.positive ? 'profit-positive' : 'profit-negative'}`}>
                    {position.pnlPercent}
                  </div>
                </div>
                <button className="btn-danger text-sm px-3 py-1">Close</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card success-gradient">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="w-5 h-5 text-success-400" />
            <span className="text-dark-400">Total Unrealized P&L</span>
          </div>
          <div className="text-2xl font-bold text-success-400">+$408.15</div>
        </div>
        
        <div className="card gradient-bg">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-5 h-5 text-primary-400" />
            <span className="text-dark-400">Winning Positions</span>
          </div>
          <div className="text-2xl font-bold text-white">3 / 4</div>
        </div>
        
        <div className="card gradient-bg">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="w-5 h-5 text-primary-400" />
            <span className="text-dark-400">Avg. Duration</span>
          </div>
          <div className="text-2xl font-bold text-white">1h 53m</div>
        </div>
      </div>
    </div>
  );
};

export default Positions;