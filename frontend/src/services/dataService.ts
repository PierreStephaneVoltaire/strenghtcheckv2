import { Metadata } from '../types';

const DATA_BASE_URL = '/data'; // This will be served from public/data in development

/**
 * Load percentile data from JSON file
 */
export async function loadPercentileData(): Promise<Record<string, any>> {
  try {
    const response = await fetch(`${DATA_BASE_URL}/percentiles.json`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to load percentile data:', error);
    throw error;
  }
}

/**
 * Load metadata from JSON file
 */
export async function loadMetadata(): Promise<Metadata> {
  try {
    const response = await fetch(`${DATA_BASE_URL}/metadata.json`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to load metadata:', error);
    throw error;
  }
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