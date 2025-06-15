import React, { useState, useEffect, useCallback } from 'react';
import { Save, AlertTriangle, CheckCircle, Loader2, Settings as SettingsIcon, DollarSign, KeyRound, BarChartHorizontal } from 'lucide-react'; // Added new icons

// Helper to convert input string to appropriate type
const parseValue = (value, originalValue) => {
  if (typeof originalValue === 'number') {
    const num = parseFloat(value);
    return isNaN(num) ? originalValue : num; // Keep original if parse fails
  }
  if (typeof originalValue === 'boolean') {
    return value === 'true' || value === true;
  }
  return value; // String or other
};


const Settings = () => {
  const [config, setConfig] = useState({});
  const [editableConfig, setEditableConfig] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const fetchConfig = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response = await fetch('/api/config');
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to fetch configuration." }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setConfig(data);
      setEditableConfig(JSON.parse(JSON.stringify(data))); // Deep clone for editing
    } catch (e) {
      console.error("Fetch config error:", e);
      setError(e.message || "Failed to fetch configuration.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleChange = useCallback((section, key, value) => {
    setEditableConfig(prev => {
      const originalValue = prev[section]?.[key];
      const parsedVal = parseValue(value, originalValue);
      return {
        ...prev,
        [section]: {
          ...prev[section],
          [key]: parsedVal,
        },
      };
    });
    setSuccessMessage(null); // Clear success message on new change
  }, []);

  const handleSaveConfig = async () => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editableConfig),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to save configuration." }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setSuccessMessage(result.message || "Configuration saved successfully!");
      await fetchConfig(); // Re-fetch to ensure UI reflects backend state
      setTimeout(() => setSuccessMessage(null), 5000); // Clear after 5s
    } catch (e) {
      console.error("Save config error:", e);
      setError(e.message || "Failed to save configuration.");
    } finally {
      setIsSaving(false);
    }
  };

  const renderInputField = (section, key, value) => {
    const originalValue = config[section]?.[key];
    let inputType = "text";
    if (typeof originalValue === 'number') inputType = "number";
    if (typeof originalValue === 'boolean') inputType = "checkbox";
    if (key === 'secret_key') inputType = "password";

    const commonProps = {
      id: `${section}-${key}`,
      name: `${section}-${key}`,
      className: "w-full bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500",
    };

    if (inputType === "checkbox") {
      return (
        <div className="flex items-center justify-end"> {/* Align checkbox to the right if desired */}
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={!!value} // Ensure boolean for checkbox
              onChange={(e) => handleChange(section, key, e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-dark-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
          </label>
        </div>
      );
    }

    return (
      <input
        type={inputType}
        value={value}
        onChange={(e) => handleChange(section, key, e.target.value)}
        {...commonProps}
        placeholder={typeof originalValue === 'number' ? '0' : 'Enter value'}
        step={typeof originalValue === 'number' && (key.includes('percentage') || key.includes('ratio') || key.includes('price')) ? '0.01' : 'any'}
      />
    );
  };

  const getSectionIcon = (sectionKey) => {
    switch(sectionKey) {
      case 'general': return SettingsIcon;
      case 'strategy': return DollarSign; // Or TrendingUp
      case 'technical_analysis': return BarChartHorizontal; // Or Zap
      case 'auth': return KeyRound; // Or Shield
      default: return SettingsIcon;
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-12 h-12 text-primary-400 animate-spin" />
        <p className="ml-3 text-xl text-gray-300">Loading configuration...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      <div className="flex items-center justify-between sticky top-0 bg-dark-950 py-4 z-10">
        <h2 className="text-2xl font-bold text-white">Bot Configuration</h2>
        <button
          onClick={handleSaveConfig}
          disabled={isSaving || isLoading}
          className="btn-success flex items-center gap-2"
        >
          {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {error && (
        <div className="card bg-danger-900/30 border border-danger-500 text-danger-300 p-3 animate-fade-in flex items-center gap-2">
          <AlertTriangle size={18} /> {error}
        </div>
      )}
      {successMessage && (
        <div className="card bg-success-900/30 border border-success-500 text-success-300 p-3 animate-fade-in flex items-center gap-2">
          <CheckCircle size={18} /> {successMessage}
        </div>
      )}

      {Object.keys(editableConfig).length === 0 && !error && (
         <div className="card text-center py-12">
          <div className="text-dark-400 mb-2">No configuration data loaded.</div>
          <div className="text-sm text-dark-500">Try refreshing the page or check API server.</div>
        </div>
      )}

      {Object.entries(editableConfig).map(([section, settings]) => {
        const SectionIcon = getSectionIcon(section);
        return (
          <div key={section} className="card">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 bg-primary-700/30 rounded-lg flex items-center justify-center">
                <SectionIcon className="w-5 h-5 text-primary-400" />
              </div>
              <h3 className="text-xl font-semibold text-white capitalize">{section.replace(/_/g, ' ')}</h3>
            </div>
            <div className="space-y-5">
              {Object.entries(settings).map(([key, value]) => (
                <div key={key} className="grid grid-cols-1 md:grid-cols-2 gap-3 items-center">
                  <label htmlFor={`${section}-${key}`} className="text-sm text-gray-300 capitalize">
                    {key.replace(/_/g, ' ')}
                    {key === 'secret_key' && <span className="text-yellow-500 text-xs ml-2">(Sensitive - Hidden)</span>}
                  </label>
                  {renderInputField(section, key, value)}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {Object.keys(editableConfig).length > 0 && (
        <div className="card border-l-4 border-l-yellow-400 bg-yellow-900/10 mt-8">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-medium text-white mb-1">Important Notice</div>
              <div className="text-sm text-gray-300">
                Changing these settings can significantly affect your bot's trading behavior and API connections.
                Ensure you understand the implications. Incorrect API keys can stop the bot.
                The bot might need a restart (via Start/Stop controls) for some settings to take full effect if not automatically handled by the backend.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;