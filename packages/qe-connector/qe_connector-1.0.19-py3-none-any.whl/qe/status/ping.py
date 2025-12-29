def ping(self):
    """Ping to server (PUBLIC)
    
    Test connectivity to the server
    
    GET /ping
    
    Returns:
        None if successful, raises exception if failed
    """
    url_path = "/ping"
    return self.query(url_path)
