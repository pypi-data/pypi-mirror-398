from typing import Any, Optional
from src.business.context import ServiceContext

async def on_request(ctx: ServiceContext, verb: str, input_data: Any) -> None:
    """
    Platform hook triggered before business logic execution.
    Can be used for logging, metrics, quota checks, etc.
    """
    # Example: Platform-level logging
    ctx.logger.info(f"[PLATFORM] Request starting for operation: {verb}", extra={"input": input_data.model_dump() if hasattr(input_data, 'model_dump') else input_data})

async def on_response(ctx: ServiceContext, verb: str, result: Any) -> None:
    """
    Platform hook triggered after business logic execution.
    """
    ctx.logger.info(f"[PLATFORM] Request completed for operation: {verb}")

async def on_error(ctx: ServiceContext, verb: str, error: Exception) -> None:
    """
    Platform hook triggered on exception.
    """
    ctx.logger.error(f"[PLATFORM] Error in operation: {verb} - {str(error)}")
