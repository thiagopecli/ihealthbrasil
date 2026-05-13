import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'
import { clearCart, getCart, getCartTotals } from '../cart'
import { showToast } from '../toast'
import { t } from '../i18n'
import { useLanguage } from '../LanguageContext'

function currency(value){
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value) || 0)
}

async function lookupCEP(cep) {
  const cleanCEP = cep.replace(/\D/g, '')
  if (cleanCEP.length !== 8) throw new Error('CEP deve ter 8 dígitos')
  const res = await fetch(`https://viacep.com.br/ws/${cleanCEP}/json/`)
  if (!res.ok) throw new Error('Erro ao buscar CEP')
  const data = await res.json()
  if (data.erro) throw new Error('CEP não encontrado')
  return {
    cep: data.cep,
    street: data.logradouro,
    neighborhood: data.bairro,
    city: data.localidade,
    state: data.uf,
    number: '',
    complement: ''
  }
}

async function calculateShipping(cep, items) {
  // Simula cálculo de frete dos Correios
  // Em produção, usar API real (Correios, Frenet, etc)
  const cleanCEP = cep.replace(/\D/g, '')
  if (cleanCEP.length !== 8) throw new Error('CEP inválido')
  
  // Calcula peso total (simulado: 0.5kg por item)
  const totalWeight = (items?.length || 1) * 0.5
  
  // Calcula distância aproximada baseado no CEP (simulado)
  const cepNum = parseInt(cleanCEP.substring(0, 5))
  let distanceFactor = 1
  if (cepNum < 10000) distanceFactor = 1.2
  else if (cepNum < 20000) distanceFactor = 1.5
  else if (cepNum < 80000) distanceFactor = 2
  else distanceFactor = 2.5
  
  // Calcula valores de frete
  const basePAC = 15 * distanceFactor
  const baseSEDEX = 35 * distanceFactor
  
  return {
    PAC: {
      name: 'PAC',
      price: parseFloat((basePAC + totalWeight * 5).toFixed(2)),
      deadline: '7-15 dias úteis'
    },
    SEDEX: {
      name: 'SEDEX',
      price: parseFloat((baseSEDEX + totalWeight * 10).toFixed(2)),
      deadline: '2-3 dias úteis'
    }
  }
}

export default function Checkout(){
  const navigate = useNavigate()
  const { language } = useLanguage()
  const [items, setItems] = React.useState([])
  const [totals, setTotals] = React.useState({ totalItems: 0, totalPrice: 0 })
  const [loading, setLoading] = React.useState(true)
  const [submitted, setSubmitted] = React.useState(false)
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState(null)
  const [orderResult, setOrderResult] = React.useState(null)
  const [paymentIntent, setPaymentIntent] = React.useState(null)
  const [lookingUpCEP, setLookingUpCEP] = React.useState(false)

  const [form, setForm] = React.useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    cpf: '',
    cep: '',
    street: '',
    number: '',
    complement: '',
    neighborhood: '',
    city: '',
    state: '',
    paymentMethod: 'credit_card',
    // Cartão de crédito
    cardNumber: '',
    cardHolder: '',
    cardExpiry: '',
    cardCVV: '',
  })
  
  const [shippingOptions, setShippingOptions] = React.useState(null)
  const [selectedShipping, setSelectedShipping] = React.useState(null)
  const [calculatingShipping, setCalculatingShipping] = React.useState(false)

  React.useEffect(() => {
    let alive = true

    async function loadCart(){
      try {
        setLoading(true)
        const [cartItems, totalsData] = await Promise.all([getCart(), getCartTotals()])
        if (!alive) return
        setItems(cartItems)
        setTotals(totalsData)
        // Se o usuário estiver autenticado, preencher dados pessoais automaticamente
        try {
          if (api.hasSession && api.hasSession()) {
            const me = await api.me()
            if (alive && me) {
              setForm(prev => ({
                ...prev,
                firstName: me.first_name || me.firstName || prev.firstName,
                lastName: me.last_name || me.lastName || prev.lastName,
                email: me.email || prev.email,
                phone: me.phone_number || me.phone || prev.phone,
                cpf: me.cpf || me.document || prev.cpf,
              }))
            }
          }
        } catch (err) {
          // ignorar falha em buscar /me - não bloqueia checkout
        }
      } catch (error) {
        if (!alive) return
        setSubmitError(String(error?.message || error))
      } finally {
        if (alive) setLoading(false)
      }
    }

    loadCart()
    return () => { alive = false }
  }, [])

  function handleInputChange(e) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  async function handleCEPLookup() {
    if (!form.cep.trim()) return
    setLookingUpCEP(true)
    setSubmitError(null)
    try {
      const data = await lookupCEP(form.cep)
      setForm(prev => ({ ...prev, ...data }))
      
      // Calcula frete
      setCalculatingShipping(true)
      try {
        const resp = await api.shippingQuote(form.cep)
        // Transformar resposta do backend para formato simples esperado pela UI
        if (resp && Array.isArray(resp.services) && resp.services.length > 0) {
          const mapped = {}
          resp.services.forEach(s => {
            const key = s.service_code || s.service_name || Math.random().toString(36).slice(2,8)
            mapped[key] = {
              name: s.service_name || key,
              price: Number(s.price) || 0,
              deadline: s.deadline || (s.delivery_days ? `${s.delivery_days} dias úteis` : '')
            }
          })
          setShippingOptions(mapped)
          const firstKey = Object.keys(mapped)[0]
          setSelectedShipping(firstKey)
          showToast('Frete calculado com sucesso!', 'success')
        } else {
          // Fallback local quando backend não retornar serviços
          const shipping = await calculateShipping(form.cep, items)
          setShippingOptions(shipping)
          setSelectedShipping('PAC')
          showToast('Frete calculado localmente (fallback).', 'info')
        }
      } catch (err) {
        // Se erro no backend, usar cálculo local
        const shipping = await calculateShipping(form.cep, items)
        setShippingOptions(shipping)
        setSelectedShipping('PAC')
        showToast('Frete calculado localmente (fallback).', 'info')
      }
    } catch (err) {
      setSubmitError(err.message)
      showToast(err.message, 'error')
    } finally {
      setLookingUpCEP(false)
      setCalculatingShipping(false)
    }
  }

  function validateForm() {
    if (!form.firstName.trim()) return 'Digite seu nome'
    if (!form.lastName.trim()) return 'Digite seu sobrenome'
    if (!form.email.trim()) return 'Digite seu email'
    if (!form.phone.trim()) return 'Digite seu telefone'
    if (!form.cpf.trim()) return 'Digite seu CPF'
    if (!form.cep.trim()) return 'Digite o CEP'
    if (!form.street.trim()) return 'Busque o CEP ou digite a rua'
    if (!form.number.trim()) return 'Digite o número'
    if (!form.city.trim()) return 'Digite a cidade'
    if (!form.state.trim()) return 'Digite o estado'
    if (!selectedShipping) return 'Selecione uma opção de entrega'

    // Validações de pagamento
    if (form.paymentMethod === 'credit_card') {
      if (!form.cardNumber.trim()) return 'Digite o número do cartão'
      if (!form.cardHolder.trim()) return 'Digite o nome do titulador'
      if (!form.cardExpiry.trim()) return 'Digite a validade do cartão'
      if (!form.cardCVV.trim()) return 'Digite o CVV do cartão'
    }

    return null
  }

  async function finishOrder(){
    const error = validateForm()
    if (error) {
      setSubmitError(error)
      showToast(error, 'error')
      return
    }

    setSubmitting(true)
    setSubmitError(null)
    try {
      const order = await api.checkoutCart({
        firstName: form.firstName,
        lastName: form.lastName,
        email: form.email,
        phone: form.phone,
        cpf: form.cpf,
        deliveryAddress: {
          cep: form.cep,
          street: form.street,
          number: form.number,
          complement: form.complement,
          neighborhood: form.neighborhood,
          city: form.city,
          state: form.state,
        },
        shipping: {
          method: selectedShipping,
          price: shippingOptions[selectedShipping].price,
          deadline: shippingOptions[selectedShipping].deadline,
        },
        paymentMethod: form.paymentMethod,
      })
      let intent = null
      if (order?.id) {
        try {
          intent = await api.createPaymentIntent(order.id, { currency: 'brl' })
        } catch {
          intent = null
        }
      }
      await clearCart()
      setItems([])
      setTotals({ totalItems: 0, totalPrice: 0 })
      setOrderResult(order)
      setPaymentIntent(intent)
      setSubmitted(true)
      showToast(t(language, 'toasts.orderCreatedSuccess'), 'success')
    } catch (error) {
      try {
        const fallbackOrder = await api.syncLocalCartAndCheckout(items, {
          firstName: form.firstName,
          lastName: form.lastName,
          email: form.email,
          phone: form.phone,
          cpf: form.cpf,
          deliveryAddress: {
            cep: form.cep,
            street: form.street,
            number: form.number,
            city: form.city,
            state: form.state,
          },
          shipping: {
            method: selectedShipping,
            price: shippingOptions[selectedShipping].price,
            deadline: shippingOptions[selectedShipping].deadline,
          },
          paymentMethod: form.paymentMethod,
        })
        await clearCart()
        setItems([])
        setTotals({ totalItems: 0, totalPrice: 0 })
        setOrderResult(fallbackOrder)
        setPaymentIntent(null)
        setSubmitted(true)
        showToast(t(language, 'toasts.mockOrderCreated'), 'info')
      } catch (fallbackError) {
        setSubmitError(String(fallbackError?.message || fallbackError))
        showToast(String(fallbackError?.message || fallbackError), 'error')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="state-card">{t(language, 'toasts.loadingCheckout')}</div>

  return (
    <div className="checkout-page">
      <div className="catalog-header">
        <div>
          <span className="eyebrow">Checkout</span>
          <h2>{t(language, 'checkout.review')}</h2>
        </div>
        <Link className="secondary-btn" to="/cart">{t(language, 'checkout.backToCart')}</Link>
      </div>

      <div className="checkout-layout">
        <section className="checkout-card">
          {submitted ? (
            <>
              <div className="state-card success">
                {orderResult?.mock
                  ? t(language, 'toasts.mockOrderSuccess')
                  : `Pedido criado com sucesso${orderResult?.id ? ` (ID: ${orderResult.id})` : ''}.`}
              </div>
              <div style={{ marginTop: '1rem', padding: '16px', background: '#f5f5f5', borderRadius: '12px' }}>
                <h4>Dados do pedido:</h4>
                <p><strong>Nome:</strong> {form.firstName} {form.lastName}</p>
                <p><strong>Email:</strong> {form.email}</p>
                <p><strong>Telefone:</strong> {form.phone}</p>
                <p><strong>Entrega:</strong> {form.street}, {form.number} - {form.city}, {form.state}</p>
                <p><strong>Método de pagamento:</strong> {form.paymentMethod === 'credit_card' ? 'Cartão de crédito' : form.paymentMethod === 'pix' ? 'PIX' : 'Boleto'}</p>
              </div>
              {paymentIntent?.checkout_url ? (
                <div className="button-row" style={{ marginTop: '1rem' }}>
                  <a className="primary-btn" href={paymentIntent.checkout_url} target="_blank" rel="noreferrer">Ir para pagamento</a>
                  <Link className="secondary-btn" to={`/orders/${orderResult?.id}`}>Acompanhar pedido</Link>
                </div>
              ) : !orderResult?.mock ? (
                <div className="button-row" style={{ marginTop: '1rem' }}>
                  <Link className="secondary-btn" to={`/orders/${orderResult?.id}`}>Acompanhar pedido</Link>
                </div>
              ) : null}
              <button className="ghost-btn" style={{ marginTop: '1rem', width: '100%' }} onClick={() => navigate('/catalog')}>Voltar ao catálogo</button>
            </>
          ) : (
            <>
              {submitError ? <div className="state-card error">{submitError}</div> : null}
              
              {/* Dados do Cliente */}
              <h3 style={{ marginTop: '0' }}>Dados pessoais</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="login-field">
                  <label>Nome *</label>
                  <input type="text" name="firstName" value={form.firstName} onChange={handleInputChange} placeholder="Seu nome" />
                </div>
                <div className="login-field">
                  <label>Sobrenome *</label>
                  <input type="text" name="lastName" value={form.lastName} onChange={handleInputChange} placeholder="Seu sobrenome" />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="login-field">
                  <label>Email *</label>
                  <input type="email" name="email" value={form.email} onChange={handleInputChange} placeholder="seu@email.com" />
                </div>
                <div className="login-field">
                  <label>Telefone *</label>
                  <input type="tel" name="phone" value={form.phone} onChange={handleInputChange} placeholder="(11) 99999-9999" />
                </div>
              </div>
              <div className="login-field">
                <label>CPF *</label>
                <input type="text" name="cpf" value={form.cpf} onChange={handleInputChange} placeholder="000.000.000-00" />
              </div>

              {/* Endereço de Entrega */}
              <h3>Endereço de entrega</h3>
              <div className="login-field">
                <label>CEP *</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    name="cep"
                    value={form.cep}
                    onChange={handleInputChange}
                    placeholder="00000-000"
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    className="primary-btn"
                    onClick={handleCEPLookup}
                    disabled={lookingUpCEP || !form.cep.trim()}
                    style={{ padding: '10px 16px' }}
                  >
                    {lookingUpCEP ? 'Buscando...' : 'Buscar'}
                  </button>
                </div>
              </div>
              <div className="login-field">
                <label>Rua *</label>
                <input type="text" name="street" value={form.street} onChange={handleInputChange} placeholder="Rua, avenida, etc" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="login-field">
                  <label>Número *</label>
                  <input type="text" name="number" value={form.number} onChange={handleInputChange} placeholder="123" />
                </div>
                <div className="login-field">
                  <label>Complemento</label>
                  <input type="text" name="complement" value={form.complement} onChange={handleInputChange} placeholder="Apto 456, Sala 2, etc" />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="login-field">
                  <label>Bairro</label>
                  <input type="text" name="neighborhood" value={form.neighborhood} onChange={handleInputChange} placeholder="Bairro" readOnly={!!form.neighborhood} />
                </div>
                <div className="login-field">
                  <label>Cidade *</label>
                  <input type="text" name="city" value={form.city} onChange={handleInputChange} placeholder="Cidade" />
                </div>
              </div>
              <div className="login-field">
                <label>Estado *</label>
                <input type="text" name="state" value={form.state} onChange={handleInputChange} placeholder="SP" maxLength="2" style={{ textTransform: 'uppercase' }} />
              </div>

              {/* Opções de Frete */}
              {shippingOptions && (
                <div style={{ marginTop: '20px', padding: '16px', background: '#f0f0f0', borderRadius: '8px' }}>
                  <h3 style={{ marginTop: 0 }}>Opções de entrega</h3>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {Object.entries(shippingOptions).map(([key, option]) => (
                      <label key={key} style={{ display: 'flex', gap: '12px', padding: '12px', background: '#fff', borderRadius: '8px', cursor: 'pointer', border: selectedShipping === key ? '2px solid #4CAF50' : '1px solid #ddd' }}>
                        <input
                          type="radio"
                          name="shipping"
                          value={key}
                          checked={selectedShipping === key}
                          onChange={(e) => setSelectedShipping(e.target.value)}
                          style={{ marginTop: '4px' }}
                        />
                        <div style={{ flex: 1 }}>
                          <strong>{option.name}</strong>
                          <p style={{ margin: '4px 0 0 0', fontSize: '0.9rem', color: '#666' }}>
                            {option.deadline}
                          </p>
                        </div>
                        <strong style={{ color: '#4CAF50', fontSize: '1.1rem' }}>{currency(option.price)}</strong>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Forma de Pagamento */}
              <h3>Forma de pagamento</h3>
              <div style={{ display: 'grid', gap: '12px' }}>
                {[
                  { value: 'credit_card', label: '💳 Cartão de crédito' },
                  { value: 'pix', label: '📲 PIX' },
                  { value: 'boleto', label: '📄 Boleto' },
                ].map(method => (
                  <label key={method.value} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '12px', border: form.paymentMethod === method.value ? '2px solid #0099cc' : '1px solid #ddd', borderRadius: '8px', background: form.paymentMethod === method.value ? '#e5f4fb' : '#fafafa' }}>
                    <input
                      type="radio"
                      name="paymentMethod"
                      value={method.value}
                      checked={form.paymentMethod === method.value}
                      onChange={handleInputChange}
                      style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                    />
                    <span style={{ fontWeight: form.paymentMethod === method.value ? '600' : '400' }}>{method.label}</span>
                  </label>
                ))}
              </div>

              {/* Campos dinâmicos de pagamento */}
              {form.paymentMethod === 'credit_card' && (
                <div style={{ marginTop: '16px', padding: '16px', background: '#f9f9f9', borderRadius: '12px', border: '1px solid #e0e0e0' }}>
                  <h4 style={{ marginTop: 0 }}>Dados do cartão</h4>
                  <div className="login-field">
                    <label>Número do cartão *</label>
                    <input
                      type="text"
                      name="cardNumber"
                      value={form.cardNumber}
                      onChange={handleInputChange}
                      placeholder="1234 5678 9012 3456"
                      maxLength="19"
                    />
                  </div>
                  <div className="login-field">
                    <label>Titulador *</label>
                    <input
                      type="text"
                      name="cardHolder"
                      value={form.cardHolder}
                      onChange={handleInputChange}
                      placeholder="Nome como aparece no cartão"
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div className="login-field">
                      <label>Validade (MM/YY) *</label>
                      <input
                        type="text"
                        name="cardExpiry"
                        value={form.cardExpiry}
                        onChange={handleInputChange}
                        placeholder="12/25"
                        maxLength="5"
                      />
                    </div>
                    <div className="login-field">
                      <label>CVV *</label>
                      <input
                        type="text"
                        name="cardCVV"
                        value={form.cardCVV}
                        onChange={handleInputChange}
                        placeholder="123"
                        maxLength="4"
                      />
                    </div>
                  </div>
                </div>
              )}

              {form.paymentMethod === 'pix' && (
                <div style={{ marginTop: '16px', padding: '16px', background: '#f0f8f0', borderRadius: '12px', border: '1px solid #c0e0c0' }}>
                  <h4 style={{ marginTop: 0 }}>Instruções de pagamento via PIX</h4>
                  <p style={{ color: '#555', lineHeight: 1.6 }}>
                    Você receberá um QR code e as instruções de pagamento por email após confirmar o pedido. 
                    O pagamento deve ser realizado em até 24 horas para confirmar o pedido.
                  </p>
                  <div style={{ marginTop: '12px', padding: '12px', background: '#e8f5e9', borderRadius: '8px', fontSize: '0.9rem', color: '#2e7d32' }}>
                    ✅ QR Code e instruções serão enviados por email
                  </div>
                </div>
              )}

              {form.paymentMethod === 'boleto' && (
                <div style={{ marginTop: '16px', padding: '16px', background: '#fff8e1', borderRadius: '12px', border: '1px solid #ffe082' }}>
                  <h4 style={{ marginTop: 0 }}>Instruções de pagamento via Boleto</h4>
                  <p style={{ color: '#555', lineHeight: 1.6 }}>
                    Você receberá o boleto por email após confirmar o pedido. 
                    O pagamento deve ser realizado em até 3 dias úteis para confirmar o pedido.
                  </p>
                  <p style={{ fontSize: '0.95rem', color: '#666', marginBottom: '12px' }}>
                    <strong>CPF para pagamento:</strong> {form.cpf}
                  </p>
                  <div style={{ marginTop: '12px', padding: '12px', background: '#fff9c4', borderRadius: '8px', fontSize: '0.9rem', color: '#f57f17' }}>
                    ⏱️ Boleto e instruções de pagamento serão enviados por email
                  </div>
                </div>
              )}

              {/* Resumo do Pedido */}
              <h3>Resumo do pedido</h3>
              <div className="summary-list">
                {items.length === 0 ? <div className="state-card">Nenhum item no carrinho.</div> : items.map((item) => (
                  <div className="summary-line" key={item.id}>
                    <span>{item.name || item.title} x {item.quantity}</span>
                    <strong>{currency((Number(item.price) || 0) * item.quantity)}</strong>
                  </div>
                ))}
              </div>
              {shippingOptions && selectedShipping && (
                <div className="summary-line">
                  <span>Frete ({shippingOptions[selectedShipping].name})</span>
                  <strong>{currency(shippingOptions[selectedShipping].price)}</strong>
                </div>
              )}
              <div className="summary-line total-line">
                <span>Total do pedido</span>
                <strong>{currency(totals.totalPrice + (shippingOptions && selectedShipping ? shippingOptions[selectedShipping].price : 0))}</strong>
              </div>

              <div className="button-row" style={{ marginTop: '20px' }}>
                <button className="primary-btn" type="button" onClick={finishOrder} disabled={submitting || items.length === 0}>
                  {submitting ? t(language, 'checkout.finalizing') : t(language, 'checkout.finishOrder')}
                </button>
                <button className="ghost-btn" type="button" onClick={() => navigate('/cart')}>Voltar ao carrinho</button>
              </div>
            </>
          )}
        </section>
        <aside className="checkout-card accent">
          <h3>{t(language, 'checkout.sandboxTitle')}</h3>
          <ul>
            <li>{t(language, 'checkout.feature1')}</li>
            <li>{t(language, 'checkout.feature2')}</li>
            <li>{t(language, 'checkout.feature3')}</li>
            <li>{t(language, 'checkout.feature4')}</li>
            <li>✅ Lookup de CEP via ViaCEP</li>
            <li>✅ Múltiplas formas de pagamento (Cartão, PIX, Boleto)</li>
          </ul>
        </aside>
      </div>
    </div>
  )
}
