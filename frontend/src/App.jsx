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
    { id: 1, title: 'Promoção de Outono', color: '#e0f2f1'},
    { id: 1, title: 'Novidades de Bem-Estas', color: '#e0f2f1'},
    { id: 1, title: 'Entrega Rápida', color: '#e0f2f1'}
  ];

  const displayBanners = [...banners, ...banners, ...banners]
  
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

      <div className='location-bar'>
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

        <nav className='category-menu'>
          <a href="#">Medicamentos</a>
          <a href="#">Bem-Estar</a>
          <a href="#">Naturais</a>
          <a href="#">Promoções</a>
        </nav>

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
        
        <div className='content-wrapper'>
          <h3>O que você procura?</h3>
        </div>
    </div>
  )
}

export default App