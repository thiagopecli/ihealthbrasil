import React from 'react'
import { Link } from 'react-router-dom'
import { clearCart, getCart, getCartTotals, removeFromCart, updateCartQuantity } from '../cart'
import { showToast } from '../toast'
import { t } from '../i18n'
import { useLanguage } from '../LanguageContext'

function currency(value){
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value) || 0)
}

export default function Cart(){
  const { language } = useLanguage()
  const [items, setItems] = React.useState([])
  const [totals, setTotals] = React.useState({ totalItems: 0, totalPrice: 0 })
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState(null)

  function toTotals(currentItems){
    return {
      totalItems: currentItems.reduce((sum, item) => sum + (item.quantity || 0), 0),
      totalPrice: currentItems.reduce((sum, item) => sum + (Number(item.price) || 0) * (item.quantity || 0), 0),
    }
  }

  function syncCart(nextItems){
    setItems(nextItems)
    setTotals(toTotals(nextItems))
  }

  React.useEffect(() => {
    let alive = true

    async function loadCart(){
      try {
        setLoading(true)
        const [cartItems, totalsData] = await Promise.all([getCart(), getCartTotals()])
        if (!alive) return
        setItems(cartItems)
        setTotals(totalsData)
      } catch (err) {
        if (!alive) return
        setError(err.message || 'Não foi possível carregar o carrinho.')
      } finally {
        if (alive) setLoading(false)
      }
    }

    loadCart()
    return () => { alive = false }
  }, [])

  async function handleQuantity(id, value){
    try {
      const nextItems = await updateCartQuantity(id, Number(value))
      syncCart(nextItems)
      showToast(t(language, 'toasts.quantityUpdated'), 'success')
    } catch (err) {
      setError(err.message || 'Falha ao atualizar item do carrinho.')
      showToast(err.message || 'Falha ao atualizar item do carrinho.', 'error')
    }
  }

  async function handleRemove(id){
    try {
      const nextItems = await removeFromCart(id)
      syncCart(nextItems)
      showToast('Item removido do carrinho.', 'success')
    } catch (err) {
      setError(err.message || t(language, 'toasts.removeItemFailed'))
      showToast(err.message || t(language, 'toasts.removeItemFailed'), 'error')
    }
  }

  async function handleClear(){
    try {
      await clearCart()
      syncCart([])
      showToast('Carrinho limpo.', 'success')
    } catch (err) {
      setError(err.message || t(language, 'toasts.clearCartFailed'))
      showToast(err.message || t(language, 'toasts.clearCartFailed'), 'error')
    }
  }

  if (loading) return <div className="state-card">{t(language, 'toasts.loadingCart')}</div>

  return (
    <div className="cart-page">
      <div className="catalog-header">
        <div>
          <span className="eyebrow">Carrinho</span>
          <h2>{t(language, 'dashboard.cartTitle')}</h2>
        </div>
        <div className="button-row">
          <Link className="secondary-btn" to="/catalog">Continuar comprando</Link>
          <button className="ghost-btn" type="button" onClick={handleClear} disabled={items.length === 0}>{t(language, 'cart.clear')}</button>
        </div>
      </div>

      {error ? <div className="state-card error">{error}</div> : null}

      {items.length === 0 ? (
        <div className="state-card">
          {t(language, 'dashboard.cartEmpty')} <Link to="/catalog">catálogo</Link>
        </div>
      ) : (
        <div className="cart-layout">
          <div className="cart-items">
            {items.map((item) => (
              <article className="cart-item" key={item.id}>
                <div>
                  <h3>{item.name || item.title}</h3>
                  <p>{currency(item.price)} cada</p>
                </div>
                <div className="cart-item-actions">
                  <input
                    type="number"
                    min="1"
                    value={item.quantity}
                    onChange={(event) => handleQuantity(item.id, event.target.value)}
                  />
                  <strong>{currency((Number(item.price) || 0) * item.quantity)}</strong>
                  <button className="ghost-btn" type="button" onClick={() => handleRemove(item.id)}>{t(language, 'cart.remove')}</button>
                </div>
              </article>
            ))}
          </div>

          <aside className="summary-card">
            <span className="eyebrow">Resumo</span>
            <div className="summary-line"><span>Itens</span><strong>{totals.totalItems}</strong></div>
            <div className="summary-line"><span>Total</span><strong>{currency(totals.totalPrice)}</strong></div>
            <Link className="primary-btn full-width" to="/checkout">Ir para checkout</Link>
          </aside>
        </div>
      )}
    </div>
  )
}
