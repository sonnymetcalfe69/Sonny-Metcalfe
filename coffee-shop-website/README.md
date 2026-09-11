# The Quayside Bean — Coffee Shop Website

A static, responsive website for a fictional independent coffee house on
Newcastle's Quayside, North East England. Pure HTML/CSS/JS — no build step
or dependencies required.

## Structure

```
coffee-shop-website/
├── index.html       # All page content (hero, about, menu, gallery, reviews, visit, newsletter)
├── css/style.css     # Styling, theming, and responsive layout
├── js/script.js      # Mobile nav toggle, sticky header, newsletter demo, footer year
└── images/           # (empty — the site currently uses CSS/SVG graphics instead of photos)
```

## Running locally

Just open `index.html` in a browser, or serve the folder:

```bash
cd coffee-shop-website
python3 -m http.server 8000
# visit http://localhost:8000
```

## Customising

- **Branding**: shop name, address, phone/email and opening hours are in
  `index.html` — search for "Quayside Bean" and the `#visit` section.
- **Menu & prices**: edit the `.menu-card` lists in the `#menu` section.
- **Colours**: CSS custom properties at the top of `css/style.css`
  (`--coffee-900`, `--gold-500`, `--tyne-500`, etc.).
- **Photos**: the gallery and about section currently use CSS gradients +
  emoji as placeholders. Drop real photos into `images/` and swap the
  `.about-photo` / `.gallery-tile` divs for `<img>` tags.
- **Newsletter form**: currently a front-end-only demo (no backend). Wire
  it up to a real mailing list provider (Mailchimp, Brevo, etc.) by
  replacing the `submit` handler in `js/script.js`.
