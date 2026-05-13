export const categories = [
  { id: 1, name: 'Analgésicos', slug: 'analgesicos', description: 'Alívio de dor e febre' },
  { id: 2, name: 'Vitaminas', slug: 'vitaminas', description: 'Suplementação diária' },
  { id: 3, name: 'Cuidados pessoais', slug: 'cuidados-pessoais', description: 'Bem-estar e higiene' },
  { id: 4, name: 'Prescrição', slug: 'prescricao', description: 'Itens com exigência de receita' }
]

export const products = [
  {
    id: 'dipirona-500mg',
    slug: 'dipirona-500mg',
    name: 'Dipirona 500mg',
    title: 'Dipirona 500mg',
    description: 'Analgésico e antitérmico para alívio de dores leves e febre.',
    price: 9.9,
    category_slug: 'analgesicos',
    category_name: 'Analgésicos',
    requires_prescription: false,
    stock: 25,
    image: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'ibuprofeno-400mg',
    slug: 'ibuprofeno-400mg',
    name: 'Ibuprofeno 400mg',
    title: 'Ibuprofeno 400mg',
    description: 'Anti-inflamatório com uso comum em quadros de dor e inflamação.',
    price: 14.5,
    category_slug: 'analgesicos',
    category_name: 'Analgésicos',
    requires_prescription: false,
    stock: 18,
    image: 'https://images.unsplash.com/photo-1512069772995-ec65ed45afd6?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'vitamina-c-1g',
    slug: 'vitamina-c-1g',
    name: 'Vitamina C 1g',
    title: 'Vitamina C 1g',
    description: 'Suplemento para rotina de imunidade e saúde geral.',
    price: 29.9,
    category_slug: 'vitaminas',
    category_name: 'Vitaminas',
    requires_prescription: false,
    stock: 32,
    image: 'https://images.unsplash.com/photo-1550572017-edd951aa8ca0?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'multivitaminico-a-z',
    slug: 'multivitaminico-a-z',
    name: 'Multivitamínico A-Z',
    title: 'Multivitamínico A-Z',
    description: 'Formulação completa para complementar a alimentação diária.',
    price: 39.9,
    category_slug: 'vitaminas',
    category_name: 'Vitaminas',
    requires_prescription: false,
    stock: 14,
    image: 'https://images.unsplash.com/photo-1556228724-4d6f3d1b65d3?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'shampoo-anticaspa',
    slug: 'shampoo-anticaspa',
    name: 'Shampoo Anticaspa',
    title: 'Shampoo Anticaspa',
    description: 'Tratamento para couro cabeludo com ação anticaspa.',
    price: 24.9,
    category_slug: 'cuidados-pessoais',
    category_name: 'Cuidados pessoais',
    requires_prescription: false,
    stock: 16,
    image: 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'antibiotico-exemplo',
    slug: 'antibiotico-exemplo',
    name: 'Antibiótico Exemplo',
    title: 'Antibiótico Exemplo',
    description: 'Produto de demonstração com exigência de prescrição médica.',
    price: 49.9,
    category_slug: 'prescricao',
    category_name: 'Prescrição',
    requires_prescription: true,
    stock: 8,
    image: 'https://images.unsplash.com/photo-1587854692152-cbe660dbde88?auto=format&fit=crop&w=800&q=80'
  }
]

function normalizeText(value){
  return String(value || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

export function findProduct(idOrSlug){
  return products.find((product) => String(product.id) === String(idOrSlug) || product.slug === idOrSlug) || null
}

export function filterProducts({ search = '', categorySlug = '', ordering = '', requiresPrescription = '' } = {}){
  let result = [...products]
  const normalizedSearch = normalizeText(search)

  if (normalizedSearch) {
    result = result.filter((product) => {
      return [product.name, product.title, product.description, product.category_name]
        .join(' ')
        .toLowerCase()
        .includes(normalizedSearch)
    })
  }

  if (categorySlug) {
    result = result.filter((product) => product.category_slug === categorySlug)
  }

  if (requiresPrescription === 'true') {
    result = result.filter((product) => product.requires_prescription)
  }

  if (requiresPrescription === 'false') {
    result = result.filter((product) => !product.requires_prescription)
  }

  if (ordering === 'price') {
    result.sort((a, b) => a.price - b.price)
  }

  if (ordering === '-price') {
    result.sort((a, b) => b.price - a.price)
  }

  if (ordering === 'name') {
    result.sort((a, b) => a.name.localeCompare(b.name))
  }

  return result
}