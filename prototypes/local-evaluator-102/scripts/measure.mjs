import { spawnSync } from 'node:child_process'
import { statSync } from 'node:fs'
import { arch, platform } from 'node:os'
import { performance } from 'node:perf_hooks'

const [goBinary, typescriptSource, typescriptArchive] = process.argv.slice(2)
const iterations = 50

function sample(command, args) {
  const started = performance.now()
  const result = spawnSync(command, args, { encoding: 'utf8' })
  if (result.status !== 0) throw new Error(result.stderr || `${command} failed`)
  return performance.now() - started
}

function summarize(values) {
  const sorted = [...values].sort((left, right) => left - right)
  return {
    p50Ms: Number(sorted[Math.floor(sorted.length * 0.5)].toFixed(3)),
    p95Ms: Number(sorted[Math.floor(sorted.length * 0.95)].toFixed(3)),
  }
}

sample(goBinary, ['version'])
sample(process.execPath, [typescriptSource, 'version'])

const goSamples = Array.from({ length: iterations }, () => sample(goBinary, ['version']))
const typescriptSamples = Array.from({ length: iterations }, () =>
  sample(process.execPath, [typescriptSource, 'version']),
)

console.log(JSON.stringify({
  measuredAt: new Date().toISOString(),
  host: `${platform()}/${arch()}`,
  iterations,
  go: {
    artifactBytes: statSync(goBinary).size,
    runtimePrerequisite: 'none',
    startup: summarize(goSamples),
  },
  typescript: {
    artifactBytes: statSync(typescriptArchive).size,
    runtimePrerequisite: `Node ${process.version}`,
    hostNodeExecutableBytes: statSync(process.execPath).size,
    startup: summarize(typescriptSamples),
  },
}, null, 2))
