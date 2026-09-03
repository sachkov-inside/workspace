import { readFileSync } from 'node:fs'
import { validateIngress } from './ingress.mts'

function read(path: string): unknown {
  return JSON.parse(readFileSync(path, 'utf8'))
}

function clone<T>(value: T): T {
  return structuredClone(value)
}

if (process.argv.length !== 6) {
  console.error('usage: contract-checks.mts <report> <source-snapshot> <case-spec> <assignment>')
  process.exit(2)
}

const [report, snapshot, caseSpec, assignment] = process.argv.slice(2).map(read)
const valid = validateIngress(report, snapshot, caseSpec, assignment)
if (!valid.accepted) throw new Error(`valid report rejected: ${valid.rejection.code}`)
console.log('ok valid report accepted')

const checks: Array<[string, string, () => [unknown, unknown]]> = [
  [
    'malformed report',
    'malformed_report',
    () => {
      const changed = clone(report) as Record<string, unknown>
      delete changed.source
      return [changed, snapshot]
    },
  ],
  [
    'incompatible report version',
    'incompatible_report_version',
    () => {
      const changed = clone(report) as Record<string, unknown>
      changed.schemaVersion = 'inside.evaluation-report.v2'
      return [changed, snapshot]
    },
  ],
  [
    'stale report SHA',
    'stale_source_revision',
    () => {
      const changed = clone(snapshot) as Record<string, unknown>
      changed.commitSha = 'b'.repeat(40)
      return [report, changed]
    },
  ],
  [
    'forbidden Platform status',
    'forbidden_report_field',
    () => {
      const changed = clone(report) as Record<string, unknown>
      changed.platformStatus = 'verified'
      return [changed, snapshot]
    },
  ],
  [
    'incompatible CaseSpec version',
    'incompatible_case_contract',
    () => {
      const changed = clone(report) as Record<string, unknown>
      ;(changed.case as Record<string, unknown>).version = '2.0.0'
      return [changed, snapshot]
    },
  ],
  [
    'missing required public scenario',
    'missing_required_scenario',
    () => {
      const changed = clone(report) as Record<string, unknown>
      const scenarios = changed.scenarios as Array<Record<string, unknown>>
      scenarios[0].id = 'fabricated-passing-scenario'
      return [changed, snapshot]
    },
  ],
  [
    'wrong attempt draft',
    'attempt_draft_mismatch',
    () => {
      const changed = clone(report) as Record<string, unknown>
      changed.attemptDraftId = 'another-attempt-draft'
      return [changed, snapshot]
    },
  ],
]

for (const [name, expectedCode, mutate] of checks) {
  const [changedReport, changedSnapshot] = mutate()
  const result = validateIngress(changedReport, changedSnapshot, caseSpec, assignment)
  if (result.accepted || result.rejection.code !== expectedCode) {
    throw new Error(`${name}: expected ${expectedCode}, got ${JSON.stringify(result)}`)
  }
  console.log(`ok ${name} rejected: ${expectedCode}`)
}
