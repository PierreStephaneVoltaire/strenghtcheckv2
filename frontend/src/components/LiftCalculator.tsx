import { useState, useEffect } from 'react';
import type { UserProfile, FilterOptions, PercentileResult, StatisticsResult } from '../types/index.js';
import type { DatabaseMetadata } from '../services/databaseService';
import { getWeightClass, calculateTotal } from '../utils/percentiles';
import { convertWeight, formatWeight, roundWeight, roundWeightDown, type Unit } from '../utils/units';
import { getCountriesWithFlags } from '../utils/countryFlags';
import { databaseService } from '../services/databaseService';
import { CalculatorIcon, TrophyIcon, ArrowPathIcon, UsersIcon } from '@heroicons/react/24/outline';

interface LiftCalculatorProps {
  metadata: DatabaseMetadata;
}

export default function LiftCalculator({ metadata }: LiftCalculatorProps) {
  const [unit, setUnit] = useState<Unit>('kg');
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
    ageDiv: 'All',
    tested: 'Any',
    country: 'All',
    federation: 'All',
    year: 'All',
    meetName: 'All',
    state: 'All'
  });

  const [percentiles, setPercentiles] = useState<PercentileResult>({
    squat: 0,
    bench: 0,
    deadlift: 0,
    total: 0
  });

  const [statistics, setStatistics] = useState<StatisticsResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableOptions, setAvailableOptions] = useState({
    countries: ['All'],
    states: ['All'],
    federations: ['All'],
    years: ['All'],
    meetNames: ['All']
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
    // Always use kg for weight class calculation since percentile data is in kg
    // Round down the bodyweight to prevent bumping to a higher weight class
    let bodyweightKg = unit === 'kg' ? profile.bodyweight : convertWeight(profile.bodyweight, 'lbs', 'kg');
    bodyweightKg = roundWeightDown(bodyweightKg, 'kg');
    const newWeightClass = getWeightClass(bodyweightKg, profile.sex);
    setFilters(prev => ({
      ...prev,
      sex: profile.sex,
      weightClass: newWeightClass
    }));
  }, [profile.bodyweight, profile.sex, unit]);

  // Load available filter options on component mount
  useEffect(() => {
    const loadOptions = async () => {
      try {
        const options = await databaseService.getDynamicOptions(filters);
        setAvailableOptions(options);
      } catch (err) {
        console.error('Failed to load filter options:', err);
      }
    };
    loadOptions();
  }, []);

  // Update available options when filters change
  useEffect(() => {
    const updateOptions = async () => {
      try {
        const options = await databaseService.getDynamicOptions(filters);
        setAvailableOptions(options);
      } catch (err) {
        console.error('Failed to update filter options:', err);
      }
    };
    updateOptions();
  }, [filters.country, filters.state]);

  // Calculate statistics and percentiles when filters or lifts change
  useEffect(() => {
    const calculateStats = async () => {
      if (isLoading) return;
      
      try {
        setIsLoading(true);
        setError(null);

        // Get statistics from database
        const stats = await databaseService.getStatistics(filters);
        setStatistics(stats);
        
        // Calculate user percentiles
        // Convert lifts to kg if needed since data is in kg
        const liftsKg = {
          squat: unit === 'kg' ? profile.lifts.squat : convertWeight(profile.lifts.squat, 'lbs', 'kg'),
          bench: unit === 'kg' ? profile.lifts.bench : convertWeight(profile.lifts.bench, 'lbs', 'kg'),
          deadlift: unit === 'kg' ? profile.lifts.deadlift : convertWeight(profile.lifts.deadlift, 'lbs', 'kg'),
          total: unit === 'kg' ? profile.lifts.total : convertWeight(profile.lifts.total, 'lbs', 'kg')
        };
        
        const newPercentiles = await databaseService.getPercentiles(
          filters,
          liftsKg.squat,
          liftsKg.bench,
          liftsKg.deadlift,
          liftsKg.total
        );
        
        setPercentiles(newPercentiles);
      } catch (err) {
        console.error('Error calculating statistics:', err);
        setError('Failed to calculate statistics. Please check your connection.');
      } finally {
        setIsLoading(false);
      }
    };

    calculateStats();
  }, [profile.lifts, filters, unit]);

  const handleLiftChange = (lift: 'squat' | 'bench' | 'deadlift', value: number) => {
    setProfile(prev => ({
      ...prev,
      lifts: {
        ...prev.lifts,
        [lift]: value
      }
    }));
  };

  const handleUnitToggle = () => {
    const newUnit: Unit = unit === 'kg' ? 'lbs' : 'kg';
    
    // Convert all weights to new unit
    setProfile(prev => ({
      ...prev,
      bodyweight: roundWeight(convertWeight(prev.bodyweight, unit, newUnit), newUnit),
      lifts: {
        squat: roundWeight(convertWeight(prev.lifts.squat, unit, newUnit), newUnit),
        bench: roundWeight(convertWeight(prev.lifts.bench, unit, newUnit), newUnit),
        deadlift: roundWeight(convertWeight(prev.lifts.deadlift, unit, newUnit), newUnit),
        total: roundWeight(convertWeight(prev.lifts.total, unit, newUnit), newUnit)
      }
    }));
    
    setUnit(newUnit);
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
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <CalculatorIcon className="h-6 w-6 text-primary-600" />
              <h2 className="text-xl font-semibold text-gray-900">Enter Your Lifts</h2>
            </div>
            
            {/* Unit Toggle */}
            <button
              onClick={handleUnitToggle}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-primary-700 bg-primary-50 border border-primary-200 rounded-md hover:bg-primary-100 transition-colors"
            >
              <ArrowPathIcon className="h-4 w-4" />
              <span>{unit === 'kg' ? 'Switch to lbs' : 'Switch to kg'}</span>
            </button>
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
                Bodyweight ({unit})
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
                Squat ({unit})
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
                Bench Press ({unit})
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
                Deadlift ({unit})
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
                Total ({unit})
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
                  <option value="All">All Ages</option>
                  {metadata.age_divisions.map(ageDiv => (
                    <option key={ageDiv} value={ageDiv}>{ageDiv}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
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

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Year
                </label>
                <select
                  value={filters.year}
                  onChange={(e) => setFilters(prev => ({ ...prev, year: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {availableOptions.years.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Country
              </label>
              <select
                value={filters.country}
                onChange={(e) => {
                  setFilters(prev => ({ 
                    ...prev, 
                    country: e.target.value,
                    state: 'All', // Reset state when country changes
                    meetName: 'All', // Reset meet when country changes
                    federation: 'All' // Reset federation when country changes
                  }));
                }}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {getCountriesWithFlags(availableOptions.countries).map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            {/* Conditional State/Province field */}
            {filters.country !== 'All' && availableOptions.states.length > 1 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  State/Province
                </label>
                <select
                  value={filters.state}
                  onChange={(e) => setFilters(prev => ({ ...prev, state: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {availableOptions.states.map(state => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Conditional Federation field */}
            {filters.country !== 'All' && availableOptions.federations.length > 1 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Federation
                </label>
                <select
                  value={filters.federation}
                  onChange={(e) => setFilters(prev => ({ ...prev, federation: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {availableOptions.federations.map(federation => (
                    <option key={federation} value={federation}>{federation}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Conditional Meet field */}
            {filters.country !== 'All' && availableOptions.meetNames.length > 1 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Meet
                </label>
                <select
                  value={filters.meetName}
                  onChange={(e) => setFilters(prev => ({ ...prev, meetName: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {availableOptions.meetNames.map(meet => (
                    <option key={meet} value={meet}>{meet}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Results Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">Your Percentile Rankings</h2>
          
          {/* Filter Summary */}
          <div className="text-sm text-gray-600 mb-4">
            <div className="flex items-center space-x-4 flex-wrap">
              <span>Weight Class: <span className="font-medium">{filters.weightClass}kg</span></span>
              <span>Equipment: <span className="font-medium">{filters.equipment}</span></span>
              <span>Age: <span className="font-medium">{filters.ageDiv}</span></span>
              <span>Tested: <span className="font-medium">{filters.tested}</span></span>
              {filters.country !== 'All' && (
                <span>Country: <span className="font-medium">{filters.country}</span></span>
              )}
              {filters.year !== 'All' && (
                <span>Year: <span className="font-medium">{filters.year}</span></span>
              )}
            </div>
          </div>

          {/* Sample Size and Loading State */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-2 text-gray-600">Loading data...</span>
            </div>
          ) : error ? (
            <div className="text-red-600 text-center py-4">{error}</div>
          ) : statistics && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-2">
                <UsersIcon className="h-5 w-5 text-blue-600" />
                <span className="text-blue-800 font-medium">
                  Sample Size: {statistics.sampleSize.toLocaleString()} lifters
                </span>
              </div>
              <div className="text-sm text-blue-600 mt-1">
                Your percentiles are calculated against this filtered dataset
              </div>
            </div>
          )}

          <div className="space-y-4">
            {/* Squat */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium text-gray-900">Squat</span>
                <span className="text-lg font-semibold">{formatWeight(profile.lifts.squat, unit)}</span>
              </div>
              <div className="flex items-center space-x-3 mb-2">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getPercentileColor(percentiles.squat)}`}>
                  {percentiles.squat.toFixed(1)}th percentile
                </div>
                <span className="text-sm text-gray-600">{getPercentileDescription(percentiles.squat)}</span>
              </div>
              {statistics && (
                <div className="text-xs text-gray-500 mb-2">
                  Mean: {formatWeight(statistics.squat.mean, 'kg')} • 
                  Median: {formatWeight(statistics.squat.median, 'kg')} • 
                  Range: {formatWeight(statistics.squat.min, 'kg')}-{formatWeight(statistics.squat.max, 'kg')}
                </div>
              )}
              <div className="bg-gray-200 rounded-full h-2">
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
                <span className="text-lg font-semibold">{formatWeight(profile.lifts.bench, unit)}</span>
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
                <span className="text-lg font-semibold">{formatWeight(profile.lifts.deadlift, unit)}</span>
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
                <span className="text-xl font-bold text-primary-600">{formatWeight(profile.lifts.total, unit)}</span>
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