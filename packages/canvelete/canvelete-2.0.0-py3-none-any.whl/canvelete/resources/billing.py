"""Billing management API resource."""

from typing import Optional, Dict, Any


class BillingResource:
    """Handler for Billing management endpoints."""
    
    def __init__(self, client):
        self.client = client
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get billing information and subscription details.
        
        Returns:
            Billing information including plan, credits, and limits
        
        Example:
            billing = client.billing.get_info()
            print(f"Plan: {billing['plan']}")
            print(f"Credits: {billing['creditBalance']}/{billing['creditLimit']}")
            print(f"Next billing: {billing['nextBillingDate']}")
        """
        response = self.client.request(
            "GET",
            "/api/v1/billing/info",
        )
        
        return response.json().get("data", {})
    
    def get_invoices(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get invoice history.
        
        Args:
            page: Page number
            limit: Results per page
        
        Returns:
            Invoice history with pagination
        
        Example:
            invoices = client.billing.get_invoices()
            for invoice in invoices["data"]:
                print(f"{invoice['date']}: ${invoice['amount']} - {invoice['status']}")
        """
        params = {"page": page, "limit": limit}
        
        response = self.client.request(
            "GET",
            "/api/v1/billing/invoices",
            params=params,
        )
        
        return response.json()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get billing summary.
        
        Returns:
            Billing summary with totals and trends
        
        Example:
            summary = client.billing.get_summary()
            print(f"Total spent: ${summary['totalSpent']}")
            print(f"This month: ${summary['currentMonth']}")
        """
        response = self.client.request(
            "GET",
            "/api/v1/billing/summary",
        )
        
        return response.json().get("data", {})
    
    def purchase_credits(
        self,
        amount: int,
        payment_method_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Purchase additional credits.
        
        Args:
            amount: Number of credits to purchase
            payment_method_id: Optional payment method ID
        
        Returns:
            Purchase confirmation with new balance
        
        Example:
            purchase = client.billing.purchase_credits(
                amount=5000,
                payment_method_id="pm_123"
            )
            print(f"New balance: {purchase['newBalance']} credits")
        """
        payload = {"creditAmount": amount}
        
        if payment_method_id:
            payload["paymentMethodId"] = payment_method_id
        
        response = self.client.request(
            "POST",
            "/api/v1/billing/credits/purchase",
            json_data=payload,
        )
        
        return response.json().get("data", {})
    
    def get_seats(self) -> Dict[str, Any]:
        """
        Get team seats information.
        
        Returns:
            Team seats data including used and available seats
        
        Example:
            seats = client.billing.get_seats()
            print(f"Seats: {seats['used']}/{seats['total']}")
        """
        response = self.client.request(
            "GET",
            "/api/v1/billing/seats",
        )
        
        return response.json().get("data", {})
    
    def add_seats(
        self,
        count: int,
    ) -> Dict[str, Any]:
        """
        Add team seats.
        
        Args:
            count: Number of seats to add
        
        Returns:
            Updated seats information
        
        Example:
            seats = client.billing.add_seats(count=5)
            print(f"New total: {seats['total']} seats")
        """
        response = self.client.request(
            "POST",
            "/api/v1/billing/seats/add",
            json_data={"count": count},
        )
        
        return response.json().get("data", {})
    
    def remove_seats(
        self,
        count: int,
    ) -> Dict[str, Any]:
        """
        Remove team seats.
        
        Args:
            count: Number of seats to remove
        
        Returns:
            Updated seats information
        
        Example:
            seats = client.billing.remove_seats(count=2)
            print(f"New total: {seats['total']} seats")
        """
        response = self.client.request(
            "DELETE",
            "/api/v1/billing/seats/remove",
            json_data={"count": count},
        )
        
        return response.json().get("data", {})
    
    def get_portal_url(self) -> str:
        """
        Get billing portal URL for managing subscription.
        
        Returns:
            URL to billing portal
        
        Example:
            url = client.billing.get_portal_url()
            print(f"Manage subscription: {url}")
        """
        response = self.client.request(
            "GET",
            "/api/billing/portal",
        )
        
        return response.json().get("url", "")
