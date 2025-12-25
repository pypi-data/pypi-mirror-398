# ACTO Documentation

This is the VitePress-based documentation site for ACTO.

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
cd docs-site
npm install
```

### Development Server

```bash
npm run dev
```

Visit `http://localhost:5173`

### Build

```bash
npm run build
```

Output is in `.vitepress/dist/`

### Preview Build

```bash
npm run preview
```

## Deployment to Vercel

### Option 1: New Vercel Project

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import the same GitHub repository
4. **Set Root Directory** to `docs-site`
5. Framework Preset will auto-detect VitePress
6. Deploy

### Option 2: Vercel CLI

```bash
cd docs-site
npx vercel --prod
```

### Custom Domain

After deployment:

1. Go to Project Settings → Domains
2. Add `docs.actobotics.net`
3. Configure DNS at your registrar:
   - Add CNAME record pointing to `cname.vercel-dns.com`

## Structure

```
docs-site/
├── .vitepress/
│   ├── config.ts      # VitePress configuration
│   └── theme/
│       ├── index.ts   # Theme entry
│       └── custom.css # Custom styles
├── public/            # Static assets
│   ├── logo.svg
│   ├── favicon.png
│   └── hero-robot.svg
├── guide/             # Guide pages
├── sdk/               # SDK documentation
├── api/               # API reference
├── cli/               # CLI documentation
├── index.md           # Homepage
└── package.json
```

## Adding Pages

1. Create a `.md` file in the appropriate directory
2. Add to sidebar in `.vitepress/config.ts`
3. Use standard Markdown with VitePress extensions

### VitePress Features

```md
::: tip
This is a tip
:::

::: warning
This is a warning
:::

::: danger
This is dangerous
:::

::: info
This is info
:::
```

Code blocks with line highlighting:

```python{2,4}
def example():
    highlighted = True  # This line is highlighted
    normal = False
    also_highlighted = True  # This too
```

## Contributing

1. Fork the repository
2. Create a branch for your changes
3. Make your edits
4. Test locally with `npm run dev`
5. Submit a pull request

