def scope(func):
    """Decorator to mark a function as a query scope"""
    func._is_scope = True
    return func
