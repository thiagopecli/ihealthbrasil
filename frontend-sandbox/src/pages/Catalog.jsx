import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { addToCart } from '../cart'
import { showToast } from '../toast'
import { t } from '../i18n'
import { useLanguage } from '../LanguageContext'

function currency(value){
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value) || 0)
}

export default function Catalog(){
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const { language } = useLanguage()
  const [addingId, setAddingId] = useState(null)
  const [filters, setFilters] = useState({ search: '', category_slug: '', ordering: 'name', requires_prescription: '' })

  useEffect(()=>{
    let alive = true
    setLoading(true)
    Promise.all([
      api.fetchCategories(),
      api.fetchProducts(new URLSearchParams(filters).toString())
    ])
      .then(([categoriesData, productsData]) => {
        if (!alive) return
        setCategories(categoriesData || [])
        setItems(productsData || [])
        setLoading(false)
      })
      .catch((err) => {
        if (!alive) return
        setError(err.message)
        setLoading(false)
      })

    return () => { alive = false }
  }, [filters])

  function updateFilter(name, value){
    setFilters((current) => ({ ...current, [name]: value }))
  }

  async function handleAdd(product){
    setAddingId(product.id)
    try {
      await addToCart(product, 1)
      showToast(t(language, 'toasts.addedToCart'), 'success')
    } catch (err) {
      setError(err.message || t(language, 'toasts.addToCartFailed'))
      showToast(err.message || t(language, 'toasts.addToCartFailed'), 'error')
    } finally {
      setAddingId(null)
    }
  }

  if(loading) return <div className="state-card">{t(language, 'toasts.loadingCatalog')}</div>
  if(error) return <div className="state-card error">{error}</div>

  return (
    <div className="catalog-page">
      <section className="catalog-header">
        <div>
          <span className="eyebrow">{t(language, 'catalog.title')}</span>
          <h2>{t(language, 'catalog.subtitle')}</h2>
        </div>
        <div className="catalog-filters">
          <input
            value={filters.search}
            onChange={(event) => updateFilter('search', event.target.value)}
            placeholder={t(language, 'catalog.search') + ' por nome, descrição ou categoria'}
          />
          <select value={filters.category_slug} onChange={(event) => updateFilter('category_slug', event.target.value)}>
            <option value="">{t(language, 'catalog.category')}</option>
            {categories.map((category) => (
              <option key={category.slug} value={category.slug}>{category.name}</option>
            ))}
          </select>
          <select value={filters.ordering} onChange={(event) => updateFilter('ordering', event.target.value)}>
            <option value="name">{t(language, 'catalog.sort')} - {t(language, 'catalog.name')}</option>
            <option value="price">{t(language, 'catalog.lowerPrice')}</option>
            <option value="-price">{t(language, 'catalog.higherPrice')}</option>
          </select>
          <select value={filters.requires_prescription} onChange={(event) => updateFilter('requires_prescription', event.target.value)}>
            <option value="">{t(language, 'catalog.prescription')}</option>
            <option value="false">Sem {t(language, 'catalog.prescription')}</option>
            <option value="true">Com {t(language, 'catalog.prescription')}</option>
          </select>
        </div>
      </section>

      <div className="catalog-grid">
        {items.map((product) => (
          <article className="product-card" key={product.id}>
            <Link to={`/product/${product.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              {product.image ? <img src={product.image} alt={product.name || product.title} style={{ cursor: 'pointer' }} /> : null}
              <div className="product-card-body" style={{ cursor: 'pointer' }}>
                <div className="product-meta">
                  <span>{product.category_name || product.category_slug}</span>
                  {product.requires_prescription ? <span className="badge badge-warn">{t(language, 'product.prescription')}</span> : <span className="badge">{t(language, 'product.free')}</span>}
                </div>
                <h3>{product.name || product.title || `Produto ${product.id}`}</h3>
                <p>{product.description}</p>
              </div>
            </Link>
            <div className="product-footer">
              <strong>{currency(product.price)}</strong>
              <div className="button-row">
                <button
                  className="primary-btn"
                  type="button"
                  onClick={() => handleAdd(product)}
                  disabled={addingId === product.id}
                >
                  {addingId === product.id ? t(language, 'catalog.addToCart') + '...' : t(language, 'catalog.addToCart')}
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
