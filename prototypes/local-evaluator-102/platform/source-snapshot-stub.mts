import { createHash } from 'node:crypto'
import { spawnSync } from 'node:child_process'
import { readFileSync, writeFileSync } from 'node:fs'

type Assignment = {
  id: string
  repositoryId: string
  remoteUrl: string
  sourceRef: string
}
type SourceSnapshot = {
  schemaVersion: 'inside.source-snapshot.v1'
  assignmentId: string
  repositoryId: string
  commitSha: string
  archiveSha256: string
  fetchedAt: string
}

interface SourceSnapshotProvider {
  fetch(assignment: Assignment): SourceSnapshot
}

class GitRemoteSourceSnapshotStub implements SourceSnapshotProvider {
  fetch(assignment: Assignment): SourceSnapshot {
    const remote = spawnSync('git', ['ls-remote', assignment.remoteUrl, assignment.sourceRef], {
      encoding: 'utf8',
    })
    if (remote.status !== 0) throw new Error(remote.stderr || 'cannot read assignment remote')
    const [commitSha, sourceRef, extra] = remote.stdout.trim().split(/\s+/)
    if (extra || sourceRef !== assignment.sourceRef || !/^[0-9a-f]{40}$/.test(commitSha)) {
      throw new Error(`remote ref ${assignment.sourceRef} is missing or invalid`)
    }
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
  if (!options.assignment || !options.output) {
    throw new Error('assignment and output are required')
  }
  const assignment = JSON.parse(readFileSync(options.assignment, 'utf8')) as Assignment
  const snapshot = new GitRemoteSourceSnapshotStub().fetch(assignment)
  writeFileSync(options.output, `${JSON.stringify(snapshot, null, 2)}\n`, { mode: 0o600 })
  console.log(`Git remote source snapshot stub -> ${options.output}`)
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  process.exitCode = 1
}
