import React, { useEffect, useState } from 'react'
import Header from '../components/Header'
import Footer from '../components/Footer'
import { useLanguage } from '../LanguageContext'
import { buildApiUrl } from '../utils/api'

export default function Profile() {
  const { t } = useLanguage()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchMe() {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('access_token')
      if (!token) {
        setError('auth_required')
        setLoading(false)
        return
      }

      try {
        const res = await fetch(buildApiUrl('/auth/me/'), {
          headers: { Authorization: `Bearer ${token}` },
        })

        if (res.status === 401) {
          setError('auth_invalid')
          setUser(null)
        } else if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          setError(data.detail || 'fetch_error')
        } else {
          const data = await res.json()
          setUser(data)
        }
      } catch {
        setError('fetch_error')
      } finally {
        setLoading(false)
      }
    }

    fetchMe()
  }, [t])

  return (
    <div className='app-container'>
      <Header />
      <main className='profile-page'>
        <h1>Meu Perfil</h1>
        {loading && <p>Carregando...</p>}
        {!loading && error && (
          <div className='alert'>
            <p>{error === 'auth_required' ? 'Você precisa fazer login para ver seu perfil.' : 'Erro ao carregar perfil.'}</p>
          </div>
        )}

        {!loading && user && (
          <div className='profile-grid'>
            <section className='panel'>
              <h2>Dados Pessoais</h2>
              <p>
                <strong>Nome: </strong>
                {user.first_name} {user.last_name}
              </p>
              <p>
                <strong>Email: </strong>
                {user.email}
              </p>
              <p>
                <strong>Telefone: </strong>
                {user.phone_number || '—'}
              </p>
            </section>

            <section className='panel'>
              <h2>Endereços de Entrega</h2>
              <p>Você ainda não adicionou endereços. (implementação posterior)</p>
            </section>

            <section className='panel'>
              <h2>Pedidos</h2>
              <p>Seus pedidos aparecerão aqui. (implementação posterior)</p>
            </section>

            <section className='panel'>
              <h2>Carrinho</h2>
              <p>Itens do carrinho serão exibidos aqui. (implementação posterior)</p>
            </section>
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}
