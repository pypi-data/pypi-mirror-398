import asyncio

import typer

from nlbone.adapters.ticketing.client import CreateTicketIn, TicketingClient

app = typer.Typer(add_completion=False)


@app.command("create")
def send_sample():
    payload = CreateTicketIn(
        assignee_id="153",
        category_id=2,
        channel="site_chat",
        direction="incoming",
        entity_id="153",
        entity_type="user",
        message="سلام خوبی",
        priority="medium",
        product_id=0,
        status="open",
        title="پشتیبانی فنی (ثبت نام و لاگین)",
        user_id=153,
    )
    client = TicketingClient()
    asyncio.run(client.create_ticket(payload, created_by_id=995836))
    print("Ticket message published (or logged if Noop).")


if __name__ == "__main__":
    app()
