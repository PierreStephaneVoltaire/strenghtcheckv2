"""
AWS Lambda function for powerlifting analytics API.
Handles database queries with read replica support.
"""

import json
import psycopg2
import os
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DatabaseService:
    """Service for database operations with read replica support."""
    
    def __init__(self):
        self.write_db_host = os.environ.get('WRITE_DB_HOST')
        self.read_db_host = os.environ.get('READ_DB_HOST', self.write_db_host)  # Fallback to write DB
        self.db_name = os.environ.get('DB_NAME', 'powerlifting')
        self.db_user = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASSWORD')
        self.db_port = int(os.environ.get('DB_PORT', '5432'))
        
    def get_connection(self, read_only: bool = True):
        """Get database connection. Use read replica for queries, write DB for updates."""
        host = self.read_db_host if read_only else self.write_db_host
        
        return psycopg2.connect(
            host=host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            port=self.db_port
        )
    
    def get_percentiles(self, filters: Dict) -> Dict:
        """Calculate percentiles for given filters using optimized views."""
        with self.get_connection(read_only=True) as conn:
            cursor = conn.cursor()
            
            # Build query based on filters
            base_table = self._get_optimal_table(filters)
            where_conditions = []
            params = []
            
            # Add filter conditions
            for field, value in filters.items():
                if value and value != 'Any':
                    if field == 'sex':
                        continue  # Already handled by table selection
                    elif field == 'equipment':
                        where_conditions.append("equipment = %s")
                        params.append(value)
                    elif field == 'weight_class':
                        where_conditions.append("weight_class = %s")
                        params.append(value)
                    elif field == 'age_div':
                        where_conditions.append("age_div = %s") 
                        params.append(value)
                    elif field == 'tested':
                        where_conditions.append("tested = %s")
                        params.append(value)
                    elif field == 'country':
                        where_conditions.append("country = %s")
                        params.append(value)
                    elif field == 'state':
                        where_conditions.append("state = %s")
                        params.append(value)
                    elif field == 'year':
                        where_conditions.append("year = %s")
                        params.append(int(value))
                    elif field == 'federation':
                        where_conditions.append("federation = %s")
                        params.append(value)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Execute query
            query = f"""
                SELECT 
                    squat_kg, bench_kg, deadlift_kg, total_kg
                FROM {base_table}
                WHERE {where_clause}
                AND squat_kg > 0 AND bench_kg > 0 AND deadlift_kg > 0 AND total_kg > 0
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if len(results) < 10:  # Minimum sample size
                return {"error": "Insufficient data for the selected filters"}
            
            # Calculate percentiles
            lifts = {
                'squat': [row[0] for row in results],
                'bench': [row[1] for row in results], 
                'deadlift': [row[2] for row in results],
                'total': [row[3] for row in results]
            }
            
            percentiles = {}
            for lift_name, lift_data in lifts.items():
                percentiles[lift_name] = np.percentile(lift_data, range(1, 100)).tolist()
            
            return {
                "percentiles": percentiles,
                "sample_size": len(results),
                "filters": filters
            }
    
    def get_metadata(self) -> Dict:
        """Get metadata for filter options."""
        with self.get_connection(read_only=True) as conn:
            cursor = conn.cursor()
            
            metadata = {}
            
            # Get unique countries
            cursor.execute("SELECT DISTINCT country FROM lifts WHERE country IS NOT NULL ORDER BY country")
            metadata['countries'] = [row[0] for row in cursor.fetchall()]
            
            # Get federations
            cursor.execute("SELECT DISTINCT federation FROM lifts WHERE federation IS NOT NULL ORDER BY federation")
            metadata['federations'] = [row[0] for row in cursor.fetchall()]
            
            # Get equipment types
            cursor.execute("SELECT DISTINCT equipment FROM lifts ORDER BY equipment")
            metadata['equipment_types'] = [row[0] for row in cursor.fetchall()]
            
            # Get weight classes by sex
            cursor.execute("SELECT DISTINCT sex, weight_class FROM lifts ORDER BY sex, weight_class")
            weight_classes = {'M': [], 'F': []}
            for sex, wc in cursor.fetchall():
                weight_classes[sex].append(wc)
            metadata['weight_classes'] = weight_classes
            
            # Get age divisions
            cursor.execute("SELECT DISTINCT age_div FROM lifts ORDER BY age_div")
            metadata['age_divisions'] = [row[0] for row in cursor.fetchall()]
            
            # Get tested statuses
            cursor.execute("SELECT DISTINCT tested FROM lifts ORDER BY tested")
            metadata['tested_statuses'] = [row[0] for row in cursor.fetchall()]
            
            # Get years
            cursor.execute("SELECT DISTINCT year FROM lifts WHERE year IS NOT NULL ORDER BY year DESC")
            metadata['years'] = [str(row[0]) for row in cursor.fetchall()]
            
            # Get states by country
            cursor.execute("""
                SELECT country, state 
                FROM lifts 
                WHERE country IS NOT NULL AND state IS NOT NULL
                GROUP BY country, state
                ORDER BY country, state
            """)
            states_by_country = {}
            for country, state in cursor.fetchall():
                if country not in states_by_country:
                    states_by_country[country] = []
                states_by_country[country].append(state)
            metadata['states_by_country'] = states_by_country
            
            # Get total record count
            cursor.execute("SELECT COUNT(*) FROM lifts")
            metadata['total_records'] = cursor.fetchone()[0]
            
            return metadata
    
    def get_distribution_data(self, filters: Dict, bins: int = 50) -> Dict:
        """Get distribution data for graphing, optimized for frontend transmission."""
        with self.get_connection(read_only=True) as conn:
            cursor = conn.cursor()
            
            base_table = self._get_optimal_table(filters)
            where_conditions = []
            params = []
            
            # Add filter conditions (same as get_percentiles)
            for field, value in filters.items():
                if value and value != 'Any':
                    if field == 'sex':
                        continue
                    elif field == 'equipment':
                        where_conditions.append("equipment = %s")
                        params.append(value)
                    elif field == 'weight_class':
                        where_conditions.append("weight_class = %s")
                        params.append(value)
                    elif field == 'age_div':
                        where_conditions.append("age_div = %s")
                        params.append(value)
                    elif field == 'tested':
                        where_conditions.append("tested = %s")
                        params.append(value)
                    elif field == 'country':
                        where_conditions.append("country = %s")
                        params.append(value)
                    elif field == 'state':
                        where_conditions.append("state = %s")
                        params.append(value)
                    elif field == 'year':
                        where_conditions.append("year = %s")
                        params.append(int(value))
                    elif field == 'federation':
                        where_conditions.append("federation = %s")
                        params.append(value)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Get data for distribution
            query = f"""
                SELECT squat_kg, bench_kg, deadlift_kg, total_kg
                FROM {base_table}
                WHERE {where_clause}
                AND squat_kg > 0 AND bench_kg > 0 AND deadlift_kg > 0 AND total_kg > 0
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if len(results) < 10:
                return {"error": "Insufficient data for distribution"}
            
            # Calculate distributions for each lift
            distributions = {}
            lift_names = ['squat', 'bench', 'deadlift', 'total']
            
            for i, lift_name in enumerate(lift_names):
                data = [row[i] for row in results]
                
                # Create histogram with specified bins
                counts, bin_edges = np.histogram(data, bins=bins)
                
                # Normalize counts
                normalized_counts = counts / len(data)
                
                # Create bin centers for plotting
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                
                distributions[lift_name] = {
                    'bins': bin_centers.tolist(),
                    'counts': normalized_counts.tolist(),
                    'total_samples': len(data)
                }
            
            return {
                'distributions': distributions,
                'sample_size': len(results),
                'filters': filters
            }
    
    def _get_optimal_table(self, filters: Dict) -> str:
        """Select optimal table/view based on filters."""
        sex = filters.get('sex', 'M')
        country = filters.get('country')
        state = filters.get('state')
        
        # Use most specific view available
        if state and state != 'Any':
            return f"{sex.lower()}ales_by_state"
        elif country and country != 'Any':
            return f"{sex.lower()}ales_by_country"
        else:
            return f"{sex.lower()}ales_by_weight_class"


def lambda_handler(event, context):
    """Main Lambda handler."""
    try:
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        
        # CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'application/json'
        }
        
        # Handle preflight requests
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        db_service = DatabaseService()
        
        # Route requests
        if path.endswith('/metadata'):
            result = db_service.get_metadata()
        elif path.endswith('/percentiles'):
            # Parse filters from query parameters
            filters = {}
            for key, value in query_params.items():
                if value:
                    filters[key] = value
            result = db_service.get_percentiles(filters)
        elif path.endswith('/distribution'):
            # Parse filters and bins from query parameters  
            filters = {}
            bins = 50  # default
            for key, value in query_params.items():
                if key == 'bins':
                    bins = int(value)
                elif value:
                    filters[key] = value
            result = db_service.get_distribution_data(filters, bins)
        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }