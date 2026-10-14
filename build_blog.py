#!/usr/bin/env python3
"""Generate the DFC blog (/blog/) — Home Notes articles.

Standalone article pages in the same style as the cost guide, plus a blog
index. Content mirrors the Home Notes email series so email + blog stay one
source of truth. Root-absolute asset/link paths (works with and without
trailing slashes under Caddy's try_files).
"""
import html, json, os

ROOT = "/Users/hugohernandez/Documentos/DFC/website/dfc-site"
SITE = "https://www.dfchomeimprovement.com"
PHONE_DISP = "(703) 596-8375"
PHONE_TEL = "+17035968375"
EMAIL = "admin@dfchomeimprovement.com"

# Cache-busting version for styles.css / *.js links. Bump on any CSS or JS change,
# or browsers keep serving their cached copy (Caddy sends no Cache-Control).
ASSET_VER = "20261009n"

GTAG = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QRMHK61G1N"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-QRMHK61G1N');
</script>"""

META_PIXEL = """<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '1029300153267702');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=1029300153267702&ev=PageView&noscript=1"/></noscript>
<!-- End Meta Pixel Code -->"""

ARTICLE_CSS = """<style>
.article-body { max-width: 780px; margin: 0 auto; padding: 0 1.5rem; }
.article-body h2 { font-size: 1.45rem; margin: 2.4rem 0 .9rem; }
.article-body h3 { font-size: 1.1rem; margin: 1.8rem 0 .6rem; }
.article-body p { line-height: 1.75; margin-bottom: 1.1rem; }
.article-body ul, .article-body ol { margin: .8rem 0 1.2rem 1.4rem; }
.article-body ul li, .article-body ol li { margin-bottom: .5rem; line-height: 1.65; }
.article-hero { width: 100%; max-width: 780px; margin: 0 auto 2rem; padding: 0 1.5rem; }
.article-hero img { width: 100%; height: auto; border-radius: 10px; display: block; }
.article-meta { font-size: .88rem; color: rgba(13,8,5,.55); margin-bottom: 2rem; }
.callout { background: #f4f0ea; border-left: 3px solid #313d2c; padding: 1.2rem 1.4rem; margin: 1.5rem 0; border-radius: 0 4px 4px 0; }
.callout p { margin: 0; }
.stat-row { display: flex; gap: 1rem; margin: 1.5rem 0 2rem; flex-wrap: wrap; }
.stat-box { flex: 1 1 160px; background: #313d2c; border-radius: 10px; padding: 1.2rem 1rem; text-align: center; }
.stat-box .n { font-family: 'Urbanist', sans-serif; font-size: 1.7rem; font-weight: 700; color: #c08a2d; }
.stat-box .l { font-size: .8rem; color: rgba(255,255,255,.75); margin-top: .3rem; line-height: 1.4; }
.author-box { display: flex; flex-direction: column; align-items: center; text-align: center; gap: .35rem; border-top: 1px solid rgba(13,8,5,.12); margin-top: 2.6rem; padding-top: 2rem; }
.author-box img { width: 96px; height: 96px; border-radius: 50%; object-fit: cover; margin-bottom: .4rem; }
.author-box .a-name { font-family: 'Urbanist', sans-serif; font-weight: 700; color: #0d0805; }
.author-box .a-role { font-size: .88rem; color: #7c573a; }
.article-sources { font-size: .85rem; color: rgba(13,8,5,.55); margin-top: 1.6rem; }
.article-sources a { color: #7c573a; }
.blog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.6rem; margin-top: 2.2rem; }
.blog-card { background: #fff; border-radius: 12px; overflow: hidden; text-decoration: none; color: inherit; box-shadow: 0 1px 3px rgba(13,8,5,.08); display: flex; flex-direction: column; transition: transform .18s ease, box-shadow .18s ease; }
.blog-card:hover { transform: translateY(-3px); box-shadow: 0 8px 22px rgba(13,8,5,.12); }
.blog-card img { width: 100%; aspect-ratio: 16/10; object-fit: cover; display: block; }
.blog-card .bc-body { padding: 1.2rem 1.3rem 1.4rem; display: flex; flex-direction: column; gap: .45rem; flex: 1; }
.blog-card .bc-tag { font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; color: #c08a2d; font-weight: 700; }
.blog-card h3 { font-size: 1.08rem; line-height: 1.35; margin: 0; }
.blog-card p { font-size: .9rem; line-height: 1.55; color: rgba(13,8,5,.65); margin: 0; }
.blog-card .bc-date { font-size: .8rem; color: rgba(13,8,5,.45); margin-top: auto; padding-top: .5rem; }
</style>"""


def head_block(title, desc, canonical_path, og_image, jsonld=None):
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(jsonld, indent=2)
    return f"""<!doctype html>
<html lang="en">
<head>
{GTAG}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js');</script>
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="article">
<meta property="og:image" content="{SITE}{og_image}">
<meta name="theme-color" content="#313d2c">
<link rel="canonical" href="{SITE}{canonical_path}">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/logo/favicon-32.png">
<link rel="icon" type="image/png" sizes="64x64" href="/assets/logo/favicon-64.png">
<link rel="apple-touch-icon" href="/assets/logo/favicon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Urbanist:wght@400;500;600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/styles.css?v={ASSET_VER}">
{ld}{ARTICLE_CSS}
{META_PIXEL}
</head>
<body data-page="article">"""


HEADER = f"""<header class="site-header" id="siteHeader">
  <a class="brand" href="/index.html" aria-label="DFC Home Improvement — home">
    <img class="mark-white" src="/assets/logo/dfc-mark-white.png" alt="DFC Home Improvement">
    <img class="mark-black" src="/assets/logo/dfc-mark-black.png" alt="" aria-hidden="true">
  </a>
  <nav class="nav" aria-label="Primary">
    <a href="/new-construction.html">New Construction</a>
    <a href="/renovations.html">Renovations</a>
    <a href="/portfolio.html">Portfolio</a>
    <a href="/blog/" class="current">Blog</a>
    <a href="/contact.html">Contact</a>
  </nav>
  <div class="header-right">
    <a class="header-phone" href="tel:{PHONE_TEL}">{PHONE_DISP}</a>
    <a class="btn header-cta" href="/contact.html">Free Consultation</a>
    <a class="header-quick" href="tel:{PHONE_TEL}" aria-label="Call {PHONE_DISP}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg><span>Call</span></a>
    <a class="header-quick" href="sms:{PHONE_TEL}" aria-label="Text {PHONE_DISP}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 9 9 0 0 1-3.8-.8L3 20.5l1.4-4.6A8 8 0 0 1 3 11.5 8.4 8.4 0 0 1 12 3a8.4 8.4 0 0 1 9 8.5z"/></svg><span>Text</span></a>
    <a class="header-portal" href="/employee/" rel="nofollow" title="Employee portal" aria-label="Open employee portal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="10" r="3.2"/><path d="M6.3 18.5c1.3-2.2 3.3-3.4 5.7-3.4s4.4 1.2 5.7 3.4"/></svg></a>
    <button class="nav-toggle" id="navToggle" aria-label="Open menu" aria-expanded="false" aria-controls="mobileMenu">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<div class="mobile-menu" id="mobileMenu" aria-hidden="true">
  <nav class="m-links" aria-label="Mobile">
    <a href="/index.html">Home</a>
    <a href="/new-construction.html">New Construction</a>
    <a href="/renovations.html">Renovations</a>
    <a href="/portfolio.html">Portfolio</a>
    <a href="/blog/">Blog</a>
    <a href="/contact.html">Contact</a>
  </nav>
  <div class="m-foot">
    <a href="/employee/" rel="nofollow">Employee Portal</a>
    <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a>
    <a href="mailto:{EMAIL}">{EMAIL}</a>
  </div>
</div>"""

AUTHOR_BOX = """<div class="author-box">
      <img src="/assets/img/brian-owner.jpg" alt="Brian Stone, Owner of DFC Home Improvement">
      <div>
        <div class="a-name">Brian Stone</div>
        <div class="a-role">Owner, DFC Home Improvement · Class A Licensed &amp; Insured</div>
      </div>
    </div>"""

CTA_BAND = f"""<section class="section cta-band">
  <div class="wrap reveal">
    <p class="eyebrow">Have something in mind?</p>
    <h2>Let's build something worth coming home to.</h2>
    <div class="cta-actions">
      <a class="btn btn--light" href="/contact.html">Request a free consultation</a>
      <a class="link-arrow light" href="tel:{PHONE_TEL}">Call {PHONE_DISP} <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 6l6 6-6 6"/></svg></a>
      <a class="link-arrow light" href="sms:{PHONE_TEL}">Text us <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 6l6 6-6 6"/></svg></a>
    </div>
  </div>
</section>"""

FOOTER = f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer-top">
      <div class="footer-brand">
        <img src="/assets/logo/dfc-logo-white.png" alt="DFC Home Improvement">
        <p>Class A licensed design-build general contractor. One accountable team from first concept to final walkthrough.</p>
        <a class="footer-bbb" href="https://www.bbb.org/us/va/fairfax/profile/residential-general-contractor/dfc-home-improvement-0241-236106972/#sealclick" target="_blank" rel="nofollow noopener"><img src="https://seal-dc-easternpa.bbb.org/seals/blue-seal-280-80-bbb-236106972.png" style="border: 0; margin-top: 18px; max-width: 220px; height: auto;" alt="DFC Home Improvement BBB Business Review" /></a>
      </div>
      <div class="footer-col">
        <h4>Explore</h4>
        <a href="/index.html">Home</a>
        <a href="/renovations.html">Renovations</a>
        <a href="/portfolio.html">Portfolio</a>
        <a href="/blog/">Blog</a>
        <a href="/contact.html">Contact</a>
      </div>
      <div class="footer-col">
        <h4>Services</h4>
        <a href="/kitchen-remodeling-northern-virginia.html">Kitchen Remodeling</a>
        <a href="/bathroom-remodeling-northern-virginia.html">Bathroom Remodeling</a>
        <a href="/home-additions-northern-virginia.html">Home Additions</a>
        <a href="/basement-finishing-northern-virginia.html">Basement Finishing</a>
        <a href="/deck-builder-northern-virginia.html">Deck Building</a>
      </div>
      <div class="footer-col footer-contact">
        <h4>Get in touch</h4>
        <a class="big" href="tel:{PHONE_TEL}">{PHONE_DISP}</a>
        <a href="mailto:{EMAIL}">{EMAIL}</a>
        <p>3060 Williams Drive Suite 300,<br>Fairfax, VA 22031</p>
        <p>Serving Northern Virginia, Richmond<br>&amp; Washington DC.</p>
        <iframe class="footer-map" title="DFC Home Improvement on Google Maps" loading="lazy" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d397841.8167024655!2d-77.21790544999999!3d38.82927295!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x846a25461367bc67%3A0x736db6227d20323!2sDFC%20Home%20Improvement!5e0!3m2!1sen!2s!4v1787672110932!5m2!1sen!2s" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; 2026 DFC Home Improvement. Class A Licensed &amp; Insured. &middot; <a href="/privacy.html">Privacy Policy</a> &middot; <a href="/terms.html">Terms of Service</a></span>
    </div>
  </div>
</footer>
<script src="/assets/js/track.js?v={ASSET_VER}" defer></script>
<script src="/assets/js/script.js?v={ASSET_VER}" defer></script>
</body>
</html>"""


# ---------------------------------------------------------------- ARTICLES
ARTICLES = [
    {
        "slug": "winter-interior-remodel-projects",
        "tag": "Planning",
        "title": "Winter Remodeling: The Indoor Projects That Make Sense Now, and What to Plan for Spring",
        "card_title": "Winter remodeling: what to build indoors now and what to plan for spring",
        "desc": "Why winter works well for kitchens, bathrooms, basements and other interior remodels, which projects are better designed now and built in spring, and how to live comfortably in the house while the work happens. From a Class A licensed design-build contractor serving Northern Virginia, DC and Richmond.",
        "card_desc": "The interior projects that work well in winter, the outdoor ones to design now and build in spring, and how to live in the house during the work.",
        "hero": "/assets/img/kitchen-thomas-jefferson.jpg",
        "hero_alt": "White kitchen with a farmhouse sink, brass hardware and French doors to the patio remodeled by DFC Home Improvement",
        "date": "2026-10-14",
        "date_disp": "October 2026",
        "body": """
    <p>Most people think of remodeling as a spring and summer thing. The yard is green, the windows are open, and that is when the idea of a new kitchen feels most urgent. But a kitchen does not care what the weather is doing outside. Neither does a bathroom, a basement or a floor. For interior work, the colder months are some of the most practical of the year, and they are also the best time to get the design side of an outdoor project finished so it is ready to build when the ground thaws.</p>

    <h2>Why interior work fits the winter</h2>
    <ul>
      <li><strong>The weather stays outside.</strong> Once the work is inside the walls, rain and cold do not stop a crew the way they stop a deck or a roof. The schedule depends on decisions, materials and inspections, not the forecast.</li>
      <li><strong>You are home to make decisions.</strong> Selections and design questions move faster when you are around, and winter is when most families have the fewest weekends booked at the pool, the beach or the ballfield.</li>
      <li><strong>It is finished before the warm months.</strong> A kitchen or bathroom started in the winter is usually done before spring. That means a summer of using it, hosting in it, or listing the house with it, instead of a summer of living around a project.</li>
      <li><strong>It lines up with the spring market.</strong> If you are thinking about selling next year, the interior updates buyers notice most, kitchens, bathrooms and flooring, have to be done before the listing photos, not after.</li>
    </ul>

    <h2>The projects that work well this winter</h2>
    <ul>
      <li><strong>Kitchens.</strong> Cabinets, counters, tile, lighting and appliances are all interior work. The 3D design and selections can happen in the first weeks, while the house is still decorated for the holidays.</li>
      <li><strong>Bathrooms.</strong> A primary bath, a hall bath or a tub to shower conversion. If the house has only one full bathroom, we plan the sequence so the time without a working shower is as short as possible.</li>
      <li><strong>Basements.</strong> Finishing a basement adds a family room, an office, a guest suite or a gym, and it is entirely indoors. Winter is also when you find out whether the basement stays dry and warm, which is useful information before you finish it.</li>
      <li><strong>Flooring, drywall and paint.</strong> Replacing carpet with hardwood or LVP, repairing walls and ceilings, and repainting rooms are all good winter work, especially combined into one whole-floor refresh.</li>
      <li><strong>Layout changes.</strong> Opening a wall between the kitchen and the living room, adding a half bath, or turning an unused room into an office. These take engineering, permits and some patience, which is exactly why starting the planning in winter pays off.</li>
    </ul>

    <h2>What to design now and build in spring</h2>
    <p>Some work depends on outdoor temperatures. Concrete has to cure, exterior paint and many sealants have minimum application temperatures set by the manufacturer, and digging footings in frozen ground is slow and messy. Decks, patios, porches, exterior painting and most additions are better built when it warms up.</p>
    <p>That does not mean waiting until spring to start. The design, the drawings, the permit application and the material selections for an outdoor project can all be done over the winter. Then, when the weather turns, the project is ready for a crew instead of just getting started on paperwork. The families who have a new deck by Memorial Day are almost always the ones who planned it in January.</p>

    <h2>Living in the house during a winter remodel</h2>
    <ol>
      <li><strong>Dust and heat.</strong> Work areas are closed off with plastic barriers and the floors leading to them are protected. Heating vents in the work zone are covered so dust does not travel through the system, while the rest of the house stays warm.</li>
      <li><strong>A temporary kitchen.</strong> For a kitchen remodel, set up a small station somewhere else in the house: the refrigerator, a microwave, a coffee maker and a folding table go a long way. Plan simple meals and use paper plates for a few weeks.</li>
      <li><strong>The holidays.</strong> If family is coming, tell us the dates before the schedule is set. It is much easier to plan the project around a holiday than to rush a kitchen to be usable by one. We wrote about how the full sequence lines up in our <a href="/blog/remodel-timeline-before-the-holidays.html">remodel timeline guide</a>.</li>
      <li><strong>Snow days.</strong> Interior work can usually continue in bad weather, but material deliveries and inspections can slip a day when the roads are bad. Those are the days to expect a small adjustment, not a stopped project.</li>
    </ol>

    <h2>How to get started</h2>
    <p>The order is the same in any season: an evaluation and measurements, then the design and selections, then permits and materials, and only then a crew start date. The part that depends on you is the design, so that is the part to start early. If you want to see how the design step works, our guide on <a href="/blog/see-it-before-you-build-it-3d-design.html">seeing your room in 3D before you build</a> walks through it.</p>

    <div class="callout">
      <p><strong>Thinking about a kitchen, bathroom, basement or a spring outdoor project?</strong> Send us a few photos of the space and what you want it to do better, and we will tell you how the project would come together this winter. One team from first concept to final walkthrough: design, permits, materials and construction. Call <a href="tel:+17035968375">(703) 596-8375</a>, <a href="/contact.html">request an evaluation</a>, or see how the process works on <a href="/our-process.html">our process page</a>.</p>
    </div>

    <p class="article-sources">Project schedules, start dates and the sequence of work are confirmed in writing for each project. Manufacturer temperature requirements for exterior materials vary by product and are followed as written.</p>
""",
    },
    {
        "slug": "see-it-before-you-build-it-3d-design",
        "tag": "Design",
        "title": "See It Before You Build It: How 3D Design Keeps a Remodel on Track",
        "card_title": "See it before you build it: how 3D design keeps a remodel on track",
        "desc": "Why the design step matters more than any other part of a kitchen, bathroom or whole-home remodel: what a photoreal 3D design actually shows, the decisions it settles before demolition, what it cannot replace, and how to get ready for a design meeting. From a Class A licensed design-build contractor serving Northern Virginia, DC and Richmond.",
        "card_desc": "What a 3D design shows, the decisions it settles before demolition, what it cannot replace, and how to prepare for a design meeting.",
        "hero": "/assets/img/3d-bradley-1.jpg",
        "hero_alt": "Photoreal 3D rendering of a kitchen with a black island, white cabinets and brass pendants designed by DFC Home Improvement",
        "date": "2026-09-30",
        "date_disp": "September 2026",
        "body": """
    <p>Ask anyone who has lived through a remodel what they would do differently and the answer is almost never about the crew. It is about a decision they made too late: the island that ended up too close to the range, the tile that looked different on a wall than on a sample board, the pendant lights nobody measured for until the electrician was standing in the kitchen. Every one of those is a design decision that got made on site instead of on screen. The 3D design step exists to move those decisions forward, to a point where changing your mind costs a conversation instead of a change order.</p>

    <h2>What a 3D design actually is</h2>
    <p>It is your room, not a stock picture. We measure the space, then model it with the proposed layout, cabinets, counters, tile, flooring, plumbing fixtures, lighting and paint colors, and render it photoreal so you can look at it the way you would look at a photo of a finished project. You see how the light falls, how much walkway is left between the island and the fridge, whether the shower niche lines up with the tile grid, and how the two colors you liked separately actually sit next to each other.</p>
    <p>You get several views of the same room, and we revise them until the design is right. That back and forth is the whole point. Moving a wall on screen takes an afternoon. Moving it after framing takes a crew, a dumpster and a permit revision.</p>

    <h2>The decisions it settles before demolition</h2>
    <ul>
      <li><strong>Layout.</strong> Where the sink, range, fridge and island go, and whether the room still works when two people are in it. Clearances that look fine on a floor plan often do not in three dimensions.</li>
      <li><strong>Selections.</strong> Cabinet style and color, counter material, tile size and pattern, flooring, hardware finish, fixture finish. Seeing them together is how you avoid a kitchen that is three good ideas that do not agree.</li>
      <li><strong>Lighting.</strong> Recessed cans, pendants, sconces and under-cabinet light are placed in the model, so the electrical plan comes from the design instead of from a guess on rough-in day.</li>
      <li><strong>Everyone in the house.</strong> A rendering is something a spouse, a parent or a teenager can react to. A floor plan usually is not. Getting the household to agree before ordering saves the most expensive kind of change, the one made after materials arrive.</li>
      <li><strong>The permit set.</strong> Once the design is approved, the drawings for permits and the material order come from it. That is what keeps the schedule honest: the crew starts when the design is locked and the materials are on site, not before.</li>
    </ul>

    <h2>What it cannot replace</h2>
    <p>A rendering shows the room as designed. It does not show what is inside the walls. Old plumbing routed the wrong way, a beam where the open wall was supposed to be, a floor that is out of level by more than the tile can hide: those are found on site and handled as concealed conditions, in writing, before the work continues. A good design reduces surprises. It does not eliminate them, and anyone who tells you otherwise has not opened enough walls.</p>
    <p>It also does not replace samples. Screens vary. Once the design is close, we still put the actual tile, counter and cabinet door sample in your kitchen, in your light, before anything is ordered.</p>

    <h2>Where it sits in the timeline</h2>
    <p>The design step runs after the project is approved and before permits. In practice that means intake and measurements first, then the renderings and revisions, then selections, then the permit drawings, and only then a crew start date. If you are aiming for a specific window, the design step is the part to start early, because it is the one step that depends on your decisions rather than ours. We wrote about how the whole sequence lines up in our <a href="/blog/remodel-timeline-before-the-holidays.html">remodel timeline guide</a>.</p>

    <h2>How to get ready for a design meeting</h2>
    <ol>
      <li><strong>Collect a handful of inspiration photos</strong>, and for each one, know what you like about it. Usually it is one thing: the island color, the way the shower is laid out, the lighting. That is far more useful than a folder of fifty kitchens.</li>
      <li><strong>Write down the must-haves and the nice-to-haves</strong> as two separate lists. A double oven, a bench in the shower, a spot for the dog bowls. The design has to serve the first list; the second list is where budget conversations happen.</li>
      <li><strong>Think about who uses the room and how.</strong> Who cooks, how many people at the counter, whether the bathroom has to work for aging parents. Those answers change the layout more than any finish does.</li>
      <li><strong>Bring your patience for measurements.</strong> Our first visit is mostly a tape measure and a camera. It is not exciting, but every rendering and every drawing depends on it.</li>
    </ol>

    <div class="callout">
      <p><strong>Planning a kitchen, bathroom or whole-home remodel?</strong> Start with the design conversation and see the room before anything is torn out. One team from first concept to final walkthrough: design, permits, materials and construction. Call <a href="tel:+17035968375">(703) 596-8375</a>, <a href="/contact.html">request an evaluation</a>, or see how the process works on <a href="/our-process.html">our process page</a>.</p>
    </div>

    <p class="article-sources">Design scope and the number of rendering revisions are confirmed in writing for each project. Concealed conditions found once work begins are documented and approved in writing before any additional work proceeds.</p>
""",
    },
    {
        "slug": "water-damage-first-48-hours",
        "tag": "Repairs",
        "title": "Water Where It Should Not Be: What to Do in the First 48 Hours, and How the Rebuild Quote Works",
        "card_title": "Water damage: the first 48 hours, and how the rebuild quote works",
        "desc": "A burst pipe, a failed shower pan or a leak under the sink: the steps that protect your home and your insurance claim in the first two days, how mitigation and rebuild fit together, and how a restoration quote lines up with the adjuster's estimate. From a Class A licensed contractor serving Northern Virginia, DC and Richmond.",
        "card_desc": "Stop the water, document everything, dry it right, and understand how mitigation, the adjuster's estimate and the rebuild quote fit together.",
        "hero": "/assets/img/bath-monteiro-ave.jpg",
        "hero_alt": "Primary bathroom with marble tile, a glass shower with gold trim and a freestanding tub renovated by DFC Home Improvement",
        "date": "2026-09-24",
        "date_disp": "September 2026",
        "body": """
    <p>Most of the water damage calls we get do not start with a flood. They start with a shower floor that has been leaking into the ceiling below for months, a dishwasher line that let go overnight, or a toilet supply that finally failed while everyone was at work. What you do in the first two days decides how big the repair gets and how smoothly the insurance side goes. Here is the order we would follow in our own homes, and then a plain explanation of how the rebuild quote actually works, because that part confuses almost everyone.</p>

    <h2>1. Stop the water at the source</h2>
    <p>Every fixture has a shutoff. Sinks and toilets have valves right behind them, water heaters have one on the cold line coming in, and the whole house has a main valve, usually where the water line enters the basement or near the meter. If you cannot find the source fast, close the main. If the water is near outlets, a panel or the ceiling light below, switch off the breakers for that area before you touch anything.</p>

    <h2>2. Take photos before you clean anything</h2>
    <p>Photograph and video the standing water, the wet walls and floors, the damaged belongings and the source itself before you move or dry anything. Get a wide shot of each room and close-ups of the worst spots. This is the evidence your insurance company will ask for, and once things are dried out and torn out, it is gone. Keep the failed part if you can, the split hose, the cracked fitting, the loose tile.</p>

    <h2>3. Call your insurer and know your deductible</h2>
    <p>Sudden and accidental water damage is usually covered by a standard homeowner policy. Slow leaks that went unnoticed for a long time, and damage from lack of maintenance, often are not, so the first question the adjuster asks is when it started and how you found it. Have your policy number ready, describe what happened without guessing at causes you do not know, and ask what your deductible is. That number matters for the decision below.</p>

    <h2>4. Get it dry within 48 hours</h2>
    <p>Mold starts growing in wet drywall and framing in about two days. A mitigation company pulls up wet flooring, cuts out saturated drywall, sets dehumidifiers and air movers, and takes moisture readings until the structure is dry. For a small spill you can do the same with towels, fans and a dehumidifier, but anything that soaked a ceiling, ran under a floor or sat overnight deserves professional drying. The insurer often has mitigation companies they work with, and you are also free to call your own.</p>

    <h2>5. Do not rebuild until two things are true</h2>
    <p>The source has to be fixed and the area has to be dry. Mitigation companies leave the room open on purpose: bare subfloor, studs showing, a clean edge where the drywall was cut. That is not neglect, it is the space waiting for the rebuild. If a contractor offers to close it up before the moisture readings are back to normal, that is the wrong contractor.</p>

    <h2>How the rebuild quote works</h2>
    <p>This is where homeowners get lost, so here is the whole picture. Mitigation and rebuild are two separate jobs, often two separate companies, and two separate invoices. Mitigation is the dry-out. The rebuild is putting the room back: subfloor, drywall, insulation, trim, paint, tile or flooring, cabinets, fixtures.</p>
    <p>Your adjuster will write an estimate for the rebuild based on what they saw or what the mitigation company documented. That estimate is a starting point, not a final word. The best thing you can do is share it with the contractor you want to use, so their quote can be lined up with it item by item. Where the adjuster missed something, like the baseboard that also has to come off or the closet that shares the wet wall, a contractor who has done this before writes it up and the adjuster reviews a supplement. That back and forth is normal.</p>
    <p>Two terms come up every time. Like kind and quality means the policy pays to put back what you had, at the same grade. Matching is the harder one: if your engineered hardwood or tile is discontinued, a patch may not match and the adjuster decides how far the replacement extends. If you want to use the moment to upgrade, say from a laminate to tile or to a different layout, the difference is paid out of pocket, and a good quote shows that difference clearly instead of blending it in.</p>

    <h2>What we need to quote a rebuild</h2>
    <p>Photos of every affected area as it sits today, including the ceiling or room below if the water traveled, the mitigation company's report if you have one, the adjuster's estimate if it has come in, and the address. With those we can usually put together a preliminary quote without a visit and tell you which items line up with the estimate and which ones do not. If you are still waiting on the adjuster, we can start with our own and adjust once theirs arrives.</p>

    <div class="callout">
      <p><strong>Dealing with water damage right now?</strong> Send us the photos and the adjuster's estimate if you have it, and we will tell you straight what the rebuild involves and how it lines up. Drywall, flooring, tile, trim, paint, plumbing and full bathroom or kitchen rebuilds, one licensed team. Call <a href="tel:+17035968375">(703) 596-8375</a> or <a href="/contact.html">get in touch</a>.</p>
    </div>

    <p class="article-sources">General guidance for typical homes in Northern Virginia, DC and Richmond; coverage depends on your policy and the cause of the loss. Confirm details with your insurance company.</p>
""",
    },
    {
        "slug": "fall-home-checklist-northern-virginia",
        "tag": "Maintenance",
        "title": "Your Fall Home Checklist: 8 Things to Do Before the First Frost in Northern Virginia",
        "card_title": "Your fall home checklist: 8 things to do before the first frost",
        "desc": "Eight checks for your heating system, outdoor faucets, gutters, drafts, fireplace, dryer vent, detectors and sump pump before the cold settles in, from a Class A licensed Northern Virginia contractor. Most take twenty minutes.",
        "card_desc": "Heating, outdoor water, gutters after the leaves, drafts, fireplace, dryer vent, detectors and the sump pump, before the cold settles in.",
        "hero": "/assets/img/outdoor-polecat-patio.jpg",
        "hero_alt": "White two-story home with black shutters and a full-width front porch built by DFC Home Improvement",
        "date": "2026-09-15",
        "date_disp": "September 2026",
        "body": """
    <p>The first hard freeze in Northern Virginia usually arrives somewhere between late October and the middle of November. Most of the winter emergencies we get called for started as something small in September: a hose left on an outdoor faucet, a furnace that never got a new filter, a downspout that dumped a month of leaves at the foundation. Here are the eight checks we would do on our own homes this month, in the order we would do them. Most take twenty minutes. None takes more than an afternoon.</p>

    <h2>1. Run the heat before you need it</h2>
    <p>Pick a mild day, switch the thermostat to heat and let it run for ten or fifteen minutes. A burning-dust smell for the first few minutes is normal. A smell that does not clear, a system that keeps cycling on and off, or air that never gets warm is not, and September is the month to find that out. Swap the filter while you are at it, and if you have a heat pump, clear leaves and mulch away from the outdoor unit. Systems older than about fifteen years deserve a professional tune-up before the season, and our own HVAC team does them.</p>

    <h2>2. Disconnect the hoses and shut off outdoor water</h2>
    <p>This is the one that floods finished basements. Even a frost-free faucet will split if a hose is left attached, because the water trapped in the line has nowhere to go when it freezes. Disconnect every hose, drain it and store it. If your outdoor faucets have an interior shutoff valve, close it and open the outside spigot to drain the pipe. Irrigation systems need to be blown out with compressed air before the first freeze, not after.</p>

    <h2>3. Do the gutters again, after the leaves</h2>
    <p>If you cleaned your gutters at the end of summer, good. Plan on a second pass in November once the oaks and maples finish dropping. Clogged gutters send water straight down the foundation wall, and in a cold snap that water becomes ice along the roof edge. Check that every downspout still discharges at least four feet from the house and that the extensions did not get kicked loose over the summer.</p>

    <h2>4. Find the drafts while it is still comfortable to fix them</h2>
    <p>On a windy day, hold a lit incense stick or a strip of tissue near window frames, door edges, the attic hatch and the spots where pipes and cables come through exterior walls. Wherever it moves, air is moving. Weatherstripping on doors and a bead of exterior caulk around window trim are the cheapest heating improvements a house can get, and an uninsulated attic hatch leaks more heat than most people would guess. If a window fogs between the panes, the seal has failed and no caulk will fix it. That one is a replacement conversation.</p>

    <h2>5. Have the fireplace looked at before the first fire</h2>
    <p>A wood-burning fireplace that saw regular use last winter should be inspected and swept before this one. Creosote builds up quietly, and the first cold night is not the moment to discover a blocked flue or a damper stuck open. Gas fireplaces are simpler: confirm the pilot lights, the glass is clean and the vent outside is clear. If a fireplace has not been used in years, have it checked before you light it.</p>

    <h2>6. Clean the dryer vent</h2>
    <p>Lint in a dryer duct plus the heavier laundry loads of winter is a fire risk that takes half an hour to remove. Pull the dryer out, disconnect the duct and clear it end to end, then check that the flap on the exterior vent opens freely and closes fully. A flap stuck open is also a draft, and an open door for mice looking for somewhere warm.</p>

    <h2>7. Test the smoke and carbon monoxide detectors</h2>
    <p>Heating season is carbon monoxide season. Press the test button on every unit, replace the batteries, and check the manufacture date printed on the back: smoke detectors are meant to be replaced after ten years, and most CO detectors after five to seven depending on the model. If you do not have a CO detector on each sleeping floor and near the furnace, this is the month to add them.</p>

    <h2>8. Test the sump pump and check the grading</h2>
    <p>Pour a bucket of water into the sump pit and confirm the pump kicks on and the water leaves. Then walk the discharge line outside and make sure it drains away from the house and will not freeze into a solid plug in January. While you are out there, look at the soil against the foundation. It should slope away from the house. Where it has settled into a low spot, top it up now, before the fall rains find it.</p>

    <h2>The project to plan now</h2>
    <p>Fall is when the calendar for interior work gets set. Bathrooms, basements and kitchens build well through the winter because the work happens indoors, and the homeowners who start design in September and October are the ones enjoying the finished space by early spring. If there is a project you keep putting off, this is a good month to get it on paper. We laid out the whole sequence from signing to the last coat of paint in <a href="/blog/remodel-timeline-before-the-holidays">our remodel timeline post</a>.</p>

    <div class="callout">
      <p><strong>Found something that is more than a Saturday fix?</strong> Send us a photo and we will tell you straight whether it is a quick repair or a bigger job. Heating, handyman repairs and full remodels, one licensed team. Call <a href="tel:+17035968375">(703) 596-8375</a> or <a href="/contact.html">get in touch</a>.</p>
    </div>

    <p class="article-sources">General guidance for typical homes in Northern Virginia, DC and Richmond; conditions vary by house. When in doubt, have a licensed professional take a look.</p>
""",
    },
    {
        "slug": "remodel-timeline-before-the-holidays",
        "tag": "Planning",
        "title": "How Long Does a Remodel Really Take? When to Start If You Want It Done Before the Holidays",
        "card_title": "How long a remodel really takes, and when to start for the holidays",
        "desc": "The real timeline of a design-build remodel in Northern Virginia, DC and Richmond, from signing to the last coat of paint: design, selections, permits, materials, construction, and the start dates that still land before Thanksgiving and Christmas.",
        "card_desc": "Design, permits, materials, construction: what each step takes, and the start dates that still land before Thanksgiving and Christmas.",
        "hero": "/assets/img/kitchen-15th-street-ne.jpg",
        "hero_alt": "Open kitchen with a marble island and dining area renovated by DFC Home Improvement",
        "date": "2026-09-09",
        "date_disp": "September 2026",
        "body": """
    <p>Every September the same question comes in: "Can we have it done by Thanksgiving?" The honest answer depends on what has to happen between the day you sign and the first day of demolition, and most of that is not construction. Here is the sequence the way we actually plan it, with the timing we work from, so you can see which projects still make it this year and which ones are honestly a January story.</p>

    <h2>Step 1 &middot; Design and 3D renders</h2>
    <p>Once you sign and make your deposit, we schedule a design intake over Zoom with our design director. In that meeting we confirm the scope, decide whether another home visit is needed to verify anything, and start on the selections. The first 3D renders are usually ready within 5 to 7 business days, and you see your finished kitchen or bathroom before anyone touches a wall.</p>
    <p>This is also where the most time is won or lost. A homeowner who picks tile, cabinets and fixtures in the first week keeps the whole schedule moving. A homeowner who takes a month to decide has moved the finish date by a month, and there is no way to get it back later.</p>

    <h2>Step 2 &middot; Permits</h2>
    <p>Not every project needs one. A bathroom that keeps its layout or a cosmetic kitchen update often needs only trade permits, or none at all. Anything that moves plumbing, opens a wall or touches structure does, and we pull it. Counties in our area typically take 1 to 3 weeks depending on their load, and in the fall that load is real: everyone is trying to finish before the holidays.</p>

    <h2>Step 3 &middot; Materials</h2>
    <p>Materials get ordered the moment selections are final, which is why Step 1 matters so much. Cabinets are the long pole in most kitchens: stock lines ship in a week or two, semi-custom typically runs 4 to 6 weeks, and full custom can take 8 to 12. Tile, vanities, fixtures and glass are shorter, but special orders and backorders still happen. Everything is delivered and staged within about 7 business days before the crew starts, so the first day on site is a working day, not a waiting day.</p>

    <h2>Step 4 &middot; Construction</h2>
    <p>Once the permit is approved and materials are in, the crew is onsite within about 10 business days. From there, the typical construction windows we plan around:</p>
    <ul>
      <li><strong>Bathroom, same layout:</strong> 2 to 3 weeks.</li>
      <li><strong>Bathroom with walls or plumbing moving:</strong> 4 to 6 weeks.</li>
      <li><strong>Kitchen, same layout:</strong> 4 to 6 weeks.</li>
      <li><strong>Kitchen with walls coming down:</strong> 8 to 12 weeks, plus engineering if a wall is load bearing.</li>
      <li><strong>Basement finishing:</strong> 6 to 10 weeks.</li>
      <li><strong>Additions and whole-home renovations:</strong> several months, planned individually.</li>
    </ul>

    <h2>What actually delays a project</h2>
    <p><strong>Late selections.</strong> By far the most common one. Every week a decision waits is a week added to the end.</p>
    <p><strong>Changes mid build.</strong> Adding a niche, moving an outlet or swapping the tile after demo is fine, but each one is a written change order, and each one costs days. Decide in design, not on site.</p>
    <p><strong>Concealed conditions.</strong> In homes built before 1990 we regularly open a wall and find outdated wiring, old pipe or a subfloor that rotted under a slow leak nobody knew about. We document it, price the fix as a written change order and get your approval before proceeding. It rarely adds more than a few days, but it is the reason we never promise a date to the day.</p>
    <p><strong>The holidays themselves.</strong> Suppliers and inspectors slow down the last two weeks of December. A project that is supposed to finish on December 23 is a project that finishes in January.</p>

    <h2>Working backwards from the holidays</h2>
    <p>Assuming selections are made in the first week of design and the permit comes back on the normal schedule, this is roughly how the calendar looks from mid September:</p>
    <ul>
      <li><strong>Bathroom, same layout:</strong> signed by early October, done before Thanksgiving. Signed by early November, done before Christmas.</li>
      <li><strong>Bathroom with layout changes, or a kitchen that keeps its layout:</strong> signed by mid September, done before Thanksgiving. Signed by early October, done before Christmas.</li>
      <li><strong>Kitchen with walls moving, or a basement:</strong> signed now, Christmas is realistic. Thanksgiving is not, and we would rather tell you that today than in November.</li>
      <li><strong>Additions and whole-home projects:</strong> start design now and the build lands in the new year, which is the best time to build them anyway.</li>
    </ul>

    <h2>If you want it done this year</h2>
    <p>The clock starts when we see the space, not when you decide. A few photos and the address are enough for us to put a quote together, and if the project fits the calendar we will tell you straight. If it does not, we will tell you that too, and plan it for the first weeks of the new year instead of rushing it through the holidays.</p>

    <p class="article-sources">Timelines are typical ranges from our own projects and depend on selections, permit review, material availability and existing conditions. Your project schedule is confirmed in writing before work begins.</p>
"""
    },
    {
        "slug": "bathroom-remodel-cost-northern-virginia",
        "tag": "Cost Guide",
        "title": "How Much Does a Bathroom Remodel Cost in Northern Virginia? (2026)",
        "card_title": "How much does a bathroom remodel cost in Northern Virginia?",
        "desc": "Real 2026 bathroom remodel prices from a Class A design-build contractor in Fairfax, Arlington, Alexandria, Vienna and Falls Church: four price tiers, what moves the total, and how long the work really takes.",
        "card_desc": "Real 2026 numbers from our own quotes: four price tiers, what moves the total, and how long it takes.",
        "hero": "/assets/img/bath-channing-street.jpg",
        "hero_alt": "Renovated bathroom with a marble look tile shower, black fixtures and a white vanity by DFC Home Improvement",
        "date": "2026-09-09",
        "date_disp": "September 2026",
        "body": """
    <p>Bathrooms are the project we get asked about more than any other, and the one where online numbers are least useful. Remodeling magazine's Cost vs. Value report puts a midrange bathroom remodel in the Washington metro at about $25,000, but that figure describes a 5 by 7 bathroom with basic fixtures and a solid surface counter. Almost nobody we meet is buying that bathroom. So here are the numbers from our own 2026 quotes across Fairfax, Arlington, Alexandria, Vienna, Falls Church and the Richmond area, and what sits inside each tier.</p>

    <h2>$8,000 to $17,000 &middot; Tub to shower conversion or a targeted update</h2>
    <p>The layout stays where it is. The tub comes out and a walk-in shower goes in with a new valve, tiled walls, a proper waterproofing membrane and a glass door. Or, in a small bath, a new vanity, floor, toilet and fixtures with the existing shower left alone. This is the tier for a bathroom that works but has one thing you cannot live with anymore, and it is where most of our conversion quotes land.</p>

    <h2>$18,000 to $38,000 &middot; Full remodel, same layout</h2>
    <p>Everything comes out to the studs. New tile floor and shower, vanity and countertop, toilet, lighting, exhaust fan, trim and paint, with the plumbing and electrical brought up to code wherever they are exposed. The fixtures stay roughly where they were, so there is no rerouting of drain lines and the permit is straightforward. Most of the single bathroom quotes we wrote this year sit inside this range, with the middle of it around $28,000 to $33,000.</p>

    <h2>$35,000 to $60,000 &middot; Primary bath with layout changes</h2>
    <p>This is where a wall moves or the plumbing does. A curbless shower with a built-in bench and niches, a freestanding tub, a double vanity, heated floors, custom glass, and often a closet that gets absorbed to make the room bigger. When a wall is load bearing an engineer signs off on it. Most of the "before and after" primary suites people picture live in this tier.</p>

    <h2>$55,000 to $75,000 &middot; Two or three bathrooms at once</h2>
    <p>Doing the primary and the kids' bath, or all three bathrooms in the house, in one project. The crew is already mobilized, the materials arrive together and the plumbing gets addressed as one system, which is why two bathrooms rarely cost double one. Older homes often add a repipe or a new water heater here while the walls are open.</p>

    <h2>The four things that move your number the most</h2>
    <p><strong>Tile.</strong> The material itself and, more than people expect, the labor. Large format porcelain, marble and mosaics take longer to set and cut than a standard 12 by 24 tile, and a shower with three niches and a bench is a different job from a plain surround. Choosing tile with a realistic allowance and upgrading only where you will see it every day is the easiest way to keep the number in range.</p>
    <p><strong>Whether the plumbing moves.</strong> Keeping the toilet, the drain and the shower valve where they are avoids opening the floor and the ceiling below. Moving them buys you the layout you actually want, which is often worth it, but it is the decision that jumps you from one tier to the next.</p>
    <p><strong>What is behind the walls and under the floor.</strong> In the last two weeks alone we quoted two bathrooms where the subfloor had rotted under a slow toilet leak nobody knew about. Failed waterproofing, old galvanized pipe and undersized wiring show up in homes built before 1990 all the time. A good contractor tells you this is possible before you sign and prices it as a written change order if it appears, not as a surprise on the final invoice.</p>
    <p><strong>Glass, fixtures and the tub.</strong> A frameless glass enclosure, a freestanding tub with a floor mounted filler, a thermostatic valve with a rain head and a hand shower: each of these is a real line on the quote. None of them are required for a beautiful bathroom, and all of them are worth it if you use them daily.</p>

    <h2>How long it actually takes</h2>
    <p>Once you sign and make your deposit, we schedule a design intake with our design director, and the first 3D renders are usually ready within 5 to 7 business days. If the county requires a permit, that is 1 to 3 weeks depending on their load. From there the crew is onsite within about 10 business days, and a same layout bathroom is typically 2 to 3 weeks of construction, 4 to 6 when walls or plumbing move. In practice that means a bathroom signed in September usually lands before Thanksgiving, and October signings are the last ones that comfortably finish before the holidays.</p>

    <h2>How to compare quotes without getting burned</h2>
    <p>The cheapest quote is almost never the cheapest project. When you compare, look at what each proposal actually includes: is the tile a specific product or an allowance that gets "adjusted" later? Is waterproofing spelled out, or just "install tile"? Are the vanity, glass and fixtures in the number? Are permits included? Is there language for the unexpected, or will every surprise become a change order at whatever price the contractor names that day?</p>
    <p>On our projects, every material and every dollar is in writing before work begins, and you see a photoreal 3D design of your finished bathroom before we touch anything. That way the number you approve is the number you pay, and the bathroom you imagined is the bathroom that gets built.</p>

    <p>If you want a real number for your bathroom, not a range, we are happy to put one together. No obligation, and the 3D design is free.</p>

    <p class="article-sources">Price tiers are drawn from DFC Home Improvement quotes written in 2026 for homes in Northern Virginia, DC and the Richmond area; your project will vary with size, selections and existing conditions. Industry benchmark: <a href="https://www.remodeling.hw.net/cost-vs-value/" target="_blank" rel="noopener">Remodeling magazine, Cost vs. Value report, Washington DC metro, midrange bathroom remodel</a>.</p>
"""
    },
    {
        "slug": "kitchen-remodel-cost-northern-virginia",
        "tag": "Cost Guide",
        "title": "How Much Does a Kitchen Remodel Cost in Northern Virginia? (2026)",
        "card_title": "How much does a kitchen remodel cost in Northern Virginia?",
        "desc": "Real 2026 kitchen remodel prices in Fairfax, Vienna, McLean, Arlington and Alexandria: four price tiers, what sits inside each one, and the three decisions that move the total. From a Class A licensed design-build contractor.",
        "card_desc": "Real 2026 numbers from a contractor who builds them: four price tiers and what moves the total.",
        "hero": "/assets/img/kitchen-polecat-warm.jpg",
        "hero_alt": "Renovated kitchen with white cabinetry, range hood and warm wood floors in Northern Virginia",
        "date": "2026-08-05",
        "date_disp": "August 2026",
        "body": """
    <p>"What's this going to cost me?" is the first question every homeowner asks, and the one most contractors dodge until they are standing in your kitchen. So here are the real numbers we see building kitchens in Fairfax, Vienna, McLean, Arlington and Alexandria in 2026, along with what actually sits inside each tier.</p>

    <h2>$18,000 to $35,000 &middot; Cosmetic refresh</h2>
    <p>Cabinet reface or repaint, new countertops, backsplash, lighting and hardware. The layout stays exactly where it is, so there is no plumbing or electrical rerouting and no permit drama. This is the tier for a kitchen that functions fine but looks tired, and it is the fastest way to a dramatic visual change.</p>

    <h2>$55,000 to $90,000 &middot; Mid-range gut</h2>
    <p>Everything comes out. Semi-custom cabinets, quartz countertops, tile backsplash, new flooring, updated lighting and appliances, and usually some electrical work to bring the room up to current code. Minor layout changes live here too: moving a sink a few feet, widening a doorway, adding an island where the plumbing allows it.</p>

    <h2>$90,000 to $140,000 &middot; Full renovation with layout changes</h2>
    <p>This is where walls come down. Opening the kitchen to the living or dining room, relocating plumbing and gas lines, custom cabinetry, upgraded appliance packages and structural work with an engineer's stamp when a wall is load bearing. Most of the "before and after" transformations people picture live in this tier.</p>

    <h2>$140,000 and up &middot; High-end and additions</h2>
    <p>Full custom cabinetry, premium stone, professional appliance suites, and often an addition or bump-out that grows the footprint. At this level the kitchen is usually part of a larger whole-home project.</p>

    <h2>The three decisions that move your number the most</h2>
    <p><strong>Cabinets.</strong> They are typically 30 to 40 percent of a kitchen budget. The jump from stock to semi-custom is meaningful; the jump from semi-custom to full custom is where budgets get away from people. If you need to save, this is the most powerful lever you have.</p>
    <p><strong>Whether the layout moves.</strong> Keeping sink, stove and refrigerator where they are avoids rerouting plumbing, gas and electrical, and that alone can be the difference between two tiers. Moving them buys you the kitchen you actually want, which is often worth it, but it should be a decision you make on purpose rather than one that surprises you.</p>
    <p><strong>What is hiding behind the walls.</strong> In homes built before 1990 we regularly find outdated wiring, undersized panels or plumbing that has to be brought to code once it is exposed. A good contractor tells you this is possible before you sign, not after demolition.</p>

    <h2>How to compare quotes without getting burned</h2>
    <p>The cheapest quote is almost never the cheapest project. When you compare, look at what each proposal actually includes: are appliances in there, or excluded? Is the countertop a specific material and thickness, or a placeholder allowance that gets "adjusted" later? Are permits included? Is there a line for the unexpected, or will every surprise become a change order?</p>
    <p>On our projects, every material and every dollar is in writing before work begins, and you see a photoreal 3D design of your finished kitchen before we touch anything. That way the number you approve is the number you pay, and the kitchen you imagined is the kitchen that gets built.</p>

    <p>If you want a real number for your kitchen, not a range, we are happy to put one together. No obligation, and the 3D design is free.</p>
"""
    },
    {
        "slug": "end-of-summer-home-checklist",
        "tag": "Maintenance",
        "title": "Your End-of-Summer Home Checklist: 7 Quick Checks That Prevent Expensive Repairs",
        "card_title": "Your end-of-summer home checklist",
        "desc": "Seven 20-minute checks (A/C, deck, caulk, gutters, water heater, trim and roof) that catch problems while they're still cheap. From a Class A licensed NoVA contractor.",
        "card_desc": "Seven 20-minute checks that catch problems while they're still cheap to fix.",
        "hero": "/assets/img/patio-pergola-summer.jpg",
        "hero_alt": "Backyard pergola patio in summer",
        "date": "2026-07-03",
        "date_disp": "July 2026",
        "body": """
    <p>Most of the expensive repairs we get called for started as something small a season earlier: a hairline of failed caulk, a clogged downspout, a filter nobody changed. Here are seven quick checks, most of them 20 minutes or less, that catch problems while they're still cheap to fix.</p>

    <h2>1. Give your A/C room to breathe</h2>
    <p>Swap the filter, rinse the outdoor unit gently with a garden hose, and keep at least two feet of clearance around it, with no shrubs and no stacked patio furniture. Late summer is when overworked systems fail, and they usually pick the hottest weekend of the year to do it. If your system is 15+ years old, it's worth having it looked at before it becomes an emergency replacement.</p>

    <h2>2. Do the deck water test</h2>
    <p>Sprinkle water on a few boards. If it beads up, your sealer is still working. If it soaks straight in, the wood is drinking every storm. Time to clean and re-seal. While you're out there, check for popped nails, soft spots and wobbly railings. A loose railing is a safety issue, not a cosmetic one.</p>

    <h2>3. Check the caulk where tub meets tile</h2>
    <p>Dark, cracked or peeling caulk lets water get behind the wall, where it rots framing quietly for years before anything shows. An $8 tube of caulk today can prevent a four-figure repair later. If the grout around it is crumbling too, that's the wall telling you water is already finding a way in.</p>

    <h2>4. Clear gutters before the fall rain</h2>
    <p>Clogged gutters dump water right at your foundation, the number one cause of the wet-basement calls we get. Make sure downspouts push water at least four feet away from the house. It's the cheapest basement waterproofing there is.</p>

    <h2>5. Flush the water heater</h2>
    <p>Sediment builds up at the bottom of the tank and makes the heater work harder for less hot water. Draining a few gallons through the valve once a year extends its life, and it's a 20-minute job with a garden hose and a floor drain.</p>

    <h2>6. Poke the exterior trim</h2>
    <p>Press a screwdriver into window sills and door frames. Paint can look fine while the wood underneath has gone soft. Caught early, it's a trim repair; caught late, it's the whole frame, and sometimes what's behind it.</p>

    <h2>7. Look up after the next big storm</h2>
    <p>Scan your ceilings for new stains and take a quick sniff in the attic: a musty smell means moisture is getting in somewhere. Roof leaks show up inside long after they start outside, so the earlier you catch the signal, the smaller the fix.</p>

    <div class="callout">
      <p><strong>Found something that's more than a Saturday fix?</strong> Send us a photo and we'll tell you straight whether it's a quick repair or something bigger. From handyman fixes to full remodels, one licensed team. Call <a href="tel:+17035968375">(703) 596-8375</a> or <a href="/contact.html">get in touch</a>.</p>
    </div>
""",
    },
    {
        "slug": "5-remodeling-mistakes-homeowners-make",
        "tag": "Hiring a Contractor",
        "title": "5 Remodeling Mistakes That Cost Homeowners Thousands (and How to Avoid Them)",
        "card_title": "5 remodeling mistakes that cost homeowners thousands",
        "desc": "The lowest bid, the missing permit, the design you never saw: the five mistakes NoVA homeowners make when hiring a remodeler, and the 2-minute checks that avoid them.",
        "card_desc": "The lowest bid, the missing permit, the design you never saw, and how to avoid all five.",
        "hero": "/assets/img/wholehome-gallery-03.jpg",
        "hero_alt": "Finished living room renovation by DFC Home Improvement",
        "date": "2026-07-03",
        "date_disp": "July 2026",
        "body": """
    <p>A good chunk of our work is fixing projects that went sideways with someone else. The same five mistakes come up again and again. Here's how to avoid them, whoever you hire.</p>

    <h2>1. Taking the bid that's way below the others</h2>
    <p>If three bids land near each other and one is dramatically lower, that bid isn't a deal. It's missing scope. It comes back later as change orders, and by then you can't switch contractors without paying twice. The gap between a licensed contractor and the cheapest bid can run $20,000 to $40,000 on a mid-range kitchen. Compare what's <em>included</em>, not just the bottom line.</p>

    <h2>2. Letting anyone skip the permit</h2>
    <p>"We can save you money by skipping the permit" is a red flag, not a favor. In Fairfax, Arlington and Alexandria, moving plumbing, electrical or walls requires one, and unpermitted work surfaces at resale, when it's most expensive to fix. The permit also buys you a county inspector checking the work; that's protection you already paid taxes for.</p>

    <h2>3. Approving a design they've never actually seen</h2>
    <p>A quote and a handshake is not a plan. Insist on seeing the space (layout, finishes, colors) before demolition day. Changes on a screen are free; changes mid-build are not. It's why every DFC project starts with a true-to-life 3D walkthrough before we pick up a tool.</p>

    <h2>4. Paying too much before work happens</h2>
    <p>A reasonable deposit is normal. Half the project in cash up front is not. Payments should be tied to completed milestones in writing (demo done, rough-in passed inspection, cabinets installed) so the money always follows the work, never the promises.</p>

    <h2>5. Skipping the 2-minute license check</h2>
    <p>Virginia lets you verify any contractor's license free at <a href="https://www.dpor.virginia.gov" target="_blank" rel="noopener">dpor.virginia.gov</a>. Look for a Class A license, the state's highest classification, and ask for a certificate of insurance sent directly from the insurer, not a photocopy. Two minutes of checking beats two years of litigation.</p>

    <div class="callout">
      <p><strong>Planning a project this year?</strong> Keep this list handy when you're comparing bids, including ours. DFC is Class A licensed and insured, every project is permitted, designed in 3D before we build, and billed by milestone. <a href="/estimate.html">Get a free estimate</a> or call <a href="tel:+17035968375">(703) 596-8375</a>.</p>
    </div>
""",
    },
    {
        "slug": "nova-home-values-2026",
        "tag": "Market Watch",
        "title": "Your Home Is Worth More Again in 2026: Here's How Northern Virginia Homeowners Can Use That",
        "card_title": "Your home is worth more again: here's how to use that",
        "desc": "Fairfax County 2026 assessments rose ~4% on average and NoVA inventory stays tight. What rising values and ~6% rates mean for the move-vs-improve decision.",
        "card_desc": "Assessments up ~4%, rates near 6%. What that combination means for the move-vs-improve math.",
        "hero": "/assets/img/wholehome-gallery-01.jpg",
        "hero_alt": "Renovated living room by DFC Home Improvement",
        "date": "2026-07-03",
        "date_disp": "July 2026",
        "body": """
    <p>If you own a home in Northern Virginia, this year's numbers are worth two minutes of your time. Fairfax County's 2026 real estate assessments came in up about 4% on average for residential properties, putting the average improved home near $830,000. The Northern Virginia Association of Realtors, in its forecast with George Mason University's Center for Regional Analysis, expects prices to keep rising modestly through 2026 while mortgage rates hover around 6% and inventory stays tight.</p>

    <div class="stat-row">
      <div class="stat-box"><div class="n">+3.99%</div><div class="l">avg. Fairfax residential assessment increase, 2026</div></div>
      <div class="stat-box"><div class="n">$760K</div><div class="l">median NoVA sold price this spring</div></div>
      <div class="stat-box"><div class="n">~6%</div><div class="l">mortgage rates expected through 2026</div></div>
    </div>

    <h2>Moving got more expensive than improving</h2>
    <p>Selling into a tight market is the easy part. It's the buying back in that hurts. Trade a pandemic-era mortgage rate for roughly 6% on the next house and your monthly payment can jump even if the next house is smaller. For a lot of NoVA families, the math now clearly favors making the house you have into the house you want.</p>

    <h2>Your equity quietly grew again</h2>
    <p>Years of rising assessments mean many homeowners are sitting on significant equity that can fund a kitchen, bath or addition, often at better terms than any other borrowing available to them. The house has already earned the renovation; the question is whether you cash that in by selling or by staying and living better.</p>

    <h2>Updated homes do best in exactly this market</h2>
    <p>With buyers still competing over limited inventory, the homes that appraise and sell strongest are the updated ones. Whether you sell in two years or stay twenty, work done right (permitted, designed, documented) protects the value this market keeps adding.</p>

    <div class="callout">
      <p><strong>Thinking about what your equity could build?</strong> Tell us what you're dreaming about and we'll give you a real number to plan around, and a 3D design so you can see it before deciding anything. <a href="/estimate.html">See your price range in 60 seconds</a> or call <a href="tel:+17035968375">(703) 596-8375</a>.</p>
    </div>

    <p class="article-sources">Sources: <a href="https://www.fairfaxcounty.gov/taxes/real-estate/press-release-notices-sent" target="_blank" rel="noopener">Fairfax County Department of Tax Administration, 2026 assessments</a> · <a href="https://www.nvar.com/news/2025-12-29/2026-economic-market-forecast/" target="_blank" rel="noopener">NVAR 2026 Regional Housing Market Forecast</a></p>
""",
    },
    {
        "slug": "nova-home-insurance-rising-2026",
        "tag": "Market Watch",
        "title": "Home Insurance Is Jumping 15 to 25% in Northern Virginia: 5 Upgrades That Push Back",
        "card_title": "Home insurance is jumping in NoVA: here's how to push back",
        "desc": "Virginia is seeing some of the steepest homeowners insurance increases in the country in 2026. Five home upgrades that can actually bring your premium down.",
        "card_desc": "Virginia premiums are among the fastest-rising in the country. Five upgrades that fight back.",
        "hero": "/assets/img/bath-marble-suite.jpg",
        "hero_alt": "Renovated bathroom by DFC Home Improvement",
        "date": "2026-07-03",
        "date_disp": "July 2026",
        "body": """
    <p>If your homeowners insurance renewal made you wince this year, you're not alone. Industry analyses put Virginia among the states with the steepest premium increases in the country for 2026, with homeowners in Fairfax, Arlington, Loudoun and Prince William counties reporting 15 to 25% year-over-year jumps, often without ever filing a claim.</p>
    <p>The drivers are mostly out of your hands: storm losses across the region, pricier building materials pushing up replacement-cost estimates, and rising reinsurance costs that carriers pass straight through to premiums. But what your specific house costs to insure is <em>not</em> out of your hands. Five things that actually move the number:</p>

    <h2>1. Ask your carrier which upgrades earn discounts before you renew</h2>
    <p>Every insurer keeps a list: roof age, water protection, updated systems, security. Ten minutes on the phone tells you exactly which improvements pay twice: once in your home, once on your premium.</p>

    <h2>2. The roof matters more than anything else</h2>
    <p>Roof age is one of the first things underwriters look at, and an aging roof can mean surcharges, or a non-renewal letter. If yours is approaching 20 years, replacing it on your schedule beats replacing it on the insurer's.</p>

    <h2>3. Stop water before it starts</h2>
    <p>Water damage is the most common home claim there is. Leak sensors under sinks and behind the washing machine, plus an automatic shutoff valve, cost a few hundred dollars. Many carriers discount for them, and they prevent the claim that would spike your rate for years.</p>

    <h2>4. Update the systems insurers worry about</h2>
    <p>Older electrical panels, aging water heaters and outdated plumbing are quiet premium-inflators in NoVA's older neighborhoods. Some panel brands and pipe types can even make a home hard to insure at all. If your home is 30+ years old and largely untouched, a systems check is worth scheduling.</p>

    <h2>5. Document your renovations: they work in your favor</h2>
    <p>Permitted, documented renovations update your home's replacement-cost profile accurately and give you leverage when you shop your policy, which in this market you should do every couple of years.</p>

    <div class="callout">
      <p><strong>Already planning one of these upgrades?</strong> We handle roofing-to-plumbing updates as one licensed team: permitted, inspected and documented, so the work counts with your insurer too. <a href="/contact.html">Get in touch</a> or call <a href="tel:+17035968375">(703) 596-8375</a>.</p>
    </div>

    <p class="article-sources">Insurance guidance is general information, not advice. Confirm available discounts with your carrier.</p>
""",
    },
    {
        "slug": "federal-energy-tax-credits-ended-2026",
        "tag": "Market Watch",
        "title": "The Federal Energy Tax Credits Ended December 31: What Still Pays Homeowners Back in 2026",
        "card_title": "The federal energy credits are gone: what still pays you back",
        "desc": "The 25C and 25D credits for insulation, windows, HVAC and solar ended Dec 31, 2025. What NoVA homeowners can still claim, and what still saves money in 2026.",
        "card_desc": "Insulation, window and HVAC credits ended Dec 31. What you can still claim, and what still saves.",
        "hero": "/assets/img/sunroom-monteiro-ave.jpg",
        "hero_alt": "Sunlit living room with large windows by DFC Home Improvement",
        "date": "2026-07-03",
        "date_disp": "July 2026",
        "body": """
    <p>Quick heads-up if energy upgrades were on your list: the federal tax credits for insulation, windows, doors, HVAC systems and solar (the Energy Efficient Home Improvement Credit, 25C, and the Residential Clean Energy Credit, 25D) ended on December 31, 2025. They were originally scheduled to run through 2032, but last year's tax legislation moved the cutoff up. Projects completed in 2026 no longer qualify for a federal credit.</p>
    <p>Before you shelve those plans, here's what's still on the table:</p>

    <h2>1. Did work in 2025? Claim it this tax season</h2>
    <p>Upgrades completed and placed in service by December 31, 2025 still qualify on the return you file this year, up to $3,200 per year under the old home-improvement credit. Dig out the receipts and manufacturer certificates before you file, and confirm the details with your tax professional.</p>

    <h2>2. State and utility rebates didn't disappear</h2>
    <p>Virginia utilities and local programs still run their own rebates for efficient HVAC equipment, water heaters and insulation. They're smaller than the federal credits were, but they're real money and always worth a check before a project. We flag applicable programs when we quote.</p>

    <h2>3. Efficiency still pays the old-fashioned way</h2>
    <p>The credits sweetened the deal; they were never the deal. Air sealing and insulation remain the cheapest comfort-per-dollar upgrade in our climate, and a right-sized modern system beats a struggling 20-year-old unit on every summer bill, credit or no credit.</p>

    <h2>4. Replace on your schedule, not the equipment's</h2>
    <p>If your A/C or furnace is 15+ years old, the question isn't if. It's whether you replace it planned (compare options, catch rebates, schedule comfortably) or in an emergency during a heat wave, when you'll pay rush pricing for whatever's on the truck.</p>

    <div class="callout">
      <p><strong>A/C or furnace getting up there in years?</strong> Our HVAC team installs and replaces central systems across Northern Virginia. We'll tell you honestly whether yours has good years left or it's time to plan. <a href="/contact.html">Get in touch</a> or call <a href="tel:+17035968375">(703) 596-8375</a>.</p>
    </div>

    <p class="article-sources">Tax information is general. Confirm your situation with a tax professional. Sources: <a href="https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit" target="_blank" rel="noopener">IRS: Energy Efficient Home Improvement Credit</a> · <a href="https://www.energystar.gov/about/federal-tax-credits" target="_blank" rel="noopener">ENERGY STAR: Federal Tax Credits</a></p>
""",
    },
]


def article_jsonld(a):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["title"],
        "description": a["desc"],
        "author": {"@type": "Organization", "name": "DFC Home Improvement", "url": SITE},
        "publisher": {
            "@type": "Organization",
            "name": "DFC Home Improvement",
            "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logo/dfc-logo-white.png"},
        },
        "datePublished": a["date"],
        "dateModified": a["date"],
        "image": f"{SITE}{a['hero']}",
        "url": f"{SITE}/blog/{a['slug']}",
        "mainEntityOfPage": f"{SITE}/blog/{a['slug']}",
    }


def build_article(a):
    body = f"""<main id="top">

<section class="page-head">
  <div class="wrap reveal">
    <p class="breadcrumb"><a href="/index.html">Home</a> / <a href="/blog/">Blog</a> / {html.escape(a['card_title'])}</p>
    <h1>{html.escape(a['title'])}</h1>
  </div>
</section>

<section class="section bg-paper">
  <div class="article-hero"><img src="{a['hero']}" alt="{html.escape(a['hero_alt'])}"></div>
  <div class="article-body">
    <p class="article-meta">By DFC Home Improvement &middot; {a['date_disp']} &middot; {html.escape(a['tag'])}</p>
{a['body']}
{AUTHOR_BOX}
  </div>
</section>
{CTA_BAND}
</main>
"""
    doc = (
        head_block(f"{a['title']} | DFC Home Improvement", a["desc"], f"/blog/{a['slug']}", a["hero"], article_jsonld(a))
        + HEADER + body + FOOTER
    )
    out = os.path.join(ROOT, "blog", a["slug"] + ".html")
    with open(out, "w") as f:
        f.write(doc)
    print("wrote", f"blog/{a['slug']}.html", f"({len(doc)//1024} kb)")


def build_index():
    cards = []
    for a in ARTICLES:
        cards.append(f"""      <a class="blog-card reveal" href="/blog/{a['slug']}">
        <img src="{a['hero']}" alt="{html.escape(a['hero_alt'])}" loading="lazy">
        <div class="bc-body">
          <span class="bc-tag">{html.escape(a['tag'])}</span>
          <h3>{html.escape(a['card_title'])}</h3>
          <p>{html.escape(a['card_desc'])}</p>
          <span class="bc-date">{a['date_disp']}</span>
        </div>
      </a>""")
    # existing cost guide, surfaced as part of the blog
    cards.append("""      <a class="blog-card reveal" href="/cost/kitchen-remodel-cost-northern-virginia">
        <img src="/assets/img/kitchen-polecat-warm.jpg" alt="Two-tone kitchen remodel by DFC Home Improvement" loading="lazy">
        <div class="bc-body">
          <span class="bc-tag">Cost Guide</span>
          <h3>How much does a kitchen remodel cost in Northern Virginia?</h3>
          <p>Real 2026 numbers by scope tier, and where the money actually goes.</p>
          <span class="bc-date">June 2026</span>
        </div>
      </a>""")
    cards_html = "\n".join(cards)
    body = f"""<main id="top">

<section class="page-head">
  <div class="wrap reveal">
    <p class="breadcrumb"><a href="/index.html">Home</a> / Blog</p>
    <h1>Home Notes: the DFC blog</h1>
    <p class="ph-desc">Practical advice for Northern Virginia, DC and Richmond homeowners: maintenance checklists, real cost numbers, market news and how to hire well. Written by the team that does the work.</p>
  </div>
</section>

<section class="section bg-paper">
  <div class="wrap">
    <div class="blog-grid">
{cards_html}
    </div>
  </div>
</section>
{CTA_BAND}
</main>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Home Notes: the DFC Home Improvement blog",
        "url": f"{SITE}/blog/",
        "publisher": {"@type": "Organization", "name": "DFC Home Improvement", "url": SITE},
    }
    doc = (
        head_block(
            "Home Notes: Homeowner Advice & Local Market News | DFC Home Improvement",
            "Practical advice for NoVA, DC and Richmond homeowners: maintenance checklists, real remodel costs, market news and how to hire a contractor well.",
            "/blog/", "/assets/img/kitchen-polecat-warm.jpg", jsonld,
        )
        + HEADER + body + FOOTER
    )
    out = os.path.join(ROOT, "blog", "index.html")
    with open(out, "w") as f:
        f.write(doc)
    print("wrote", "blog/index.html", f"({len(doc)//1024} kb)")


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "blog"), exist_ok=True)
    for a in ARTICLES:
        build_article(a)
    build_index()
    print("done.")
