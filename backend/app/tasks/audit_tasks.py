import logging
import asyncio
from app.tasks.celery_app import celery_app
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)

@celery_app.task(name='process_audit', bind=True, max_retries=3)
def process_audit_task(self, audit_id: str):
    """Background task to process audit"""
    try:
        logger.info(f"Processing audit {audit_id}")
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            audit_service.process_audit(audit_id)
        )
        loop.close()
        
        logger.info(f"Audit {audit_id} processed successfully")
        return {"status": "completed", "audit_id": audit_id}
        
    except Exception as e:
        logger.error(f"Error processing audit {audit_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
