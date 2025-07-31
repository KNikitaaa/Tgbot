from .admin import router as admin_router
from .commands import router as commands_router

routers = [
    commands_router,
    admin_router
]

__all__ = ['routers']