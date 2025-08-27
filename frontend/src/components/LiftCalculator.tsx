import { useState, useEffect } from 'react';
import { UserProfile, FilterOptions, PercentileResult, Metadata } from '../types';
import { calculateLiftPercentiles, generateFilterKey, getWeightClass, calculateTotal } from '../utils/percentiles';
import { CalculatorIcon, TrophyIcon } from '@heroicons/react/24/outline';

interface LiftCalculatorProps {
  percentileData: Record<string, any>;
  metadata: Metadata;
}

export default function LiftCalculator({ percentileData, metadata }: LiftCalculatorProps) {
  const [profile, setProfile] = useState<UserProfile>({
    bodyweight: 80,
    sex: 'M',
    lifts: {
      squat: 150,
      bench: 100,
      deadlift: 200,
      total: 450
    }
  });

  const [filters, setFilters] = useState<FilterOptions>({
    sex: 'M',
    equipment: 'Raw',
    weightClass: '83',
    ageDiv: 'Open',
    tested: 'Any',
    country: 'Any',
    federation: 'Any'
  });

  const [percentiles, setPercentiles] = useState<PercentileResult>({
    squat: 0,
    bench: 0,
    deadlift: 0,
    total: 0
  });

  // Update total when individual lifts change
  useEffect(() => {
    const newTotal = calculateTotal(profile.lifts);
    setProfile(prev => ({
      ...prev,
      lifts: {
        ...prev.lifts,
        total: newTotal
      }
    }));
  }, [profile.lifts.squat, profile.lifts.bench, profile.lifts.deadlift]);

  // Update weight class when bodyweight changes
  useEffect(() => {
    const newWeightClass = getWeightClass(profile.bodyweight, profile.sex);
    setFilters(prev => ({
      ...prev,
      sex: profile.sex,
      weightClass: newWeightClass
    }));
  }, [profile.bodyweight, profile.sex]);

  // Calculate percentiles when data changes
  useEffect(() => {
    const filterKey = generateFilterKey(filters);
    const data = percentileData[filterKey];
    
    if (data && data.percentiles) {
      const newPercentiles = calculateLiftPercentiles(profile.lifts, data.percentiles);
      setPercentiles(newPercentiles);
    } else {
      setPercentiles({ squat: 0, bench: 0, deadlift: 0, total: 0 });
    }
  }, [profile.lifts, filters, percentileData]);

  const handleLiftChange = (lift: 'squat' | 'bench' | 'deadlift', value: number) => {
    setProfile(prev => ({
      ...prev,
      lifts: {
        ...prev.lifts,
        [lift]: value
      }
    }));
  };

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 90) return 'text-green-600 bg-green-50';
    if (percentile >= 75) return 'text-blue-600 bg-blue-50';
    if (percentile >= 50) return 'text-yellow-600 bg-yellow-50';
    if (percentile >= 25) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const getPercentileDescription = (percentile: number) => {
    if (percentile >= 95) return 'Elite';
    if (percentile >= 90) return 'Advanced';
    if (percentile >= 75) return 'Intermediate';
    if (percentile >= 50) return 'Novice';
    if (percentile >= 25) return 'Beginner';
    return 'Untrained';
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="flex items-center justify-center space-x-2">
          <TrophyIcon className="h-8 w-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">Powerlifting Percentile Calculator</h1>
        </div>
        <p className="text-gray-600">Compare your lifts to powerlifters worldwide using OpenPowerlifting data</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
          <div className="flex items-center space-x-2 mb-4">
            <CalculatorIcon className="h-6 w-6 text-primary-600" />
            <h2 className="text-xl font-semibold text-gray-900">Enter Your Lifts</h2>
          </div>

          {/* Profile Inputs */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sex
              </label>
              <select
                value={profile.sex}
                onChange={(e) => setProfile(prev => ({ ...prev, sex: e.target.value as 'M' | 'F' }))}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bodyweight (kg)
              </label>
              <input
                type="number"
                value={profile.bodyweight}
                onChange={(e) => setProfile(prev => ({ ...prev, bodyweight: Number(e.target.value) }))}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                min="40"
                max="200"
              />
            </div>
          </div>

          {/* Lift Inputs */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Squat (kg)
              </label>
              <input
                type="number"
                value={profile.lifts.squat}
                onChange={(e) => handleLiftChange('squat', Number(e.target.value))}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bench Press (kg)
              </label>
              <input
                type="number"
                value={profile.lifts.bench}
                onChange={(e) => handleLiftChange('bench', Number(e.target.value))}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Deadlift (kg)
              </label>
              <input
                type="number"
                value={profile.lifts.deadlift}
                onChange={(e) => handleLiftChange('deadlift', Number(e.target.value))}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Total (kg)
              </label>
              <input
                type="number"
                value={profile.lifts.total}
                readOnly
                className="w-full p-2 border border-gray-300 rounded-md bg-gray-50 cursor-not-allowed"
              />
            </div>
          </div>

          {/* Filter Options */}
          <div className="border-t pt-6 space-y-4">
            <h3 className="font-medium text-gray-900">Filter Options</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Equipment
                </label>
                <select
                  value={filters.equipment}
                  onChange={(e) => setFilters(prev => ({ ...prev, equipment: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {metadata.equipment_types.map(equipment => (
                    <option key={equipment} value={equipment}>{equipment}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Age Division
                </label>
                <select
                  value={filters.ageDiv}
                  onChange={(e) => setFilters(prev => ({ ...prev, ageDiv: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {metadata.age_divisions.map(ageDiv => (
                    <option key={ageDiv} value={ageDiv}>{ageDiv}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tested Status
              </label>
              <select
                value={filters.tested}
                onChange={(e) => setFilters(prev => ({ ...prev, tested: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="Any">Any</option>
                {metadata.tested_statuses.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">Your Percentile Rankings</h2>
          
          <div className="text-sm text-gray-600">
            Weight Class: <span className="font-medium">{filters.weightClass}kg</span> • 
            Equipment: <span className="font-medium">{filters.equipment}</span> • 
            Age: <span className="font-medium">{filters.ageDiv}</span>
          </div>

          <div className="space-y-4">
            {/* Squat */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium text-gray-900">Squat</span>
                <span className="text-lg font-semibold">{profile.lifts.squat}kg</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getPercentileColor(percentiles.squat)}`}>
                  {percentiles.squat.toFixed(1)}th percentile
                </div>
                <span className="text-sm text-gray-600">{getPercentileDescription(percentiles.squat)}</span>
              </div>
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(percentiles.squat, 100)}%` }}
                />
              </div>
            </div>

            {/* Bench */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium text-gray-900">Bench Press</span>
                <span className="text-lg font-semibold">{profile.lifts.bench}kg</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getPercentileColor(percentiles.bench)}`}>
                  {percentiles.bench.toFixed(1)}th percentile
                </div>
                <span className="text-sm text-gray-600">{getPercentileDescription(percentiles.bench)}</span>
              </div>
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(percentiles.bench, 100)}%` }}
                />
              </div>
            </div>

            {/* Deadlift */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium text-gray-900">Deadlift</span>
                <span className="text-lg font-semibold">{profile.lifts.deadlift}kg</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getPercentileColor(percentiles.deadlift)}`}>
                  {percentiles.deadlift.toFixed(1)}th percentile
                </div>
                <span className="text-sm text-gray-600">{getPercentileDescription(percentiles.deadlift)}</span>
              </div>
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(percentiles.deadlift, 100)}%` }}
                />
              </div>
            </div>

            {/* Total */}
            <div className="border-2 border-primary-200 rounded-lg p-4 bg-primary-50">
              <div className="flex justify-between items-center mb-2">
                <span className="font-semibold text-gray-900">Total</span>
                <span className="text-xl font-bold text-primary-600">{profile.lifts.total}kg</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getPercentileColor(percentiles.total)}`}>
                  {percentiles.total.toFixed(1)}th percentile
                </div>
                <span className="text-sm text-gray-600 font-medium">{getPercentileDescription(percentiles.total)}</span>
              </div>
              <div className="mt-2 bg-primary-200 rounded-full h-3">
                <div 
                  className="bg-primary-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(percentiles.total, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}