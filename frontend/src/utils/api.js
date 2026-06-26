const DEV_API_BASE_URL = 'http://127.0.0.1:8000/api'

export function getApiBaseUrl() {
  if (import.meta.env.DEV) {
    return DEV_API_BASE_URL
  }

  return import.meta.env.VITE_API_URL || DEV_API_BASE_URL
}

export function buildApiUrl(path) {
  const baseUrl = getApiBaseUrl().replace(/\/$/, '')
  const normalizedPath = path.startsWith('/') ? path : `/${path}`

  return `${baseUrl}${normalizedPath}`
}