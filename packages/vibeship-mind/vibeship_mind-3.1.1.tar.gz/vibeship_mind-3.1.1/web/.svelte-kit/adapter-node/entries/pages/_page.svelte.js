import { x as ensure_array_like, y as attr_class } from "../../chunks/index.js";
import { e as escape_html } from "../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let terminalLines = [];
    let selectedTool = "mind_recall";
    const tools = {
      mind_recall: {
        name: "mind_recall()",
        category: "core",
        desc: "Load context at session start",
        output: `## Memory: Active
Last captured: 2 hours ago

## Reminders Due
- Review auth flow when we work on login

## Recent Decisions
- file-based storage (simpler, git-trackable)

## Continue From
Last: two-layer memory system`,
        explain: {
          what: "Loads everything Claude needs to remember about your project - past decisions, learnings, what you were working on, and any reminders.",
          auto: true,
          autoWhen: "Called automatically at the start of every session",
          manual: "Call manually if context feels stale or after long breaks"
        }
      },
      mind_log: {
        name: "mind_log(msg, type)",
        category: "core",
        desc: "Log to SESSION, MEMORY, or SELF_IMPROVE",
        output: `> mind_log("using flexbox for layout", type="experience")

{
  "success": true,
  "logged": "using flexbox for layout",
  "type": "experience",
  "target": "SESSION.md"
}`,
        explain: {
          what: "Saves thoughts, decisions, and learnings as you work. Routes by type: SESSION (experience, blocker, assumption, rejected), MEMORY (decision, learning, problem, progress), SELF_IMPROVE (feedback, preference, blind_spot, skill), or reinforce to boost pattern confidence.",
          auto: false,
          autoWhen: null,
          manual: "Claude calls this throughout your session to remember what's happening"
        }
      },
      mind_session: {
        name: "mind_session()",
        category: "reading",
        desc: "Check current session state",
        output: `## Experience
- trying flexbox approach
- user wants vibeship.co style

## Blockers
(none)

## Assumptions
- API returns JSON`,
        explain: {
          what: "Shows what's been logged in the current session - your experiences, blockers, rejected approaches, and assumptions.",
          auto: false,
          autoWhen: null,
          manual: "Useful to review what's happened so far or debug why Claude seems confused"
        }
      },
      mind_search: {
        name: "mind_search(query)",
        category: "reading",
        desc: "Search across memories",
        output: `> mind_search("authentication")

Found 3 results:
- [decision] use JWT for auth tokens
- [learning] Safari blocks third-party cookies
- [problem] CORS issue with auth endpoint`,
        explain: {
          what: "Searches through all your project memories to find relevant past decisions, learnings, and problems.",
          auto: false,
          autoWhen: null,
          manual: "Ask Claude to search when you need to recall why something was done a certain way"
        }
      },
      mind_status: {
        name: "mind_status()",
        category: "reading",
        desc: "Check memory health",
        output: `## Mind Status

Memory: 47 entries (12.3 KB)
Session: 4 items
Reminders: 2 pending
Stack: typescript, react

Health: OK`,
        explain: {
          what: "Quick health check - how many memories, file sizes, detected tech stack, and if everything's working.",
          auto: false,
          autoWhen: null,
          manual: "Run if Mind seems broken or you're curious about memory stats"
        }
      },
      mind_reminders: {
        name: "mind_reminders()",
        category: "reading",
        desc: "List pending reminders",
        output: `## Pending Reminders

1. [tomorrow] Review PR #42
2. [context: "auth"] Add rate limiting
3. [in 3 days] Update dependencies`,
        explain: {
          what: "Shows all your pending reminders - both time-based (tomorrow, in 3 days) and context-triggered (when you mention X).",
          auto: true,
          autoWhen: "Due reminders shown automatically in mind_recall()",
          manual: "Check the full list anytime you want to see what's pending"
        }
      },
      mind_blocker: {
        name: "mind_blocker(desc)",
        category: "actions",
        desc: "Log blocker + auto-search",
        output: `> mind_blocker("CORS error on API call")

Logged to SESSION.md

Searching memory for solutions...
Found: "Fixed CORS by adding proxy in vite.config"

Related gotcha: configure proxy for dev server`,
        explain: {
          what: "Logs what's blocking you AND automatically searches memory for related solutions. Two-in-one problem solver.",
          auto: false,
          autoWhen: null,
          manual: "Tell Claude you're stuck - it'll log it and try to find past solutions"
        }
      },
      mind_remind: {
        name: "mind_remind(msg, when)",
        category: "actions",
        desc: "Set time or context reminder",
        output: `> mind_remind("add tests", when="when I mention auth")

{
  "success": true,
  "type": "context",
  "triggers_on": "auth",
  "message": "add tests"
}`,
        explain: {
          what: "Set reminders that trigger by time (tomorrow, in 3 days) or by context (when you mention a topic).",
          auto: false,
          autoWhen: null,
          manual: "Say 'remind me to...' and Claude will set it up automatically"
        }
      },
      mind_reminder_done: {
        name: "mind_reminder_done(idx)",
        category: "actions",
        desc: "Mark reminder complete",
        output: `> mind_reminder_done(1)

{
  "success": true,
  "marked_done": "Review PR #42"
}`,
        explain: {
          what: "Marks a reminder as done so it stops showing up.",
          auto: true,
          autoWhen: "'Next session' reminders auto-mark when surfaced",
          manual: "Tell Claude you finished something it reminded you about"
        }
      },
      mind_edges: {
        name: "mind_edges(intent)",
        category: "actions",
        desc: "Check for gotchas before coding",
        output: `> mind_edges("implement file upload")

## Warnings

[!] Max file size varies by hosting provider
[!] Safari handles FormData differently
[!] Consider chunked upload for large files

Proceed with caution.`,
        explain: {
          what: "Checks for known gotchas before you implement something risky. Like a senior dev warning you about edge cases.",
          auto: false,
          autoWhen: null,
          manual: "Ask before implementing tricky features like auth, file upload, payments"
        }
      },
      mind_checkpoint: {
        name: "mind_checkpoint()",
        category: "actions",
        desc: "Force process pending memories",
        output: `Processing pending memories...

Indexed: 3 new entries
Promoted: 1 item from SESSION
Regenerated: MIND:CONTEXT

Done.`,
        explain: {
          what: "Forces Mind to process and index everything right now, instead of waiting for the next session.",
          auto: true,
          autoWhen: "Happens automatically on session gaps (>30 min)",
          manual: "Run after big changes if you want context updated immediately"
        }
      },
      mind_add_global_edge: {
        name: "mind_add_global_edge()",
        category: "actions",
        desc: "Add cross-project gotcha",
        output: `> mind_add_global_edge(
    title="Safari FormData",
    description="Safari handles FormData differently",
    workaround="Use polyfill or manual boundary"
  )

{
  "success": true,
  "added_to": "global_edges.json",
  "applies_to": ["javascript", "typescript"]
}`,
        explain: {
          what: "Adds a gotcha that applies across ALL your projects - platform bugs, language quirks, things every project should know.",
          auto: false,
          autoWhen: null,
          manual: "When you hit a gotcha that's not project-specific (browser bugs, OS quirks)"
        }
      }
    };
    const categories = [
      { id: "core", label: "Core" },
      { id: "reading", label: "Reading" },
      { id: "actions", label: "Actions" }
    ];
    $$renderer2.push(`<div class="hero svelte-1uha8ag"><h1 class="svelte-1uha8ag">Give Claude a <span class="highlight svelte-1uha8ag">Mind<span class="claude-underline svelte-1uha8ag"></span></span></h1> <p class="subtitle svelte-1uha8ag">Memory for Claude Code that persists across sessions.
		Decisions, learnings, and reminders.
		Install with 2 commands. Free forever.</p> <div class="terminal svelte-1uha8ag"><div class="terminal-header svelte-1uha8ag"><span class="terminal-dot svelte-1uha8ag"></span> <span class="terminal-dot svelte-1uha8ag"></span> <span class="terminal-dot svelte-1uha8ag"></span> <span class="terminal-title svelte-1uha8ag">mind_recall()</span></div> <div class="terminal-body svelte-1uha8ag"><!--[-->`);
    const each_array = ensure_array_like(terminalLines);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let line = each_array[$$index];
      if (line.startsWith(">")) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="line command svelte-1uha8ag">${escape_html(line)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        if (line.startsWith("Welcome")) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="line welcome svelte-1uha8ag">${escape_html(line)}</div>`);
        } else {
          $$renderer2.push("<!--[!-->");
          if (line.startsWith("##")) {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`<div class="line heading svelte-1uha8ag">${escape_html(line)}</div>`);
          } else {
            $$renderer2.push("<!--[!-->");
            if (line.startsWith("-")) {
              $$renderer2.push("<!--[-->");
              $$renderer2.push(`<div class="line item svelte-1uha8ag">${escape_html(line)}</div>`);
            } else {
              $$renderer2.push("<!--[!-->");
              if (line.startsWith("Implementing")) {
                $$renderer2.push("<!--[-->");
                $$renderer2.push(`<div class="line continue svelte-1uha8ag">${escape_html(line)}</div>`);
              } else {
                $$renderer2.push("<!--[!-->");
                $$renderer2.push(`<div class="line svelte-1uha8ag">${escape_html(line)}</div>`);
              }
              $$renderer2.push(`<!--]-->`);
            }
            $$renderer2.push(`<!--]-->`);
          }
          $$renderer2.push(`<!--]-->`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--> <span class="cursor svelte-1uha8ag">_</span></div></div> <div class="cta svelte-1uha8ag"><a href="https://github.com/vibeforge1111/vibeship-mind" class="btn btn-primary btn-lg svelte-1uha8ag">Get Started</a></div></div> <section class="features svelte-1uha8ag"><h2 class="svelte-1uha8ag">Why Mind?</h2> <p class="section-subtitle svelte-1uha8ag">Without memory, Claude starts every session blank. These problems go away.</p> <div class="feature-grid svelte-1uha8ag"><div class="feature svelte-1uha8ag"><h3 class="svelte-1uha8ag">Rabbit Holes</h3> <p class="svelte-1uha8ag">Claude goes down the wrong path for an hour before you notice. Mind tracks what's been tried so it doesn't loop.</p></div> <div class="feature svelte-1uha8ag"><h3 class="svelte-1uha8ag">Doesn't Remember You</h3> <p class="svelte-1uha8ag">Your preferences, your stack, your way of doing things - gone every session. Mind remembers who it's working with.</p></div> <div class="feature svelte-1uha8ag"><h3 class="svelte-1uha8ag">Session Memory Lost</h3> <p class="svelte-1uha8ag">Terminal closes. All that context? Vanished. Mind persists what matters between sessions.</p></div> <div class="feature svelte-1uha8ag"><h3 class="svelte-1uha8ag">Forgets What's Built</h3> <p class="svelte-1uha8ag">Claude references features that don't exist, or rebuilds things you have. Mind tracks what's done vs not.</p></div> <div class="feature svelte-1uha8ag"><h3 class="svelte-1uha8ag">Spaghetti Code</h3> <p class="svelte-1uha8ag">No memory means disconnected updates. Claude patches on patches. Mind keeps the full picture for coherent changes.</p></div> <div class="feature feature-highlight svelte-1uha8ag"><h3 class="svelte-1uha8ag">2 Commands to Fix All This</h3> <p class="svelte-1uha8ag">pip install, mind init. These problems stop. Fully automated after.</p></div></div></section> <section class="how-it-works svelte-1uha8ag"><h2 class="svelte-1uha8ag">How It Works</h2> <p class="section-subtitle svelte-1uha8ag">MCP tools run locally, filtering what's worth remembering into the right place.</p> <div class="architecture-flow svelte-1uha8ag"><div class="arch-box claude-code-box svelte-1uha8ag"><div class="arch-label svelte-1uha8ag">Claude Code</div> <div class="arch-desc svelte-1uha8ag">Working on your project</div></div> <div class="arch-connector svelte-1uha8ag"><span class="connector-line svelte-1uha8ag"></span> <span class="connector-label svelte-1uha8ag">calls MCP tools</span></div> <div class="arch-box mcp-box svelte-1uha8ag"><div class="arch-label svelte-1uha8ag">Mind MCP Server</div> <div class="mcp-tools-grid svelte-1uha8ag"><code class="svelte-1uha8ag">mind_recall()</code> <code class="svelte-1uha8ag">mind_log()</code> <code class="svelte-1uha8ag">mind_search()</code> <code class="svelte-1uha8ag">mind_blocker()</code> <code class="svelte-1uha8ag">mind_remind()</code> <code class="svelte-1uha8ag">mind_edges()</code></div> <div class="arch-desc svelte-1uha8ag">12 commands Claude can call when needed</div></div> <div class="arch-connector svelte-1uha8ag"><span class="connector-line svelte-1uha8ag"></span> <span class="connector-label svelte-1uha8ag">filters &amp; routes</span></div> <div class="arch-box storage-box svelte-1uha8ag"><div class="arch-label svelte-1uha8ag">.mind/ folder</div> <div class="storage-split svelte-1uha8ag"><div class="storage-side long-term svelte-1uha8ag"><div class="storage-header svelte-1uha8ag">Long-term Memory</div> <div class="storage-file svelte-1uha8ag">MEMORY.md</div> <div class="storage-items svelte-1uha8ag"><span class="svelte-1uha8ag">decisions</span> <span class="svelte-1uha8ag">learnings</span> <span class="svelte-1uha8ag">problems solved</span></div> <div class="storage-note svelte-1uha8ag">Persists forever. Worth remembering.</div></div> <div class="storage-divider svelte-1uha8ag"></div> <div class="storage-side short-term svelte-1uha8ag"><div class="storage-header svelte-1uha8ag">Short-term Memory</div> <div class="storage-file svelte-1uha8ag">SESSION.md</div> <div class="storage-items svelte-1uha8ag"><span class="svelte-1uha8ag">experiences</span> <span class="svelte-1uha8ag">assumptions</span> <span class="svelte-1uha8ag">current blockers</span></div> <div class="storage-note svelte-1uha8ag">Clears on session end. Working memory.</div></div></div></div> <div class="arch-connector svelte-1uha8ag"><span class="connector-line svelte-1uha8ag"></span> <span class="connector-label svelte-1uha8ag">injects context</span></div> <div class="arch-box context-box svelte-1uha8ag"><div class="arch-label svelte-1uha8ag">CLAUDE.md</div> <div class="arch-desc svelte-1uha8ag">Fresh context loaded every session</div></div></div> <div class="flow-section svelte-1uha8ag"><h3 class="svelte-1uha8ag">The Filtering Logic</h3> <p class="flow-explanation svelte-1uha8ag">When Claude logs something, Mind decides where it goes based on whether it's useful long-term:</p> <div class="filter-examples svelte-1uha8ag"><div class="filter-example svelte-1uha8ag"><div class="filter-input svelte-1uha8ag">"We decided to use Zustand for state"</div> <div class="filter-right svelte-1uha8ag"><div class="filter-arrow svelte-1uha8ag">→</div> <div class="filter-output memory svelte-1uha8ag">MEMORY.md <span class="why svelte-1uha8ag">future sessions need this</span></div></div></div> <div class="filter-example svelte-1uha8ag"><div class="filter-input svelte-1uha8ag">"Trying the flexbox approach now"</div> <div class="filter-right svelte-1uha8ag"><div class="filter-arrow svelte-1uha8ag">→</div> <div class="filter-output session svelte-1uha8ag">SESSION.md <span class="why svelte-1uha8ag">only matters right now</span></div></div></div> <div class="filter-example svelte-1uha8ag"><div class="filter-input svelte-1uha8ag">"Safari doesn't support :has() in older versions"</div> <div class="filter-right svelte-1uha8ag"><div class="filter-arrow svelte-1uha8ag">→</div> <div class="filter-output memory svelte-1uha8ag">MEMORY.md <span class="why svelte-1uha8ag">gotcha worth keeping</span></div></div></div></div></div></section> <section class="reminders svelte-1uha8ag"><h2 class="svelte-1uha8ag">Smart Reminders</h2> <p class="section-subtitle svelte-1uha8ag">Time-based or context-triggered. Never forget what matters.</p> <div class="reminders-grid svelte-1uha8ag"><div class="reminder-type svelte-1uha8ag"><div class="reminder-header svelte-1uha8ag">Time-Based</div> <div class="reminder-examples svelte-1uha8ag"><div class="reminder-example svelte-1uha8ag"><code class="svelte-1uha8ag">"tomorrow"</code> <span class="svelte-1uha8ag">Next day</span></div> <div class="reminder-example svelte-1uha8ag"><code class="svelte-1uha8ag">"in 3 days"</code> <span class="svelte-1uha8ag">Relative date</span></div> <div class="reminder-example svelte-1uha8ag"><code class="svelte-1uha8ag">"next session"</code> <span class="svelte-1uha8ag">On next recall</span></div> <div class="reminder-example svelte-1uha8ag"><code class="svelte-1uha8ag">"2025-12-25"</code> <span class="svelte-1uha8ag">Specific date</span></div></div></div> <div class="reminder-type svelte-1uha8ag"><div class="reminder-header svelte-1uha8ag">Context-Based</div> <div class="reminder-examples svelte-1uha8ag"><div class="reminder-example svelte-1uha8ag"><code class="svelte-1uha8ag">"when I mention auth"</code> <span class="svelte-1uha8ag">Keyword trigger</span></div> <div class="reminder-example svelte-1uha8ag"><code class="svelte-1uha8ag">"when we work on API"</code> <span class="svelte-1uha8ag">Topic trigger</span></div></div> <div class="reminder-note svelte-1uha8ag">Surfaces automatically when relevant keywords appear in conversation.</div></div></div></section> <section class="tools svelte-1uha8ag"><h2 class="svelte-1uha8ag">12 MCP Tools</h2> <p class="section-subtitle svelte-1uha8ag">Click a command to see what it does</p> <div class="tool-explorer svelte-1uha8ag"><div class="tool-list svelte-1uha8ag"><!--[-->`);
    const each_array_1 = ensure_array_like(categories);
    for (let $$index_2 = 0, $$length = each_array_1.length; $$index_2 < $$length; $$index_2++) {
      let cat = each_array_1[$$index_2];
      $$renderer2.push(`<div class="tool-category-section svelte-1uha8ag"><div class="tool-category-label svelte-1uha8ag">${escape_html(cat.label)}</div> <!--[-->`);
      const each_array_2 = ensure_array_like(Object.entries(tools).filter(([_, t]) => t.category === cat.id));
      for (let $$index_1 = 0, $$length2 = each_array_2.length; $$index_1 < $$length2; $$index_1++) {
        let [key, tool] = each_array_2[$$index_1];
        $$renderer2.push(`<button${attr_class("tool-item svelte-1uha8ag", void 0, { "active": selectedTool === key })}><code class="svelte-1uha8ag">${escape_html(tool.name)}</code> <span class="svelte-1uha8ag">${escape_html(tool.desc)}</span></button>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="tool-output-wrapper svelte-1uha8ag"><div class="tool-output svelte-1uha8ag"><div class="tool-output-header svelte-1uha8ag"><span class="tool-output-dot svelte-1uha8ag"></span> <span class="tool-output-dot svelte-1uha8ag"></span> <span class="tool-output-dot svelte-1uha8ag"></span> <span class="tool-output-title svelte-1uha8ag">${escape_html(tools[selectedTool].name)}</span></div> <div class="tool-output-body svelte-1uha8ag"><pre class="svelte-1uha8ag">${escape_html(tools[selectedTool].output)}</pre></div></div> <div class="tool-explain svelte-1uha8ag"><div class="tool-explain-what svelte-1uha8ag"><p class="svelte-1uha8ag">${escape_html(tools[selectedTool].explain.what)}</p></div> <div class="tool-explain-usage svelte-1uha8ag">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="usage-tag auto svelte-1uha8ag"><span class="tag-label svelte-1uha8ag">Auto</span> <span class="tag-desc svelte-1uha8ag">${escape_html(tools[selectedTool].explain.autoWhen)}</span></div>`);
    }
    $$renderer2.push(`<!--]--> <div class="usage-tag manual svelte-1uha8ag"><span class="tag-label svelte-1uha8ag">Manual</span> <span class="tag-desc svelte-1uha8ag">${escape_html(tools[selectedTool].explain.manual)}</span></div></div></div></div></div></section> <section class="get-started-cta svelte-1uha8ag"><h2 class="svelte-1uha8ag">Ready to Give Claude a <span class="highlight svelte-1uha8ag">Mind</span>?</h2> <p class="svelte-1uha8ag">2 commands. Zero friction.</p> <div class="install-steps svelte-1uha8ag"><div class="install-step svelte-1uha8ag"><div class="step-label svelte-1uha8ag">1. Install Mind</div> <div class="install-preview svelte-1uha8ag"><button class="copy-btn svelte-1uha8ag">Copy</button> <code class="svelte-1uha8ag">pip install vibeship-mind</code></div></div> <div class="install-step svelte-1uha8ag"><div class="step-label svelte-1uha8ag">2. Initialize in your project</div> <div class="install-preview svelte-1uha8ag"><button class="copy-btn svelte-1uha8ag">Copy</button> <code class="svelte-1uha8ag">cd your-project</code> <code class="svelte-1uha8ag">mind init</code></div></div> <div class="install-step svelte-1uha8ag"><div class="step-label svelte-1uha8ag">3. Connect to Claude Code</div> <div class="mcp-config-box svelte-1uha8ag"><button class="copy-btn svelte-1uha8ag">Copy</button> <div class="config-label svelte-1uha8ag">Add to your MCP config:</div> <pre class="svelte-1uha8ag">{
  "mcpServers": {
    "mind": {
      "command": "mind",
      "args": ["mcp"]
    }
  }
}</pre></div> <div class="step-note svelte-1uha8ag">Then say: "Let's run The Mind"</div></div></div> <div class="cta-buttons svelte-1uha8ag"><a href="https://pypi.org/project/vibeship-mind/" class="btn btn-primary btn-lg svelte-1uha8ag" target="_blank">View on PyPI</a> <a href="https://github.com/vibeforge1111/vibeship-mind" class="btn btn-secondary btn-lg svelte-1uha8ag" target="_blank">GitHub</a></div></section> <footer class="svelte-1uha8ag"><p class="svelte-1uha8ag">Built by <a href="https://x.com/meta_alchemist" target="_blank" class="svelte-1uha8ag">@meta_alchemist</a>  · 
		A <a href="https://vibeship.co" target="_blank" class="svelte-1uha8ag">vibeship.co</a> project</p></footer>`);
  });
}
export {
  _page as default
};
