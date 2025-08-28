import type { FilterOptions, StatisticsResult, PercentileResult } from '../types/index.js';

const API_BASE_URL = 'http://localhost:8000/api';

export interface DatabaseMetadata {
  total_records: number;
  countries: number;
  meets: number;
  date_range: {
    min_year: number;
    max_year: number;
  };
  equipment_types: string[];
  age_divisions: string[];
  tested_statuses: string[];
  weight_classes: {
    M: string[];
    F: string[];
  };
}

class DatabaseService {
  private metadata: DatabaseMetadata | null = null;

  async getMetadata(): Promise<DatabaseMetadata> {
    if (this.metadata) {
      return this.metadata;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/metadata`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.metadata = await response.json();
      return this.metadata!;
    } catch (error) {
      console.error('Failed to load metadata:', error);
      throw error;
    }
  }

  async getStatistics(filters: FilterOptions): Promise<StatisticsResult> {
    try {
      const response = await fetch(`${API_BASE_URL}/statistics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get statistics:', error);
      throw error;
    }
  }

  async getPercentiles(
    filters: FilterOptions,
    squatKg: number,
    benchKg: number,
    deadliftKg: number,
    totalKg: number
  ): Promise<PercentileResult> {
    try {
      const params = new URLSearchParams({
        squat_kg: squatKg.toString(),
        bench_kg: benchKg.toString(),
        deadlift_kg: deadliftKg.toString(),
        total_kg: totalKg.toString(),
      });

      const response = await fetch(`${API_BASE_URL}/percentiles?${params}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get percentiles:', error);
      throw error;
    }
  }

  async getFilterOptions(
    filterType: 'country' | 'state' | 'federation' | 'year' | 'meetName',
    currentFilters: FilterOptions
  ): Promise<string[]> {
    try {
      const params = new URLSearchParams({
        sex: currentFilters.sex,
        equipment: currentFilters.equipment,
        weightClass: currentFilters.weightClass,
        ageDiv: currentFilters.ageDiv,
        tested: currentFilters.tested,
        country: currentFilters.country,
        state: currentFilters.state,
        federation: currentFilters.federation,
        year: currentFilters.year,
      });

      const response = await fetch(`${API_BASE_URL}/filter-options/${filterType}?${params}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get filter options:', error);
      return ['All']; // Return default fallback
    }
  }

  /**
   * Get dynamic filter options based on current selections
   */
  async getDynamicOptions(filters: FilterOptions) {
    const [countries, states, federations, years, meetNames] = await Promise.all([
      this.getFilterOptions('country', filters),
      filters.country !== 'All' ? this.getFilterOptions('state', filters) : Promise.resolve(['All']),
      filters.country !== 'All' ? this.getFilterOptions('federation', filters) : Promise.resolve(['All']),
      this.getFilterOptions('year', filters),
      filters.country !== 'All' ? this.getFilterOptions('meetName', filters) : Promise.resolve(['All']),
    ]);

    return {
      countries,
      states,
      federations,
      years,
      meetNames,
    };
  }
}

export const databaseService = new DatabaseService();