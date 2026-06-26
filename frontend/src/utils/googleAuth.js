import { buildApiUrl } from './api'

const GOOGLE_SCRIPT_SRC = 'https://accounts.google.com/gsi/client'

function loadGoogleScript() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.oauth2) {
      resolve()
      return
    }

    const existing = document.querySelector(`script[src="${GOOGLE_SCRIPT_SRC}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true })
      existing.addEventListener('error', () => reject(new Error('google_script_error')), { once: true })
      return
    }

    const script = document.createElement('script')
    script.src = GOOGLE_SCRIPT_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('google_script_error'))
    document.head.appendChild(script)
  })
}

export async function getGoogleUserProfile() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  if (!clientId) {
    throw new Error('google_client_id_missing')
  }

  await loadGoogleScript()

  const tokenResponse = await new Promise((resolve, reject) => {
    const tokenClient = window.google.accounts.oauth2.initTokenClient({
      client_id: clientId,
      scope: 'openid email profile',
      callback: (response) => {
        if (response.error) {
          reject(new Error(response.error))
          return
        }
        resolve(response)
      },
    })

    tokenClient.requestAccessToken({ prompt: 'consent' })
  })

  const userResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
    headers: {
      Authorization: `Bearer ${tokenResponse.access_token}`,
    },
  })

  if (!userResponse.ok) {
    throw new Error('google_userinfo_error')
  }

  return userResponse.json()
}

export async function authenticateWithGoogle(idToken, clientId) {
  const response = await fetch(buildApiUrl('/auth/google-oauth/'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      id_token: idToken,
      client_id: clientId,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.id_token?.[0] || 'Google authentication failed')
  }

  return response.json()
}
