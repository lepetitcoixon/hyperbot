import React from 'react';
import { Activity, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

const QuickActions = () => {
  const actions = [
    {
      title: 'View Trades',
      description: 'Monitor recent trading activity',
      icon: Activity,
      color: 'bg-primary-600 hover:bg-primary-700',
    },
    {
      title: 'Open Position',
      description: 'Manually open a new position',
      icon: TrendingUp,
      color: 'bg-success-600 hover:bg-success-700',
    },
    {
      title: 'Close All',
      description: 'Close all active positions',
      icon: TrendingDown,
      color: 'bg-danger-600 hover:bg-danger-700',
    },
    {
      title: 'Analytics',
      description: 'View detailed performance metrics',
      icon: BarChart3,
      color: 'bg-purple-600 hover:bg-purple-700',
    },
  ];

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-6">
        <div className="w-6 h-6 bg-yellow-500 rounded flex items-center justify-center">
          <span className="text-xs">⚡</span>
        </div>
        <h3 className="text-lg font-semibold text-white">Quick Actions</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((action, index) => {
          const Icon = action.icon;
          return (
            <button
              key={index}
              className={`${action.color} text-white p-4 rounded-lg transition-all duration-200 hover:scale-105 hover:shadow-lg group`}
            >
              <div className="flex flex-col items-center text-center space-y-2">
                <Icon className="w-6 h-6 group-hover:scale-110 transition-transform" />
                <div className="font-medium">{action.title}</div>
                <div className="text-xs opacity-90">{action.description}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default QuickActions;