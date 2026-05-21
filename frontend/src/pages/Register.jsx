import React, { useEffect, useState } from 'react'
import { Mail, Lock, User, Phone } from 'lucide-react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useLanguage } from '../LanguageContext'
import Header from '../components/Header'
import Footer from '../components/Footer'
import logoImg from '../assets/Logo_preto_branco.png.png'
import { getGoogleUserProfile } from '../utils/googleAuth'

export default function Register() {
  const { t } = useLanguage()
  const navigate = useNavigate()
  const location = useLocation()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [phone, setPhone] = useState('')
  const [agree, setAgree] = useState(true)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)

  useEffect(() => {
    if (location.state?.googleName) {
      setName(location.state.googleName)
    }
    if (location.state?.googleEmail) {
      setEmail(location.state.googleEmail)
    }
  }, [location.state])

  function validate() {
    if (!name || !email || !password) {
      setError(t('register_error_required'))
      return false
    }
    if (!agree) {
      setError(t('register_error_required'))
      return false
    }
    const re = /\S+@\S+\.\S+/
    if (!re.test(email)) {
      setError(t('register_error_email'))
      return false
    }
    if (password !== confirm) {
      setError(t('register_error_password_match'))
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
      // prepare payload
      const names = name.trim().split(/\s+/)
      const first_name = names.shift() || ''
      const last_name = names.join(' ') || ''
      const payload = {
        username: email.split('@')[0],
        email,
        password,
        first_name,
        last_name,
        phone_number: phone || '',
      }

      const res = await fetch(`${apiBase}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        // try to extract message
        const errMsg = data.detail || Object.values(data)[0]?.[0] || t('register_error_required')
        setError(errMsg)
        setLoading(false)
        return
      }

      // Auto-login after register
      const tokenRes = await fetch(`${apiBase}/auth/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: payload.username, password }),
      })
      const tokenData = await tokenRes.json()
      if (tokenRes.ok) {
        localStorage.setItem('access_token', tokenData.access)
        localStorage.setItem('refresh_token', tokenData.refresh)

        const meRes = await fetch(`${apiBase}/auth/me/`, {
          headers: { Authorization: `Bearer ${tokenData.access}` },
        })
        if (meRes.ok) {
          const meData = await meRes.json()
          localStorage.setItem('user', JSON.stringify(meData))
        }

        navigate('/')
      } else {
        setError(t('register_error_required'))
      }
    } catch (err) {
      console.error('Register error', err)
      setError(t('register_error_required'))
    } finally {
      setLoading(false)
    }
  }

  async function handleGooglePrefill() {
    try {
      setGoogleLoading(true)
      const profile = await getGoogleUserProfile()
      if (profile?.name) setName(profile.name)
      if (profile?.email) setEmail(profile.email)
      setError('')
    } catch {
      setError(t('google_auth_error'))
    } finally {
      setGoogleLoading(false)
    }
  }

  return (
    <>
      <Header />
      <main className="auth-page">
        <div className="auth-card">
          <aside className="auth-left">
            <img src={logoImg} alt="iHealth" className="auth-left-logo" />
            <h2>{t('register_title')}</h2>
            <p className="auth-lead">{t('register_subtitle')}</p>
            <ul className="auth-benefits">
              <li>{t('ml_benefit_1')}</li>
              <li>{t('ml_benefit_2')}</li>
              <li>{t('ml_benefit_3')}</li>
            </ul>
          </aside>

          <section className="auth-right">
            <h1 className="auth-heading">{t('create_account')}</h1>

            <div className="social-row" style={{ marginBottom: 8 }}>
              <button type="button" className="social-btn google" onClick={handleGooglePrefill} disabled={googleLoading}>
                {googleLoading ? t('loading') : t('register_with_google')}
              </button>
            </div>

            <div className="or-separator"><span>{t('or')}</span></div>

            <form className="auth-form" onSubmit={handleSubmit}>
              <label className="label">{t('name')}</label>
              <div className="input-with-icon">
                <User size={18} />
                <input value={name} onChange={(e) => setName(e.target.value)} placeholder={t('name_placeholder')} />
              </div>

              <label className="label">{t('email')}</label>
              <div className="input-with-icon">
                <Mail size={18} />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('email_placeholder')} />
              </div>

              <label className="label">{t('password')}</label>
              <div className="input-with-icon">
                <Lock size={18} />
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t('password_placeholder')} />
              </div>

              <label className="label">{t('confirm_password')}</label>
              <div className="input-with-icon">
                <Lock size={18} />
                <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder={t('confirm_password_placeholder')} />
              </div>

              <label className="label">{t('phone')}</label>
              <div className="input-with-icon">
                <Phone size={18} />
                <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder={t('phone_placeholder')} />
              </div>

              <div style={{ marginTop: 10 }}>
                <label style={{ fontSize: 13 }}>
                  <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
                  <span style={{ marginLeft: 8 }}>{t('terms_text')}</span>
                </label>
              </div>

              {error && <p className="form-error">{error}</p>}

              <button className="buy-button" style={{ marginTop: 18 }} type="submit" disabled={loading}>
                {loading ? t('loading') : t('create_account')}
              </button>

              <div className="register-row">
                <span>{t('has_account')}</span>
                <Link to="/login" className="login-register-link">{t('login')}</Link>
              </div>
            </form>
          </section>
        </div>
      </main>
      <Footer />
    </>
  )
}
