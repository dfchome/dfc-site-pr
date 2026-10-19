/* ------------------------------------------------------------------
   AI Kitchen Inspiration (ai-kitchen-inspiration.html)

   Ported from the Fox Remodeling / McManus tool. Same wizard, same prompt,
   same before/after slider. On DFC:
   - the image model is reached through /api/ai-preview (dfc-api on Railway,
     the key never reaches the browser);
   - the lead goes out through FormSubmit, the same path as the price
     estimator, so it lands in the same inbox (hugo@, cc admin@);
   - the design is parked on the server only when the visitor sends it, so
     the email can link to it.
   ------------------------------------------------------------------ */
(function () {
  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  if (!$('#aipDrop')) return;

  const LEAD_ENDPOINT = 'https://formsubmit.co/ajax/hugo@dfchomeimprovement.com';
  const LEAD_CC = 'admin@dfchomeimprovement.com';
  const PHONE = '(703) 596-8375';

  const OPTIONS = {
    "Design style":   ["Transitional", "Modern Farmhouse", "Classic Traditional", "Contemporary", "Warm Minimal", "Coastal"],
    "Cabinets":       ["Shaker", "Flat Panel", "Raised Panel", "Glass Front", "Open Shelving", "Two Tone"],
    "Countertops":    ["Quartz", "Quartzite", "Granite", "Marble", "Butcher Block", "Solid Surface"],
    "Backsplash":     ["Subway Tile", "Full Slab", "Herringbone Tile", "Zellige Tile", "Mosaic Accent", "Natural Stone"],
    "Color palette":  ["Warm Neutrals", "Crisp White", "Cool Grays", "Deep and Moody", "Earthy and Natural", "Two Tone Contrast"],
    "Budget range":   ["Under $50k", "$50k to $75k", "$75k to $100k", "$100k to $150k", "$150k+", "Not sure yet"]
  };
  const ORDER = ["Design style", "Cabinets", "Countertops", "Backsplash", "Color palette", "Budget range"];
  // Budget stays a list even in Advanced: a free-text budget is not useful to anyone.
  const FREE_TEXT = ["Design style", "Cabinets", "Countertops", "Backsplash", "Color palette"];
  const HINT = {
    "Design style":  "e.g. warm transitional with brass accents",
    "Cabinets":      "e.g. inset shaker, painted sage",
    "Countertops":   "e.g. honed white quartzite, thick edge",
    "Backsplash":    "e.g. zellige tile up to the ceiling",
    "Color palette": "e.g. creamy whites with black accents"
  };

  const track = (name, params, fb) => { if (typeof window.dfcTrack === 'function') window.dfcTrack(name, params || {}, fb); };
  const answers = {};
  let advanced = false, b64 = null, mime = null, objURL = null, savedURL = '', lastImage = null;

  /* ---- steps ---- */
  function goStep(n) {
    $$('.aip-panel').forEach(p => p.classList.toggle('show', +p.dataset.panel === n));
    $$('.aip-step').forEach(s => {
      const i = +s.dataset.step;
      s.classList.toggle('active', i === n);
      s.classList.toggle('done', i < n);
    });
    $$('.aip-line').forEach(l => l.classList.toggle('fill', +l.dataset.line < n));
    const top = $('.aip-card').getBoundingClientRect().top + window.scrollY - 110;
    window.scrollTo({ top, behavior: 'smooth' });
  }

  /* ---- 1. the photo: downscaled in the browser before it is sent ---- */
  const drop = $('#aipDrop'), file = $('#aipFile');
  drop.addEventListener('click', () => file.click());
  drop.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); file.click(); } });
  $('#aipChange').addEventListener('click', e => { e.stopPropagation(); file.click(); });
  ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('drag'); }));
  ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('drag'); }));
  drop.addEventListener('drop', e => { if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); });
  file.addEventListener('change', e => { if (e.target.files[0]) handleFile(e.target.files[0]); });

  function handleFile(f) {
    if (!f.type.startsWith('image/')) return;
    objURL = URL.createObjectURL(f);
    $('#aipPreviewImg').src = objURL;
    $('#aipPreview').classList.add('show');
    drop.style.display = 'none';
    $('#aipToStyle').disabled = true;
    const img = new Image();
    img.onload = () => {
      const max = 1280, scale = Math.min(1, max / Math.max(img.width, img.height));
      const c = document.createElement('canvas');
      c.width = Math.round(img.width * scale);
      c.height = Math.round(img.height * scale);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      b64 = c.toDataURL('image/jpeg', 0.88).split(',')[1];
      mime = 'image/jpeg';
      $('#aipToStyle').disabled = false;
    };
    // A format the canvas cannot decode (some HEICs) still has to work.
    img.onerror = () => {
      const r = new FileReader();
      r.onload = () => { b64 = r.result.split(',')[1]; mime = f.type; $('#aipToStyle').disabled = false; };
      r.readAsDataURL(f);
    };
    img.src = objURL;
    track('ai_photo_added', { tool: 'ai kitchen inspiration' });
  }
  $('#aipToStyle').addEventListener('click', () => goStep(2));
  $('#aipBack').addEventListener('click', () => goStep(1));

  /* ---- 2. the finishes ---- */
  const grid = $('#aipGrid');
  function renderFields() {
    grid.innerHTML = '';
    ORDER.forEach(key => {
      const asText = advanced && FREE_TEXT.includes(key);
      const field = document.createElement('div');
      field.className = 'aip-field' + (answers[key] ? ' answered' : '');
      const label = document.createElement('label');
      label.textContent = key;
      field.appendChild(label);

      if (asText) {
        const inp = document.createElement('input');
        inp.type = 'text'; inp.className = 'aip-txt';
        inp.placeholder = HINT[key] || ''; inp.value = answers[key] || '';
        inp.setAttribute('aria-label', key);
        inp.addEventListener('input', () => {
          const v = inp.value.trim();
          if (v) { answers[key] = v; field.classList.add('answered'); }
          else { delete answers[key]; field.classList.remove('answered'); }
          updateProgress();
        });
        field.appendChild(inp);
      } else {
        const btn = document.createElement('button');
        btn.type = 'button'; btn.className = 'aip-dd';
        btn.setAttribute('aria-haspopup', 'listbox');
        const val = document.createElement('span');
        val.textContent = answers[key] || 'Select';
        btn.append(val, Object.assign(document.createElement('i'), { className: 'aip-caret' }));
        const list = document.createElement('div');
        list.className = 'aip-list';
        OPTIONS[key].forEach(opt => {
          const o = document.createElement('button');
          o.type = 'button';
          o.className = 'aip-opt' + (answers[key] === opt ? ' sel' : '');
          o.innerHTML = '<span></span><svg class="ck" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
          o.querySelector('span').textContent = opt;
          o.addEventListener('click', () => {
            answers[key] = opt;
            val.textContent = opt;
            field.classList.add('answered');
            list.querySelectorAll('.aip-opt').forEach(x => x.classList.remove('sel'));
            o.classList.add('sel');
            field.classList.remove('open');
            updateProgress();
          });
          list.appendChild(o);
        });
        btn.addEventListener('click', e => {
          e.stopPropagation();
          const wasOpen = field.classList.contains('open');
          $$('.aip-field').forEach(f => f.classList.remove('open'));
          if (!wasOpen) field.classList.add('open');
        });
        field.append(btn, list);
      }
      grid.appendChild(field);
    });
  }
  document.addEventListener('click', () => $$('.aip-field').forEach(f => f.classList.remove('open')));
  document.addEventListener('keydown', e => { if (e.key === 'Escape') $$('.aip-field').forEach(f => f.classList.remove('open')); });

  $('#aipAdv').addEventListener('change', e => {
    advanced = e.target.checked;
    $('#aipNotesWrap').hidden = !advanced;
    renderFields();
    updateProgress();
  });

  function updateProgress() {
    const n = ORDER.filter(k => answers[k] && String(answers[k]).trim()).length;
    $('#aipCount').textContent = n + ' of 6 chosen';
    $('#aipPct').textContent = Math.round(n / 6 * 100) + '%';
    $('#aipFill').style.width = (n / 6 * 100) + '%';
    const g = $('#aipGo');
    g.disabled = n < 6;
    g.textContent = n < 6 ? 'Choose ' + (6 - n) + ' more' : 'Show me my kitchen';
  }

  function buildPrompt() {
    let p = 'You are an expert kitchen designer. Photorealistically remodel the kitchen shown in this'
          + ' photo in a ' + answers['Design style'] + ' style.'
          + ' Cabinetry: ' + answers['Cabinets'] + '.'
          + ' Countertops: ' + answers['Countertops'] + '.'
          + ' Backsplash: ' + answers['Backsplash'] + '.'
          + ' Overall color palette: ' + answers['Color palette'] + '.'
          + ' Budget level: ' + answers['Budget range'] + '.';
    const notes = $('#aipNotes') ? $('#aipNotes').value.trim() : '';
    if (advanced && notes) p += ' Additional notes from the homeowner to honor: ' + notes + '.';
    p += ' Keep the EXACT same room layout, camera angle, perspective, proportions and window and door'
       + ' positions. Only change finishes, materials, cabinetry, fixtures and styling.'
       + ' Produce one clean, realistic, high-end result with natural lighting.'
       + ' Do not add any text, labels, people or watermarks.';
    return p;
  }

  /* ---- 3. generate ---- */
  $('#aipGo').addEventListener('click', generate);
  async function generate() {
    goStep(3);
    $('#aipLoading').style.display = 'block';
    $('#aipResult').style.display = 'none';
    $('#aipErr').classList.remove('show');
    try {
      const res = await fetch('/api/ai-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: buildPrompt(), image: b64, mimeType: mime || 'image/jpeg' })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((data.error && (data.error.message || data.error)) || 'the design service is busy.');
      const part = ((data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts) || []).find(p => p.inlineData);
      if (!part) throw new Error('no image came back.');
      showResult(part.inlineData.data, part.inlineData.mimeType || 'image/png');
      track('ai_design_generated', { tool: 'ai kitchen inspiration', style: answers['Design style'], budget: answers['Budget range'] }, 'AIDesignGenerated');
    } catch (err) {
      $('#aipErr').textContent = 'Sorry, ' + String(err.message || err).replace(/\.?$/, '.') + ' Please go back and try once more, or call us at ' + PHONE + '.';
      $('#aipErr').classList.add('show');
    }
  }

  function showResult(data, type) {
    const url = 'data:' + type + ';base64,' + data;
    $('#aipLoading').style.display = 'none';
    $('#aipResult').style.display = 'block';
    $('#aipAfter').src = url;
    $('#aipBefore').src = objURL;
    $('#aipOpen').href = url;
    requestAnimationFrame(initSlider);
    // Held in memory only; parked on the server only if the visitor sends it.
    lastImage = data;
    savedURL = '';
  }

  let sliderReady = false;
  function initSlider() {
    const ba = $('#aipBa'), before = ba.querySelector('.aip-before'), div = $('#aipDiv'), beforeImg = $('#aipBefore');
    const size = () => { beforeImg.style.width = ba.clientWidth + 'px'; };
    const setPct = p => { p = Math.max(0, Math.min(100, p)); before.style.width = p + '%'; div.style.left = p + '%'; };
    size();
    setPct(50);
    if (sliderReady) return;
    sliderReady = true;
    window.addEventListener('resize', size);
    let dragging = false;
    const move = x => { const r = ba.getBoundingClientRect(); setPct((x - r.left) / r.width * 100); };
    ba.addEventListener('pointerdown', e => { dragging = true; ba.setPointerCapture(e.pointerId); move(e.clientX); });
    ba.addEventListener('pointermove', e => { if (dragging) move(e.clientX); });
    ba.addEventListener('pointerup', () => { dragging = false; });
    ba.addEventListener('pointercancel', () => { dragging = false; });
  }

  $('#aipRestart').addEventListener('click', () => {
    b64 = null; objURL = null; savedURL = ''; lastImage = null;
    drop.style.display = 'block';
    $('#aipPreview').classList.remove('show');
    $('#aipToStyle').disabled = true;
    $('#aipSend').classList.remove('show');
    file.value = '';
    Object.keys(answers).forEach(k => delete answers[k]);
    if ($('#aipNotes')) $('#aipNotes').value = '';
    renderFields(); updateProgress(); goStep(1);
  });

  /* ---- 4. send it to DFC ---- */
  $('#aipSendOpen').addEventListener('click', () => {
    $('#aipSend').classList.add('show');
    $('#aipSend').scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => $('#aipName').focus(), 400);
  });

  $('#aipForm').addEventListener('submit', async e => {
    e.preventDefault();
    const form = e.target, btn = $('#aipSubmit'), status = $('#aipStatus');
    const val = id => (($(id) || {}).value || '').trim();
    status.className = 'aip-status';
    if (!form.checkValidity()) {
      status.textContent = 'Please complete every field above.';
      status.classList.add('is-error');
      form.reportValidity();
      return;
    }
    if (val('#aipHoney')) return;   // honeypot: a bot filled the hidden field
    btn.disabled = true;
    const label = btn.textContent;
    btn.textContent = 'Sending...';
    status.textContent = '';

    // Park the design so the email can link to it. Best effort: the lead
    // still goes if this fails, it just arrives without the picture.
    if (lastImage && !savedURL) {
      try {
        const r = await fetch('/api/ai-save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ image: lastImage }) });
        const j = await r.json();
        if (j && j.url) savedURL = location.origin + j.url;
      } catch (err) { /* carry on without it */ }
    }

    const fd = new FormData();
    fd.append('name', val('#aipName'));
    fd.append('phone', val('#aipPhone'));
    fd.append('email', val('#aipEmail'));
    fd.append('project_address', val('#aipAddress'));
    ORDER.forEach(k => fd.append(k, answers[k] || 'not given'));
    const notes = $('#aipNotes') ? $('#aipNotes').value.trim() : '';
    if (notes) fd.append('Their notes', notes);
    fd.append('design_image', savedURL || 'Could not be saved, ask them for a screenshot');
    fd.append('_subject', 'Kitchen design from the AI Kitchen Inspiration tool');
    fd.append('_template', 'table');
    fd.append('_captcha', 'false');
    fd.append('_cc', LEAD_CC);
    fd.append('source', 'AI Kitchen Inspiration tool');
    fd.append('page_url', location.href);
    fd.append('submitted_at', new Date().toISOString());

    try {
      const r = await fetch(LEAD_ENDPOINT, { method: 'POST', headers: { Accept: 'application/json' }, body: fd });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || (j && j.success === 'false')) throw new Error('send failed');
      track('generate_lead', { form_source: 'ai kitchen inspiration' }, 'AIDesignLead');
      form.reset();
      status.textContent = 'Thank you, your design is on its way. We will call you within 24 hours to talk it through.';
      status.classList.add('is-ok');
    } catch (err) {
      status.textContent = 'Sorry, that did not send. Please call or text us at ' + PHONE + '.';
      status.classList.add('is-error');
    } finally {
      btn.disabled = false;
      btn.textContent = label;
    }
  });

  renderFields();
  updateProgress();
})();
