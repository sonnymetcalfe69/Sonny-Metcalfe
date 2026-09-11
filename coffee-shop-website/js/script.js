// Mobile nav toggle
const navToggle = document.getElementById('nav-toggle');
const mainNav = document.getElementById('main-nav');

if (navToggle && mainNav) {
  navToggle.addEventListener('click', () => {
    const isOpen = mainNav.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });

  mainNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mainNav.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// Sticky header shadow on scroll
const header = document.getElementById('site-header');
if (header) {
  const onScroll = () => {
    header.style.boxShadow = window.scrollY > 8 ? '0 6px 20px rgba(44,24,16,0.08)' : 'none';
  };
  document.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

// Newsletter form (static demo — no backend wired up)
const newsletterForm = document.getElementById('newsletter-form');
const newsletterStatus = document.getElementById('newsletter-status');

if (newsletterForm && newsletterStatus) {
  newsletterForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const emailInput = document.getElementById('newsletter-email');
    const email = emailInput.value.trim();
    if (!email) return;
    newsletterStatus.textContent = `Thanks — we'll pop ${email} on the list!`;
    newsletterForm.reset();
  });
}

// Footer year
const yearEl = document.getElementById('year');
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}
