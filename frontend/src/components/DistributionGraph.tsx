import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTheme } from '../contexts/ThemeContext';
import type { FilterOptions } from '../types/index';

interface DistributionData {
  bins: number[];
  counts: number[];
  total_samples: number;
}

interface DistributionResponse {
  distributions: {
    squat: DistributionData;
    bench: DistributionData;
    deadlift: DistributionData;
    total: DistributionData;
  };
  sample_size: number;
  filters: FilterOptions;
}

interface DistributionGraphProps {
  filters: FilterOptions;
  selectedLift: 'squat' | 'bench' | 'deadlift' | 'total';
}

const DistributionGraph: React.FC<DistributionGraphProps> = ({ filters, selectedLift }) => {
  const [distributionData, setDistributionData] = useState<DistributionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { theme } = useTheme();

  useEffect(() => {
    const fetchDistributionData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Build query parameters
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
          if (value && value !== 'All' && value !== 'Any') {
            params.append(key, value);
          }
        });
        params.append('bins', '40'); // Reasonable number of bins for distribution

        // For local development, use mock data
        if (import.meta.env.DEV) {
          // Generate mock distribution data
          const mockData = generateMockDistribution(selectedLift);
          setDistributionData(mockData);
        } else {
          // In production, fetch from API
          const response = await fetch(`/api/distribution?${params.toString()}`);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          setDistributionData(data);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load distribution data');
      } finally {
        setLoading(false);
      }
    };

    fetchDistributionData();
  }, [filters, selectedLift]);

  const generateMockDistribution = (lift: string): DistributionResponse => {
    // Generate realistic distribution data based on lift type
    const liftRanges = {
      squat: { min: 80, max: 300, mean: 150 },
      bench: { min: 60, max: 220, mean: 110 },
      deadlift: { min: 100, max: 350, mean: 180 },
      total: { min: 250, max: 800, mean: 450 }
    };

    const range = liftRanges[lift as keyof typeof liftRanges];
    const bins: number[] = [];
    const counts: number[] = [];
    
    // Create 40 bins
    for (let i = 0; i < 40; i++) {
      const binCenter = range.min + (range.max - range.min) * (i / 39);
      bins.push(Math.round(binCenter));
      
      // Generate normal distribution-like data
      const distanceFromMean = Math.abs(binCenter - range.mean) / (range.max - range.min);
      const count = Math.exp(-distanceFromMean * distanceFromMean * 8) * 0.1;
      counts.push(count);
    }

    return {
      distributions: {
        squat: { bins, counts, total_samples: 1000 },
        bench: { bins, counts, total_samples: 1000 },
        deadlift: { bins, counts, total_samples: 1000 },
        total: { bins, counts, total_samples: 1000 }
      },
      sample_size: 1000,
      filters
    };
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {selectedLift.charAt(0).toUpperCase() + selectedLift.slice(1)} Distribution
        </h3>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading distribution...</span>
        </div>
      </div>
    );
  }

  if (error || !distributionData) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {selectedLift.charAt(0).toUpperCase() + selectedLift.slice(1)} Distribution
        </h3>
        <div className="text-center py-8">
          <div className="text-red-600 dark:text-red-400">
            {error || 'Failed to load distribution data'}
          </div>
        </div>
      </div>
    );
  }

  const liftData = distributionData.distributions[selectedLift];
  
  // Transform data for recharts
  const chartData = liftData.bins.map((bin, index) => ({
    weight: bin,
    frequency: liftData.counts[index] * 100, // Convert to percentage
    count: Math.round(liftData.counts[index] * liftData.total_samples)
  }));

  // Theme-aware colors
  const colors = {
    primary: '#3b82f6',
    grid: theme === 'dark' ? '#374151' : '#e5e7eb',
    text: theme === 'dark' ? '#d1d5db' : '#374151',
    background: theme === 'dark' ? '#1f2937' : '#ffffff'
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg p-3">
          <p className="text-sm text-gray-900 dark:text-white font-medium">
            Weight: {label}kg
          </p>
          <p className="text-sm text-primary-600">
            Frequency: {payload[0].value.toFixed(1)}%
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Count: {payload[0].payload.count} lifters
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {selectedLift.charAt(0).toUpperCase() + selectedLift.slice(1)} Distribution
        </h3>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {distributionData.sample_size.toLocaleString()} lifters
        </div>
      </div>
      
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <BarChart
            data={chartData}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 60,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis 
              dataKey="weight" 
              stroke={colors.text}
              tick={{ fill: colors.text }}
              label={{ 
                value: 'Weight (kg)', 
                position: 'insideBottom', 
                offset: -10,
                style: { textAnchor: 'middle', fill: colors.text }
              }}
            />
            <YAxis 
              stroke={colors.text}
              tick={{ fill: colors.text }}
              label={{ 
                value: 'Frequency (%)', 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: colors.text }
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar 
              dataKey="frequency" 
              fill={colors.primary}
              stroke={colors.primary}
              strokeWidth={1}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
        Distribution shows the percentage of lifters at each weight level for the selected filters
      </div>
    </div>
  );
};

export default DistributionGraph;