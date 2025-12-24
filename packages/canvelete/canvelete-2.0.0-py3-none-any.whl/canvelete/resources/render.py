"""Render API resource."""

from typing import Optional, Dict, Any, Iterator


class RenderResource:
    """Handler for Render API endpoints."""
    
    def __init__(self, client):
        self.client = client
    
    def create(
        self,
        design_id: Optional[str] = None,
        template_id: Optional[str] = None,
        dynamic_data: Optional[Dict[str, Any]] = None,
        format: str = "png",
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: int = 90,
        output_file: Optional[str] = None,
    ) -> bytes:
        """
        Render a design or template to an image/PDF.
        
        Args:
            design_id: Design ID to render
            template_id: Template ID to render (alternative to design_id)
            dynamic_data: Dynamic data to inject into template
            format: Output format (png, jpg, jpeg, pdf)
            width: Output width (defaults to design width)
            height: Output height (defaults to design height)
            quality: Image quality (1-100)
            output_file: Optional path to save the output
        
        Returns:
            Binary image/PDF data
        
        Raises:
            ValidationError: If neither design_id nor template_id provided
        """
        if not design_id and not template_id:
            from ..exceptions import ValidationError
            raise ValidationError("Either design_id or template_id is required")
        
        payload = {
            "format": format.lower(),
            "quality": quality,
        }
        
        if design_id:
            payload["designId"] = design_id
        if template_id:
            payload["templateId"] = template_id
        if dynamic_data:
            payload["dynamicData"] = dynamic_data
        if width:
            payload["width"] = width
        if height:
            payload["height"] = height
        
        response = self.client.request(
            "POST",
            "/api/automation/render",
            json_data=payload,
        )
        
        # Response is binary data
        image_data = response.content
        
        # Save to file if requested
        if output_file:
            with open(output_file, "wb") as f:
                f.write(image_data)
        
        return image_data
    
    def list(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        List render history.
        
        Args:
            page: Page number (1-indexed)
            limit: Number of results per page
        
        Returns:
            Response with renders data and pagination info
        """
        params = {"page": page, "limit": limit}
        
        response = self.client.request(
            "GET",
            "/api/automation/render",
            params=params,
        )
        
        return response.json()
    
    def iterate_all(
        self,
        limit: int = 50,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate through all renders with automatic pagination.
        
        Args:
            limit: Number of results per page
        
        Yields:
            Individual render dictionaries
        """
        page = 1
        while True:
            response = self.list(page=page, limit=limit)
            
            renders = response.get("data", [])
            if not renders:
                break
            
            for render in renders:
                yield render
            
            # Check if there are more pages
            pagination = response.get("pagination", {})
            if page >= pagination.get("totalPages", 1):
                break
            
            page += 1

    def create_async(
        self,
        design_id: Optional[str] = None,
        template_id: Optional[str] = None,
        dynamic_data: Optional[Dict[str, Any]] = None,
        format: str = "png",
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: int = 90,
        webhook_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an async render job (queued).
        
        Args:
            design_id: Design ID to render
            template_id: Template ID to render
            dynamic_data: Dynamic data to inject
            format: Output format (png, jpg, pdf)
            width: Output width
            height: Output height
            quality: Image quality (1-100)
            webhook_url: Optional webhook URL for completion notification
        
        Returns:
            Render job data with ID and status
        
        Example:
            job = client.render.create_async(
                design_id="design_123",
                format="pdf",
                webhook_url="https://myapp.com/webhooks/render"
            )
            print(f"Job ID: {job['id']}, Status: {job['status']}")
        """
        if not design_id and not template_id:
            from ..exceptions import ValidationError
            raise ValidationError("Either design_id or template_id is required")
        
        payload = {
            "format": format.lower(),
            "quality": quality,
            "async": True,
        }
        
        if design_id:
            payload["designId"] = design_id
        if template_id:
            payload["templateId"] = template_id
        if dynamic_data:
            payload["dynamicData"] = dynamic_data
        if width:
            payload["width"] = width
        if height:
            payload["height"] = height
        if webhook_url:
            payload["webhookUrl"] = webhook_url
        
        response = self.client.request(
            "POST",
            "/api/v1/render",
            json_data=payload,
        )
        
        return response.json().get("data", {})
    
    def get_status(self, render_id: str) -> Dict[str, Any]:
        """
        Get render job status.
        
        Args:
            render_id: Render job ID
        
        Returns:
            Render status data
        
        Example:
            status = client.render.get_status("render_123")
            print(f"Status: {status['status']}")
            if status['status'] == 'completed':
                print(f"URL: {status['url']}")
        """
        response = self.client.request(
            "GET",
            f"/api/v1/render/{render_id}",
        )
        
        return response.json().get("data", {})
    
    def wait_for_completion(
        self,
        render_id: str,
        timeout: int = 300,
        poll_interval: int = 2,
    ) -> Dict[str, Any]:
        """
        Wait for a render job to complete.
        
        Args:
            render_id: Render job ID
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds
        
        Returns:
            Completed render data
        
        Raises:
            TimeoutError: If render doesn't complete within timeout
            
        Example:
            job = client.render.create_async(design_id="design_123")
            result = client.render.wait_for_completion(job['id'])
            print(f"Render complete: {result['url']}")
        """
        import time
        
        start_time = time.time()
        
        while True:
            status = self.get_status(render_id)
            
            if status["status"] == "completed":
                return status
            
            if status["status"] == "failed":
                raise Exception(f"Render failed: {status.get('error', 'Unknown error')}")
            
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Render did not complete within {timeout} seconds")
            
            time.sleep(poll_interval)
    
    def get_history(
        self,
        design_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get render history for a specific design.
        
        Args:
            design_id: Design ID
            page: Page number
            limit: Results per page
        
        Returns:
            Render history with pagination
        
        Example:
            history = client.render.get_history(design_id="design_123")
            for render in history["data"]:
                print(f"{render['createdAt']}: {render['format']} - {render['status']}")
        """
        params = {"page": page, "limit": limit}
        
        response = self.client.request(
            "GET",
            f"/api/v1/render/design/{design_id}/history",
            params=params,
        )
        
        return response.json()
    
    def batch_create(
        self,
        renders: list,
    ) -> list:
        """
        Create multiple render jobs in batch.
        
        Args:
            renders: List of render configurations
        
        Returns:
            List of created render jobs
        
        Example:
            jobs = client.render.batch_create([
                {"design_id": "design_1", "format": "png"},
                {"design_id": "design_2", "format": "pdf"},
                {"design_id": "design_3", "format": "jpg"}
            ])
            
            for job in jobs:
                print(f"Job {job['id']}: {job['status']}")
        """
        results = []
        
        for render_config in renders:
            try:
                job = self.create_async(**render_config)
                results.append(job)
            except Exception as e:
                results.append({
                    "error": str(e),
                    "config": render_config,
                })
        
        return results
    
    def wait_for_batch(
        self,
        jobs: list,
        timeout: int = 300,
    ) -> list:
        """
        Wait for multiple render jobs to complete.
        
        Args:
            jobs: List of render job data (from create_async or batch_create)
            timeout: Maximum wait time in seconds
        
        Returns:
            List of completed render results
        
        Example:
            jobs = client.render.batch_create([...])
            results = client.render.wait_for_batch(jobs, timeout=600)
            
            for result in results:
                if result.get('status') == 'completed':
                    print(f"Success: {result['url']}")
                else:
                    print(f"Failed: {result.get('error')}")
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def wait_for_job(job):
            try:
                return self.wait_for_completion(
                    job["id"],
                    timeout=timeout,
                    poll_interval=2,
                )
            except Exception as e:
                return {
                    "id": job["id"],
                    "status": "failed",
                    "error": str(e),
                }
        
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(wait_for_job, job): job for job in jobs}
            
            for future in as_completed(futures):
                results.append(future.result())
        
        return results
