import React from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../api'
import { t } from '../i18n'
import { useLanguage } from '../LanguageContext'

function currency(value){
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value) || 0)
}

function fmtDate(value){
  if (!value) return '—'
  return new Date(value).toLocaleString('pt-BR')
}

function normalizeStatus(value){
  return String(value || '').trim().toLowerCase()
}

function statusLabel(value){
  const status = normalizeStatus(value)

  if (!status) return 'Pendente'
  if (['paid', 'confirmed', 'succeeded', 'approved', 'completed'].includes(status)) return 'Pago'
  if (['processing', 'pending', 'waiting'].includes(status)) return 'Em processamento'
  if (['failed', 'cancelled', 'canceled', 'rejected'].includes(status)) return 'Falhou'
  return value
}

function statusTone(value){
  const status = normalizeStatus(value)

  if (['paid', 'confirmed', 'succeeded', 'approved', 'completed'].includes(status)) return 'success'
  if (['failed', 'cancelled', 'canceled', 'rejected'].includes(status)) return 'error'
  return 'info'
}

function TimelineItem({ title, value, tone }){
  return (
    <div className={`timeline-item ${tone || ''}`.trim()}>
      <span className="timeline-dot" aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        <p>{value}</p>
      </div>
    </div>
  )
}

export default function OrderDetail(){
  const { id } = useParams()
  const { language } = useLanguage()
  const [order, setOrder] = React.useState(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState(null)

  async function loadOrder(){
    if (!id) return
    setError(null)
    try {
      const data = await api.fetchOrder(id)
      setOrder(data)
    } catch (err) {
      setError(err.message || 'Não foi possível carregar o pedido.')
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => {
    let alive = true

    async function firstLoad(){
      if (!alive) return
      setLoading(true)
      await loadOrder()
    }

    firstLoad()

    const intervalId = window.setInterval(() => {
      loadOrder()
    }, 15000)

    return () => {
      alive = false
      window.clearInterval(intervalId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (loading) return <div className="state-card">{t(language, 'toasts.loadingOrder')}</div>
  if (error) return <div className="state-card error">{error}</div>
  if (!order) return <div className="state-card">Pedido não encontrado.</div>

  return (
    <div className="catalog-page">
      <section className="catalog-header">
        <div>
          <span className="eyebrow">Pedido</span>
          <h2>Pedido #{order.id}</h2>
        </div>
        <div className="button-row">
          <button className="secondary-btn" type="button" onClick={loadOrder}>Atualizar agora</button>
          <Link className="ghost-btn" to="/orders">{t(language, 'orderDetail.goBack')}</Link>
        </div>
      </section>

      <div className="checkout-layout">
        <section className="checkout-card">
          <div className="order-status-bar">
            <span className={`status-pill ${statusTone(order.status)}`}>{statusLabel(order.status)}</span>
            <span className="status-subtitle">Atualizado em tempo quase real com o backend.</span>
          </div>
          <div className="summary-line"><span>Status técnico</span><strong>{order.status}</strong></div>
          <div className="summary-line"><span>Total</span><strong>{currency(order.total_price)}</strong></div>
          <div className="summary-line"><span>Criado em</span><strong>{fmtDate(order.created_at)}</strong></div>
          <div className="summary-line"><span>Pagamento</span><strong>{order.payment?.gateway_status || 'pendente'}</strong></div>

          <div style={{ marginTop: '1rem' }}>
            <h3>Linha do tempo</h3>
            <div className="timeline-list">
              <TimelineItem title="Pedido criado" value={fmtDate(order.created_at)} tone="info" />
              <TimelineItem title="Status atual" value={statusLabel(order.status)} tone={statusTone(order.status)} />
              <TimelineItem title="Pagamento" value={order.payment?.gateway_status || 'pendente'} tone={statusTone(order.payment?.gateway_status)} />
              <TimelineItem title="Última transação" value={order.payment?.gateway_transaction_id || '—'} tone="info" />
            </div>
          </div>

          <div style={{ marginTop: '1rem' }}>
            <h3>Itens</h3>
            <ul style={{ marginTop: '0.5rem', paddingLeft: '1rem' }}>
              {(order.items || []).map((item) => (
                <li key={item.id}>
                  {item.product?.name || 'Produto'} x {item.quantity} - {currency(item.total_price)}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <aside className="checkout-card accent">
          <h3>Status de pagamento</h3>
          <p>Esta tela atualiza automaticamente a cada 15 segundos para refletir mudanças de status no backend.</p>
          <div className="summary-line"><span>Gateway</span><strong>{order.payment?.gateway || '—'}</strong></div>
          <div className="summary-line"><span>Transação</span><strong>{order.payment?.gateway_transaction_id || '—'}</strong></div>
          <div className="summary-line"><span>Pagamento criado em</span><strong>{fmtDate(order.payment?.created_at)}</strong></div>
          {order.payment?.checkout_url ? (
            <a className="primary-btn full-width" href={order.payment.checkout_url} target="_blank" rel="noreferrer">
              Continuar pagamento
            </a>
          ) : null}
        </aside>
      </div>
    </div>
  )
}
