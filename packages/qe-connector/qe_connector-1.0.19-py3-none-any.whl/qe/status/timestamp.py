def timestamp(self):
    """Get server timestamp (PUBLIC)
    
    Get server timestamp in milliseconds
    
    GET /timestamp
    
    Returns:
        int: Server timestamp in milliseconds
    """
    url_path = "/timestamp"
    response = self.query(url_path)
    return response.get("serverTimeMilli")
