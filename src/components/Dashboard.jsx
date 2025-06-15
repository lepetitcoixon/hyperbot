import React from 'react';
import StatCard from './StatCard';
import ProfitChart from './ProfitChart'; // Remains for now, may need data later
import MarketOverview from './MarketOverview'; // Remains for now
import QuickActions from './QuickActions'; // Remains for now
import { DollarSign, Target, TrendingUp, BarChart3, AlertCircle, Info } from 'lucide-react';

const formatCurrency = (value, decimals = 2) => {
  const num = parseFloat(value);
  if (isNaN(num)) return "N/A";
  return `$${num.toFixed(decimals)}`;
};

const Dashboard = ({ botData, botStatus, error }) => {
  if (botStatus === 'LOADING_STATUS') {
    return <div className="text-center py-10 text-xl text-gray-400">Loading dashboard data...</div>;
  }

  if (error) {
    return (
      <div className="bg-danger-900/30 border border-danger-500 text-danger-300 p-6 rounded-lg shadow-lg animate-fade-in">
        <div className="flex items-center mb-3">
          <AlertCircle size={24} className="mr-3" />
          <h2 className="text-2xl font-semibold">Error Loading Dashboard</h2>
        </div>
        <p className="text-lg">{error}</p>
        <p className="mt-2 text-sm">Please check the API server connection and try refreshing.</p>
      </div>
    );
  }

  if (!botData) {
    return (
      <div className="bg-dark-800 border border-dark-700 text-gray-400 p-6 rounded-lg shadow-lg animate-fade-in">
        <div className="flex items-center mb-3">
          <Info size={24} className="mr-3" />
          <h2 className="text-2xl font-semibold">Bot Data Not Available</h2>
        </div>
        <p className="text-lg">The bot data could not be loaded. The bot might be initializing or there might be an issue with the API response.</p>
      </div>
    );
  }

  // Prepare stats from botData
  const accountSummary = botData.account_summary || {};
  const activePositions = botData.active_positions || [];

  const stats = [
    {
      title: 'Total Capital',
      value: formatCurrency(accountSummary.total_capital),
      unit: '', // Unit is part of value
      icon: DollarSign,
      gradient: 'gradient-bg-blue' // Example gradient
    },
    {
      title: 'Available Capital',
      value: formatCurrency(accountSummary.available_capital),
      unit: '',
      icon: DollarSign,
      gradient: 'gradient-bg-green'
    },
    {
      title: 'Reserved Capital',
      value: formatCurrency(accountSummary.reserved_capital),
      unit: '',
      icon: DollarSign,
      gradient: 'gradient-bg-orange'
    },
    {
      title: 'Active Positions',
      value: activePositions.length,
      unit: '',
      icon: Target,
      gradient: 'gradient-bg-purple'
    },
    // Placeholders for stats not currently available from API
    { title: 'Total P&L', value: "N/A", icon: TrendingUp, gradient: 'gradient-bg-gray' },
    { title: 'Win Rate', value: "N/A", icon: TrendingUp, gradient: 'gradient-bg-gray' },
    { title: 'Daily Volume', value: "N/A", icon: BarChart3, gradient: 'gradient-bg-gray' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <StatCard
            key={index}
            title={stat.title}
            value={stat.value}
            unit={stat.unit}
            icon={stat.icon}
            gradient={stat.gradient}
          />
        ))}
      </div>

      {/* Charts and Market Overview - these will need to be updated to use live data later */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ProfitChart /> {/* Placeholder - needs data */}
        </div>
        <div>
          <MarketOverview /> {/* Placeholder - needs data */}
        </div>
      </div>

      <QuickActions /> {/* Placeholder */}
    </div>
  );
};

export default Dashboard;