export interface LiftData {
  squat: number;
  bench: number;
  deadlift: number;
  total: number;
}

export interface UserProfile {
  bodyweight: number;
  sex: 'M' | 'F';
  lifts: LiftData;
}

export interface FilterOptions {
  sex: 'M' | 'F';
  equipment: string;
  weightClass: string;
  ageDiv: string;
  tested: string;
  country?: string;
  federation?: string;
  yearRange?: [number, number];
}

export interface PercentileData {
  squat: number[];
  bench: number[];
  deadlift: number[];
  total: number[];
}

export interface FilterCombination {
  percentiles: PercentileData;
  sample_size: number;
  filters: FilterOptions;
}

export interface PercentileResult {
  squat: number;
  bench: number;
  deadlift: number;
  total: number;
}

export interface Metadata {
  countries: string[];
  federations: string[];
  equipment_types: string[];
  weight_classes: {
    M: string[];
    F: string[];
  };
  age_divisions: string[];
  tested_statuses: string[];
  date_range: {
    min_year: number;
    max_year: number;
  };
  total_records: number;
  last_updated: string;
}