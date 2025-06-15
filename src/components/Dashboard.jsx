import React from 'react';
import StatCard from './StatCard';
import ProfitChart from './ProfitChart';
import MarketOverview from './MarketOverview';
import QuickActions from './QuickActions';
import { DollarSign, Target, TrendingUp, BarChart3 } from 'lucide-react';

const Dashboard = ({ botData }) => {
  const stats = [
    {
      title: 'Total P&L',
      value: `$${botData.totalPnL.toLocaleString()}`,
      change: '+12.5%',
      icon: DollarSign,
      positive: true,
      gradient: 'success-gradient'
    },
    {
      title: 'Active Positions',
      value: botData.activePositions,
      change: '+3',
      icon: Target,
      positive: true,
      gradient: 'gradient-bg'
    },
    {
      title: 'Win Rate',
      value: `${botData.winRate}%`,
      change: '+2.1%',
      icon: TrendingUp,
      positive: true,
      gradient: 'success-gradient'
    },
    {
      title: 'Daily Volume',
      value: `$${botData.dailyVolume.toLocaleString()}`,
      change: '+15.3%',
      icon: BarChart3,
      positive: true,
      gradient: 'gradient-bg'
    }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Charts and Market Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ProfitChart />
        </div>
        <div>
          <MarketOverview />
        </div>
      </div>

      {/* Quick Actions */}
      <QuickActions />
    </div>
  );
};

export default Dashboard;