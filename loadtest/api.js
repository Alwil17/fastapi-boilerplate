// k6 load test: public probes plus an authenticated read.
//
//   make loadtest                              # against http://host.docker.internal:8000
//   make loadtest BASE_URL=https://staging.example.com VUS=100 DURATION=2m
//
// setup() registers one throwaway user and logs in once, so it stays inside the
// register/login rate limits. Run against staging, not production: it creates a user.
// Rate limits apply to every request from this machine's IP; the authenticated reads
// are not limited. Thresholds fail the run (non-zero exit) when the API is too slow.
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  vus: Number(__ENV.VUS || 20),
  duration: __ENV.DURATION || '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export function setup() {
  const email = `loadtest-${Date.now()}@example.com`;
  const password = 'Load-test-passw0rd';
  const registered = http.post(
    `${BASE_URL}/auth/register`,
    JSON.stringify({ name: 'Load test', email, password }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  if (registered.status !== 201) {
    throw new Error(`register failed: ${registered.status} ${registered.body}`);
  }
  const login = http.post(`${BASE_URL}/auth/token`, { username: email, password });
  if (login.status !== 200) {
    throw new Error(`login failed: ${login.status} ${login.body}`);
  }
  return { token: login.json('access_token') };
}

export default function (data) {
  const auth = { headers: { Authorization: `Bearer ${data.token}` } };
  const responses = http.batch([
    ['GET', `${BASE_URL}/health/live`],
    ['GET', `${BASE_URL}/health/ready`],
    ['GET', `${BASE_URL}/auth/me`, null, auth],
  ]);
  check(responses[0], { 'live is 200': (r) => r.status === 200 });
  check(responses[1], { 'ready is 200': (r) => r.status === 200 });
  check(responses[2], { 'me is 200': (r) => r.status === 200 });
}
