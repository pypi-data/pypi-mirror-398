import { Link } from 'react-router-dom';
import { Home, ArrowLeft, Github, FileQuestion } from 'lucide-react';
import { config } from '../config';
import { SEO } from '../components/SEO';

export function NotFound() {
  return (
    <>
      <SEO
        title="404 - Page Not Found"
        description="The page you're looking for doesn't exist."
      />
      <div className="min-h-screen flex items-center justify-center px-4 relative">
        {/* Background */}
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: 'url(/hero.png)' }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/60 to-black/70" />

        {/* Content */}
        <div className="relative z-10 text-center max-w-2xl">
          <div className="mb-8 flex justify-center">
            <div className="relative">
              <FileQuestion size={80} className="text-white/20" />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-6xl font-bold text-white">404</span>
              </div>
            </div>
          </div>

          <h1 className="text-4xl md:text-5xl font-medium text-white mb-4">
            Page Not Found
          </h1>
          <p className="text-lg text-gray-300 mb-8 leading-relaxed">
            The page you're looking for doesn't exist or has been moved.
            <br />
            Let's get you back on track.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/"
              className="group px-6 py-3 bg-white text-gray-900 text-sm font-medium rounded-md hover:bg-gray-100 transition-colors inline-flex items-center justify-center gap-2"
            >
              <Home size={16} />
              Go Home
              <ArrowLeft size={16} className="group-hover:-translate-x-0.5 transition-transform" />
            </Link>
            <a
              href={config.links.docs}
              className="px-6 py-3 text-sm font-medium text-white border border-white/30 rounded-md hover:bg-white/10 transition-colors inline-flex items-center justify-center gap-2"
            >
              Documentation
            </a>
            <a
              href={config.social.github}
              className="px-6 py-3 text-sm font-medium text-white hover:text-gray-200 transition-colors inline-flex items-center justify-center gap-2"
            >
              <Github size={16} />
              GitHub
            </a>
          </div>

          {/* Helpful Links */}
          <div className="mt-12 pt-8 border-t border-white/10">
            <p className="text-sm text-gray-400 mb-4">Popular Pages</p>
            <div className="flex flex-wrap gap-3 justify-center">
              <Link to="/about" className="text-sm text-gray-300 hover:text-white transition-colors">
                About
              </Link>
              <span className="text-gray-600">•</span>
              <a href={config.links.dashboard} className="text-sm text-gray-300 hover:text-white transition-colors">
                Dashboard
              </a>
              <span className="text-gray-600">•</span>
              <a href={config.links.docs} className="text-sm text-gray-300 hover:text-white transition-colors">
                Documentation
              </a>
              <span className="text-gray-600">•</span>
              <a href={config.links.pypi} className="text-sm text-gray-300 hover:text-white transition-colors">
                PyPI
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

