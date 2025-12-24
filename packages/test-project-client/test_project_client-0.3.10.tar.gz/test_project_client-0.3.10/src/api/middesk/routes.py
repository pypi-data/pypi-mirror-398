from fastapi import APIRouter, Depends
from src.api.dependencies import get_context
from src.business.context import ServiceContext
import src.platform.hooks as platform_hooks

router = APIRouter(prefix="/middesk", tags=["middesk"])

