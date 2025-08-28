"""FastAPI server for powerlifting statistics queries."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sqlite3
import os
from pydantic import BaseModel
import numpy as np

app = FastAPI(title="Powerlifting Statistics API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = "../data-processing/powerlifting.db"

class FilterOptions(BaseModel):
    sex: str
    equipment: str
    weightClass: str
    ageDiv: str = "All"
    tested: str = "Any"
    country: str = "All"
    state: str = "All"
    federation: str = "All"
    year: str = "All"
    meetName: str = "All"

class LiftStatistics(BaseModel):
    mean: float
    median: float
    min: float
    max: float
    std: float
    percentile25: float
    percentile75: float
    percentile90: float
    percentile95: float
    percentile99: float

class StatisticsResult(BaseModel):
    sampleSize: int
    squat: LiftStatistics
    bench: LiftStatistics
    deadlift: LiftStatistics
    total: LiftStatistics

class PercentileResult(BaseModel):
    squat: float
    bench: float
    deadlift: float
    total: float

def get_database_connection():
    """Get database connection."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found")
    return sqlite3.connect(DB_PATH)

def build_where_clause(filters: FilterOptions) -> tuple[str, list]:
    """Build WHERE clause for SQL query based on filters."""
    conditions = []
    params = []
    
    # Required filters
    conditions.append("sex = ?")
    params.append(filters.sex)
    
    conditions.append("equipment = ?")
    params.append(filters.equipment)
    
    conditions.append("weight_class = ?")
    params.append(filters.weightClass)
    
    # Optional filters
    if filters.ageDiv != "All":
        conditions.append("age_div = ?")
        params.append(filters.ageDiv)
    
    if filters.tested != "Any":
        conditions.append("tested = ?")
        params.append(filters.tested)
    
    if filters.country != "All":
        conditions.append("country = ?")
        params.append(filters.country)
    
    if filters.state != "All":
        conditions.append("state = ?")
        params.append(filters.state)
    
    if filters.federation != "All":
        conditions.append("federation = ?")
        params.append(filters.federation)
    
    if filters.year != "All":
        conditions.append("year = ?")
        params.append(int(filters.year))
    
    if filters.meetName != "All":
        conditions.append("meet_name = ?")
        params.append(filters.meetName)
    
    where_clause = " AND ".join(conditions)
    return where_clause, params

def calculate_lift_statistics(values: List[float]) -> LiftStatistics:
    """Calculate comprehensive statistics for a list of lift values."""
    if not values:
        return LiftStatistics(
            mean=0, median=0, min=0, max=0, std=0,
            percentile25=0, percentile75=0, percentile90=0, 
            percentile95=0, percentile99=0
        )
    
    np_values = np.array(values)
    
    return LiftStatistics(
        mean=round(float(np.mean(np_values)), 1),
        median=round(float(np.median(np_values)), 1),
        min=round(float(np.min(np_values)), 1),
        max=round(float(np.max(np_values)), 1),
        std=round(float(np.std(np_values)), 1),
        percentile25=round(float(np.percentile(np_values, 25)), 1),
        percentile75=round(float(np.percentile(np_values, 75)), 1),
        percentile90=round(float(np.percentile(np_values, 90)), 1),
        percentile95=round(float(np.percentile(np_values, 95)), 1),
        percentile99=round(float(np.percentile(np_values, 99)), 1)
    )

@app.post("/api/statistics")
async def get_statistics(filters: FilterOptions) -> StatisticsResult:
    """Get comprehensive statistics for the filtered dataset."""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        where_clause, params = build_where_clause(filters)
        
        # Get all lift data for statistical calculations
        query = f"""
        SELECT squat_kg, bench_kg, deadlift_kg, total_kg
        FROM lifts 
        WHERE {where_clause}
        AND squat_kg > 0 AND bench_kg > 0 AND deadlift_kg > 0 AND total_kg > 0
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            conn.close()
            return StatisticsResult(
                sampleSize=0,
                squat=LiftStatistics(mean=0, median=0, min=0, max=0, std=0, 
                                   percentile25=0, percentile75=0, percentile90=0, 
                                   percentile95=0, percentile99=0),
                bench=LiftStatistics(mean=0, median=0, min=0, max=0, std=0, 
                                    percentile25=0, percentile75=0, percentile90=0, 
                                    percentile95=0, percentile99=0),
                deadlift=LiftStatistics(mean=0, median=0, min=0, max=0, std=0, 
                                      percentile25=0, percentile75=0, percentile90=0, 
                                      percentile95=0, percentile99=0),
                total=LiftStatistics(mean=0, median=0, min=0, max=0, std=0, 
                                    percentile25=0, percentile75=0, percentile90=0, 
                                    percentile95=0, percentile99=0)
            )
        
        # Separate lift values
        squat_values = [row[0] for row in results if row[0] > 0]
        bench_values = [row[1] for row in results if row[1] > 0]
        deadlift_values = [row[2] for row in results if row[2] > 0]
        total_values = [row[3] for row in results if row[3] > 0]
        
        # Calculate statistics for each lift
        stats_result = StatisticsResult(
            sampleSize=len(results),
            squat=calculate_lift_statistics(squat_values),
            bench=calculate_lift_statistics(bench_values),
            deadlift=calculate_lift_statistics(deadlift_values),
            total=calculate_lift_statistics(total_values)
        )
        
        conn.close()
        return stats_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/percentiles")
async def get_percentiles(
    filters: FilterOptions,
    squat_kg: float,
    bench_kg: float,
    deadlift_kg: float,
    total_kg: float
) -> PercentileResult:
    """Get user percentiles within the filtered dataset."""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        where_clause, params = build_where_clause(filters)
        
        # Calculate percentiles for each lift
        percentiles = {}
        lifts = {
            'squat': ('squat_kg', squat_kg),
            'bench': ('bench_kg', bench_kg),
            'deadlift': ('deadlift_kg', deadlift_kg),
            'total': ('total_kg', total_kg)
        }
        
        for lift_name, (column, user_value) in lifts.items():
            # Count total lifts and lifts below user's value
            query_total = f"""
            SELECT COUNT(*) 
            FROM lifts 
            WHERE {where_clause} AND {column} > 0
            """
            
            query_below = f"""
            SELECT COUNT(*) 
            FROM lifts 
            WHERE {where_clause} AND {column} > 0 AND {column} < ?
            """
            
            cursor.execute(query_total, params)
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                percentiles[lift_name] = 0.0
            else:
                cursor.execute(query_below, params + [user_value])
                below_count = cursor.fetchone()[0]
                percentile = round((below_count / total_count) * 100, 1)
                percentiles[lift_name] = percentile
        
        conn.close()
        
        return PercentileResult(
            squat=percentiles['squat'],
            bench=percentiles['bench'],
            deadlift=percentiles['deadlift'],
            total=percentiles['total']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/filter-options/{filter_type}")
async def get_filter_options(
    filter_type: str,
    sex: str = Query(...),
    equipment: str = Query(...),
    weightClass: str = Query(...),
    ageDiv: str = Query(default="All"),
    tested: str = Query(default="Any"),
    country: str = Query(default="All"),
    state: str = Query(default="All"),
    federation: str = Query(default="All"),
    year: str = Query(default="All"),
) -> List[str]:
    """Get available options for a specific filter based on current filter state."""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build base filters (excluding the one we're querying)
        base_filters = FilterOptions(
            sex=sex,
            equipment=equipment,
            weightClass=weightClass,
            ageDiv=ageDiv,
            tested=tested,
            country=country,
            state=state,
            federation=federation,
            year=year
        )
        
        where_clause, params = build_where_clause(base_filters)
        
        # Remove the condition for the filter we're querying
        if filter_type in ['country', 'state', 'federation', 'year', 'meetName']:
            # Rebuild where clause excluding this filter
            temp_filters = base_filters.dict()
            temp_filters[filter_type] = "All"
            temp_filter_obj = FilterOptions(**temp_filters)
            where_clause, params = build_where_clause(temp_filter_obj)
        
        # Map filter type to column name
        column_map = {
            'country': 'country',
            'state': 'state', 
            'federation': 'federation',
            'year': 'year',
            'meetName': 'meet_name'
        }
        
        if filter_type not in column_map:
            raise HTTPException(status_code=400, detail="Invalid filter type")
        
        column = column_map[filter_type]
        
        query = f"""
        SELECT DISTINCT {column}
        FROM lifts
        WHERE {where_clause} AND {column} IS NOT NULL AND {column} != ''
        ORDER BY {column}
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        options = ['All'] + [str(row[0]) for row in results]
        
        conn.close()
        return options
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/metadata")
async def get_metadata():
    """Get basic metadata about the dataset."""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get basic counts
        cursor.execute("SELECT COUNT(*) FROM lifts")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT country) FROM lifts WHERE country IS NOT NULL")
        countries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT meet_name) FROM lifts WHERE meet_name IS NOT NULL")
        meets = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(year), MAX(year) FROM lifts WHERE year IS NOT NULL")
        year_range = cursor.fetchone()
        
        # Get unique values for key filters
        cursor.execute("SELECT DISTINCT equipment FROM lifts ORDER BY equipment")
        equipment_types = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT age_div FROM lifts ORDER BY age_div")
        age_divisions = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT tested FROM lifts ORDER BY tested")
        tested_statuses = [row[0] for row in cursor.fetchall()]
        
        # Get weight classes by sex
        cursor.execute("SELECT DISTINCT weight_class FROM lifts WHERE sex = 'M' ORDER BY CAST(REPLACE(weight_class, '+', '') AS INTEGER)")
        weight_classes_m = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT weight_class FROM lifts WHERE sex = 'F' ORDER BY CAST(REPLACE(weight_class, '+', '') AS INTEGER)")
        weight_classes_f = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_records": total_records,
            "countries": countries,
            "meets": meets,
            "date_range": {
                "min_year": year_range[0],
                "max_year": year_range[1]
            },
            "equipment_types": equipment_types,
            "age_divisions": age_divisions,
            "tested_statuses": tested_statuses,
            "weight_classes": {
                "M": weight_classes_m,
                "F": weight_classes_f
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)