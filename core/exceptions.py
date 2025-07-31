class DatabaseError(Exception):
    """Base database exception"""
    pass

class MonitoringError(Exception):
    """Monitoring related errors"""
    pass

class TelethonError(Exception):
    """Telethon client exceptions"""
    pass

class ConfigError(Exception):
    """Configuration errors"""
    pass