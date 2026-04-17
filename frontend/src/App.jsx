import './App.css'
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Pagination, Autoplay } from 'swiper/modules';
import logoImg from './assets/Logo_ConnectHub_Branca.svg'
import { useState, useEffect, useRef } from 'react';
import { Search, ShoppingCart, MapPin, ChevronDown } from 'lucide-react'
import 'swiper/css'
import 'swiper/css/navigation'
import 'swiper/css/pagination'

function App() {
  const [isLangOpen, setIsLangOpen] = useState(false);
  const langRef = useRef(null);

  useEffect(() => {
    function handleClickFora(event) {
      if (langRef.current && !langRef.current.contains(event.target)) {
        setIsLangOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickFora);
    return () => {
      document.removeEventListener("mousedown", handleClickFora);
    };
  }, [langRef])

  const banners = [
    { id: 1, title: 'Promoção de Outono', color: '#ffffff'},
    { id: 1, title: 'Novidades de Bem-Estas', color: '#ffffff'},
    { id: 1, title: 'Entrega Rápida', color: '#ffffff'}
  ];

  const displayBanners = [...banners, ...banners, ...banners]

  const produtosDestaque = [
    {
      id: 1,
      nome:"Vitamina C",
      preco:"49,90",
      categoria: "Suplementos",
      imagem: "https://img.freepik.com/fotos-gratis/embalagens-de-comprimidos-e-capsulas-de-medicamentos_1339-2255.jpg?semt=ais_hybrid&w=740&q=80"
    },
    {
      id: 2,
      nome:"Ômega 3",
      preco:"79,90",
      categoria: "Saúde",
      imagem: "https://img.freepik.com/fotos-gratis/embalagens-de-comprimidos-e-capsulas-de-medicamentos_1339-2255.jpg?semt=ais_hybrid&w=740&q=80"
    },
    {
      id: 3,
      nome:"Whey Protein",
      preco:"129,90",
      categoria: "Esporte",
      imagem: "https://img.freepik.com/fotos-gratis/embalagens-de-comprimidos-e-capsulas-de-medicamentos_1339-2255.jpg?semt=ais_hybrid&w=740&q=80"
    },
    {
      id: 4,
      nome:"Magnésio Quelato",
      preco:"35,00",
      categoria: "Minerais",
      imagem: "https://img.freepik.com/fotos-gratis/embalagens-de-comprimidos-e-capsulas-de-medicamentos_1339-2255.jpg?semt=ais_hybrid&w=740&q=80"
    }
  ];

  const categorias = ["Todos", "Minerais", "Suplementos", "Esporte", "Saúde"]

  const [categoriaAtiva, setCategoriaAtiva] = useState("Todos");

  const produtosFiltrados = categoriaAtiva === "Todos"
    ? produtosDestaque
    : produtosDestaque.filter(produto => produto.categoria === categoriaAtiva);
  
  const [isFilterOpen, setIsFilterOpen] = useState(false)

  const [isVisible, setisVisible] = useState(true)
  const [lastScrollY, setlastScrollY] = useState(0)

  useEffect (() => {
    const controlSubheader = () => {
    if (window.scrollY > lastScrollY && window.scrollY > 100) {
      setisVisible(false);  
    } else {
      setisVisible(true);
    }
    setlastScrollY(window.scrollY);
  };
  
  window.addEventListener('scroll', controlSubheader);
  return () => window.removeEventListener('scroll', controlSubheader);
}, [lastScrollY]);

  return (
    <div className='app-container'>
      <header className='main-header'>
        <div className='logo-area'>
          <img src={logoImg} alt='iHealth Brasil' className='logo-img'/>
            <div className='logo-text'>
              <strong>ConnectHub</strong>
              <span>Onde tecnologia e natureza se encontram</span>
            </div>
        </div>
        <div className='search-bar'>
          <Search className='search-icon' size={20}/>
          <input type="text" placeholder='Pesquisar'/>
        </div>
        <div className='user-menu'>
          <button className='login-btn'>Entrar</button>
          <button className='cart-btn'>
            <ShoppingCart size={20}/>
            Seu carrinho
          </button>
        </div>
      </header>

      <div className={`subheader ${isVisible ? '' : 'hidden'}`}>
        <div className='subheader-left'>
          <button className='open-filters-btn' onClick={() => setIsFilterOpen(true)}>
            <span>☰</span> Filtros
          </button>
            {isFilterOpen && <div className='filter-overlay' onClick={() => setIsFilterOpen(false)}></div>}

            <aside className={`filter-sidebar ${isFilterOpen ? 'open' : ''}`}>
              <div className='sidebar-header'>
                <h3>Filtros</h3>
                <button className='close-btn' onClick={() => setIsFilterOpen(false)}>✕</button>
              </div>

              <div className='filter-groups'>
                <h4>Categorias</h4>
                  {categorias.map((cat) => (
                    <button
                    key={cat}
                    className={`filter-link ${categoriaAtiva === cat ? 'active' : ''}`}
                    onClick={() => {
                      setCategoriaAtiva(cat);
                      setIsFilterOpen(false);
                      }}
                    >
                      {cat}
                    </button>
                  ))}
              </div>
            </aside>

          <div className='delivery-info'>
            <span>
              Entregar em:
            </span>
                <strong>
                  São Paulo, SP
                  <MapPin size={20}/>
                  <ChevronDown size={20}/>
                </strong>
          </div>
        </div>

        <nav className='category-menu'>
          <a href="#">Medicamentos</a>
          <a href="#">Bem-Estar</a>
          <a href="#">Naturais</a>
          <a href="#">Promoções</a>
        </nav>

        <div className='subheader-right'>            
          <div className='language-selector' ref={langRef} onClick={() => setIsLangOpen(!isLangOpen)}>
            <div className='selected-lang'>
              <span className='Flag'>🇧🇷</span>
              <span>PT</span>
              <ChevronDown size={14} className={isLangOpen ? 'rotate' : ''}/>
            </div>
        

          {isLangOpen && (
            <ul className='lang-dropdown'>
              <li onClick={() => setIsLangOpen(false)}><span className='flag'>🇧🇷</span>Potuguês</li>
              <li onClick={() => setIsLangOpen(false)}><span className='flag'>🇺🇸</span>Inglês</li>
              <li onClick={() => setIsLangOpen(false)}><span className='flag'>🇪🇸</span>Espanhol</li>
              <li onClick={() => setIsLangOpen(false)}><span className='flag'>🇫🇷</span>Françês</li>
            </ul>
            )}
          </div>
        </div>
      </div>        
      <section className='main-banner'>
        <Swiper
          modules={[Navigation, Pagination, Autoplay]}
          slidesPerView={1.2}
          centeredSlides={true}
          spaceBetween={20}
          loop={true}
          loopedSlides={3}
          loopAdditionalSlides={3}
          speed={600}
          pagination={{ clickable: true,
            renderBullet: function (index, className){
              if (index > 3) return "";
              return `<span class"${className}"></span>`;
            },
           }}
          navigation={true}
          className="mySwiper"
> 
          {displayBanners.map((banner, index) => (
            <SwiperSlide key={index}>
              <div className='banner-item' style={{ backgroundColor: banner.color }}>
                <h2>{banner.title}</h2>
              </div>
            </SwiperSlide>
          ))}
        </Swiper>
      </section>
        
      <section className='products-section'>
        <div className='products-container'>
          <div className='section-header'>
            <h2>Produtos em Destaque</h2>
            <a href="#" className='view-all'>Ver todos</a>
          </div>

          <div className='products-grid'>
            {produtosFiltrados.map((produto) => (
              <div key={produto.id} className='product-card'>
                <div className='product-image'>
                  <img src={produto.imagem} alt={produto.nome} />
                </div>
                <div className='product-info'>
                  <span className='product-category'>{produto.categoria}</span>
                  <h3>{produto.nome}</h3>
                  <p className='product-price'>R$ {produto.preco}</p>
                  <button className='buy-button'>Comprar agora</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

    </div>
  )
}

export default App