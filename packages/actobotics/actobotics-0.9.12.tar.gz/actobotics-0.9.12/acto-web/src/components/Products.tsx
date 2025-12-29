import { Code2, Server, LayoutDashboard, Terminal, ArrowRight } from 'lucide-react';
import { config } from '../config';
import { ScrollAnimation } from './ScrollAnimation';

const products = [
  {
    icon: Code2,
    name: 'Python SDK',
    tagline: 'Create proofs locally',
    description: 'Generate cryptographic execution proofs from your robot telemetry and logs. Your data never leaves your system until you choose to verify.',
    features: [
      'Local proof generation',
      'Ed25519 signatures',
      'Async/await support',
      'Telemetry normalization',
    ],
    cta: 'View on PyPI',
    ctaLink: config.links.pypi,
    bg: '/bg2.png',
  },
  {
    icon: Server,
    name: 'REST API',
    tagline: 'Verify & submit proofs',
    description: 'Submit proofs for verification, store them in the registry, and query your proof history. The source of truth for all proofs.',
    features: [
      'Proof verification',
      'Proof registry',
      'Search & filtering',
      'Batch operations',
    ],
    cta: 'API Documentation',
    ctaLink: config.links.docs + '/api/overview',
    bg: '/bg1.png',
  },
  {
    icon: LayoutDashboard,
    name: 'Dashboard',
    tagline: 'Manage everything',
    description: 'Connect your Solana wallet to manage API keys, view proof history, monitor your robot fleet, and track usage statistics.',
    features: [
      'Multi-wallet support',
      'API key management',
      'Fleet overview',
      'Usage analytics',
    ],
    cta: 'Open Dashboard',
    ctaLink: config.links.dashboard,
    bg: '/bg3.png',
  },
  {
    icon: Terminal,
    name: 'CLI Tools',
    tagline: 'Power user interface',
    description: 'Full-featured command-line interface for proof creation, key management, and API interaction with shell completion.',
    features: [
      'Interactive mode',
      'Shell completion',
      'JSON output',
      'Pipeline support',
    ],
    cta: 'CLI Documentation',
    ctaLink: config.links.docs + '/cli/overview',
    bg: '/bg4.png',
  },
];

export function Products() {
  return (
    <section className="py-16 md:py-24">
      {/* Header - consistent with other sections */}
      <div className="max-w-6xl mx-auto px-4 md:px-6 mb-12 md:mb-16">
        <ScrollAnimation animation="blur-in" delay={0}>
          <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight">The ACTO Ecosystem</h2>
          <p className="text-gray-500 max-w-2xl leading-relaxed">
            Everything you need to generate, verify, and manage cryptographic proofs for your autonomous systems.
          </p>
        </ScrollAnimation>
      </div>

      {/* 4 Column Grid - full width */}
      <div className="px-4 md:px-8 lg:px-12 xl:px-16 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
          {products.map((product, index) => {
            const Icon = product.icon;
            
            return (
              <ScrollAnimation key={product.name} animation="blur-in" delay={60 + index * 80}>
                <div
                  className="group relative overflow-hidden border border-gray-200 rounded-2xl p-6 hover:border-gray-300 hover:shadow-xl transition-all flex flex-col"
                >
                {/* Background Image */}
                <div
                  className="absolute inset-0 bg-cover bg-center bg-no-repeat"
                  style={{ backgroundImage: `url(${product.bg})` }}
                />
                {/* White overlay for 50% visibility */}
                <div className="absolute inset-0 bg-white/50" />
                
                {/* Content */}
                <div className="relative z-10 flex flex-col h-full">
                {/* Icon */}
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-5 group-hover:bg-gray-900 transition-colors">
                  <Icon className="w-6 h-6 text-gray-700 group-hover:text-white transition-colors" />
                </div>

                {/* Title */}
                <h3 className="text-xl font-medium text-gray-900 mb-1">{product.name}</h3>
                <p className="text-sm text-gray-500 mb-4">{product.tagline}</p>

                {/* Description */}
                <p className="text-sm text-gray-600 leading-relaxed mb-5 flex-grow">
                  {product.description}
                </p>

                {/* Features */}
                <ul className="space-y-2 mb-6">
                  {product.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-xs text-gray-600">
                      <div className="w-1 h-1 bg-gray-400 rounded-full flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                <a
                  href={product.ctaLink}
                  target={product.ctaLink.startsWith('http') ? '_blank' : undefined}
                  rel={product.ctaLink.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className="inline-flex items-center gap-2 text-sm font-medium text-gray-900 hover:text-gray-600 transition-colors mt-auto"
                >
                  {product.cta}
                  <ArrowRight size={14} />
                </a>
                </div>
                </div>
              </ScrollAnimation>
            );
          })}
      </div>
    </section>
  );
}
