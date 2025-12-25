# bctrl

**Remote browser automation for AI agents**

Run browser automation code locally while browsers execute on remote servers.

## Status

The Python SDK is under development. For now, use the TypeScript/JavaScript SDK:

```bash
npm install bctrl
```

## What is bctrl?

bctrl provides a seamless, local-feeling API for browser automation that actually executes on remote infrastructure. Instead of managing browser instances locally, your code sends stateless HTTP commands to a control plane that manages browser lifecycles on remote host machines.

**Features:**
- No local browser setup - browsers run remotely
- Anti-detection built-in via Kameleo
- Human-like mouse movements via ML
- AI-native with Stagehand integration
- Puppeteer, Playwright, or Selenium APIs

## Coming Soon

```python
from bctrl import BctrlClient

client = BctrlClient(base_url="http://your-control-plane:3000")

session = client.sessions.create(driver="playwright", humanize=True)

page = session.page
page.goto("https://example.com")
page.click("#login")

# AI-powered automation
session.stagehand.act("Search for 'TypeScript tutorials'")

session.stop()
```

## Links

- [GitHub](https://github.com/bctrl/bctrl)
- [TypeScript SDK](https://www.npmjs.com/package/bctrl)

## License

ISC
