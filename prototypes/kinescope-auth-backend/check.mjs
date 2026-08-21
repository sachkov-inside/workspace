import { createHmac, timingSafeEqual } from 'node:crypto'
import { createServer } from 'node:http'

const NOW = 2_000_000_000
const JWT_SECRET = 'local-prototype-secret'
const CALLBACK_AUTH = `Basic ${Buffer.from('kinescope:local-callback-secret').toString('base64')}`
const VIDEO_ID = '7127f2d7-0e96-40d0-9a03-2e987c096466'
const memberships = new Map([
  ['active-member', NOW + 300],
  ['expired-member', NOW - 1],
])

const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url')

function signJwt(payload) {
  const unsigned = `${encode({ alg: 'HS256', typ: 'JWT' })}.${encode(payload)}`
  const signature = createHmac('sha256', JWT_SECRET).update(unsigned).digest('base64url')
  return `${unsigned}.${signature}`
}

function safeEqual(actual, expected) {
  const left = Buffer.from(actual)
  const right = Buffer.from(expected)
  return left.length === right.length && timingSafeEqual(left, right)
}

function verifyJwt(token) {
  const parts = token.split('.')
  if (parts.length !== 3 || parts.some((part) => !part)) throw new Error('malformed token')
  const [headerPart, payloadPart, signature] = parts

  const header = JSON.parse(Buffer.from(headerPart, 'base64url'))
  const payload = JSON.parse(Buffer.from(payloadPart, 'base64url'))
  const expected = createHmac('sha256', JWT_SECRET)
    .update(`${headerPart}.${payloadPart}`)
    .digest('base64url')

  if (header.alg !== 'HS256' || !safeEqual(signature, expected)) throw new Error('invalid signature')
  if (payload.iss !== 'inside-platform' || payload.aud !== 'kinescope-drm') throw new Error('invalid audience')
  if (!payload.sub || !payload.vid || !Number.isInteger(payload.exp) || payload.exp <= NOW) {
    throw new Error('invalid claims')
  }
  return payload
}

function authorize({ id, token, type }) {
  try {
    if (type !== 'video' || id !== VIDEO_ID || !token) return 403
    const claims = verifyJwt(token)
    const membershipExpiresAt = memberships.get(claims.sub)
    return claims.vid === id && membershipExpiresAt > NOW ? 200 : 403
  } catch {
    return 403
  }
}

const server = createServer(async (request, response) => {
  if (request.method !== 'POST') return response.writeHead(405).end()
  if (!safeEqual(request.headers.authorization ?? '', CALLBACK_AUTH)) {
    return response.writeHead(401).end()
  }

  try {
    const chunks = []
    for await (const chunk of request) chunks.push(chunk)
    const status = authorize(JSON.parse(Buffer.concat(chunks).toString('utf8')))
    response.writeHead(status).end()
  } catch {
    response.writeHead(400).end()
  }
})

const token = (sub, overrides = {}) => signJwt({
  iss: 'inside-platform',
  aud: 'kinescope-drm',
  sub,
  vid: VIDEO_ID,
  exp: NOW + 60,
  ...overrides,
})

async function run() {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
  const { port } = server.address()
  const endpoint = `http://127.0.0.1:${port}`
  const activeToken = token('active-member')
  const tamperedToken = `${activeToken.slice(0, -1)}${activeToken.endsWith('A') ? 'B' : 'A'}`
  const cases = [
    ['anonymous', '', 403],
    ['active', activeToken, 200],
    ['expired-membership', token('expired-member'), 403],
    ['tampered', tamperedToken, 403],
    ['extra-segment', `${activeToken}.anything`, 403],
    ['expired-token', token('active-member', { exp: NOW - 1 }), 403],
    ['wrong-video', token('active-member', { vid: 'another-video' }), 403],
  ]

  try {
    for (const [name, authToken, expected] of cases) {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          authorization: CALLBACK_AUTH,
          'content-type': 'application/json',
        },
        body: JSON.stringify({ id: VIDEO_ID, token: authToken, type: 'video' }),
      })
      if (response.status !== expected) throw new Error(`${name}: expected ${expected}, got ${response.status}`)
      console.log(`ok ${name}: ${response.status}`)
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ id: VIDEO_ID, token: activeToken, type: 'video' }),
    })
    if (response.status !== 401) throw new Error(`callback-auth: expected 401, got ${response.status}`)
    console.log(`ok callback-auth: ${response.status}`)
  } finally {
    server.close()
  }
}

await run()
