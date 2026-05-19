import React, { useState, useEffect } from 'react'
import { Mail, Lock } from 'lucide-react'
import { useNavigate, Link } from 'react-router-dom'
import { useLanguage } from '../LanguageContext'
import Header from '../components/Header'
import Footer from '../components/Footer'
import logoImg from '../assets/Logo_preto_branco.png.png'
import { authenticateWithGoogle } from '../utils/googleAuth'

export default function Login() {
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)

  useEffect(() => {
    // Load Google script
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    document.head.appendChild(script)
  }, [])

  function validate() {
    if (!email || !password) {
      setError(t('login_error_required'))
      return false
    }

    // simple email pattern
    const re = /\S+@\S+\.\S+/
    if (!re.test(email)) {
      setError(t('login_error_email'))
      return false
    }

    setError('')
    return true
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)

    try {
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
      const res = await fetch(`${apiBase}/auth/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email, password }),
      })

      const data = await res.json()
      if (!res.ok) {
        setError(data.detail || 'invalid_credentials')
        setLoading(false)
        return
      }

      // Store tokens and fetch user profile
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)

      // fetch /me
      const meRes = await fetch(`${apiBase}/auth/me/`, {
        headers: { Authorization: `Bearer ${data.access}` },
      })
      if (meRes.ok) {
        const meData = await meRes.json()
        localStorage.setItem('user', JSON.stringify(meData))
      }

      navigate('/')
    } catch (err) {
      console.error('Login error', err)
      setError(t('login_error_required'))
    } finally {
      setLoading(false)
    }
  }

  async function handleGoogleAuth() {
    try {
      setGoogleLoading(true)
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
      if (!clientId) {
        setError(t('google_client_id_missing'))
        setGoogleLoading(false)
        return
      }

      // Get Google ID token using OAuth
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

      // Send ID token to backend for authentication
      const result = await authenticateWithGoogle(tokenResponse.credential, clientId)

      // Store tokens in localStorage
      localStorage.setItem('access_token', result.access)
      localStorage.setItem('refresh_token', result.refresh)
      localStorage.setItem('user', JSON.stringify(result.user))

      // Redirect to home
      navigate('/')
    } catch (err) {
      setError(t('google_auth_error'))
      console.error('Google auth error:', err)
    } finally {
      setGoogleLoading(false)
    }
  }

  // Dev helper: quick login with test user
  async function handleQuickLogin() {
    setError('')
    setLoading(true)
    try {
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
      const res = await fetch(`${apiBase}/auth/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'test_user_ai@example.com', password: 'TestPass123' }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setError(JSON.stringify(data))
        setLoading(false)
        return
      }

      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      const meRes = await fetch(`${apiBase}/auth/me/`, { headers: { Authorization: `Bearer ${data.access}` } })
      if (meRes.ok) {
        const me = await meRes.json()
        localStorage.setItem('user', JSON.stringify(me))
      }
      navigate('/')
    } catch (err) {
      console.error('Quick login error', err)
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header />
      <main className="auth-page">
        <div className="auth-card">
          <aside className="auth-left">
            <img src={logoImg} alt="iHealth" className="auth-left-logo" />
            <h2>{t('ml_login_title')}</h2>
            <p className="auth-lead">{t('ml_login_text')}</p>
            <ul className="auth-benefits">
              <li>{t('ml_benefit_1')}</li>
              <li>{t('ml_benefit_2')}</li>
              <li>{t('ml_benefit_3')}</li>
            </ul>
          </aside>

          <section className="auth-right">
            <h1 className="auth-heading">{t('login')}</h1>

            <div className="social-row">
              <button type="button" className="social-btn google" onClick={handleGoogleAuth} disabled={googleLoading}>
                {googleLoading ? t('loading') : t('login_with_google')}
              </button>
            </div>

            <div className="or-separator"><span>{t('or')}</span></div>

            <form className="auth-form" onSubmit={handleSubmit}>
              <label className="label">{t('email')}</label>
              <div className="input-with-icon">
                <Mail size={18} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('email_placeholder')}
                />
              </div>

              <label className="label">{t('password')}</label>
              <div className="input-with-icon">
                <Lock size={18} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('password_placeholder')}
                />
              </div>

              <div className="auth-actions">
                <a href="#" className="forgot-link">{t('forgot_password')}</a>
                <button className="buy-button" type="submit" disabled={loading}>
                  {loading ? t('loading') : t('entrar')}
                </button>
              </div>

              {error && <p className="form-error">{error}</p>}

              <div className="register-row">
                <span>{t('no_account')}</span>
                <Link to="/register" className="login-register-link">{t('create_account')}</Link>
              </div>
              <div style={{ marginTop: 12 }}>
                <button type="button" className="social-btn" onClick={handleQuickLogin} style={{ background: '#eee', color: '#111' }}>
                  Login de Teste (dev)
                </button>
              </div>
            </form>
          </section>
        </div>
      </main>
      <Footer />
    </>
  )
}
