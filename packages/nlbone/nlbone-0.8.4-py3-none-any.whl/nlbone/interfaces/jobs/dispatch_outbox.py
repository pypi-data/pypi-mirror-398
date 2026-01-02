from nlbone.adapters.messaging.internal_router import internal_router
from nlbone.core.ports.event_bus import IntegrationPublisher


def run_dispatch_outbox(outbox_repo, publisher: IntegrationPublisher):
    batch = outbox_repo.fetch_pending(limit=200)
    for rec in batch:
        try:
            topic = rec["topic"]
            payload = rec["payload"]
            if topic.startswith("internal."):
                internal_router.handle(topic, payload)
            else:
                publisher.publish(topic, payload)
            outbox_repo.mark_sent(rec["id"])
        # except TemporaryError:
        #     outbox_repo.schedule_retry(rec["id"], rec["retries"])
        except Exception:
            # mark_failed یا retry policy
            outbox_repo.schedule_retry(rec["id"], rec["retries"])
