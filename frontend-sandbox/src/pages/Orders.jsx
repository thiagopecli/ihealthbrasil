import React from 'react'
import { Link } from 'react-router-dom'
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

export default function Orders(){
  const { language } = useLanguage()
  const [orders, setOrders] = React.useState([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState(null)
  const [selectedId, setSelectedId] = React.useState(null)
  const [selectedOrder, setSelectedOrder] = React.useState(null)
  const [loadingDetail, setLoadingDetail] = React.useState(false)

  async function loadOrders(){
    setError(null)
    setLoading(true)
    try {
      const data = await api.fetchOrders()
      setOrders(data || [])
    } catch (err) {
      setError(err.message || 'Não foi possível carregar os pedidos.')
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => {
    loadOrders()
  }, [])

  React.useEffect(() => {
    const intervalId = window.setInterval(async () => {
      try {
        const data = await api.fetchOrders()
        setOrders(data || [])

        if (selectedId) {
          const detail = await api.fetchOrder(selectedId)
          setSelectedOrder(detail)
        }
      } catch {
        // Mantem UX silenciosa durante polling.
      }
    }, 15000)

    return () => window.clearInterval(intervalId)
  }, [selectedId])

  async function openOrder(orderId){
    setSelectedId(orderId)
    setLoadingDetail(true)
    try {
      const detail = await api.fetchOrder(orderId)
      setSelectedOrder(detail)
    } catch (err) {
      setError(err.message || 'Não foi possível carregar o detalhe do pedido.')
    } finally {
      setLoadingDetail(false)
    }
  }

  return (
    <div className="catalog-page">
      <section className="catalog-header">
        <div>
          <span className="eyebrow">Pedidos</span>
          <h2>Acompanhamento de pedidos e pagamento</h2>
        </div>
        <div className="button-row">
          <button className="secondary-btn" type="button" onClick={loadOrders}>Atualizar</button>
        </div>
      </section>

      {loading ? <div className="state-card">{t(language, 'toasts.loadingOrders')}</div> : null}
      {error ? <div className="state-card error">{error}</div> : null}

      {!loading && !error && orders.length === 0 ? (
        <div className="state-card">Você ainda não possui pedidos registrados.</div>
      ) : null}

      {!loading && orders.length > 0 ? (
        <div className="cart-layout">
          <div className="cart-items">
            {orders.map((order) => (
              <article className="cart-item" key={order.id}>
                <div>
                  <h3>Pedido #{order.id}</h3>
                  <p>Status: {order.status}</p>
                  <p>Criado em: {fmtDate(order.created_at)}</p>
                  <p>Total: {currency(order.total_price)}</p>
                  {order.payment ? <p>Pagamento: {order.payment.gateway_status}</p> : <p>Pagamento: pendente</p>}
                </div>
                <div className="cart-item-actions">
                  <button className="secondary-btn" type="button" onClick={() => openOrder(order.id)}>
                    {t(language, 'orders.viewDetails')}
                  </button>
                  <Link className="ghost-btn" to={`/orders/${order.id}`}>
                    Abrir página
                  </Link>
                </div>
              </article>
            ))}
          </div>

          <aside className="summary-card">
            <span className="eyebrow">Detalhe</span>
            {loadingDetail ? <div>{t(language, 'toasts.loading')}</div> : null}
            {!loadingDetail && !selectedOrder ? <div>Selecione um pedido.</div> : null}
            {!loadingDetail && selectedOrder ? (
              <div>
                <div className="summary-line"><span>ID</span><strong>#{selectedOrder.id}</strong></div>
                <div className="summary-line"><span>Status</span><strong>{selectedOrder.status}</strong></div>
                <div className="summary-line"><span>Total</span><strong>{currency(selectedOrder.total_price)}</strong></div>
                <div className="summary-line"><span>Pagamento</span><strong>{selectedOrder.payment?.gateway_status || 'pendente'}</strong></div>
                <div style={{ marginTop: '1rem' }}>
                  <strong>Itens</strong>
                  <ul style={{ marginTop: '0.5rem', paddingLeft: '1rem' }}>
                    {(selectedOrder.items || []).map((item) => (
                      <li key={item.id}>
                        {item.product?.name || 'Produto'} x {item.quantity} - {currency(item.total_price)}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}
          </aside>
        </div>
      ) : null}
    </div>
  )
}
