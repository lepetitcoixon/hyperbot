import React from 'react';

// Default gradient if none is provided, or handle in CSS
const StatCard = ({ title, value, unit = '', icon: Icon, gradient = 'bg-dark-800' }) => {
  return (
    <div className={`p-5 rounded-xl shadow-lg transition-all duration-300 hover:shadow-2xl ${gradient}`}>
      <div className="flex items-center gap-3 mb-3">
        {Icon && (
          <div className="p-2 bg-dark-700/50 rounded-lg">
            <Icon className="w-5 h-5 text-primary-400" />
          </div>
        )}
        <h3 className="text-md font-medium text-gray-300">{title}</h3>
      </div>
      <div className="text-3xl font-bold text-white">
        {value}
        {unit && <span className="text-lg ml-1">{unit}</span>}
      </div>
      {/* Removed change display as it's not consistently available */}
    </div>
  );
};

export default StatCard;