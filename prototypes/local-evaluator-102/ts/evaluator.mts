import { spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const EVALUATOR_VERSION = '0.1.0-prototype'
const CASE_SCHEMA = 'inside.case-spec.v1'
const ASSIGNMENT_SCHEMA = 'inside.assignment.v1'
const REPORT_SCHEMA = 'inside.evaluation-report.v1'

type Diagnostic = { code: string; message: string }
type ScenarioResult = {
  id: string
  status: 'passed' | 'failed'
  durationMs: number
  diagnostic: Diagnostic | null
}

type CaseSpec = {
  schemaVersion: string
  case: { id: string; version: string; title: string }
  variants: Array<{ id: string; runtime: string; framework: string; database: string }>
  publicScenario: { id: string; orderAcceptanceMaxMs: number; deliveryDeadlineMs: number }
}

type Assignment = {
  schemaVersion: string
  id: string
  attemptDraftId: string
  repositoryId: string
  remoteUrl: string
  sourceRef: string
  caseId: string
  caseVersion: string
  variantId: string
}

function fail(message: string): never {
  throw new Error(message)
}

function readJson<T>(path: string): T {
  return JSON.parse(readFileSync(path, 'utf8')) as T
}

function commandText(cwd: string, command: string, args: string[]): string {
  const result = spawnSync(command, args, { cwd, encoding: 'utf8' })
  if (result.status !== 0) {
    fail(`${command} ${args.join(' ')}: ${(result.stderr || result.stdout).trim()}`)
  }
  return result.stdout.trim()
}

function isSha(value: string): boolean {
  return /^[0-9a-f]{40}$/.test(value)
}

function remoteRefSha(cwd: string, remoteUrl: string, sourceRef: string): string {
  const fields = commandText(cwd, 'git', ['ls-remote', remoteUrl, sourceRef]).split(/\s+/)
  if (fields.length !== 2 || fields[1] !== sourceRef || !isSha(fields[0])) {
    fail(`remote ref ${sourceRef} is missing or invalid`)
  }
  return fields[0]
}

function validateInputs(spec: CaseSpec, assignment: Assignment): void {
  if (spec.schemaVersion !== CASE_SCHEMA) fail(`incompatible CaseSpec schema ${spec.schemaVersion}`)
  if (assignment.schemaVersion !== ASSIGNMENT_SCHEMA) {
    fail(`incompatible assignment schema ${assignment.schemaVersion}`)
  }
  if (!spec.case?.id || !spec.case.version || spec.publicScenario?.id !== 'temporary-partner-failure') {
    fail('CaseSpec is missing the prototype case or public scenario')
  }
  if (assignment.caseId !== spec.case.id || assignment.caseVersion !== spec.case.version) {
    fail('assignment does not match the CaseSpec identity/version')
  }
  if (!assignment.attemptDraftId || !assignment.sourceRef) {
    fail('assignment is missing attempt draft or source ref')
  }
  if (!spec.variants.some((variant) => variant.id === assignment.variantId)) {
    fail(`assignment variant ${assignment.variantId} is not supported by the CaseSpec`)
  }
}

function parseFlags(args: string[]): Record<string, string> {
  const values: Record<string, string> = {}
  for (let index = 0; index < args.length; index += 2) {
    const name = args[index]
    const value = args[index + 1]
    if (!name?.startsWith('--') || value === undefined) fail(`invalid argument ${name ?? ''}`)
    values[name.slice(2)] = value
  }
  return values
}

function runScenario(root: string, mode: string): { result: ScenarioResult; composeFailed: boolean } {
  const evidenceDirectory = mkdtempSync(join(tmpdir(), 'inside-evaluator-evidence-'))
  const project = `inside-eval-${process.pid}-${Date.now()}`
  const compose = ['compose', '-p', project, '-f', join(root, 'compose.yaml')]
  const environment = {
    ...process.env,
    EVIDENCE_DIR: evidenceDirectory,
    PROTOTYPE_FIXTURE_MODE: mode,
  }
  let composeFailed = false

  try {
    const up = spawnSync(
      'docker',
      [...compose, 'up', '--build', '--abort-on-container-exit', '--exit-code-from', 'scenario'],
      { cwd: root, env: environment, stdio: 'ignore', timeout: 90_000 },
    )
    composeFailed = up.status !== 0

    try {
      return {
        result: readJson<ScenarioResult>(join(evidenceDirectory, 'scenario.json')),
        composeFailed,
      }
    } catch {
      const message = up.error?.message ?? 'Docker scenario exited without structured evidence; inspect local Compose logs'
      return {
        result: {
          id: 'temporary-partner-failure',
          status: 'failed',
          durationMs: 0,
          diagnostic: { code: 'scenario_runtime_failed', message },
        },
        composeFailed: true,
      }
    }
  } finally {
    spawnSync('docker', [...compose, 'down', '--volumes', '--remove-orphans', '--rmi', 'local'], {
      cwd: root,
      env: environment,
      encoding: 'utf8',
      timeout: 30_000,
    })
    rmSync(evidenceDirectory, { recursive: true, force: true })
  }
}

function run(args: string[]): void {
  const flags = parseFlags(args)
  const root = flags['prototype-root']
  const repositoryRoot = flags['repository-root']
  const casePath = flags.case
  const assignmentPath = flags.assignment
  const output = flags.output
  const mode = flags['fixture-mode'] ?? 'pass'
  if (!root || !repositoryRoot || !casePath || !assignmentPath || !output) {
    fail('prototype-root, repository-root, case, assignment, and output are required')
  }
  if (mode !== 'pass' && mode !== 'bad-signature') fail(`unsupported fixture mode ${mode}`)

  const spec = readJson<CaseSpec>(casePath)
  const assignment = readJson<Assignment>(assignmentPath)
  validateInputs(spec, assignment)
  const startedAt = new Date().toISOString()
  const dockerServer = commandText(root, 'docker', [
    'version',
    '--format',
    '{{.Server.Os}}/{{.Server.Arch}} {{.Server.Version}}',
  ])
  const dockerCompose = commandText(root, 'docker', ['compose', 'version', '--short'])
  const commitSha = commandText(repositoryRoot, 'git', ['rev-parse', 'HEAD'])
  if (!isSha(commitSha)) fail('preflight git HEAD: expected a 40-character commit SHA')
  const remoteUrl = commandText(repositoryRoot, 'git', ['remote', 'get-url', 'origin'])
  if (remoteUrl !== assignment.remoteUrl) {
    fail(`preflight repository mismatch: expected ${assignment.remoteUrl}, got ${remoteUrl}`)
  }
  const pushedSha = remoteRefSha(repositoryRoot, assignment.remoteUrl, assignment.sourceRef)
  if (pushedSha !== commitSha) {
    fail(`preflight unpushed HEAD: local ${commitSha} differs from ${pushedSha} at ${assignment.sourceRef}`)
  }

  const scenario = runScenario(root, mode)
  const report = {
    schemaVersion: REPORT_SCHEMA,
    case: { id: spec.case.id, version: spec.case.version },
    variantId: assignment.variantId,
    attemptDraftId: assignment.attemptDraftId,
    evaluator: {
      id: 'inside-local-evaluator',
      version: EVALUATOR_VERSION,
      language: 'typescript',
    },
    assignment: { id: assignment.id, repositoryId: assignment.repositoryId },
    source: { commitSha },
    execution: {
      method: 'local',
      startedAt,
      finishedAt: new Date().toISOString(),
      environment: {
        os: process.platform,
        arch: process.arch,
        dockerServer,
        dockerCompose,
      },
    },
    scenarios: [scenario.result],
    verdict: scenario.result.status,
  }
  writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`, { mode: 0o600 })
  console.log(`${scenario.result.id}: ${scenario.result.status} (typescript) -> ${output}`)
  if (scenario.composeFailed || scenario.result.status !== 'passed') {
    const diagnostic = scenario.result.diagnostic
    fail(`scenario failed [${diagnostic?.code ?? 'unknown'}]: ${diagnostic?.message ?? 'no diagnostic'}`)
  }
}

try {
  const command = process.argv[2]
  if (command === 'version') {
    console.log(EVALUATOR_VERSION)
  } else if (command === 'run') {
    run(process.argv.slice(3))
  } else {
    fail('usage: evaluator.mts <version|run>')
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  process.exitCode = 1
}
