import { readFileSync } from 'node:fs'

type JsonObject = Record<string, unknown>
type IngressResult =
  | { accepted: true; assignmentId: string; attemptDraftId: string; commitSha: string; verdict: string }
  | { accepted: false; rejection: { code: string; message: string } }

class Rejection extends Error {
  readonly code: string

  constructor(code: string, message: string) {
    super(message)
    this.code = code
  }
}

function reject(code: string, message: string): never {
  throw new Rejection(code, message)
}

function object(value: unknown, path: string): JsonObject {
  if (value === null || Array.isArray(value) || typeof value !== 'object') {
    reject('malformed_report', `${path} must be an object`)
  }
  return value as JsonObject
}

function exactKeys(value: JsonObject, expected: string[], path: string): void {
  const actual = Object.keys(value).sort()
  const wanted = [...expected].sort()
  if (actual.join('\0') !== wanted.join('\0')) {
    reject('malformed_report', `${path} fields must be exactly: ${wanted.join(', ')}`)
  }
}

function string(value: unknown, path: string): string {
  if (typeof value !== 'string' || value.length === 0) {
    reject('malformed_report', `${path} must be a non-empty string`)
  }
  return value
}

function dateTime(value: unknown, path: string): string {
  const parsed = string(value, path)
  if (Number.isNaN(Date.parse(parsed))) reject('malformed_report', `${path} must be an ISO date-time`)
  return parsed
}

function validateScenario(value: unknown, index: number): { id: string; status: 'passed' | 'failed' } {
  const scenario = object(value, `scenarios[${index}]`)
  exactKeys(scenario, ['id', 'status', 'durationMs', 'diagnostic'], `scenarios[${index}]`)
  const id = string(scenario.id, `scenarios[${index}].id`)
  if (scenario.status !== 'passed' && scenario.status !== 'failed') {
    reject('malformed_report', `scenarios[${index}].status is invalid`)
  }
  if (!Number.isInteger(scenario.durationMs) || (scenario.durationMs as number) < 0) {
    reject('malformed_report', `scenarios[${index}].durationMs must be a non-negative integer`)
  }
  if (scenario.diagnostic !== null) {
    const diagnostic = object(scenario.diagnostic, `scenarios[${index}].diagnostic`)
    exactKeys(diagnostic, ['code', 'message'], `scenarios[${index}].diagnostic`)
    string(diagnostic.code, `scenarios[${index}].diagnostic.code`)
    string(diagnostic.message, `scenarios[${index}].diagnostic.message`)
  }
  return { id, status: scenario.status }
}

export function validateIngress(
  reportInput: unknown,
  snapshotInput: unknown,
  caseSpecInput: unknown,
  assignmentInput: unknown,
): IngressResult {
  try {
    const report = object(reportInput, 'report')
    if ('platformStatus' in report) {
      reject('forbidden_report_field', 'local evaluator cannot set Platform completion status')
    }
    exactKeys(
      report,
      ['schemaVersion', 'case', 'variantId', 'attemptDraftId', 'evaluator', 'assignment', 'source', 'execution', 'scenarios', 'verdict'],
      'report',
    )
    if (report.schemaVersion !== 'inside.evaluation-report.v1') {
      reject('incompatible_report_version', `unsupported report schema ${String(report.schemaVersion)}`)
    }

    const reportCase = object(report.case, 'report.case')
    exactKeys(reportCase, ['id', 'version'], 'report.case')
    const reportAssignment = object(report.assignment, 'report.assignment')
    exactKeys(reportAssignment, ['id', 'repositoryId'], 'report.assignment')
    const source = object(report.source, 'report.source')
    exactKeys(source, ['commitSha'], 'report.source')
    const reportSha = string(source.commitSha, 'report.source.commitSha')
    if (!/^[0-9a-f]{40}$/.test(reportSha)) reject('malformed_report', 'report source SHA is invalid')

    const evaluator = object(report.evaluator, 'report.evaluator')
    exactKeys(evaluator, ['id', 'version', 'language'], 'report.evaluator')
    if (evaluator.id !== 'inside-local-evaluator' || evaluator.version !== '0.1.0-prototype') {
      reject('incompatible_evaluator_version', 'evaluator identity/version is not supported')
    }
    if (evaluator.language !== 'go' && evaluator.language !== 'typescript') {
      reject('malformed_report', 'evaluator language is invalid')
    }

    const execution = object(report.execution, 'report.execution')
    exactKeys(execution, ['method', 'startedAt', 'finishedAt', 'environment'], 'report.execution')
    if (execution.method !== 'local') reject('malformed_report', 'execution method must be local')
    dateTime(execution.startedAt, 'report.execution.startedAt')
    dateTime(execution.finishedAt, 'report.execution.finishedAt')
    const environment = object(execution.environment, 'report.execution.environment')
    exactKeys(environment, ['os', 'arch', 'dockerServer', 'dockerCompose'], 'report.execution.environment')
    for (const field of ['os', 'arch', 'dockerServer', 'dockerCompose']) {
      string(environment[field], `report.execution.environment.${field}`)
    }

    if (!Array.isArray(report.scenarios) || report.scenarios.length === 0) {
      reject('malformed_report', 'report.scenarios must not be empty')
    }
    const scenarios = report.scenarios.map(validateScenario)
    if (report.verdict !== 'passed' && report.verdict !== 'failed') {
      reject('malformed_report', 'report.verdict is invalid')
    }
    const derivedVerdict = scenarios.every((scenario) => scenario.status === 'passed') ? 'passed' : 'failed'
    if (report.verdict !== derivedVerdict) reject('malformed_report', 'report verdict contradicts scenarios')

    const caseSpec = object(caseSpecInput, 'caseSpec')
    if (caseSpec.schemaVersion !== 'inside.case-spec.v1') {
      reject('incompatible_case_contract', 'CaseSpec schema is not supported')
    }
    const expectedCase = object(caseSpec.case, 'caseSpec.case')
    if (reportCase.id !== expectedCase.id || reportCase.version !== expectedCase.version) {
      reject('incompatible_case_contract', 'report references a different CaseSpec identity/version')
    }
    const publicScenario = object(caseSpec.publicScenario, 'caseSpec.publicScenario')
    const requiredScenarioId = string(publicScenario.id, 'caseSpec.publicScenario.id')
    if (scenarios.length !== 1 || scenarios[0].id !== requiredScenarioId) {
      reject('missing_required_scenario', `report must contain required public scenario ${requiredScenarioId}`)
    }

    const assignment = object(assignmentInput, 'assignment')
    if (assignment.schemaVersion !== 'inside.assignment.v1') {
      reject('incompatible_assignment', 'assignment schema is not supported')
    }
    if (
      reportAssignment.id !== assignment.id ||
      reportAssignment.repositoryId !== assignment.repositoryId ||
      report.variantId !== assignment.variantId ||
      reportCase.id !== assignment.caseId ||
      reportCase.version !== assignment.caseVersion
    ) {
      reject('assignment_mismatch', 'report does not belong to this assignment')
    }
    const attemptDraftId = string(report.attemptDraftId, 'report.attemptDraftId')
    if (attemptDraftId !== assignment.attemptDraftId) {
      reject('attempt_draft_mismatch', 'report does not belong to the current attempt draft')
    }

    const snapshot = object(snapshotInput, 'sourceSnapshot')
    exactKeys(
      snapshot,
      ['schemaVersion', 'assignmentId', 'repositoryId', 'commitSha', 'archiveSha256', 'fetchedAt'],
      'sourceSnapshot',
    )
    if (snapshot.schemaVersion !== 'inside.source-snapshot.v1') {
      reject('incompatible_snapshot_version', 'source snapshot schema is not supported')
    }
    if (snapshot.assignmentId !== assignment.id || snapshot.repositoryId !== assignment.repositoryId) {
      reject('assignment_mismatch', 'source snapshot does not belong to this assignment')
    }
    const snapshotSha = string(snapshot.commitSha, 'sourceSnapshot.commitSha')
    if (!/^[0-9a-f]{40}$/.test(snapshotSha)) reject('malformed_snapshot', 'source snapshot SHA is invalid')
    if (!/^[0-9a-f]{64}$/.test(string(snapshot.archiveSha256, 'sourceSnapshot.archiveSha256'))) {
      reject('malformed_snapshot', 'source snapshot archive digest is invalid')
    }
    dateTime(snapshot.fetchedAt, 'sourceSnapshot.fetchedAt')
    if (reportSha !== snapshotSha) {
      reject('stale_source_revision', `report SHA ${reportSha} differs from source snapshot SHA ${snapshotSha}`)
    }

    return {
      accepted: true,
      assignmentId: string(assignment.id, 'assignment.id'),
      attemptDraftId,
      commitSha: reportSha,
      verdict: report.verdict,
    }
  } catch (error) {
    if (error instanceof Rejection) {
      return { accepted: false, rejection: { code: error.code, message: error.message } }
    }
    return {
      accepted: false,
      rejection: { code: 'malformed_report', message: error instanceof Error ? error.message : String(error) },
    }
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.length !== 6) {
    console.error('usage: ingress.mts <report> <source-snapshot> <case-spec> <assignment>')
    process.exit(2)
  }
  const inputs = process.argv.slice(2).map((path) => JSON.parse(readFileSync(path, 'utf8')))
  const result = validateIngress(inputs[0], inputs[1], inputs[2], inputs[3])
  console.log(JSON.stringify(result))
  if (!result.accepted) process.exitCode = 1
}
