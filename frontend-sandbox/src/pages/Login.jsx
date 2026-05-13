import React, {useState} from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api'
import { showToast } from '../toast'
import { t } from '../i18n'
import { useLanguage } from '../LanguageContext'

export default function Login(){
  const [username,setUsername]=useState('')
  const [password,setPassword]=useState('')
  const [error,setError]=useState(null)
  const { language } = useLanguage()
  const nav = useNavigate()

  async function handleSubmit(e){
    e.preventDefault()
    setError(null)
    try{
      await api.login(username,password)
      window.dispatchEvent(new Event('ihealthbrasil:auth-updated'))
      showToast('Login realizado com sucesso.', 'success')
      nav('/dashboard')
    }catch(err){
      setError(err.message)
      showToast(err.message || 'Falha no login.', 'error')
    }
  }

  return (
    <div className="login-page">
      <section className="login-panel">
        <div className="login-copy">
          <span className="eyebrow">{t(language, 'login.eyebrow')}</span>
          <h2>{t(language, 'login.title')}</h2>
          <p>
            {t(language, 'login.description')}
          </p>
        </div>

        <form className="login-card" onSubmit={handleSubmit}>
          <h3>{t(language, 'login.login')}</h3>
          <div className="login-field">
            <label htmlFor="login-username">{t(language, 'login.username')}</label>
            <input
              id="login-username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              placeholder={t(language, 'login.username')}
            />
          </div>
          <div className="login-field">
            <label htmlFor="login-password">{t(language, 'login.password')}</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              placeholder={t(language, 'login.password')}
            />
          </div>
          {error ? <div className="login-error">{error}</div> : null}
          <button className="primary-btn full-width" type="submit">{t(language, 'login.login')}</button>

          <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.9rem' }}>
            {t(language, 'login.noAccount')} <Link to="/register" style={{ color: 'var(--azul-ciano)', textDecoration: 'none', fontWeight: '600' }}>{t(language, 'login.createAccount')}</Link>
          </p>
        </form>
      </section>
    </div>
  )
}
