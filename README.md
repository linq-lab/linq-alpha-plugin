# LinqAlpha plugins for Claude

The public marketplace for LinqAlpha's Claude plugins. Adding this repository as
a marketplace makes every plugin below installable in Claude Code, Cowork and
Claude Desktop.

| Plugin | What it adds |
|---|---|
| `linq-alpha` | The LinqAlpha connector plus guide-first research skills for financial data |

## Add the marketplace

**Claude Code**

```
/plugin marketplace add linq-lab/linq-alpha-plugin
/plugin install linq-alpha@linq-alpha
```

**Cowork and Claude Desktop**

Open **Customize → Plugins**, press **+** in *Personal plugins*, choose **Add
marketplace**, and enter `linq-lab/linq-alpha-plugin`. The plugins in this
repository then appear alongside the ones from Anthropic's catalog.

A personal marketplace is scoped to you alone; it does not change what your
organization requires or distributes.

**Distributed by your organization**

Team and Enterprise owners can install a plugin for everyone instead. An
organization marketplace has to live in a private or internal repository, so
point that repository's `.claude-plugin/marketplace.json` at this one rather
than adding this repository directly:

```json
{
  "plugins": [
    {
      "name": "linq-alpha",
      "source": { "source": "github", "repo": "linq-lab/linq-alpha-plugin" }
    }
  ]
}
```

## Updates

Claude compares the `version` in each plugin's `.claude-plugin/plugin.json`
against the copy you have installed. Press **Update** on the marketplace, or run
`/plugin marketplace update linq-alpha`, to pull the current tree.

## Source

Published from LinqAlpha's internal repository on every merge to `main`. Pull
requests are not accepted here — the commits in this repository are generated.
Send issues and questions to support@linqalpha.com.
