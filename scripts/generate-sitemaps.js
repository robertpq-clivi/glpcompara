#!/usr/bin/env node
/**
 * GLPcompara — Sitemap Generator
 * Generates at repo root:
 *   sitemap-core.xml, sitemap-blog.xml, sitemap-index.xml, sitemap.xml (flat)
 *
 * Usage:
 *   node scripts/generate-sitemaps.js
 *   npm run generate:sitemaps
 *
 * To add pages: edit CORE_PAGES or BLOG_PAGES arrays below.
 */

const fs   = require('fs');
const path = require('path');

// ── CONFIG ───────────────────────────────────────────────────────────────────
const BASE_URL  = 'https://glpcompara.com.mx';
const TODAY     = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
const PUBLIC_DIR = path.join(__dirname, '..'); // Sitemaps at repo root → served at domain root

// ── CORE PAGES ────────────────────────────────────────────────────────────────
const CORE_PAGES = [
  { path: '/',                                   priority: '1.0', changefreq: 'weekly' },
  { path: '/pages/estudios-de-laboratorio.html', priority: '0.9', changefreq: 'weekly' },
  { path: '/farmacias', priority: '0.8', changefreq: 'monthly' },
  { path: '/blog/',                              priority: '0.7', changefreq: 'weekly' },
];

// ── BLOG PAGES (artículos GLP-1) ────────────────────────────────────────────────
// changefreq: monthly | priority: 0.8
const BLOG_PAGES = [
  'que-son-los-medicamentos-glp1',
  'cuanto-peso-se-puede-perder-con-glp1',
  'que-es-mounjaro-como-funciona',
  'mounjaro-precio-mexico',
  'que-es-wegovy-como-ayuda-bajar-de-peso',
  'wegovy-precio-mexico',
  'que-es-ozempic-para-que-sirve',
  'ozempic-sirve-para-bajar-de-peso',
  'ozempic-precio-mexico',
  'mounjaro-vs-wegovy',
  'mounjaro-vs-ozempic',
  'wegovy-vs-ozempic',
  'semaglutida-vs-tirzepatida',
  'glp1-vs-cirugia-bariatrica',
  'cuanto-cuesta-bajar-de-peso-con-glp1-mexico',
  'como-obtener-receta-glp1',
  'mejor-medicamento-para-controlar-el-apetito',
  'mejor-medicamento-para-bajar-de-peso-2026',
  'por-que-no-bajo-de-peso-con-ozempic',
  'historias-de-exito-antes-y-despues-glp1',
  'mitos-sobre-ozempic-y-wegovy',
  'los-glp1-son-para-toda-la-vida',
  // — 2º lote —
  'quien-es-candidato-glp1',
  'beneficios-y-riesgos-glp1',
  'que-pasa-al-dejar-glp1',
  'mounjaro-para-bajar-de-peso',
  'cuanto-peso-se-pierde-con-mounjaro',
  'efectos-secundarios-mounjaro',
  'que-comer-con-mounjaro',
  'cuanto-peso-se-pierde-con-wegovy',
  'efectos-secundarios-wegovy',
  'quien-puede-usar-wegovy',
  'ozempic-sin-diabetes',
  'efectos-secundarios-ozempic',
  'alimentos-evitar-con-ozempic',
  'cuanto-tarda-ozempic-en-hacer-efecto',
  'ozempic-vs-saxenda',
  'cambiar-de-ozempic-a-mounjaro',
  'plan-de-alimentacion-glp1',
  'proteina-y-glp1',
  'nausea-glp1-como-manejarla',
  'evitar-molestias-gastrointestinales-glp1',
  // — 3er lote —
  'como-funciona-glp1-para-controlar-el-apetito',
  'la-ciencia-detras-de-la-perdida-de-peso-con-glp1',
  'por-que-los-glp1-revolucionan-tratamiento-obesidad',
  'diferencias-obesidad-sobrepeso-resistencia-insulina',
  'por-que-algunas-personas-pierden-mas-peso',
  'resultados-reales-mounjaro-mes-a-mes',
  'mounjaro-y-resistencia-a-la-insulina',
  'wegovy-resultados-3-6-12-meses',
  'que-sucede-si-dejas-wegovy',
  'como-maximizar-resultados-wegovy',
  'dieta-recomendada-wegovy',
  'resultados-reales-ozempic',
  'por-que-ozempic-reduce-el-apetito',
  'glp1-vs-dieta-tradicional',
  'glp1-vs-medicamentos-orales',
  'que-tratamiento-para-bajar-de-peso-mejores-resultados',
  'como-evitar-perder-masa-muscular',
  'ejercicio-recomendado-glp1',
  'importancia-entrenamiento-de-fuerza',
  'alimentos-que-aumentan-la-saciedad',
  'como-controlar-la-ansiedad-por-la-comida',
  'como-acelerar-la-perdida-de-peso-saludable',
  'como-mantener-el-peso-perdido',
  'errores-comunes-al-bajar-de-peso',
  'estrenimiento-tratamiento-glp1',
  'es-normal-sentir-menos-hambre',
  'senales-de-que-tu-dosis-necesita-ajuste',
  'efectos-secundarios-que-requieren-atencion-medica',
  'por-que-deje-de-perder-peso-con-mounjaro',
  'como-romper-un-estancamiento-de-peso-glp1',
  // — Mounjaro (lote 1) —
  'mounjaro-resultados-semana-a-semana',
  'mounjaro-semana-1',
  'mounjaro-semana-2',
  'mounjaro-semana-4',
  'mounjaro-mes-2',
  'mounjaro-mes-3',
  'mounjaro-mes-6',
  'mounjaro-perdida-peso-primeros-30-dias',
  'mounjaro-antes-y-despues',
  'cuando-se-notan-cambios-con-mounjaro',
  'guia-dosis-mounjaro',
  'mejor-dosis-mounjaro-para-bajar-de-peso',
  'cada-cuanto-se-aplica-mounjaro',
  'calendario-escalamiento-dosis-mounjaro',
  'reducir-nauseas-mounjaro',
  'mounjaro-estrenimiento',
  'cuanta-proteina-con-mounjaro',
  'mejor-desayuno-mounjaro',
  // — Mounjaro (lote 2) —
  'por-que-algunos-bajan-mas-rapido-con-mounjaro',
  'perdida-de-peso-promedio-con-mounjaro',
  'como-evitar-estancarte-con-mounjaro',
  'cuanto-tiempo-usar-mounjaro',
  'que-pasa-si-dejas-mounjaro-tras-meta',
  'como-mantener-peso-tras-mounjaro',
  'que-sucede-al-aumentar-dosis-mounjaro',
  'olvidar-dosis-mounjaro',
  'como-aplicar-mounjaro-correctamente',
  'errores-comunes-al-usar-mounjaro',
  'mas-efectos-secundarios-al-subir-dosis-mounjaro',
  'cuanto-tarda-cada-dosis-mounjaro',
  'por-que-mounjaro-malestar-estomacal',
  'fatiga-al-iniciar-mounjaro',
  'cuando-consultar-medico-efectos-mounjaro',
  'alimentos-reducir-efectos-mounjaro',
  'mejores-ejercicios-con-mounjaro',
  'menu-semanal-mounjaro',
].map(slug => ({ path: `/blog/${slug}.html`, priority: '0.8', changefreq: 'monthly' }));

// ── LABORATORIO (contenido heredado, ahora en glpcompara.com.mx) ────────────────
// Páginas de aterrizaje de laboratorio
const LAB_PAGES = [
  '/pages/analisis-clinicos.html',
  '/pages/examenes-de-sangre.html',
  '/pages/laboratorio-clinico.html',
  '/pages/laboratorio-de-analisis-clinicos.html',
  '/pages/laboratorio-medico.html',
  '/pages/pruebas-de-laboratorio.html',
  '/pages/estudios-clinicos.html',
].map(p => ({ path: p, priority: '0.6', changefreq: 'monthly' }));

// Posts de blog de laboratorio: TODO blog/*.html que no sea index ni esté en BLOG_PAGES (GLP-1)
const glpSet = new Set(BLOG_PAGES.map(b => b.path));
const LAB_BLOG = fs.readdirSync(path.join(PUBLIC_DIR, 'blog'))
  .filter(f => f.endsWith('.html') && f !== 'index.html')
  .map(f => `/blog/${f}`)
  .filter(p => !glpSet.has(p))
  .sort()
  .map(p => ({ path: p, priority: '0.6', changefreq: 'monthly' }));

const LAB_ALL = [...LAB_PAGES, ...LAB_BLOG];

// ── HELPERS ───────────────────────────────────────────────────────────────────
function urlEntry({ path: p, priority, changefreq }) {
  return [
    '  <url>',
    `    <loc>${BASE_URL}${p}</loc>`,
    `    <lastmod>${TODAY}</lastmod>`,
    `    <changefreq>${changefreq}</changefreq>`,
    `    <priority>${priority}</priority>`,
    '  </url>',
  ].join('\n');
}

function buildSitemap(pages) {
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...pages.map(urlEntry),
    '</urlset>',
  ].join('\n');
}

function buildSitemapIndex() {
  const sitemaps = ['sitemap-core.xml', 'sitemap-blog.xml', 'sitemap-lab.xml'];
  const entries  = sitemaps.map(name => [
    '  <sitemap>',
    `    <loc>${BASE_URL}/${name}</loc>`,
    `    <lastmod>${TODAY}</lastmod>`,
    '  </sitemap>',
  ].join('\n'));

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...entries,
    '</sitemapindex>',
  ].join('\n');
}

function write(filename, content) {
  const filepath = path.join(PUBLIC_DIR, filename);
  fs.writeFileSync(filepath, content, 'utf8');
  const lines = content.split('\n').length;
  console.log(`  ✓ ${filename} (${lines} lines)`);
}

// ── GENERATE ──────────────────────────────────────────────────────────────────
console.log('\n🗺️  GLPcompara Sitemap Generator');
console.log(`   BASE_URL : ${BASE_URL}`);
console.log(`   lastmod  : ${TODAY}`);
console.log(`   Output   : repo root/\n`);

if (!fs.existsSync(PUBLIC_DIR)) fs.mkdirSync(PUBLIC_DIR, { recursive: true });

write('sitemap-core.xml',  buildSitemap(CORE_PAGES));
write('sitemap-blog.xml',  buildSitemap(BLOG_PAGES));
write('sitemap-lab.xml',   buildSitemap(LAB_ALL));
write('sitemap-index.xml', buildSitemapIndex());
// Flat sitemap (for crawlers that fetch /sitemap.xml directly)
write('sitemap.xml',       buildSitemap([...CORE_PAGES, ...BLOG_PAGES, ...LAB_ALL]));

// Remove the legacy lab sitemap if present
const legacy = path.join(PUBLIC_DIR, 'sitemap-estudios.xml');
if (fs.existsSync(legacy)) { fs.unlinkSync(legacy); console.log('  ✗ removed legacy sitemap-estudios.xml'); }

console.log(`\n✅ Done — ${CORE_PAGES.length} core, ${BLOG_PAGES.length} GLP-1 blog, ${LAB_ALL.length} lab URLs\n`);
