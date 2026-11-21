// AI for Research: small progressive enhancements. The site works without this file.
(() => {
  // Sticky header shadow
  const header = document.querySelector('[data-header]');
  const onScroll = () => header && header.classList.toggle('is-scrolled', window.scrollY > 8);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Mobile navigation
  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('[data-nav]');
  if (toggle && nav) {
    const setOpen = (open) => {
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
    };
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
    nav.addEventListener('click', (e) => { if (e.target.closest('a')) setOpen(false); });
  }

  // Scroll reveal
  const items = document.querySelectorAll('.reveal, .reveal-stagger');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach((el) => io.observe(el));
  } else {
    items.forEach((el) => el.classList.add('is-visible'));
  }

  // Contact form: preselect topic from ?topic= and set a useful email subject
  const form = document.querySelector('[data-contact-form]');
  if (form) {
    const params = new URLSearchParams(window.location.search);
    const topic = form.querySelector('[data-topic]');
    const subject = form.querySelector('[data-subject]');
    const wanted = params.get('topic');
    if (topic && wanted && [...topic.options].some((o) => o.value === wanted)) topic.value = wanted;
    const service = params.get('service');
    const message = form.querySelector('#message');
    if (service && message && !message.value) {
      message.value = `I'm interested in: ${service.replace(/-/g, ' ')}.\n\n`;
    }
    form.addEventListener('submit', () => {
      if (topic && subject) subject.value = `[aiforresearch.eu] ${topic.options[topic.selectedIndex].text}`;
    });
  }
})();
