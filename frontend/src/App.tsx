import { useState, useEffect } from 'react';
import LiftCalculator from './components/LiftCalculator';
import { ThemeProvider } from './contexts/ThemeContext';
import { ThemeToggle } from './components/ThemeToggle';
import { databaseService } from './services/databaseService';
import type { DatabaseMetadata } from './services/databaseService';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

function App() {
  const [metadata, setMetadata] = useState<DatabaseMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function initializeData() {
      try {
        setLoading(true);
        setError(null);
        
        const metadata = await databaseService.getMetadata();
        setMetadata(metadata);
      } catch (err) {
        console.error('Failed to load metadata:', err);
        setError('Failed to connect to the database. Please make sure the API server is running.');
      } finally {
        setLoading(false);
      }
    }

    initializeData();
  }, []);

  if (loading) {
    return (
      <ThemeProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <div className="text-gray-600 dark:text-gray-400">Loading powerlifting data...</div>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  if (error || !metadata) {
    return (
      <ThemeProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center space-y-4 max-w-md">
            <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto" />
            <div className="text-gray-900 dark:text-white text-lg font-semibold">Database Connection Error</div>
            <div className="text-gray-600 dark:text-gray-400">
              {error || 'Unable to connect to the database.'}
            </div>
            <button 
              onClick={() => window.location.reload()}
              className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors"
            >
              Retry
            </button>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-4">
              Make sure the API server is running on port 8000.
            </div>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
        {/* Header with theme toggle */}
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Powerlifting Analytics
            </h1>
            <ThemeToggle />
          </div>
        </header>

        <LiftCalculator 
          metadata={metadata}
        />
        
        {/* Footer */}
        <footer className="mt-12 py-8 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="max-w-4xl mx-auto px-6 text-center space-y-2">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Data from <a href="https://www.openpowerlifting.org/" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:text-primary-700 underline">OpenPowerlifting.org</a>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {metadata.total_records.toLocaleString()} total records • 
              {metadata.countries.toLocaleString()} countries • 
              {metadata.meets.toLocaleString()} meets
            </div>
          </div>
        </footer>
      </div>
    </ThemeProvider>
  );
}

export default App;