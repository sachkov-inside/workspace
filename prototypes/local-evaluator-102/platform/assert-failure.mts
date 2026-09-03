import { readFileSync } from 'node:fs'

const report = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const scenario = report.scenarios?.[0]
if (report.verdict !== 'failed' || scenario?.diagnostic?.code !== 'signature_rejected') {
  throw new Error(`expected signature_rejected report, got ${JSON.stringify(report)}`)
}
console.log('ok bad signature is diagnosed as signature_rejected')
