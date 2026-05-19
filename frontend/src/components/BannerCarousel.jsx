import { Swiper, SwiperSlide } from 'swiper/react'
import { Navigation, Pagination, Autoplay } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/navigation'
import 'swiper/css/pagination'

function BannerCarousel({ banners }) {
  return (
    <section className='main-banner'>
      <Swiper
        modules={[Navigation, Pagination, Autoplay]}
        slidesPerView={1.2}
        centeredSlides={true}
        spaceBetween={20}
        loop={true}
        speed={600}
        pagination={{
          clickable: true,
          renderBullet: function (index, className) {
            if (index > 3) return ''
            return `<span class="${className}"></span>`
          },
        }}
        navigation={true}
        className='mySwiper'
      >
        {banners.map((banner, index) => (
          <SwiperSlide key={`${banner.id}-${index}`}>
            <div className='banner-item' style={{ backgroundColor: banner.color }}>
              <h2>{banner.title}</h2>
            </div>
          </SwiperSlide>
        ))}
      </Swiper>
    </section>
  )
}

export default BannerCarousel