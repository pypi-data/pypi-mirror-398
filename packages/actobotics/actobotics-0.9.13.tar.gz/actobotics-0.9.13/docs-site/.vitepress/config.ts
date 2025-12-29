import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'ACTO Documentation',
  description: 'Robotics-first proof-of-execution toolkit',
  
  // Clean URLs without .html
  cleanUrls: true,
  
  // Head tags
  head: [
    ['link', { rel: 'icon', href: '/favicon.png' }],
    ['meta', { name: 'theme-color', content: '#1a1a1a' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'ACTO Documentation' }],
    ['meta', { property: 'og:description', content: 'Robotics-first proof-of-execution toolkit' }],
    ['meta', { property: 'og:image', content: 'https://docs.actobotics.net/og-image.png' }],
    // Preload fonts (same as dashboard)
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
  ],
  
  // Disable dark mode completely - light only
  appearance: false,

  // Theme configuration
  themeConfig: {
    logo: '/logo.svg',
    siteTitle: 'ACTO',
    
    // Navigation bar
    nav: [
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'SDK', link: '/sdk/installation' },
      { text: 'API', link: '/api/overview' },
      { text: 'CLI', link: '/cli/overview' },
      {
        text: 'Links',
        items: [
          { text: 'Dashboard', link: 'https://api.actobotics.net/dashboard' },
          { text: 'Website', link: 'https://actobotics.net' },
          { text: 'PyPI', link: 'https://pypi.org/project/actobotics/' },
          { text: 'GitHub', link: 'https://github.com/actobotics/ACTO' },
        ]
      }
    ],

    // Sidebar navigation
    sidebar: {
      '/guide/': [
        {
          text: 'Introduction',
          items: [
            { text: 'What is ACTO?', link: '/guide/introduction' },
            { text: 'Quick Start', link: '/guide/quickstart' },
            { text: 'Core Concepts', link: '/guide/concepts' },
          ]
        },
        {
          text: 'Proof Protocol',
          items: [
            { text: 'How Proofs Work', link: '/guide/proofs' },
            { text: 'Telemetry Format', link: '/guide/telemetry' },
            { text: 'Verification', link: '/guide/verification' },
          ]
        },
        {
          text: 'Fleet Management',
          items: [
            { text: 'Overview', link: '/guide/fleet/overview' },
            { text: 'Device Monitoring', link: '/guide/fleet/devices' },
            { text: 'Device Groups', link: '/guide/fleet/groups' },
            { text: 'Health Reporting', link: '/guide/fleet/health' },
          ]
        },
        {
          text: 'Security',
          items: [
            { text: 'Authentication', link: '/guide/security/authentication' },
            { text: 'Token Gating', link: '/guide/security/token-gating' },
            { text: 'Best Practices', link: '/guide/security/best-practices' },
          ]
        },
        {
          text: 'Advanced',
          items: [
            { text: 'Architecture', link: '/guide/architecture' },
            { text: 'Self-Hosting', link: '/guide/self-hosting' },
            { text: 'Threat Model', link: '/guide/threat-model' },
          ]
        }
      ],
      '/sdk/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Installation', link: '/sdk/installation' },
            { text: 'Configuration', link: '/sdk/configuration' },
            { text: 'Basic Usage', link: '/sdk/basic-usage' },
          ]
        },
        {
          text: 'Client Reference',
          items: [
            { text: 'ACTOClient', link: '/sdk/client' },
            { text: 'AsyncACTOClient', link: '/sdk/async-client' },
            { text: 'FleetClient', link: '/sdk/fleet-client' },
          ]
        },
        {
          text: 'Proof Creation',
          items: [
            { text: 'Creating Proofs', link: '/sdk/creating-proofs' },
            { text: 'Telemetry Bundle', link: '/sdk/telemetry-bundle' },
            { text: 'Key Management', link: '/sdk/key-management' },
          ]
        },
        {
          text: 'Models',
          items: [
            { text: 'ProofEnvelope', link: '/sdk/models/proof-envelope' },
            { text: 'TelemetryBundle', link: '/sdk/models/telemetry-bundle' },
            { text: 'Response Models', link: '/sdk/models/responses' },
          ]
        },
        {
          text: 'Exceptions',
          items: [
            { text: 'Error Handling', link: '/sdk/exceptions' },
          ]
        }
      ],
      '/api/': [
        {
          text: 'REST API',
          items: [
            { text: 'Overview', link: '/api/overview' },
            { text: 'Authentication', link: '/api/authentication' },
            { text: 'Rate Limiting', link: '/api/rate-limiting' },
            { text: 'Errors', link: '/api/errors' },
          ]
        },
        {
          text: 'Proof Endpoints',
          items: [
            { text: 'Submit Proof', link: '/api/proofs/submit' },
            { text: 'Get Proof', link: '/api/proofs/get' },
            { text: 'List Proofs', link: '/api/proofs/list' },
            { text: 'Search Proofs', link: '/api/proofs/search' },
          ]
        },
        {
          text: 'Verification',
          items: [
            { text: 'Verify Proof', link: '/api/verification/verify' },
            { text: 'Batch Verify', link: '/api/verification/batch' },
          ]
        },
        {
          text: 'Fleet Management',
          items: [
            { text: 'Fleet Overview', link: '/api/fleet/overview' },
            { text: 'Device Details', link: '/api/fleet/devices' },
            { text: 'Health Reporting', link: '/api/fleet/health' },
            { text: 'Device Groups', link: '/api/fleet/groups' },
          ]
        },
        {
          text: 'Other Endpoints',
          items: [
            { text: 'Statistics', link: '/api/statistics' },
            { text: 'Access Control', link: '/api/access' },
            { text: 'Health Check', link: '/api/health' },
          ]
        }
      ],
      '/cli/': [
        {
          text: 'CLI Reference',
          items: [
            { text: 'Overview', link: '/cli/overview' },
            { text: 'Installation', link: '/cli/installation' },
          ]
        },
        {
          text: 'Commands',
          items: [
            { text: 'acto keys', link: '/cli/commands/keys' },
            { text: 'acto proof', link: '/cli/commands/proof' },
            { text: 'acto registry', link: '/cli/commands/registry' },
            { text: 'acto access', link: '/cli/commands/access' },
            { text: 'acto server', link: '/cli/commands/server' },
            { text: 'acto interactive', link: '/cli/commands/interactive' },
          ]
        },
        {
          text: 'Configuration',
          items: [
            { text: 'Config File', link: '/cli/config' },
            { text: 'Shell Completion', link: '/cli/completion' },
          ]
        }
      ]
    },

    // Social links
    socialLinks: [
      { icon: 'github', link: 'https://github.com/actobotics/ACTO' },
      { icon: 'x', link: 'https://x.com/actoboticsnet' }
    ],

    // Search
    search: {
      provider: 'local',
      options: {
        detailedView: true,
      }
    },

    // Edit link
    editLink: {
      pattern: 'https://github.com/actobotics/ACTO/edit/main/docs-site/:path',
      text: 'Edit this page on GitHub'
    },

    // Footer
    footer: {
      message: 'https://www.actobotics.net',
      copyright: 'Copyright © 2025 ACTO'
    },

    // Outline
    outline: {
      level: [2, 3],
      label: 'On this page'
    },

    // Last updated
    lastUpdated: {
      text: 'Last updated',
      formatOptions: {
        dateStyle: 'medium',
        timeStyle: 'short'
      }
    }
  },

  // Markdown configuration
  markdown: {
    lineNumbers: true,
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    }
  }
})

