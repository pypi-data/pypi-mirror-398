"""Usage tracking API resource."""

from typing import Optional, Dict, Any
from datetime import datetime


class UsageResource:
    """Handler for Usage tracking endpoints."""
    
    def __init__(self, client):
        self.client = client
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Returns:
            Usage statistics including credits, API calls, and limits
        
        Example:
            stats = client.usage.get_stats()
            print(f"Credits: {stats['creditsUsed']}/{stats['creditLimit']}")
            print(f"API Calls: {stats['apiCalls']}/{stats['apiCallLimit']}")
        """
        response = self.client.request(
            "GET",
            "/api/v1/usage/stats",
        )
        
        return response.json().get("data", {})
    
    def get_history(
        self,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get usage history.
        
        Args:
            page: Page number
            limit: Results per page
            start_date: Filter by start date
            end_date: Filter by end date
        
        Returns:
            Usage history with pagination
        
        Example:
            from datetime import datetime, timedelta
            
            history = client.usage.get_history(
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now()
            )
            
            for event in history["data"]:
                print(f"{event['type']}: {event['creditsUsed']} credits")
        """
        params = {"page": page, "limit": limit}
        
        if start_date:
            params["startDate"] = start_date.isoformat()
        if end_date:
            params["endDate"] = end_date.isoformat()
        
        response = self.client.request(
            "GET",
            "/api/v1/usage/history",
            params=params,
        )
        
        return response.json()
    
    def get_api_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.
        
        Returns:
            API usage statistics by endpoint
        
        Example:
            stats = client.usage.get_api_stats()
            for endpoint, count in stats["endpoints"].items():
                print(f"{endpoint}: {count} calls")
        """
        response = self.client.request(
            "GET",
            "/api/v1/usage/api-stats",
        )
        
        return response.json().get("data", {})
    
    def get_activities(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get recent usage activities.
        
        Args:
            page: Page number
            limit: Results per page
        
        Returns:
            Recent activities with details
        
        Example:
            activities = client.usage.get_activities(limit=10)
            for activity in activities["data"]:
                print(f"{activity['timestamp']}: {activity['action']}")
        """
        params = {"page": page, "limit": limit}
        
        response = self.client.request(
            "GET",
            "/api/usage/activities",
            params=params,
        )
        
        return response.json()
    
    def get_analytics(
        self,
        period: str = "month",
    ) -> Dict[str, Any]:
        """
        Get usage analytics.
        
        Args:
            period: Time period (day, week, month, year)
        
        Returns:
            Analytics data with trends
        
        Example:
            analytics = client.usage.get_analytics(period="month")
            print(f"Total renders: {analytics['totalRenders']}")
            print(f"Average per day: {analytics['averagePerDay']}")
        """
        params = {"period": period}
        
        response = self.client.request(
            "GET",
            "/api/usage/analytics",
            params=params,
        )
        
        return response.json().get("data", {})
