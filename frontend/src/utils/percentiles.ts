import { LiftData, PercentileData, PercentileResult, FilterOptions } from '../types';

/**
 * Calculate percentile for a given value within a percentile array
 */
export function calculatePercentile(value: number, percentileArray: number[]): number {
  if (!value || value <= 0 || !percentileArray || percentileArray.length === 0) {
    return 0;
  }

  // Binary search to find the percentile
  let left = 0;
  let right = percentileArray.length - 1;
  
  // If value is less than the minimum (1st percentile)
  if (value <= percentileArray[0]) {
    return 1;
  }
  
  // If value is greater than the maximum (99th percentile)
  if (value >= percentileArray[right]) {
    return 99;
  }
  
  // Binary search for the exact percentile
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    
    if (percentileArray[mid] === value) {
      return mid + 1; // +1 because array is 0-indexed but percentiles start at 1
    }
    
    if (percentileArray[mid] < value) {
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }
  
  // Interpolate between the two closest values
  const lowerIndex = right;
  const upperIndex = left;
  
  if (lowerIndex >= 0 && upperIndex < percentileArray.length) {
    const lowerValue = percentileArray[lowerIndex];
    const upperValue = percentileArray[upperIndex];
    const lowerPercentile = lowerIndex + 1;
    const upperPercentile = upperIndex + 1;
    
    // Linear interpolation
    const ratio = (value - lowerValue) / (upperValue - lowerValue);
    const percentile = lowerPercentile + ratio * (upperPercentile - lowerPercentile);
    
    return Math.round(percentile * 10) / 10; // Round to 1 decimal place
  }
  
  return left + 1;
}

/**
 * Calculate percentiles for all lifts
 */
export function calculateLiftPercentiles(
  lifts: LiftData,
  percentileData: PercentileData
): PercentileResult {
  return {
    squat: calculatePercentile(lifts.squat, percentileData.squat),
    bench: calculatePercentile(lifts.bench, percentileData.bench),
    deadlift: calculatePercentile(lifts.deadlift, percentileData.deadlift),
    total: calculatePercentile(lifts.total, percentileData.total),
  };
}

/**
 * Generate a filter key for looking up percentile data
 */
export function generateFilterKey(filters: FilterOptions): string {
  return `${filters.sex}_${filters.equipment}_${filters.weightClass}_${filters.ageDiv}_${filters.tested}`;
}

/**
 * Determine weight class for a given bodyweight and sex
 */
export function getWeightClass(bodyweight: number, sex: 'M' | 'F'): string {
  const weightClasses = sex === 'M' 
    ? [59, 66, 74, 83, 93, 105, 120, 999] 
    : [47, 52, 57, 63, 72, 84, 999];
  
  for (const wc of weightClasses) {
    if (bodyweight <= wc) {
      if (wc === 999) {
        const prevWc = weightClasses[weightClasses.indexOf(wc) - 1];
        return `${prevWc}+`;
      }
      return wc.toString();
    }
  }
  
  const heaviest = weightClasses[weightClasses.length - 2];
  return `${heaviest}+`;
}

/**
 * Calculate total from individual lifts
 */
export function calculateTotal(lifts: Pick<LiftData, 'squat' | 'bench' | 'deadlift'>): number {
  return lifts.squat + lifts.bench + lifts.deadlift;
}