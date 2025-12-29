import { Github } from 'lucide-react';
import { config } from '../config';

const footerLinks = {
  product: [
    { label: 'Dashboard', href: config.links.dashboard },
    { label: 'Documentation', href: config.links.docs },
    { label: 'API Reference', href: config.links.docs + '/api/overview' },
    { label: 'PyPI Package', href: config.links.pypi },
  ],
  resources: [
    { label: 'Getting Started', href: config.links.docs + '/guide/quickstart' },
    { label: 'SDK Guide', href: config.links.docs + '/sdk/basic-usage' },
    { label: 'CLI Commands', href: config.links.docs + '/cli/commands' },
    { label: 'Fleet Management', href: config.links.docs + '/guide/fleet/overview' },
  ],
  company: [
    { label: 'About', href: '/about' },
    { label: 'GitHub', href: config.social.github },
    { label: 'X (Twitter)', href: config.social.x },
  ],
};

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-gray-200 bg-gray-50">
      <div className="px-4 md:px-8 lg:px-12 xl:px-16 py-12 md:py-16">
        {/* Main Footer */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12 mb-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <img src="/logo_b.png" alt="ACTO Logo" className="h-5 w-auto" />
              <span className="text-lg font-serif font-medium tracking-tight text-gray-900">ACTO</span>
            </div>
            <p className="text-sm text-gray-500 leading-relaxed mb-4">
              Robotics-first proof-of-execution toolkit. Generate and verify cryptographic proofs for autonomous systems.
            </p>
            <div className="flex gap-4">
              <a
                href={config.social.github}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="GitHub"
              >
                <Github size={20} />
              </a>
              <a
                href={config.social.x}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="X (Twitter)"
              >
                <svg width="18" height="18" viewBox="0 0 1200 1227" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="M714.163 519.284L1160.89 0H1055.03L667.137 450.887L357.328 0H0L468.492 681.821L0 1226.37H105.866L515.491 750.218L842.672 1226.37H1200L714.137 519.284H714.163ZM569.165 687.828L521.697 619.934L144.011 79.6944H306.615L611.412 515.685L658.88 583.579L1055.08 1150.3H892.476L569.165 687.854V687.828Z"/>
                </svg>
              </a>
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Product</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Resources</h3>
            <ul className="space-y-3">
              {footerLinks.resources.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Company</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <p className="text-sm text-gray-400">
              © {currentYear} ACTO. All rights reserved.
            </p>
            <div className="flex gap-6">
              <a href="/privacy" className="text-sm text-gray-400 hover:text-gray-600 transition-colors">
                Privacy Policy
              </a>
              <a href="/terms" className="text-sm text-gray-400 hover:text-gray-600 transition-colors">
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
