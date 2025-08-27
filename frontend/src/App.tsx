import { useState, useEffect } from 'react';
import LiftCalculator from './components/LiftCalculator';
import { loadAllData } from './services/dataService';
import { Metadata } from './types';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

function App() {
  const [percentileData, setPercentileData] = useState<Record<string, any> | null>(null);
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function initializeData() {
      try {
        setLoading(true);
        setError(null);
        
        const { percentileData, metadata } = await loadAllData();
        
        setPercentileData(percentileData);
        setMetadata(metadata);
      } catch (err) {
        console.error('Failed to load data:', err);
        setError('Failed to load powerlifting data. Please refresh the page to try again.');
      } finally {
        setLoading(false);
      }
    }

    initializeData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <div className="text-gray-600">Loading powerlifting data...</div>
        </div>
      </div>
    );
  }

  if (error || !percentileData || !metadata) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto" />
          <div className="text-gray-900 text-lg font-semibold">Data Loading Error</div>
          <div className="text-gray-600">
            {error || 'Unable to load the required data files.'}
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors"
          >
            Retry
          </button>
          <div className="text-xs text-gray-500 mt-4">
            Make sure the data files are available in the public/data directory.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <LiftCalculator 
        percentileData={percentileData} 
        metadata={metadata}
      />
      
      {/* Footer */}
      <footer className="mt-12 py-8 border-t border-gray-200 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center space-y-2">
          <div className="text-sm text-gray-600">
            Data from <a href="https://www.openpowerlifting.org/" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:text-primary-700 underline">OpenPowerlifting.org</a>
          </div>
          <div className="text-xs text-gray-500">
            Last updated: {new Date(metadata.last_updated).toLocaleDateString()} • 
            {metadata.total_records.toLocaleString()} total records
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;