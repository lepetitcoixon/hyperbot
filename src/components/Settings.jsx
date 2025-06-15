import React, { useState } from 'react';
import { Save, RefreshCw, AlertTriangle, Shield, Zap, TrendingUp } from 'lucide-react';

const Settings = () => {
  const [settings, setSettings] = useState({
    // Strategy Settings
    maxCapital: 10000,
    leverage: 5,
    takeProfit: 5.3,
    stopLoss: 1.25,
    trailingStopActivation: 1.5,
    trailingStopDistance: 1.5,
    capitalPercentage: 100,
    
    // Technical Analysis
    rsiPeriod: 14,
    rsiLowerBound: 15,
    rsiUpperBound: 35,
    rsiUpperBoundShort: 65,
    rsiOverboughtShort: 85,
    bollingerPeriod: 20,
    bollingerStdDev: 2,
    bbWidthMin: 0.01,
    bbWidthMax: 0.08,
    
    // Risk Management
    enableStopLoss: true,
    enableTakeProfit: true,
    enableTrailingStop: true,
    maxPositions: 1,
    
    // Notifications
    enableNotifications: true,
    notifyOnTrade: true,
    notifyOnError: true,
    notifyOnPnL: true
  });

  const handleSave = () => {
    // Here you would save settings to your backend
    console.log('Saving settings:', settings);
    alert('Settings saved successfully!');
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to default values?')) {
      // Reset to default values
      setSettings({
        maxCapital: 10000,
        leverage: 5,
        takeProfit: 5.3,
        stopLoss: 1.25,
        trailingStopActivation: 1.5,
        trailingStopDistance: 1.5,
        capitalPercentage: 100,
        rsiPeriod: 14,
        rsiLowerBound: 15,
        rsiUpperBound: 35,
        rsiUpperBoundShort: 65,
        rsiOverboughtShort: 85,
        bollingerPeriod: 20,
        bollingerStdDev: 2,
        bbWidthMin: 0.01,
        bbWidthMax: 0.08,
        enableStopLoss: true,
        enableTakeProfit: true,
        enableTrailingStop: true,
        maxPositions: 1,
        enableNotifications: true,
        notifyOnTrade: true,
        notifyOnError: true,
        notifyOnPnL: true
      });
    }
  };

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Bot Settings</h2>
        <div className="flex items-center gap-4">
          <button onClick={handleReset} className="btn-danger flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Reset to Default
          </button>
          <button onClick={handleSave} className="btn-success flex items-center gap-2">
            <Save className="w-4 h-4" />
            Save Settings
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Strategy Settings */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-primary-600/20 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-primary-400" />
            </div>
            <h3 className="text-lg font-semibold text-white">Strategy Settings</h3>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-dark-400 mb-2">Max Capital ($)</label>
                <input
                  type="number"
                  value={settings.maxCapital}
                  onChange={(e) => updateSetting('maxCapital', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm text-dark-400 mb-2">Leverage</label>
                <input
                  type="number"
                  value={settings.leverage}
                  onChange={(e) => updateSetting('leverage', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-dark-400 mb-2">Take Profit (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={settings.takeProfit}
                  onChange={(e) => updateSetting('takeProfit', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm text-dark-400 mb-2">Stop Loss (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={settings.stopLoss}
                  onChange={(e) => updateSetting('stopLoss', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm text-dark-400 mb-2">Capital Usage (%)</label>
              <input
                type="range"
                min="1"
                max="100"
                value={settings.capitalPercentage}
                onChange={(e) => updateSetting('capitalPercentage', Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-dark-400 mt-1">
                <span>1%</span>
                <span className="text-white font-medium">{settings.capitalPercentage}%</span>
                <span>100%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Technical Analysis */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-purple-600/20 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-white">Technical Analysis</h3>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-dark-400 mb-2">RSI Period</label>
                <input
                  type="number"
                  value={settings.rsiPeriod}
                  onChange={(e) => updateSetting('rsiPeriod', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm text-dark-400 mb-2">Bollinger Period</label>
                <input
                  type="number"
                  value={settings.bollingerPeriod}
                  onChange={(e) => updateSetting('bollingerPeriod', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-dark-400 mb-2">RSI Lower Bound</label>
                <input
                  type="number"
                  value={settings.rsiLowerBound}
                  onChange={(e) => updateSetting('rsiLowerBound', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm text-dark-400 mb-2">RSI Upper Bound</label>
                <input
                  type="number"
                  value={settings.rsiUpperBound}
                  onChange={(e) => updateSetting('rsiUpperBound', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-dark-400 mb-2">BB Width Min</label>
                <input
                  type="number"
                  step="0.001"
                  value={settings.bbWidthMin}
                  onChange={(e) => updateSetting('bbWidthMin', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm text-dark-400 mb-2">BB Width Max</label>
                <input
                  type="number"
                  step="0.001"
                  value={settings.bbWidthMax}
                  onChange={(e) => updateSetting('bbWidthMax', Number(e.target.value))}
                  className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Risk Management */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-danger-600/20 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-danger-400" />
            </div>
            <h3 className="text-lg font-semibold text-white">Risk Management</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-white">Enable Stop Loss</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.enableStopLoss}
                  onChange={(e) => updateSetting('enableStopLoss', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-white">Enable Take Profit</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.enableTakeProfit}
                  onChange={(e) => updateSetting('enableTakeProfit', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-white">Enable Trailing Stop</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.enableTrailingStop}
                  onChange={(e) => updateSetting('enableTrailingStop', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            
            <div>
              <label className="block text-sm text-dark-400 mb-2">Max Simultaneous Positions</label>
              <input
                type="number"
                min="1"
                max="10"
                value={settings.maxPositions}
                onChange={(e) => updateSetting('maxPositions', Number(e.target.value))}
                className="w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-yellow-600/20 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
            </div>
            <h3 className="text-lg font-semibold text-white">Notifications</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-white">Enable Notifications</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.enableNotifications}
                  onChange={(e) => updateSetting('enableNotifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-white">Notify on Trade</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notifyOnTrade}
                  onChange={(e) => updateSetting('notifyOnTrade', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-white">Notify on Error</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notifyOnError}
                  onChange={(e) => updateSetting('notifyOnError', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-white">Notify on P&L Changes</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notifyOnPnL}
                  onChange={(e) => updateSetting('notifyOnPnL', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Warning Notice */}
      <div className="card border-l-4 border-l-yellow-400 bg-yellow-900/10">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
          <div>
            <div className="font-medium text-white mb-1">Important Notice</div>
            <div className="text-sm text-dark-400">
              Changing these settings will affect your bot's trading behavior. Make sure you understand the implications before saving changes. 
              It's recommended to test new settings with smaller amounts first.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;