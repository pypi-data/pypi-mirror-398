import httpx

from .engine import Agent, Curli, Store, Tools

class Space:
    account = Store(profile = "anon")
    session = Store(profile = "main")

space = Space()
curli = Curli(httpx, session_store=space.session, account_store=space.account)
agent = Agent(curli)
tools = Tools()

curli.default(headers={
    "accept": "application/json",
    "Content-Type": "application/json",
})
