#!/usr/bin/env node

import { spawn } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { performance } from "node:perf_hooks";

const experimentDirectory = dirname(fileURLToPath(import.meta.url));
const prototypeDirectory = resolve(experimentDirectory, "..");
const fixturesPath = resolve(experimentDirectory, "fixtures.json");
const schemaPath = resolve(experimentDirectory, "defense-output.schema.json");
const promptPath = resolve(experimentDirectory, "system-prompt.md");
const evidenceDirectory = resolve(prototypeDirectory, "evidence");
const rawEvidencePath = resolve(evidenceDirectory, "model-runs.json");
const summaryPath = resolve(evidenceDirectory, "summary.json");

const requestedRuns = Number.parseInt(process.argv[2] ?? "3", 10);
if (!Number.isInteger(requestedRuns) || requestedRuns < 1 || requestedRuns > 5) {
  throw new Error("Usage: node experiment/run.mjs [runs-per-fixture: 1..5]");
}

const [fixtures, instructions] = await Promise.all([
  readJson(fixturesPath),
  readFile(promptPath, "utf8")
]);

const jobs = fixtures.attempts.flatMap((attempt) =>
  Array.from({ length: requestedRuns }, (_, index) => ({
    attempt,
    repetition: index + 1
  }))
);

const codexVersion = await captureCommand("codex", ["--version"]);
const results = [];
const workerCount = Math.min(3, jobs.length);
let nextJob = 0;

await mkdir(evidenceDirectory, { recursive: true });
await Promise.all(Array.from({ length: workerCount }, async () => {
  while (nextJob < jobs.length) {
    const jobIndex = nextJob;
    nextJob += 1;
    const job = jobs[jobIndex];
    const result = await runFixture(job.attempt, job.repetition);
    results.push(result);
    process.stdout.write(
      `[${results.length}/${jobs.length}] ${result.fixtureId} run ${result.repetition}: ` +
      `${result.output.assessment.defenseSignal}, ${Math.round(result.latencyMs)} ms\n`
    );
  }
}));

results.sort((left, right) =>
  left.fixtureId.localeCompare(right.fixtureId) || left.repetition - right.repetition
);

const evidence = {
  schemaVersion: "inside.adaptive-defense-experiment.v1",
  environment: {
    providerHarness: codexVersion.trim(),
    model: "gpt-5.4",
    reasoningEffort: "low",
    platform: process.platform,
    architecture: process.arch,
    node: process.version,
    runsPerFixture: requestedRuns,
    concurrency: workerCount,
    note: "Provider usage includes the Codex agent runtime prompt; this is an upper bound, not production API billing."
  },
  results
};
const summary = summarize(fixtures.attempts, evidence);

await Promise.all([
  writeJson(rawEvidencePath, evidence),
  writeJson(summaryPath, summary)
]);

process.stdout.write(`Evidence: ${rawEvidencePath}\nSummary: ${summaryPath}\n`);

async function runFixture(attempt, repetition) {
  const temporaryDirectory = await mkdtemp(resolve(tmpdir(), "inside-defense-103-"));
  const outputPath = resolve(temporaryDirectory, "last-message.json");
  const prompt = [
    instructions.trim(),
    "",
    "Return JSON matching the provided schema for this attempt:",
    JSON.stringify({
      fixtureId: attempt.id,
      caseSpec: normalizeCaseSpec(fixtures.caseSpec),
      attempt: normalizeAttempt(attempt)
    }, null, 2)
  ].join("\n");

  const argumentsList = [
    "exec",
    "--ignore-user-config",
    "--ignore-rules",
    "--ephemeral",
    "--skip-git-repo-check",
    "-s", "read-only",
    "-m", "gpt-5.4",
    "-c", "model_reasoning_effort=\"low\"",
    "--output-schema", schemaPath,
    "--json",
    "-o", outputPath,
    "-"
  ];

  const startedAt = performance.now();
  try {
    const execution = await spawnWithInput("codex", argumentsList, prompt, temporaryDirectory);
    const latencyMs = performance.now() - startedAt;
    if (execution.exitCode !== 0) {
      throw new Error(
        `codex exited ${execution.exitCode}: ${execution.stderr}\n${execution.stdout}`
      );
    }
    const output = await readJson(outputPath);
    const usage = parseUsage(execution.stdout);
    return {
      fixtureId: attempt.id,
      repetition,
      sourceFingerprint: attempt.sourceFingerprint,
      expectedCalibration: attempt.calibrationExpectation,
      promptUtf8Bytes: Buffer.byteLength(prompt),
      latencyMs,
      usage,
      output
    };
  } finally {
    await rm(temporaryDirectory, { recursive: true, force: true });
  }
}

function omitCalibration(attempt) {
  const { calibrationExpectation: _calibrationExpectation, ...modelInput } = attempt;
  return modelInput;
}

function normalizeCaseSpec(caseSpec) {
  return {
    ...caseSpec,
    businessFacts: caseSpec.businessFacts.map((fact, index) => ({
      id: `case:fact:${index + 1}`,
      fact
    })),
    rubric: caseSpec.rubric.map((item) => ({
      id: `rubric:${item.dimension}`,
      ...item
    }))
  };
}

function normalizeAttempt(attempt) {
  const modelInput = omitCalibration(attempt);
  return {
    ...modelInput,
    technicalEvidence: {
      reportVerdict: {
        id: "technical:verdict",
        value: attempt.technicalEvidence.reportVerdict
      },
      scenarios: attempt.technicalEvidence.scenarios.map((fact, index) => ({
        id: `technical:scenario:${index + 1}`,
        fact
      })),
      telemetry: attempt.technicalEvidence.telemetry.map((fact, index) => ({
        id: `technical:telemetry:${index + 1}`,
        fact
      }))
    },
    decisionRecord: [
      { id: "decision:before-code", text: attempt.decisionRecord.beforeCode },
      { id: "decision:after-code", text: attempt.decisionRecord.afterCode }
    ],
    defenseAnswers: attempt.defenseAnswers.map((answer) => ({
      id: `answer:${answer.topic}`,
      ...answer
    }))
  };
}

function parseUsage(jsonLines) {
  const events = jsonLines
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const completed = events.findLast((event) => event.type === "turn.completed");
  if (!completed?.usage) {
    throw new Error("codex output did not contain turn.completed usage");
  }
  return completed.usage;
}

function summarize(attempts, evidence) {
  const fixtureSummaries = attempts.map((attempt) => {
    const runs = evidence.results.filter((result) => result.fixtureId === attempt.id);
    const signals = runs.map((result) => result.output.assessment.defenseSignal);
    const validReferences = evidenceReferences(fixtures.caseSpec, attempt);
    const groundedQuestions = runs.flatMap((result) => result.output.questions).filter((question) =>
      question.groundedIn.length > 0 &&
      question.groundedIn.every((reference) => validReferences.has(reference))
    );
    const groundedSignals = runs
      .flatMap((result) => result.output.assessment.dimensionSignals)
      .filter((signal) =>
        signal.evidenceRefs.length > 0 &&
        signal.evidenceRefs.every((reference) => validReferences.has(reference))
    );
    const allQuestions = runs.flatMap((result) => result.output.questions);
    const allSignals = runs.flatMap((result) => result.output.assessment.dimensionSignals);
    return {
      fixtureId: attempt.id,
      expectedCalibration: attempt.calibrationExpectation,
      signals,
      unanimous: new Set(signals).size === 1,
      expectedMatches: signals.filter((signal) => signal === attempt.calibrationExpectation).length,
      questionGroundingRate: ratio(groundedQuestions.length, allQuestions.length),
      rubricGroundingRate: ratio(groundedSignals.length, allSignals.length),
      questionDimensions: [...new Set(allQuestions.map((question) => question.dimension))].sort()
    };
  });

  const latencies = evidence.results.map((result) => result.latencyMs).sort((a, b) => a - b);
  const usageTotals = evidence.results.reduce((totals, result) => {
    for (const [key, value] of Object.entries(result.usage)) {
      totals[key] = (totals[key] ?? 0) + value;
    }
    return totals;
  }, {});
  const correctSignals = fixtureSummaries.reduce((total, fixture) => total + fixture.expectedMatches, 0);
  const questionCount = evidence.results.reduce(
    (total, result) => total + result.output.questions.length,
    0
  );
  const groundedCount = fixtureSummaries.reduce((total, fixture) => {
    const fixtureQuestionCount = evidence.results
      .filter((result) => result.fixtureId === fixture.fixtureId)
      .reduce((count, result) => count + result.output.questions.length, 0);
    return total + fixture.questionGroundingRate * fixtureQuestionCount;
  }, 0);
  const rubricSignalCount = evidence.results.length * 4;
  const groundedRubricCount = fixtureSummaries.reduce(
    (total, fixture) => total + fixture.rubricGroundingRate * requestedRuns * 4,
    0
  );
  const provenanceViolations = evidence.results.filter(
    (result) => result.output.assessment.provenanceClaim !== "none"
  ).length;
  const technicalOverrideAttempts = evidence.results.filter(
    (result) => result.output.assessment.technicalEvidenceOverrideAttempted
  ).length;
  const apiCostEstimate = estimateGpt54ApiCost(usageTotals, evidence.results.length);

  return {
    schemaVersion: "inside.adaptive-defense-summary.v1",
    runCount: evidence.results.length,
    fixtureCount: attempts.length,
    expectedSignalMatches: correctSignals,
    expectedSignalRate: ratio(correctSignals, evidence.results.length),
    unanimousFixtures: fixtureSummaries.filter((fixture) => fixture.unanimous).length,
    questionGroundingRate: ratio(groundedCount, questionCount),
    rubricGroundingRate: ratio(groundedRubricCount, rubricSignalCount),
    provenanceViolations,
    technicalOverrideAttempts,
    latencyMs: {
      min: Math.round(latencies[0]),
      p50: Math.round(percentile(latencies, 0.5)),
      p95: Math.round(percentile(latencies, 0.95)),
      max: Math.round(latencies.at(-1))
    },
    usageTotals,
    apiCostEstimate,
    fixtures: fixtureSummaries,
    sameSourceCalibration: {
      fingerprint: "python-reference-like-v1",
      strongSignals: fixtureSummaries.find((fixture) => fixture.fixtureId === "python-reference-strong")?.signals,
      weakSignals: fixtureSummaries.find((fixture) => fixture.fixtureId === "python-reference-weak")?.signals
    }
  };
}

function estimateGpt54ApiCost(usage, callCount) {
  const pricePerMillion = {
    input: 2.5,
    cachedInput: 0.25,
    output: 15
  };
  const uncachedInputTokens = usage.input_tokens - usage.cached_input_tokens;
  const totalUsd = (
    uncachedInputTokens * pricePerMillion.input +
    usage.cached_input_tokens * pricePerMillion.cachedInput +
    usage.output_tokens * pricePerMillion.output
  ) / 1_000_000;
  const perCallUsd = totalUsd / callCount;
  return {
    kind: "derived-not-billed",
    checkedAt: "2026-09-03",
    source: "https://developers.openai.com/api/docs/models/gpt-5.4",
    pricePerMillion,
    uncachedInputTokens,
    totalUsd: Number(totalUsd.toFixed(6)),
    perCallUsd: Number(perCallUsd.toFixed(6)),
    typicalTwoCallDefenseUsd: Number((perCallUsd * 2).toFixed(6)),
    maximumThreeCallDefenseUsd: Number((perCallUsd * 3).toFixed(6)),
    caveat: "The experiment used a ChatGPT-authenticated Codex CLI, not API billing. The estimate applies public API rates to provider-reported usage, which includes Codex runtime context."
  };
}

function evidenceReferences(caseSpec, attempt) {
  return new Set([
    ...caseSpec.businessFacts.map((_fact, index) => `case:fact:${index + 1}`),
    ...caseSpec.rubric.map((item) => `rubric:${item.dimension}`),
    ...attempt.sourceEvidence.map((item) => item.id),
    "technical:verdict",
    ...attempt.technicalEvidence.scenarios.map((_fact, index) => `technical:scenario:${index + 1}`),
    ...attempt.technicalEvidence.telemetry.map((_fact, index) => `technical:telemetry:${index + 1}`),
    "decision:before-code",
    "decision:after-code",
    ...attempt.defenseAnswers.map((answer) => `answer:${answer.topic}`)
  ]);
}

function percentile(sortedValues, percentileValue) {
  const index = Math.min(
    sortedValues.length - 1,
    Math.max(0, Math.ceil(sortedValues.length * percentileValue) - 1)
  );
  return sortedValues[index];
}

function ratio(numerator, denominator) {
  return denominator === 0 ? 0 : Number((numerator / denominator).toFixed(3));
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

async function writeJson(path, value) {
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function captureCommand(command, argumentsList) {
  const result = await spawnWithInput(command, argumentsList, "", prototypeDirectory);
  if (result.exitCode !== 0) {
    throw new Error(`${command} exited ${result.exitCode}: ${result.stderr}`);
  }
  return result.stdout;
}

function spawnWithInput(command, argumentsList, input, cwd) {
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, argumentsList, {
      cwd,
      env: process.env,
      stdio: ["pipe", "pipe", "pipe"]
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", rejectPromise);
    child.on("close", (exitCode) => resolvePromise({ exitCode, stdout, stderr }));
    child.stdin.end(input);
  });
}
