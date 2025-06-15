import React from 'react';

const StatCard = ({ title, value, change, icon: Icon, positive, gradient }) => {
  return (
    <div className={`stat-card ${gradient}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-dark-700/50 rounded-lg flex items-center justify-center">
            <Icon className="w-5 h-5 text-primary-400" />
          </div>
          <div className="text-sm text-dark-400">{title}</div>
        </div>
        <div className={`text-sm font-medium ${positive ? 'profit-positive' : 'profit-negative'}`}>
          {change}
        </div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
};

export default StatCard;