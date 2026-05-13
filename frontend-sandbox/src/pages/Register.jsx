import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api'
import { showToast } from '../toast'
import { t } from '../i18n'
import { useLanguage } from '../LanguageContext'

export default function Register() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [phone, setPhone] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { language } = useLanguage()
  const nav = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    if (password !== passwordConfirm) {
      const msg = t(language, 'register.passwordMismatch')
      setError(msg)
      showToast(msg, 'error')
      return
    }

    if (password.length < 8) {
      const msg = t(language, 'register.passwordShort')
      setError(msg)
      showToast(msg, 'error')
      return
    }

    setLoading(true)
    try {
      await api.register(username, email, password, firstName, lastName, 'PATIENT', phone)
      showToast(t(language, 'register.success'), 'success')
      nav('/login')
    } catch (err) {
      const errorMessage = err.message || 'Falha ao criar conta.'
      setError(errorMessage)
      showToast(errorMessage, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <section className="login-panel">
        <div className="login-copy">
          <span className="eyebrow">{t(language, 'register.eyebrow')}</span>
          <h2>{t(language, 'register.title')}</h2>
          <p>
            {t(language, 'register.description')}
          </p>
        </div>

        <form className="login-card" onSubmit={handleSubmit}>
          <h3>{t(language, 'register.createAccount')}</h3>

          <div className="login-field">
            <label htmlFor="register-username">{t(language, 'register.username')} *</label>
            <input
              id="register-username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={t(language, 'register.username')}
              required
            />
          </div>

          <div className="login-field">
            <label htmlFor="register-email">{t(language, 'register.email')} *</label>
            <input
              id="register-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu.email@example.com"
              required
            />
          </div>

          <div className="login-field">
            <label htmlFor="register-firstname">{t(language, 'register.firstName')}</label>
            <input
              id="register-firstname"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder={t(language, 'register.firstName')}
            />
          </div>

          <div className="login-field">
            <label htmlFor="register-lastname">{t(language, 'register.lastName')}</label>
            <input
              id="register-lastname"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder={t(language, 'register.lastName')}
            />
          </div>

          <div className="login-field">
            <label htmlFor="register-phone">{t(language, 'register.phone')}</label>
            <input
              id="register-phone"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="(11) 99999-9999"
            />
          </div>

          <div className="login-field">
            <label htmlFor="register-password">{t(language, 'register.passwordMin')}</label>
            <input
              id="register-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t(language, 'register.password')}
              required
            />
          </div>

          <div className="login-field">
            <label htmlFor="register-password-confirm">{t(language, 'register.passwordConfirm')} *</label>
            <input
              id="register-password-confirm"
              type="password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              placeholder={t(language, 'register.passwordConfirm')}
              required
            />
          </div>

          {error ? <div className="login-error">{error}</div> : null}

          <button className="primary-btn full-width" type="submit" disabled={loading}>
            {loading ? t(language, 'register.creating') : t(language, 'register.createAccount')}
          </button>

          <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.9rem' }}>
            {t(language, 'register.haveAccount')} <Link to="/login" style={{ color: 'var(--azul-ciano)', textDecoration: 'none', fontWeight: '600' }}>{t(language, 'register.login')}</Link>
          </p>
        </form>
      </section>
    </div>
  )
}
