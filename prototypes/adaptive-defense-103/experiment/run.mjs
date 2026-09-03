#!/usr/bin/env node

import { spawn } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { performance } from "node:perf_hooks";

const experimentDirectory = dirname(fileURLToPath(import.meta.url));
const prototypeDirectory = resolve(experimentDirectory, "..");
const evidenceDirectory = resolve(prototypeDirectory, "evidence");
const rawEvidencePath = resolve(evidenceDirectory, "model-runs.json");
const summaryPath = resolve(evidenceDirectory, "summary.json");
const questionSchemaPath = resolve(experimentDirectory, "question-output.schema.json");
const assessmentSchemaPath = resolve(experimentDirectory, "assessment-output.schema.json");

const requestedRuns = Number.parseInt(process.argv[2] ?? "3", 10);
if (!Number.isInteger(requestedRuns) || requestedRuns < 1 || requestedRuns > 5) {
  throw new Error("Usage: node experiment/run.mjs [runs-per-fixture: 1..5]");
}

const [fixtures, commonPrompt, questionPrompt, assessmentPrompt, finalAssessmentPrompt] = await Promise.all([
  readJson(resolve(experimentDirectory, "fixtures.json")),
  readFile(resolve(experimentDirectory, "system-prompt.md"), "utf8"),
  readFile(resolve(experimentDirectory, "question-prompt.md"), "utf8"),
  readFile(resolve(experimentDirectory, "assessment-prompt.md"), "utf8"),
  readFile(resolve(experimentDirectory, "final-assessment-prompt.md"), "utf8")
]);

const fixtureInputs = fixtures.attempts.map((attempt, index) => ({
  attempt,
  opaqueAttemptId: `attempt-${String(index + 1).padStart(2, "0")}`,
  modelInput: normalizeModelInput(attempt)
}));
const jobs = fixtureInputs.flatMap((fixtureInput) =>
  Array.from({ length: requestedRuns }, (_, index) => ({
    ...fixtureInput,
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
    const result = await runFixture(jobs[jobIndex]);
    results.push(result);
    process.stdout.write(
      `[${results.length}/${jobs.length}] ${result.fixtureId} run ${result.repetition}: ` +
      `${result.output.assessment.defenseSignal}, ${Math.round(result.latencyMs)} ms / ` +
      `${result.providerCallCount} calls\n`
    );
  }
}));

results.sort((left, right) =>
  left.fixtureId.localeCompare(right.fixtureId) || left.repetition - right.repetition
);

const evidence = {
  schemaVersion: "inside.adaptive-defense-experiment.v2",
  environment: {
    providerHarness: codexVersion.trim(),
    model: "gpt-5.4",
    reasoningEffort: "low",
    platform: process.platform,
    architecture: process.arch,
    node: process.version,
    runsPerFixture: requestedRuns,
    fixtureCount: fixtures.attempts.length,
    concurrency: workerCount,
    providerCallCount: results.reduce((total, result) => total + result.providerCallCount, 0),
    note: "Provider usage includes the Codex agent runtime prompt; this is not production API billing."
  },
  blindInputAudit: {
    opaqueAttemptIds: true,
    answersExcludedFromQuestionCall: true,
    prohibitedFixtureMetadataExcluded: [
      "id",
      "archetype",
      "sourceFingerprint",
      "calibrationExpectation",
      "defenseAnswers.topic",
      "defenseAnswers.dimensions",
      "defenseAnswers.respondsTo"
    ]
  },
  results
};
const summary = summarize(fixtures.attempts, evidence);

await Promise.all([
  writeJson(rawEvidencePath, evidence),
  writeJson(summaryPath, summary)
]);

process.stdout.write(`Evidence: ${rawEvidencePath}\nSummary: ${summaryPath}\n`);

async function runFixture(job) {
  const temporaryDirectory = await mkdtemp(resolve(tmpdir(), "inside-defense-103-"));
  try {
    const questionInput = {
      attemptId: job.opaqueAttemptId,
      caseSpec: normalizeCaseSpec(fixtures.caseSpec),
      attempt: job.modelInput
    };
    assertBlindQuestionInput(questionInput, job.attempt);
    const questionPhase = await runModelPhase({
      phaseName: "questions",
      schemaPath: questionSchemaPath,
      prompt: makePrompt(commonPrompt, questionPrompt, questionInput),
      temporaryDirectory
    });
    assertAttemptId(questionPhase.output, job.opaqueAttemptId);

    const initialExchanges = pairAnswers(questionPhase.output.questions, job.attempt.defenseAnswers);
    const assessmentInput = { ...questionInput, exchanges: initialExchanges };
    const assessmentPhase = await runModelPhase({
      phaseName: "assessment",
      schemaPath: assessmentSchemaPath,
      prompt: makePrompt(commonPrompt, assessmentPrompt, assessmentInput),
      temporaryDirectory
    });
    assertAttemptId(assessmentPhase.output, job.opaqueAttemptId);
    const recordedFollowUps = assessmentPhase.output.followUps;
    let allExchanges = initialExchanges;
    let finalAssessment = assessmentPhase.output.assessment;
    const phases = {
      questions: withoutOutput(questionPhase),
      assessment: withoutOutput(assessmentPhase)
    };

    if (recordedFollowUps.length > 0) {
      const usedAnswers = new Set(initialExchanges.map((exchange) => exchange.answer));
      const followUpExchanges = pairAnswers(
        recordedFollowUps,
        job.attempt.defenseAnswers,
        usedAnswers,
        initialExchanges.length + 1
      );
      allExchanges = [...initialExchanges, ...followUpExchanges];
      const finalPhase = await runModelPhase({
        phaseName: "final-assessment",
        schemaPath: assessmentSchemaPath,
        prompt: makePrompt(commonPrompt, finalAssessmentPrompt, {
          ...questionInput,
          exchanges: allExchanges
        }),
        temporaryDirectory
      });
      assertAttemptId(finalPhase.output, job.opaqueAttemptId);
      if (finalPhase.output.followUps.length > 0) {
        throw new Error("final assessment exceeded the follow-up budget");
      }
      finalAssessment = finalPhase.output.assessment;
      phases.finalAssessment = withoutOutput(finalPhase);
    }

    const phaseMeasurements = Object.values(phases);
    const output = {
      schemaVersion: "inside.adaptive-defense-result.v1",
      attemptId: job.opaqueAttemptId,
      questions: questionPhase.output.questions,
      followUps: recordedFollowUps,
      assessment: finalAssessment
    };

    return {
      fixtureId: job.attempt.id,
      opaqueAttemptId: job.opaqueAttemptId,
      repetition: job.repetition,
      sourceFingerprint: job.attempt.sourceFingerprint,
      expectedCalibration: job.attempt.calibrationExpectation,
      providerCallCount: phaseMeasurements.length,
      latencyMs: phaseMeasurements.reduce((total, phase) => total + phase.latencyMs, 0),
      promptUtf8Bytes: phaseMeasurements.reduce((total, phase) => total + phase.promptUtf8Bytes, 0),
      usage: addUsage(...phaseMeasurements.map((phase) => phase.usage)),
      phases,
      exchanges: allExchanges,
      output
    };
  } finally {
    await rm(temporaryDirectory, { recursive: true, force: true });
  }
}

async function runModelPhase({ phaseName, schemaPath, prompt, temporaryDirectory }) {
  const outputPath = resolve(temporaryDirectory, `${phaseName}-last-message.json`);
  const argumentsList = [
    "exec",
    "--ignore-user-config",
    "--ignore-rules",
    "--ephemeral",
    "--skip-git-repo-check",
    "-s", "read-only",
    "-m", "gpt-5.4",
    "-c", "model_reasoning_effort=\"low\"",
    "-c", "shell_environment_policy.inherit=\"none\"",
    "--output-schema", schemaPath,
    "--json",
    "-o", outputPath,
    "-"
  ];

  const startedAt = performance.now();
  const execution = await spawnWithInput("codex", argumentsList, prompt, temporaryDirectory);
  const latencyMs = performance.now() - startedAt;
  if (execution.exitCode !== 0) {
    throw new Error(
      `codex ${phaseName} exited ${execution.exitCode}: ${execution.stderr}\n${execution.stdout}`
    );
  }
  return {
    latencyMs,
    promptUtf8Bytes: Buffer.byteLength(prompt),
    usage: parseUsage(execution.stdout),
    output: await readJson(outputPath)
  };
}

function makePrompt(common, phase, input) {
  return [common.trim(), "", phase.trim(), "", "Input data:", JSON.stringify(input, null, 2)].join("\n");
}

function normalizeCaseSpec(caseSpec) {
  return {
    id: caseSpec.id,
    version: caseSpec.version,
    title: caseSpec.title,
    businessFacts: tagFacts("case:fact", caseSpec.businessFacts),
    rubric: caseSpec.rubric.map((item) => ({
      id: `rubric:${item.dimension}`,
      dimension: item.dimension,
      question: item.question
    }))
  };
}

function normalizeModelInput(attempt) {
  return {
    variantId: attempt.variantId,
    sourceSnapshot: { id: "source:snapshot", ...attempt.sourceSnapshot },
    sourceFacts: attempt.sourceEvidence.map((item, index) => ({
      id: `source:fact:${index + 1}`,
      fact: item.fact
    })),
    technicalEvidence: {
      reportVerdict: { id: "technical:verdict", value: attempt.technicalEvidence.reportVerdict },
      scenarios: tagFacts("technical:scenario", attempt.technicalEvidence.scenarios),
      telemetry: tagFacts("technical:telemetry", attempt.technicalEvidence.telemetry)
    },
    decisionRecord: [
      { id: "decision:before-code", text: attempt.decisionRecord.beforeCode },
      { id: "decision:after-code", text: attempt.decisionRecord.afterCode }
    ]
  };
}

function tagFacts(prefix, facts) {
  return facts.map((fact, index) => ({ id: `${prefix}:${index + 1}`, fact }));
}

function pairAnswers(questions, answerFixtures, usedAnswers = new Set(), firstExchangeNumber = 1) {
  const unused = answerFixtures.filter((answer) => !usedAnswers.has(answer.text));
  return questions.map((question, index) => {
    const scores = unused.map((answer) =>
      question.groundedIn.filter((reference) => answer.respondsTo.includes(reference)).length * 10 +
      (answer.dimensions.includes(question.dimension) ? 1 : 0)
    );
    const bestIndex = scores.length === 0 ? -1 : scores.indexOf(Math.max(...scores));
    const answer = bestIndex < 0
      ? { text: "I cannot add anything beyond my previous answers." }
      : unused.splice(bestIndex, 1)[0];
    return { id: `exchange:${firstExchangeNumber + index}`, question, answer: answer.text };
  });
}

function assertBlindQuestionInput(input, attempt) {
  const serialized = JSON.stringify(input);
  const prohibitedValues = [
    attempt.id,
    attempt.archetype,
    attempt.sourceFingerprint,
    attempt.calibrationExpectation,
    ...attempt.defenseAnswers.flatMap((answer) => [answer.topic, answer.text])
  ];
  const leaked = prohibitedValues.filter((value) => serialized.includes(value));
  if (leaked.length > 0) {
    throw new Error(`question input leaks fixture calibration metadata: ${leaked.join(", ")}`);
  }
}

function assertAttemptId(output, expectedAttemptId) {
  if (output.attemptId !== expectedAttemptId) {
    throw new Error(`model returned attemptId ${output.attemptId}; expected ${expectedAttemptId}`);
  }
}

function withoutOutput(phase) {
  const { output: _output, ...measurements } = phase;
  return measurements;
}

function parseUsage(jsonLines) {
  const events = jsonLines.split("\n").filter(Boolean).map((line) => JSON.parse(line));
  const completed = events.findLast((event) => event.type === "turn.completed");
  if (!completed?.usage) throw new Error("codex output did not contain turn.completed usage");
  return completed.usage;
}

function addUsage(...usageRecords) {
  return usageRecords.reduce((totals, usage) => {
    for (const [key, value] of Object.entries(usage)) totals[key] = (totals[key] ?? 0) + value;
    return totals;
  }, {});
}

function summarize(attempts, evidence) {
  const normalizedCaseSpec = normalizeCaseSpec(fixtures.caseSpec);
  const fixtureSummaries = attempts.map((attempt) => {
    const runs = evidence.results.filter((result) => result.fixtureId === attempt.id);
    const signals = runs.map((result) => result.output.assessment.defenseSignal);
    const baseReferences = collectIds({ caseSpec: normalizedCaseSpec, attempt: normalizeModelInput(attempt) });
    const assessmentReferences = new Set(baseReferences);
    runs.forEach((result) => result.exchanges.forEach((exchange) => {
      assessmentReferences.add(exchange.id);
      assessmentReferences.add(exchange.question.id);
    }));
    const allQuestions = runs.flatMap((result) => result.output.questions);
    const groundedQuestions = allQuestions.filter((question) =>
      question.groundedIn.length > 0 && question.groundedIn.every((reference) => baseReferences.has(reference))
    );
    const allSignals = runs.flatMap((result) => result.output.assessment.dimensionSignals);
    const groundedSignals = allSignals.filter((signal) =>
      signal.evidenceRefs.length > 0 && signal.evidenceRefs.every((reference) => assessmentReferences.has(reference))
    );
    const allFollowUps = runs.flatMap((result) => result.output.followUps);
    const groundedFollowUps = allFollowUps.filter((question) =>
      question.groundedIn.length > 0 && question.groundedIn.every((reference) => assessmentReferences.has(reference))
    );
    return {
      fixtureId: attempt.id,
      expectedCalibration: attempt.calibrationExpectation,
      signals,
      unanimous: new Set(signals).size === 1,
      expectedMatches: signals.filter((signal) => signal === attempt.calibrationExpectation).length,
      questionGroundingRate: ratio(groundedQuestions.length, allQuestions.length),
      rubricGroundingRate: ratio(groundedSignals.length, allSignals.length),
      followUpGroundingRate: ratio(groundedFollowUps.length, allFollowUps.length),
      questionDimensions: [...new Set(allQuestions.map((question) => question.dimension))].sort(),
      followUpCounts: runs.map((result) => result.output.followUps.length)
    };
  });

  const providerLatencies = evidence.results
    .flatMap((result) => Object.values(result.phases).map((phase) => phase.latencyMs))
    .sort((left, right) => left - right);
  const defenseLatencies = evidence.results.map((result) => result.latencyMs).sort((left, right) => left - right);
  const usageTotals = evidence.results.reduce((totals, result) => addUsage(totals, result.usage), {});
  const expectedSignalMatches = fixtureSummaries.reduce((total, fixture) => total + fixture.expectedMatches, 0);
  const totalQuestions = evidence.results.reduce((total, result) => total + result.output.questions.length, 0);
  const groundedQuestions = fixtureSummaries.reduce((total, fixture) => {
    const count = evidence.results
      .filter((result) => result.fixtureId === fixture.fixtureId)
      .reduce((subtotal, result) => subtotal + result.output.questions.length, 0);
    return total + fixture.questionGroundingRate * count;
  }, 0);
  const rubricSignalCount = evidence.results.length * 4;
  const groundedRubricSignals = fixtureSummaries.reduce(
    (total, fixture) => total + fixture.rubricGroundingRate * requestedRuns * 4,
    0
  );
  const totalFollowUps = evidence.results.reduce((total, result) => total + result.output.followUps.length, 0);
  const groundedFollowUps = fixtureSummaries.reduce((total, fixture) => {
    const count = evidence.results
      .filter((result) => result.fixtureId === fixture.fixtureId)
      .reduce((subtotal, result) => subtotal + result.output.followUps.length, 0);
    return total + fixture.followUpGroundingRate * count;
  }, 0);
  const provenanceViolations = evidence.results.filter(
    (result) => result.output.assessment.provenanceClaim !== "none"
  ).length;
  const technicalOverrideAttempts = evidence.results.filter(
    (result) => result.output.assessment.technicalEvidenceOverrideAttempted
  ).length;

  return {
    schemaVersion: "inside.adaptive-defense-summary.v2",
    runCount: evidence.results.length,
    providerCallCount: evidence.environment.providerCallCount,
    fixtureCount: attempts.length,
    blindQuestionGeneration: true,
    expectedSignalMatches,
    expectedSignalRate: ratio(expectedSignalMatches, evidence.results.length),
    unanimousFixtures: fixtureSummaries.filter((fixture) => fixture.unanimous).length,
    questionGroundingRate: ratio(groundedQuestions, totalQuestions),
    rubricGroundingRate: ratio(groundedRubricSignals, rubricSignalCount),
    followUpGroundingRate: ratio(groundedFollowUps, totalFollowUps),
    provenanceViolations,
    technicalOverrideAttempts,
    providerLatencyMs: latencySummary(providerLatencies),
    defenseLatencyMs: latencySummary(defenseLatencies),
    usageTotals,
    apiCostEstimate: estimateGpt54ApiCost(usageTotals, evidence.environment.providerCallCount),
    fixtures: fixtureSummaries,
    sameSourceCalibration: {
      fingerprint: "python-reference-like-v1",
      strongSignals: fixtureSummaries.find((fixture) => fixture.fixtureId === "python-reference-strong")?.signals,
      weakSignals: fixtureSummaries.find((fixture) => fixture.fixtureId === "python-reference-weak")?.signals
    }
  };
}

function collectIds(value, ids = new Set()) {
  if (Array.isArray(value)) value.forEach((item) => collectIds(item, ids));
  else if (value && typeof value === "object") {
    if (typeof value.id === "string") ids.add(value.id);
    Object.values(value).forEach((item) => collectIds(item, ids));
  }
  return ids;
}

function latencySummary(sortedValues) {
  return {
    min: Math.round(sortedValues[0]),
    p50: Math.round(percentile(sortedValues, 0.5)),
    p95: Math.round(percentile(sortedValues, 0.95)),
    max: Math.round(sortedValues.at(-1))
  };
}

function estimateGpt54ApiCost(usage, callCount) {
  const pricePerMillion = { input: 2.5, cachedInput: 0.25, output: 15 };
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
    caveat: "The experiment used a ChatGPT-authenticated Codex CLI, not API billing. Usage includes Codex runtime context."
  };
}

function percentile(sortedValues, percentileValue) {
  const index = Math.min(sortedValues.length - 1, Math.max(0, Math.ceil(sortedValues.length * percentileValue) - 1));
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
  if (result.exitCode !== 0) throw new Error(`${command} exited ${result.exitCode}: ${result.stderr}`);
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
