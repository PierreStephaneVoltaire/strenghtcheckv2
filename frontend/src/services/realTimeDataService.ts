/**
 * Real-time data service for API integration
 * This service will replace the static JSON file approach with live database queries
 */

import type { Metadata } from "../types/index.js";

class RealTimeDataService {
  private baseUrl: string;

  constructor() {
    // In production, this will be the API Gateway URL
    // In development, it can point to local Lambda or mock server
    this.baseUrl = import.meta.env.PROD 
      ? "/api"  // CloudFront will route this to API Gateway
      : "http://localhost:3001/api"; // Local development server
  }

  /**
   * Get metadata for filter options
   */
  async getMetadata(): Promise<Metadata> {
    try {
      const response = await fetch(`${this.baseUrl}/metadata`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to fetch metadata:", error);
      
      // Return fallback metadata for development
      if (import.meta.env.DEV) {
        return this.getFallbackMetadata();
      }
      throw error;
    }
  }

  private getFallbackMetadata(): Metadata {
    return {
      countries: ["USA", "Canada", "United Kingdom", "Australia", "Germany"],
      federations: ["USAPL", "CPU", "GBPF", "APU", "BVDK"],
      equipment_types: ["Raw", "Wraps", "Single-ply", "Multi-ply"],
      weight_classes: {
        M: ["59", "66", "74", "83", "93", "105", "120", "120+"],
        F: ["47", "52", "57", "63", "72", "84", "84+"]
      },
      age_divisions: ["Open", "Sub-Junior", "Junior", "Masters 1", "Masters 2"],
      tested_statuses: ["Tested", "Untested"],
      date_range: { min_year: 2000, max_year: 2024 },
      years: Array.from({ length: 25 }, (_, i) => String(2024 - i)),
      meet_names: ["Sample Meet 1", "Sample Meet 2"],
      states_by_country: {
        "USA": ["AL", "CA", "FL", "NY", "TX"],
        "Canada": ["AB", "BC", "ON", "QC"]
      },
      total_records: 100000,
      last_updated: new Date().toISOString()
    };
  }
}

export const realTimeDataService = new RealTimeDataService();
