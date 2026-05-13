import React, {useEffect, useState} from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api'
import { addToCart } from '../cart'
import { showToast } from '../toast'
import { t } from '../i18n'
import { useLanguage } from '../LanguageContext'

function currency(value){
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value) || 0)
}

export default function Product(){
  const {id} = useParams()
  const navigate = useNavigate()
  const { language } = useLanguage()
  const [item,setItem] = useState(null)
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState(null)
  const [adding, setAdding] = useState(false)

  useEffect(()=>{
    setLoading(true)
    api.fetchProduct(id).then(d=>{setItem(d);setLoading(false)}).catch(e=>{setError(e.message);setLoading(false)})
  },[id])

  async function handleAdd(){
    if (!item) return
    setAdding(true)
    try {
      await addToCart(item, 1)
      showToast('Item adicionado ao carrinho.', 'success')
    } catch (err) {
      setError(err.message || 'Não foi possível adicionar ao carrinho.')
      showToast(err.message || 'Não foi possível adicionar ao carrinho.', 'error')
    } finally {
      setAdding(false)
    }
  }

  if(loading) return <div className="state-card">{t(language, 'toasts.loadingProduct')}</div>
  if(error) return <div className="state-card error">{error}</div>
  if(!item) return <div className="state-card">Produto não encontrado</div>

  return (
    <div className="product-detail">
      <div className="product-detail-media">
        {item.image ? <img src={item.image} alt={item.name || item.title} /> : null}
      </div>
      <div className="product-detail-info">
        <span className="eyebrow">{item.category_name || item.category_slug}</span>
        <h2>{item.name || item.title}</h2>
        <div className="price-tag">{currency(item.price)}</div>
        <p>{item.description}</p>
        <div className="detail-grid">
          <div><span>Estoque</span><strong>{item.stock ?? '—'}</strong></div>
          <div><span>{t(language, 'product.prescription')}</span><strong>{item.requires_prescription ? t(language, 'product.yes') : t(language, 'product.no')}</strong></div>
        </div>
        <div className="button-row">
          <button className="primary-btn" type="button" onClick={handleAdd} disabled={adding}>
            {adding ? 'Adicionando...' : 'Adicionar ao carrinho'}
          </button>
          <button className="secondary-btn" type="button" onClick={() => navigate('/cart')}>Ir para carrinho</button>
          <Link className="ghost-btn" to="/catalog">{t(language, 'product.back')}</Link>
        </div>
      </div>
    </div>
  )
}
