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
  recordScenario(
    "provider-unavailable",
    "dotnet-deliberate",
    ["START", "PROVIDER_ERROR", "RETRY", "PROVIDER_ERROR", "RETRY", "PROVIDER_ERROR"],
    "Retry budget returns the defense to pending and emits no mastery signal."
  ),
  recordScenario(
    "low-confidence",
    "dotnet-deliberate",
    ["START", "ANSWER", "ANSWER", "ANSWER", "LOW_CONFIDENCE"],
    "A completed bounded answer set with confidence below 0.75 routes to inconclusive/manual calibration."
  ),
  recordScenario(
    "technical-evidence-conflict",
    "dotnet-critical-misunderstanding",
    ["START", "ANSWER", "ANSWER", "ANSWER", "ANSWER", "ANSWER", "EVIDENCE_CONFLICT"],
    "Technical failure remains visible while the AI signal becomes inconclusive."
  ),
  recordScenario(
    "illegal-answer-before-start",
    "dotnet-deliberate",
    ["ANSWER"],
    "The reducer records the illegal transition without changing the pending defense or answer count."
  )
];

const evidence = {
  schemaVersion: "inside.adaptive-defense-failure-scenarios.v1",
  source: "defense-lab.html#DefenseSession",
  kind: "recorded-observations-not-tests",
  scenarios
};
const evidencePath = resolve(prototypeDirectory, "evidence", "failure-scenarios.json");
await writeFile(evidencePath, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
process.stdout.write(`Recorded ${scenarios.length} failure scenarios\nEvidence: ${evidencePath}\n`);

function recordScenario(id, fixtureId, actions, interpretation) {
  let state = DefenseSession.initial(fixtureId, fixtures[fixtureId]);
  for (const type of actions) state = DefenseSession.reduce(state, { type });
  return {
    id,
    fixtureId,
    actions,
    observed: {
      attemptState: state.attemptState,
      defenseState: state.defenseState,
      providerCalls: state.providerCalls,
      answersRecorded: state.answersRecorded,
      technicalResult: state.technicalResult,
      defenseSignal: state.defenseSignal,
      verifiedCandidate: state.verifiedCandidate,
      retryAfter: state.retryAfter,
      resolutionPath: state.resolutionPath,
      lastEvent: state.lastEvent
    },
    interpretation
  };
}
