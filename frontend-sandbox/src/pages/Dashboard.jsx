import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { products } from '../mockData'
import { addToCart } from '../cart'
import { showToast } from '../toast'
import { t } from '../i18n'
import { useLanguage } from '../LanguageContext'

export default function Dashboard(){
  const { language } = useLanguage()
  const featured = products.slice(0, 4)
  const highlights = t(language, 'dashboard.features')
  const [addingId, setAddingId] = useState(null)

  async function handleAdd(product){
    setAddingId(product.id)
    try {
      await addToCart(product, 1)
      showToast(t(language, 'toasts.addedToCart'), 'success')
    } catch (err) {
      showToast(err.message || t(language, 'toasts.addToCartFailed'), 'error')
    } finally {
      setAddingId(null)
    }
  }

  return (
    <div>
      <section className="main-banner">
        <div className="banner-item banner-item-primary">
          <div className="banner-copy">
            <span className="banner-tag">{t(language, 'dashboard.bannerTag')}</span>
            <h1>{t(language, 'dashboard.bannerTitle')}</h1>
            <p>
              {t(language, 'dashboard.bannerDescription')}
            </p>
            <div className="hero-actions">
              <Link className="buy-button" to="/catalog">{t(language, 'dashboard.openCatalog')}</Link>
              <Link className="secondary-button" to="/login">{t(language, 'header.login')}</Link>
            </div>
          </div>
          <div className="banner-visual">
            <div className="banner-orb banner-orb-one" />
            <div className="banner-orb banner-orb-two" />
            <div className="banner-card-stack">
              <div className="floating-card floating-card-top">{t(language, 'dashboard.fastDelivery')}</div>
              <div className="floating-card floating-card-bottom">Novidades de bem-estar</div>
            </div>
          </div>
        </div>
      </section>

      <section className="products-section">
        <div className="products-container">
          <div className="section-header">
            <h2>{t(language, 'dashboard.featured')}</h2>
            <Link to="/catalog" className="view-all">Ver todos</Link>
          </div>
          <div className="products-grid">
            {featured.map((produto) => (
              <article key={produto.id} className="product-card">
                <Link to={`/product/${produto.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <div className="product-image" style={{ cursor: 'pointer' }}><img src={produto.image} alt={produto.name} /></div>
                  <div className="product-info" style={{ cursor: 'pointer' }}>
                    <span className="product-category">{produto.category_name}</span>
                    <h3>{produto.name}</h3>
                    <p className="product-price">R$ {String(produto.price).replace('.', ',')}</p>
                  </div>
                </Link>
                <button
                  className="buy-button"
                  type="button"
                  onClick={() => handleAdd(produto)}
                  disabled={addingId === produto.id}
                  style={{ width: '100%', marginTop: '8px' }}
                >
                  {addingId === produto.id ? t(language, 'catalog.addToCart') + '...' : t(language, 'catalog.addToCart')}
                </button>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="products-section">
        <div className="products-container">
          <div className="section-header">
            <h2>{t(language, 'dashboard.howItWorks')}</h2>
            <Link to="/catalog" className="view-all">{t(language, 'catalog.search')}</Link>
          </div>
          <div className="products-grid feature-grid">
            {highlights.map((item) => (
              <article className="feature-card" key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
