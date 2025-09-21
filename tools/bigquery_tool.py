"""
BigQuery tool for the Trip Planner ADK application.

This tool provides functionality to cache and retrieve POI data,
reviews, and analytics using Google BigQuery.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from adk import Tool

from schemas import POI, TripRequest

logger = logging.getLogger(__name__)


class BigQueryTool(Tool):
    """BigQuery tool for caching POI data and analytics."""
    
    def __init__(self, project_id: str, dataset_id: str, location: str = "US"):
        """Initialize BigQuery tool."""
        super().__init__("bigquery_tool", "BigQuery data caching and analytics tool")
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.location = location
        self.client = None
        
        try:
            self.client = bigquery.Client(project=project_id)
            self._ensure_dataset_exists()
            self._ensure_tables_exist()
            logger.info(f"BigQuery tool initialized for project {project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute BigQuery operations."""
        if operation == "cache_poi":
            return self.cache_poi(**kwargs)
        elif operation == "get_popular_pois":
            return self.get_popular_pois(**kwargs)
        elif operation == "log_trip_analytics":
            return self.log_trip_analytics(**kwargs)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _initialize_tables(self):
        """Initialize BigQuery tables if they don't exist."""
        try:
            # Check if dataset exists, create if not
            try:
                self.client.get_dataset(self.dataset_ref)
            except NotFound:
                dataset = bigquery.Dataset(self.dataset_ref)
                dataset.location = "US"
                self.client.create_dataset(dataset)
                logger.info(f"Created dataset {self.dataset}")
            
            # Define table schemas
            self._create_pois_table()
            self._create_reviews_table()
            self._create_search_cache_table()
            self._create_trip_analytics_table()
            
        except Exception as e:
            logger.error(f"Error initializing BigQuery tables: {e}")
    
    def _create_pois_table(self):
        """Create the POIs table if it doesn't exist."""
        table_id = f"{self.project_id}.{self.dataset}.pois"
        
        schema = [
            bigquery.SchemaField("poi_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("latitude", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("longitude", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("address", "JSON", mode="REQUIRED"),
            bigquery.SchemaField("rating", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("review_count", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("price_level", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("opening_hours", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("website", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("phone", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("photos", "STRING", mode="REPEATED"),
            bigquery.SchemaField("amenities", "STRING", mode="REPEATED"),
            bigquery.SchemaField("suitable_for_groups", "STRING", mode="REPEATED"),
            bigquery.SchemaField("estimated_visit_duration", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("popularity_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("accessibility_features", "STRING", mode="REPEATED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED")
        ]
        
        self._create_table_if_not_exists(table_id, schema)
    
    def _create_reviews_table(self):
        """Create the reviews table if it doesn't exist."""
        table_id = f"{self.project_id}.{self.dataset}.reviews"
        
        schema = [
            bigquery.SchemaField("review_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("poi_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("author_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("rating", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("text", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("language", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
        ]
        
        self._create_table_if_not_exists(table_id, schema)
    
    def _create_search_cache_table(self):
        """Create the search cache table if it doesn't exist."""
        table_id = f"{self.project_id}.{self.dataset}.search_cache"
        
        schema = [
            bigquery.SchemaField("cache_key", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("location", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("search_params", "JSON", mode="REQUIRED"),
            bigquery.SchemaField("results", "JSON", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("expires_at", "TIMESTAMP", mode="REQUIRED")
        ]
        
        self._create_table_if_not_exists(table_id, schema)
    
    def _create_trip_analytics_table(self):
        """Create the trip analytics table if it doesn't exist."""
        table_id = f"{self.project_id}.{self.dataset}.trip_analytics"
        
        schema = [
            bigquery.SchemaField("trip_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("destination", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("start_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("end_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("group_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("budget_range", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("total_cost", "NUMERIC", mode="NULLABLE"),
            bigquery.SchemaField("poi_count", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
        ]
        
        self._create_table_if_not_exists(table_id, schema)
    
    def _create_table_if_not_exists(self, table_id: str, schema: List[bigquery.SchemaField]):
        """Create a table if it doesn't exist."""
        try:
            self.client.get_table(table_id)
        except NotFound:
            table = bigquery.Table(table_id, schema=schema)
            self.client.create_table(table)
            logger.info(f"Created table {table_id}")
    
    def cache_poi(self, poi: POI) -> bool:
        """
        Cache a POI in BigQuery.
        
        Args:
            poi: POI object to cache
            
        Returns:
            True if successful, False otherwise
        """
        try:
            table_id = f"{self.project_id}.{self.dataset}.pois"
            
            row = {
                "poi_id": poi.id,
                "name": poi.name,
                "description": poi.description,
                "category": poi.category.value,
                "latitude": poi.coordinates.latitude,
                "longitude": poi.coordinates.longitude,
                "address": poi.address.dict(),
                "rating": poi.rating,
                "review_count": poi.review_count,
                "price_level": poi.price_level,
                "opening_hours": poi.opening_hours,
                "website": poi.website,
                "phone": poi.phone,
                "photos": poi.photos,
                "amenities": poi.amenities,
                "suitable_for_groups": [g.value for g in poi.suitable_for_groups],
                "estimated_visit_duration": poi.estimated_visit_duration,
                "popularity_score": poi.popularity_score,
                "accessibility_features": poi.accessibility_features,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            table = self.client.get_table(table_id)
            errors = self.client.insert_rows_json(table, [row])
            
            if errors:
                logger.error(f"Error caching POI {poi.id}: {errors}")
                return False
            
            logger.info(f"Cached POI {poi.id} in BigQuery")
            return True
            
        except Exception as e:
            logger.error(f"Error caching POI {poi.id}: {e}")
            return False
    
    def get_cached_pois(
        self,
        location: str,
        radius_km: float = 10,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve cached POIs near a location.
        
        Args:
            location: Location coordinates as "lat,lng"
            radius_km: Search radius in kilometers
            category: POI category filter
            limit: Maximum number of results
            
        Returns:
            List of cached POI data
        """
        try:
            lat, lng = map(float, location.split(','))
            
            query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset}.pois`
            WHERE ST_DWITHIN(
                ST_GEOGPOINT(longitude, latitude),
                ST_GEOGPOINT({lng}, {lat}),
                {radius_km * 1000}
            )
            """
            
            if category:
                query += f" AND category = '{category}'"
            
            query += f" ORDER BY rating DESC LIMIT {limit}"
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            pois = []
            for row in results:
                poi_data = dict(row)
                pois.append(poi_data)
            
            logger.info(f"Retrieved {len(pois)} cached POIs near {location}")
            return pois
            
        except Exception as e:
            logger.error(f"Error retrieving cached POIs: {e}")
            return []
    
    def get_popular_pois(
        self,
        destination: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get popular POIs by review count and rating.
        
        Args:
            destination: Destination city/area
            category: POI category filter
            limit: Maximum number of results
            
        Returns:
            List of popular POI data
        """
        try:
            query = f"""
            SELECT *,
                   (rating * LOG(review_count + 1)) as popularity_score
            FROM `{self.project_id}.{self.dataset}.pois`
            WHERE LOWER(JSON_EXTRACT_SCALAR(address, '$.city')) LIKE '%{destination.lower()}%'
               OR LOWER(JSON_EXTRACT_SCALAR(address, '$.formatted_address')) LIKE '%{destination.lower()}%'
            """
            
            if category:
                query += f" AND category = '{category}'"
            
            query += f"""
            ORDER BY popularity_score DESC
            LIMIT {limit}
            """
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            pois = []
            for row in results:
                poi_data = dict(row)
                pois.append(poi_data)
            
            logger.info(f"Retrieved {len(pois)} popular POIs for {destination}")
            return pois
            
        except Exception as e:
            logger.error(f"Error retrieving popular POIs: {e}")
            return []
    
    def cache_search_results(
        self,
        cache_key: str,
        location: str,
        search_params: Dict[str, Any],
        results: List[Dict[str, Any]],
        ttl_hours: int = 24
    ) -> bool:
        """
        Cache search results with TTL.
        
        Args:
            cache_key: Unique cache key
            location: Search location
            search_params: Search parameters used
            results: Search results to cache
            ttl_hours: Time to live in hours
            
        Returns:
            True if successful, False otherwise
        """
        try:
            table_id = f"{self.project_id}.{self.dataset}.search_cache"
            
            expires_at = datetime.utcnow().replace(microsecond=0)
            expires_at = expires_at.replace(hour=expires_at.hour + ttl_hours)
            
            row = {
                "cache_key": cache_key,
                "location": location,
                "search_params": search_params,
                "results": results,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at
            }
            
            table = self.client.get_table(table_id)
            errors = self.client.insert_rows_json(table, [row])
            
            if errors:
                logger.error(f"Error caching search results: {errors}")
                return False
            
            logger.info(f"Cached search results with key {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching search results: {e}")
            return False
    
    def get_cached_search_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached search results if not expired.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached results or None if not found/expired
        """
        try:
            query = f"""
            SELECT results
            FROM `{self.project_id}.{self.dataset}.search_cache`
            WHERE cache_key = '{cache_key}'
              AND expires_at > CURRENT_TIMESTAMP()
            ORDER BY created_at DESC
            LIMIT 1
            """
            
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            if results:
                cached_data = results[0]['results']
                logger.info(f"Retrieved cached search results for key {cache_key}")
                return cached_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached search results: {e}")
            return None
    
    def log_trip_analytics(self, trip_request: TripRequest, itinerary_data: Dict[str, Any]) -> bool:
        """
        Log trip analytics data.
        
        Args:
            trip_request: Original trip request
            itinerary_data: Generated itinerary data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            table_id = f"{self.project_id}.{self.dataset}.trip_analytics"
            
            row = {
                "trip_id": itinerary_data.get("id", ""),
                "user_id": trip_request.user_id,
                "destination": trip_request.destination,
                "start_date": trip_request.start_date.isoformat(),
                "end_date": trip_request.end_date.isoformat(),
                "group_type": trip_request.group_type.value,
                "budget_range": trip_request.budget_range.value,
                "total_cost": float(itinerary_data.get("total_cost", 0)),
                "poi_count": len(itinerary_data.get("pois", [])),
                "created_at": datetime.utcnow()
            }
            
            table = self.client.get_table(table_id)
            errors = self.client.insert_rows_json(table, [row])
            
            if errors:
                logger.error(f"Error logging trip analytics: {errors}")
                return False
            
            logger.info(f"Logged trip analytics for trip {row['trip_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging trip analytics: {e}")
            return False
    
    def get_destination_analytics(self, destination: str) -> Dict[str, Any]:
        """
        Get analytics for a destination.
        
        Args:
            destination: Destination to analyze
            
        Returns:
            Analytics data
        """
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_trips,
                AVG(total_cost) as avg_cost,
                AVG(poi_count) as avg_poi_count,
                group_type,
                budget_range,
                COUNT(*) as count
            FROM `{self.project_id}.{self.dataset}.trip_analytics`
            WHERE LOWER(destination) LIKE '%{destination.lower()}%'
            GROUP BY group_type, budget_range
            ORDER BY count DESC
            """
            
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            analytics = {
                "destination": destination,
                "total_trips": 0,
                "average_cost": 0,
                "average_poi_count": 0,
                "popular_groups": [],
                "popular_budgets": []
            }
            
            if results:
                analytics["total_trips"] = results[0]["total_trips"]
                analytics["average_cost"] = float(results[0]["avg_cost"] or 0)
                analytics["average_poi_count"] = float(results[0]["avg_poi_count"] or 0)
                
                for row in results[:3]:  # Top 3 group types
                    analytics["popular_groups"].append({
                        "group_type": row["group_type"],
                        "count": row["count"]
                    })
                
                for row in results[:3]:  # Top 3 budget ranges
                    analytics["popular_budgets"].append({
                        "budget_range": row["budget_range"],
                        "count": row["count"]
                    })
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting destination analytics: {e}")
            return {}