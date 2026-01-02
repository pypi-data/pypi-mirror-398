import click
from a2a.client.agent_client import AgentClient

@click.command()
@click.argument("url")
def ping(url):
    client = AgentClient(url)
    print(client.send({"type": "HEARTBEAT"}))

if __name__ == "__main__":
    ping()
