// Run with: node --test tests/ui/dashboard.test.cjs
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const html = fs.readFileSync("sentinel/web/index.html", "utf8");
function dashboard() {
  const elements = new Map(
    [...html.matchAll(/id="([^"]+)"/g)].map(([, id]) => [
      id,
      {
        value: "",
        checked: false,
        disabled: false,
        textContent: "",
        innerHTML: "",
        className: "",
        parentElement: {},
        attributes: {},
        handlers: {},
        setAttribute(k, v) {
          this.attributes[k] = v;
        },
        addEventListener(k, f) {
          this.handlers[k] = f;
        },
        querySelector() {
          return this.innerHTML.includes("<button") ? {} : null;
        },
      },
    ]),
  );
  const context = vm.createContext({
    document: {
      getElementById: (id) => elements.get(id),
      querySelectorAll: () => [],
      hidden: false,
    },
    AbortSignal,
    URLSearchParams,
    setInterval() {},
    fetch: async () => ({ ok: true, json: async () => [] }),
  });
  // Exercise functions independently of startup network traffic.
  const script = html
    .split("<script>")[1]
    .split("</script>")[0]
    .replace(/updateMode\(\);\s*loadEnvironment\(\);\s*refresh\(\);/, "");
  vm.runInContext(script, context);
  return { elements, context, run: (code) => vm.runInContext(code, context) };
}
const ledger = (project) => ({
  project_path: project,
  findings: [],
  source_files: [],
  final_verification_state: "no_candidates",
  analyzer_runs: [],
  feedback: [],
});
test("evidence is escaped in text and HTML attributes", () => {
  const { run } = dashboard();
  assert.equal(run(`escape('"<script>')`), "&quot;&lt;script&gt;");
  assert.match(
    run(`gate('<img src=x>', 'warn', '<script>bad()</script>')`),
    /&lt;script&gt;/,
  );
});
test("report selection preserves the new assessment draft", () => {
  const { elements, context, run } = dashboard();
  elements.get("path").value = "/draft/project";
  context.state = ledger("/saved/project");
  run("renderLedger(state)");
  assert.equal(elements.get("path").value, "/draft/project");
  assert.match(elements.get("conclusion").innerHTML, /coverage was incomplete/);
});
test("a slow older selection cannot replace the newest selection", async () => {
  const { elements, context, run } = dashboard();
  let resolveOld;
  context.request = async (url) => {
    if (url.endsWith("/artifacts")) return [];
    if (url.endsWith("/old"))
      return new Promise((resolve) => {
        resolveOld = resolve;
      });
    return ledger("/new-project");
  };
  const old = run("loadLedger('old')");
  await run("loadLedger('new')");
  resolveOld(ledger("/old-project"));
  await old;
  assert.equal(run("selected"), "new");
  assert.equal(elements.get("results").attributes["aria-busy"], "false");
});
test("refresh failures show a connection error rather than an empty history", async () => {
  const { elements, context, run } = dashboard();
  context.request = async () => {
    throw new Error("offline");
  };
  await run("refresh()");
  assert.match(
    elements.get("sync-status").textContent,
    /Connection unavailable/,
  );
  assert.match(elements.get("scan-list").innerHTML, /Cannot load assessments/);
});
test("unchanged polling preserves history buttons and keyboard focus", async () => {
  const { elements, context, run } = dashboard();
  context.records = [
    {
      ledger_name: "one.json",
      final_state: "verified",
      findings: 1,
      confirmed: 1,
    },
  ];
  context.request = async () => context.records;
  run("scans=records;selected='one.json';renderScanList()");
  elements.get("scan-list").innerHTML += "<!-- focus sentinel -->";
  await run("refresh()");
  assert.match(elements.get("scan-list").innerHTML, /focus sentinel/);
});

test("live status names the current tool without exposing command arguments", () => {
  const { elements, context, run } = dashboard();
  context.event = { category: "phase", status: "started", summary: "scout" };
  run("updateActivity(event)");
  assert.equal(
    elements.get("notice").textContent,
    "Sentinel · Analyzing contracts…",
  );
  context.event = {
    category: "command",
    status: "started",
    summary:
      "/usr/bin/myth analyze /private/project/Vault.sol --execution-timeout 60",
  };
  run("updateActivity(event)");
  assert.equal(elements.get("notice").textContent, "Running Mythril analysis…");
  assert.match(elements.get("activity-context").textContent, /symbolic analysis/);
  assert.doesNotMatch(elements.get("activity-context").textContent, /private|Vault.sol|--/);
  context.event.status = "completed";
  run("updateActivity(event)");
  assert.equal(
    elements.get("notice").textContent,
    "Sentinel · Analyzing contracts…",
  );
  assert.match(elements.get("activity-context").textContent, /Scout is collecting/);
  context.event = {
    category: "phase",
    status: "started",
    summary: "blue team",
  };
  run("updateActivity(event)");
  assert.equal(
    elements.get("notice").textContent,
    "Blue team · Patching the vulnerable code…",
  );
});

test("findings emphasize severity and evidence without absolute locations", () => {
  const { context, run } = dashboard();
  run("displayRoots=['/Users/alice/Private Project']");
  context.finding = {
    severity: "high",
    status: "candidate",
    description: "Reentrancy\nAn external call occurs before a balance update.",
    file: "/Users/alice/Private Project/src/Vault.sol",
    line: 13,
    source: "slither",
    detector: "reentrancy",
    evidence: ["See /Users/alice/Private Project/src/Vault.sol"],
  };
  const output = run("observationRow(finding)");
  assert.match(output, /severity high/);
  assert.match(output, /Scanner detected/);
  assert.match(output, /Vault.sol:13/);
  assert.match(output, /external call/);
  assert.doesNotMatch(output, /Users|alice|Private Project/);
  context.finding.description = "<img src=x onerror=alert(1)> external call";
  assert.doesNotMatch(run("observationRow(finding)"), /<img/);
});

test("visible patch uses recorded diff and marks changed lines", () => {
  const { context, elements, run } = dashboard();
  context.state = {
    ...ledger("/project"),
    original_source: { "src/Vault.sol": "call();\nbalance = 0;" },
    patched_source: { "src/Vault.sol": "balance = 0;\ncall();" },
    patch_diff:
      "--- src/Vault.sol\n+++ src/Vault.sol\n@@ -1,2 +1,2 @@\n+balance = 0;\n call();\n-balance = 0;",
    patch_artifact: {
      original_file: "src/Vault.sol",
      rationale: "Update balance before calling.",
    },
    judge_result: { verified: true },
  };
  run("renderRepair(state)");
  assert.equal(elements.get("repair-status").textContent, "Verified");
  const html = elements.get("repair").innerHTML;
  assert.match(html, /aria-label="Patch diff"/);
  assert.match(html, /aria-label="Original code"/);
  assert.match(html, /aria-label="Repaired code"/);
  assert.match(html, /removed-line/);
  assert.match(html, /added-line/);
  assert.doesNotMatch(html, /<details/);
  assert.match(html, /Update balance before calling/);
  context.state.judge_result.verified = false;
  run("renderRepair(state)");
  assert.match(elements.get("repair-status").textContent, /Not verified/);
});
test("missing patch data is explicit and does not invent repaired code", () => {
  const { context, elements, run } = dashboard();
  context.state = { ...ledger("/project"), scout_only: true };
  run("renderRepair(state)");
  assert.match(elements.get("repair").innerHTML, /No repair was attempted/);
  assert.doesNotMatch(elements.get("repair").innerHTML, /source-code/);
});

test("groups matching reentrancy signals but preserves unrelated rules and files", () => {
  const { context, run } = dashboard();
  context.findings = [
    {
      id: "root",
      status: "confirmed",
      detector: "external-call-order",
      file: "src/Vault.sol",
      line: 13,
    },
    {
      id: "slither",
      status: "candidate",
      detector: "reentrancy-eth",
      file: "src/Vault.sol",
      line: 11,
      description: "Reentrancy in Vault.withdraw() (src/Vault.sol#11-16):",
    },
    {
      id: "support",
      status: "candidate",
      detector: "SWC-107",
      file: "src/Vault.sol",
      line: 15,
    },
    {
      id: "separate",
      status: "candidate",
      detector: "SWC-114",
      file: "src/Vault.sol",
      line: 13,
    },
    {
      id: "other-file",
      status: "candidate",
      detector: "SWC-107",
      file: "test/Vault.sol",
      line: 13,
    },
    {
      id: "other-function",
      status: "candidate",
      detector: "SWC-107",
      file: "src/Vault.sol",
      line: 30,
    },
    {
      id: "info",
      status: "candidate",
      severity: "informational",
      detector: "solc-version",
      file: "src/Vault.sol",
      line: 1,
    },
  ];
  const groups = run("groupFindings(findings)");
  assert.equal(groups.roots.length, 1);
  assert.equal(groups.roots[0].anchor.id, "slither");
  assert.deepEqual(
    Array.from(groups.roots[0].supporting, (f) => f.id),
    ["slither", "support"],
  );
  assert.deepEqual(
    Array.from(groups.candidates, (f) => f.id),
    ["separate", "other-file", "other-function"],
  );
  assert.equal(groups.technical[0].id, "info");
  assert.equal(context.findings.length, 7);
});
test("verification reports unavailable gates as not run, never passed", () => {
  const { context, elements, run } = dashboard();
  context.state = ledger("/project");
  run("renderVerification(state)");
  assert.equal(
    (elements.get("verification").innerHTML.match(/Not run/g) || []).length,
    4,
  );
  assert.doesNotMatch(elements.get("verification").innerHTML, /✓/);
  context.state = {
    ...ledger("/project"),
    exploit_confirmed: true,
    compilation_result: { success: true },
    regression_result: { success: false },
    exploit_result: { exit_code: 1 },
    judge_result: { build_passed: true, exploit_neutralized: true },
  };
  run("renderVerification(state)");
  assert.match(elements.get("verification").innerHTML, /✓ Blocked/);
  assert.match(elements.get("verification").innerHTML, /! Failed/);
});
test("primary assessment has no raw signal dump", () => {
  const { context, elements, run } = dashboard();
  context.state = {
    ...ledger("/project"),
    findings: [
      {
        id: "r",
        status: "confirmed",
        file: "Vault.sol",
        line: 1,
        severity: "high",
        source: "local-heuristic",
        description: "External call before state update",
        detector: "external-call-order",
      },
    ],
    patch_artifact: {},
    judge_result: { verified: true },
  };
  run("renderAssessment(state,true)");
  assert.match(
    elements.get("conclusion").innerHTML,
    /1 confirmed vulnerability/,
  );
  assert.match(
    elements.get("findings").innerHTML,
    /Detected by · Sentinel heuristic/,
  );
  assert.match(html, /<h2>Other observations/);
});

test("downloads expose readable audit and complete evidence files as downloads", () => {
  const { elements, run, context } = dashboard();
  context.names = [
    "sentinel-report-20260929.json",
    "sentinel-report-20260929.md",
    "sentinel-report-20260929.sarif",
    "sentinel-report-20260929__Vault.patch.sol",
  ];
  run("renderDownloads(names)");
  const output = elements.get("artifacts").innerHTML;
  assert.match(output, /Complete evidence · JSON/);
  assert.match(output, /Audit report · Markdown/);
  assert.match(
    output,
    /download href="\/reports\/sentinel-report-20260929.json"/,
  );
  assert.doesNotMatch(output, /Technical details|Other files|Vault.patch.sol/);
  assert.equal((output.match(/class="download-link"/g) || []).length, 3);
});
test("lifecycle animation is enabled only for an active assessment", () => {
  const { elements, run } = dashboard();
  run("setRunning(true)");
  assert.equal(elements.get("phases").className, "stage-track is-running");
  run("setRunning(false)");
  assert.equal(elements.get("phases").className, "stage-track");
});

test("critical candidates join key findings without becoming confirmed", () => {
  const { context, elements, run } = dashboard();
  context.state = {
    ...ledger("/project"),
    findings: [
      {
        id: "critical",
        severity: "critical",
        status: "candidate",
        description: "Critical candidate",
        file: "Vault.sol",
        line: 2,
      },
      {
        id: "low",
        severity: "low",
        status: "candidate",
        description: "Low candidate",
        file: "Vault.sol",
        line: 4,
      },
      {
        id: "unknown",
        severity: "unknown",
        status: "candidate",
        description: "Unknown candidate",
        file: "Vault.sol",
        line: 5,
      },
    ],
  };
  run("renderAssessment(state, true)");
  const primary = elements.get("findings").innerHTML;
  assert.match(primary, /Critical candidate/);
  assert.match(primary, /Scanner detected/);
  assert.doesNotMatch(primary, /confirmed-label/);
  const secondary = elements.get("observations").innerHTML;
  assert.doesNotMatch(secondary, /Critical candidate/);
  assert.ok(
    secondary.indexOf("Low candidate") < secondary.indexOf("Unknown candidate"),
  );
});

test("observation cards disclose details and explain actual validation coverage", () => {
  const { context, run } = dashboard();
  context.finding = {
    id: "one",
    severity: "medium",
    status: "candidate",
    detector: "SWC-104",
    source: "mythril",
    description: "Raw technical description",
    evidence: ["<script>unsafe</script>"],
  };
  const card = run("observationRow(finding, {candidate_id:'another'})");
  assert.match(card, /^<details class="observation">/);
  const face = card.split("</summary>")[0];
  assert.match(face, /A failed external call may go unnoticed/);
  assert.doesNotMatch(face, /Raw technical description|Needs validation/);
  assert.match(card, /not individually exploit-tested/i);
  assert.doesNotMatch(card, /<script>/);
  context.finding.description = "<script>unsafe</script>";
  assert.match(run("scannerEvidence(finding)"), /&lt;script&gt;/);
  assert.match(
    run("observationRow(finding, {scout_only:true})"),
    /Detection-only assessment/,
  );
  assert.match(
    run(
      "observationRow(finding, {candidate_id:'one', final_verification_state:'execution_unavailable'})",
    ),
    /execution tool was unavailable/,
  );
  context.finding.status = "discarded";
  assert.match(run("observationRow(finding)"), /Not reproduced/);
});
