from fastapi import APIRouter, Depends
from pushikoo.api.security import verify_token
from pushikoo.api.v1.pip import router as pip_router
from pushikoo.api.v1.adapter import router as adapter_router
from pushikoo.api.v1.instance import router as instance_router
from pushikoo.api.v1.message import router as message_router
from pushikoo.api.v1.warning import router as warning_router
from pushikoo.api.v1.cron import router as cron_router
from pushikoo.api.v1.system import router as system_router
from pushikoo.api.v1.oauth import router as oauth_router
from pushikoo.api.v1.flow import router as flow_router

__all__ = ["oauth_router"]

router = APIRouter(prefix="/v1", tags=["v1"], dependencies=[Depends(verify_token)])
router.include_router(pip_router)
router.include_router(adapter_router)
router.include_router(instance_router)
router.include_router(message_router)
router.include_router(warning_router)
router.include_router(cron_router)
router.include_router(system_router)
router.include_router(flow_router)
