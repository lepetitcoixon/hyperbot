import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';

const ProfitChart = () => {
  const data = [
    { time: '00:00', value: 1200 },
    { time: '04:00', value: 1450 },
    { time: '08:00', value: 1680 },
    { time: '12:00', value: 1520 },
    { time: '16:00', value: 1890 },
    { time: '20:00', value: 2340 },
    { time: '24:00', value: 2858 },
  ];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white">Profit & Loss Chart</h3>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-success-400 rounded-full"></div>
          <span className="text-sm text-dark-400">Cumulative P&L</span>
        </div>
      </div>
      
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              stroke="#9CA3AF"
              fontSize={12}
            />
            <YAxis 
              stroke="#9CA3AF"
              fontSize={12}
              tickFormatter={(value) => `$${value}`}
            />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke="#22C55E" 
              strokeWidth={3}
              dot={{ fill: '#22C55E', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#22C55E', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ProfitChart;