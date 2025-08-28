import type { Metadata } from '../types/index.js';

// Determine data URL based on environment
const getDataBaseUrl = () => {
  // In development, serve from public/data
  // In production, this will be served from the same CloudFront distribution
  if (import.meta.env.DEV) {
    return '/data';
  }
  
  // In production, data will be served from the same origin
  // The build process or deployment script will handle the correct path
  return '/data';
};

const DATA_BASE_URL = getDataBaseUrl();

// Fallback sample data for development/testing
const FALLBACK_PERCENTILE_DATA = {
  "M_Raw_83_Open_Tested": {
    "percentiles": {
      "squat": Array.from({length: 99}, (_, i) => 100 + i * 2),
      "bench": Array.from({length: 99}, (_, i) => 60 + i * 1.5),
      "deadlift": Array.from({length: 99}, (_, i) => 120 + i * 2.5),
      "total": Array.from({length: 99}, (_, i) => 280 + i * 6)
    },
    "sample_size": 1000,
    "filters": {
      "sex": "M",
      "equipment": "Raw",
      "weight_class": "83",
      "age_div": "Open",
      "tested": "Tested"
    }
  }
};

const FALLBACK_METADATA = {
  "countries": ["USA", "CAN", "GBR", "AUS"],
  "federations": ["USAPL", "CPU", "GBPF", "APU"],
  "equipment_types": ["Raw", "Wraps", "Single-ply", "Multi-ply"],
  "weight_classes": {
    "M": ["59", "66", "74", "83", "93", "105", "120", "120+"],
    "F": ["47", "52", "57", "63", "72", "84", "84+"]
  },
  "age_divisions": ["Open", "Sub-Junior", "Junior", "Masters 1", "Masters 2"],
  "tested_statuses": ["Tested", "Untested"],
  "date_range": {
    "min_year": 2000,
    "max_year": 2024
  },
  "years": Array.from({length: 25}, (_, i) => String(2000 + i)),
  "meet_names": ["Sample Meet 1", "Sample Meet 2"],
  "states_by_country": {
    "USA": ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"],
    "CAN": ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"]
  },
  "total_records": 100,
  "last_updated": new Date().toISOString()
};

/**
 * Load percentile data from JSON file
 */
export async function loadPercentileData(): Promise<Record<string, any>> {
  try {
    console.log(`Loading percentile data from: ${DATA_BASE_URL}/percentiles.json`);
    const response = await fetch(`${DATA_BASE_URL}/percentiles.json`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log(`Loaded percentile data with ${Object.keys(data).length} combinations`);
    return data;
  } catch (error) {
    console.warn('Failed to load percentile data, using fallback:', error);
    if (import.meta.env.DEV) {
      console.log('Using fallback sample data for development');
      return FALLBACK_PERCENTILE_DATA;
    }
    throw error;
  }
}

/**
 * Load metadata from JSON file
 */
export async function loadMetadata(): Promise<Metadata> {
  try {
    console.log(`Loading metadata from: ${DATA_BASE_URL}/metadata.json`);
    const response = await fetch(`${DATA_BASE_URL}/metadata.json`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log(`Loaded metadata with ${data.total_records} total records`);
    
    // Enrich the metadata with additional fields if they don't exist
    const enrichedData = {
      ...data,
      years: data.years || generateYearArray(data.date_range.min_year, data.date_range.max_year),
      meet_names: data.meet_names || [],
      states_by_country: data.states_by_country || getDefaultStatesByCountry()
    };
    
    return enrichedData;
  } catch (error) {
    console.warn('Failed to load metadata, using fallback:', error);
    if (import.meta.env.DEV) {
      console.log('Using fallback metadata for development');
      return FALLBACK_METADATA as Metadata;
    }
    throw error;
  }
}

/**
 * Generate array of years from min to max
 */
function generateYearArray(minYear: number, maxYear: number): string[] {
  const years = [];
  for (let year = minYear; year <= maxYear; year++) {
    years.push(year.toString());
  }
  return years.reverse(); // Show most recent first
}

/**
 * Get default states by country mapping
 */
function getDefaultStatesByCountry(): Record<string, string[]> {
  return {
    "USA": ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"],
    "Canada": ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"],
    "Australia": ["NSW", "QLD", "SA", "TAS", "VIC", "WA", "ACT", "NT"],
    "UK": ["England", "Scotland", "Wales", "N.Ireland"]
  };
}

/**
 * Load all data needed for the application
 */
export async function loadAllData(): Promise<{
  percentileData: Record<string, any>;
  metadata: Metadata;
}> {
  const [percentileData, metadata] = await Promise.all([
    loadPercentileData(),
    loadMetadata()
  ]);
  
  return { percentileData, metadata };
}