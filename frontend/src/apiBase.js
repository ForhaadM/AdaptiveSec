// Returns '' when running under the Vite dev server (relative URLs proxied to localhost:8000).
// Returns 'http://localhost:8000' when running inside a Chrome extension
// (where chrome-extension:// pages cannot use relative fetch/WebSocket URLs).
const API_BASE =
  typeof chrome !== 'undefined' && chrome?.runtime?.id
    ? 'http://localhost:8000'
    : ''

export default API_BASE
