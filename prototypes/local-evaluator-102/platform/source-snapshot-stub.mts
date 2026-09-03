import { createHash } from 'node:crypto'
import { readFileSync, writeFileSync } from 'node:fs'

type Assignment = { id: string; repositoryId: string }
type SourceSnapshot = {
  schemaVersion: 'inside.source-snapshot.v1'
  assignmentId: string
  repositoryId: string
  commitSha: string
  archiveSha256: string
  fetchedAt: string
}

interface SourceSnapshotProvider {
  fetch(assignment: Assignment, commitSha: string): SourceSnapshot
}

class FixtureSourceSnapshotProvider implements SourceSnapshotProvider {
  fetch(assignment: Assignment, commitSha: string): SourceSnapshot {
    if (!/^[0-9a-f]{40}$/.test(commitSha)) throw new Error('commit SHA must contain 40 lowercase hex characters')
    return {
      schemaVersion: 'inside.source-snapshot.v1',
      assignmentId: assignment.id,
      repositoryId: assignment.repositoryId,
      commitSha,
      archiveSha256: createHash('sha256')
        .update(`${assignment.repositoryId}:${commitSha}:fixture-archive`)
        .digest('hex'),
      fetchedAt: new Date().toISOString(),
    }
  }
}

function flags(args: string[]): Record<string, string> {
  const result: Record<string, string> = {}
  for (let index = 0; index < args.length; index += 2) {
    const key = args[index]
    const value = args[index + 1]
    if (!key?.startsWith('--') || value === undefined) throw new Error(`invalid argument ${key ?? ''}`)
    result[key.slice(2)] = value
  }
  return result
}

try {
  const options = flags(process.argv.slice(2))
  if (!options.assignment || !options.sha || !options.output) {
    throw new Error('assignment, sha, and output are required')
  }
  const assignment = JSON.parse(readFileSync(options.assignment, 'utf8')) as Assignment
  const snapshot = new FixtureSourceSnapshotProvider().fetch(assignment, options.sha)
  writeFileSync(options.output, `${JSON.stringify(snapshot, null, 2)}\n`, { mode: 0o600 })
  console.log(`source snapshot fixture -> ${options.output}`)
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  process.exitCode = 1
}
