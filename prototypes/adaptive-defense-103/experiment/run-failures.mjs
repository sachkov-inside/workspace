#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const experimentDirectory = dirname(fileURLToPath(import.meta.url));
const prototypeDirectory = resolve(experimentDirectory, "..");
const html = await readFile(resolve(prototypeDirectory, "defense-lab.html"), "utf8");
const inlineScript = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
if (!inlineScript) throw new Error("defense-lab.html must contain one inline script");

const moduleEnd = inlineScript.indexOf("    const walkthroughs =");
const { fixtures, DefenseSession } = new Function(
  `${inlineScript.slice(0, moduleEnd)}; return { fixtures, DefenseSession };`
)();

const scenarios = [
  runScenario("provider-unavailable", "dotnet-deliberate", [
    "START", "PROVIDER_ERROR", "RETRY", "PROVIDER_ERROR", "RETRY", "PROVIDER_ERROR"
  ], {
    attemptState: "defense_pending",
    defenseState: "pending",
    providerCalls: 3,
    defenseSignal: "—",
    verifiedCandidate: false,
    resolutionPath: "manual/support; no negative signal"
  }),
  runScenario("low-confidence", "dotnet-deliberate", ["START", "LOW_CONFIDENCE"], {
    attemptState: "evaluated",
    defenseState: "completed",
    defenseSignal: "inconclusive",
    verifiedCandidate: false,
    resolutionPath: "manual calibration or new Attempt"
  }),
  runScenario("technical-evidence-conflict", "dotnet-critical-misunderstanding", [
    "START", "EVIDENCE_CONFLICT"
  ], {
    technicalResult: "Технические проверки не пройдены",
    defenseSignal: "inconclusive",
    verifiedCandidate: false,
    resolutionPath: "manual calibration or new Attempt"
  }),
  runScenario("illegal-answer-before-start", "dotnet-deliberate", ["ANSWER"], {
    attemptState: "defense_pending",
    defenseState: "pending",
    answersRecorded: 0
  }, "Ignored illegal transition:")
];

if (scenarios.some((scenario) => !scenario.passed)) {
  throw new Error(`failure-mode mismatch: ${JSON.stringify(scenarios, null, 2)}`);
}

const evidence = {
  schemaVersion: "inside.adaptive-defense-failure-runs.v1",
  source: "defense-lab.html#DefenseSession",
  scenarios
};
const evidencePath = resolve(prototypeDirectory, "evidence", "failure-runs.json");
await writeFile(evidencePath, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
process.stdout.write(`PASS: ${scenarios.length} failure-mode runs\nEvidence: ${evidencePath}\n`);

function runScenario(id, fixtureId, actions, expected, lastEventPrefix) {
  let state = DefenseSession.initial(fixtureId, fixtures[fixtureId]);
  for (const type of actions) state = DefenseSession.reduce(state, { type });
  const observed = Object.fromEntries(Object.keys(expected).map((key) => [key, state[key]]));
  const fieldsMatch = Object.entries(expected).every(([key, value]) => state[key] === value);
  const eventMatches = lastEventPrefix === undefined || state.lastEvent.startsWith(lastEventPrefix);
  return { id, actions, expected, observed, passed: fieldsMatch && eventMatches };
}
