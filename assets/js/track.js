/* Lead-action tracking for DFC Home Improvement.
 *
 * One delegated click listener counts the actions that turn a visitor into a
 * lead, on every page that loads this file:
 *   tel:            -> phone_call_click
 *   sms:            -> text_click
 *   mailto:         -> email_click
 *   Jobber request  -> consultation_click
 *   contact page    -> contact_page_click
 * Forms that post their own leads (estimate.html) call dfcTrack('generate_lead')
 * after a successful submit.
 *
 * GA4 gets the event name plus where on the page the click happened. Meta gets a
 * custom event (trackCustom), never a standard Lead/Contact, so ad campaigns that
 * optimise on standard events are not affected by plain clicks.
 */
(function () {
  function where(el) {
    var s = el.closest('.site-header, .mobile-menu, .hero, .cta-band, .form-card, .contact-info, .site-footer, main, section');
    if (!s) return 'page';
    if (s.classList.contains('site-header')) return 'header';
    if (s.classList.contains('mobile-menu')) return 'mobile_menu';
    if (s.classList.contains('hero')) return 'hero';
    if (s.classList.contains('cta-band')) return 'cta_band';
    if (s.classList.contains('form-card')) return 'contact_form';
    if (s.classList.contains('contact-info')) return 'contact_info';
    if (s.classList.contains('site-footer')) return 'footer';
    return 'body';
  }

  function send(name, params, fbName) {
    params = params || {};
    try { if (typeof window.gtag === 'function') window.gtag('event', name, params); } catch (e) {}
    try { if (fbName && typeof window.fbq === 'function') window.fbq('trackCustom', fbName, params); } catch (e) {}
  }
  window.dfcTrack = send;

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var p = {
      link_location: where(a),
      link_text: (a.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60)
    };
    if (/^tel:/i.test(href)) send('phone_call_click', p, 'PhoneCallClick');
    else if (/^sms:/i.test(href)) send('text_click', p, 'TextClick');
    else if (/^mailto:/i.test(href)) send('email_click', p, 'EmailClick');
    else if (/getjobber\.com/i.test(href)) send('consultation_click', p, 'ConsultationClick');
    else if (/(^|\/)contact(\.html)?\/?([?#]|$)/i.test(href)) send('contact_page_click', p);
  }, true);
})();
