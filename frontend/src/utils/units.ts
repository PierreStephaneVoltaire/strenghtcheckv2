/**
 * Unit conversion utilities for powerlifting data
 */

export type Unit = 'kg' | 'lbs';

/**
 * Convert weight from kg to lbs
 */
export function kgToLbs(kg: number): number {
  return kg * 2.20462262185;
}

/**
 * Convert weight from lbs to kg
 */
export function lbsToKg(lbs: number): number {
  return lbs / 2.20462262185;
}

/**
 * Convert weight between units
 */
export function convertWeight(weight: number, fromUnit: Unit, toUnit: Unit): number {
  if (fromUnit === toUnit) {
    return weight;
  }
  
  if (fromUnit === 'kg' && toUnit === 'lbs') {
    return kgToLbs(weight);
  }
  
  if (fromUnit === 'lbs' && toUnit === 'kg') {
    return lbsToKg(weight);
  }
  
  return weight;
}

/**
 * Format weight with appropriate precision and unit
 */
export function formatWeight(weight: number, unit: Unit): string {
  const precision = unit === 'kg' ? 1 : 0;
  return `${weight.toFixed(precision)}${unit}`;
}

/**
 * Round weight to appropriate precision for unit
 */
export function roundWeight(weight: number, unit: Unit): number {
  if (unit === 'kg') {
    return Math.round(weight * 10) / 10; // Round to 0.1 kg
  } else {
    return Math.round(weight); // Round to nearest lb
  }
}

/**
 * Round weight down for weight class determination to prevent bumping to higher class
 */
export function roundWeightDown(weight: number, unit: Unit): number {
  if (unit === 'kg') {
    return Math.floor(weight * 10) / 10; // Round down to 0.1 kg
  } else {
    return Math.floor(weight); // Round down to nearest lb
  }
}