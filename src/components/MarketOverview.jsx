import React from 'react';
import { ChevronDown } from 'lucide-react';

const MarketOverview = () => {
  const markets = [
    { symbol: 'BTC/USDT', price: '$57,499', change: '-0.24%', volume: '2.4B', negative: true },
    { symbol: 'ETH/USDT', price: '$2451.5', change: '-0.24%', volume: '1.1B', negative: true },
    { symbol: 'BNB/USDT', price: '$489.1', change: '+0.24%', volume: '453M', negative: false },
    { symbol: 'XRP/USDT', price: '$0.61', change: '+19.33%', volume: '892M', negative: false },
    { symbol: 'SOL/USDT', price: '$198.45', change: '+5.67%', volume: '667M', negative: false },
    { symbol: 'ADA/USDT', price: '$1.23', change: '-2.15%', volume: '234M', negative: true },
  ];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white">Market Overview</h3>
        <div className="flex items-center gap-2 text-sm text-dark-400 cursor-pointer hover:text-white transition-colors">
          <span>24h</span>
          <ChevronDown className="w-4 h-4" />
        </div>
      </div>
      
      <div className="space-y-3">
        {markets.map((market, index) => (
          <div key={index} className="market-item">
            <div>
              <div className="font-medium text-white">{market.symbol}</div>
              <div className="text-sm text-dark-400">{market.price}</div>
            </div>
            <div className="text-right">
              <div className={`text-sm font-medium ${market.negative ? 'profit-negative' : 'profit-positive'}`}>
                {market.change}
              </div>
              <div className="text-xs text-dark-400">{market.volume}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MarketOverview;