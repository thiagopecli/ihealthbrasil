import { useLanguage } from '../LanguageContext'

function ProductGrid({ produtos }) {
  const { t } = useLanguage()

  const categoryKeyMap = {
    'Todos': 'todos',
    'Minerais': 'minerais',
    'Suplementos': 'suplementos',
    'Esporte': 'esporte',
    'Saúde': 'saude',
  }

  return (
    <section className='products-section'>
      <div className='products-container'>
        <div className='section-header'>
          <h2>{t('produtosDestaque')}</h2>
          <a href='#' className='view-all'>
            {t('verTodos')}
          </a>
        </div>

        <div className='products-grid'>
          {produtos.map((produto) => (
            <div key={produto.id} className='product-card'>
              <div className='product-image'>
                <img src={produto.imagem} alt={produto.nome} />
              </div>
              <div className='product-info'>
                <span className='product-category'>
                  {t(categoryKeyMap[produto.categoria] || produto.categoria)}
                </span>
                <h3>{produto.nome}</h3>
                <p className='product-price'>R$ {produto.preco}</p>
                <button className='buy-button'>{t('comprarAgora')}</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default ProductGrid