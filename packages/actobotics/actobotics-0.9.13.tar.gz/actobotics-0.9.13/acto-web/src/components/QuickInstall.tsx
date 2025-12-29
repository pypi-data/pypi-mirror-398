import { useState } from 'react';
import { Copy, Check, ArrowRight, Shield, Cpu, Clock } from 'lucide-react';
import { config } from '../config';
import { ScrollAnimation } from './ScrollAnimation';
import { AnimatedCounter } from './AnimatedCounter';

export function QuickInstall() {
  const [copied, setCopied] = useState(false);
  const installCommand = 'pip install actobotics';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(installCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section 
      className="border-t border-gray-200 text-gray-900 relative overflow-hidden"
      style={{ background: 'radial-gradient(ellipse at center, #fafaf9 0%, #a8a29e 100%)' }}
    >
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-20 md:py-32">
        {/* Centered content */}
        <div className="max-w-3xl mx-auto text-center">
          <ScrollAnimation animation="blur-in" delay={0}>
            <p className="text-sm text-stone-500 mb-6 tracking-wide uppercase">Get Started</p>
          </ScrollAnimation>
          
          {/* Main install command - large and prominent */}
          <ScrollAnimation animation="blur-in" delay={60}>
            <div className="mb-8">
              <button
                onClick={handleCopy}
                className="group inline-flex items-center gap-4 px-8 py-5 bg-stone-900 text-white rounded-2xl hover:bg-stone-800 transition-all shadow-xl hover:shadow-2xl"
              >
                <code className="text-xl md:text-2xl font-mono font-medium tracking-tight">
                  {installCommand}
                </code>
                <div className="w-px h-8 bg-stone-700" />
                {copied ? (
                  <Check size={24} className="text-green-400" />
                ) : (
                  <Copy size={24} className="text-stone-400 group-hover:text-white transition-colors" />
                )}
              </button>
              <p className="mt-4 text-sm text-stone-500">
                {copied ? 'Copied to clipboard' : 'Click to copy'}
              </p>
            </div>
          </ScrollAnimation>

          {/* Tagline */}
          <ScrollAnimation animation="blur-in" delay={120}>
            <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-gray-900">
              One command. Zero configuration.
            </h2>
            <p className="text-stone-600 leading-relaxed mb-12 max-w-xl mx-auto">
              Install the SDK and connect directly to our hosted API. 
              No server setup, no infrastructure—just cryptographic proofs in minutes.
            </p>
          </ScrollAnimation>

          {/* Three column stats/features */}
          <div className="grid grid-cols-3 gap-8 mb-12">
            <ScrollAnimation animation="blur-in" delay={180}>
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-white border border-stone-200 flex items-center justify-center shadow-sm">
                  <Shield size={24} className="text-stone-600" />
                </div>
                <p className="text-2xl font-semibold text-gray-900 mb-1">Ed25519</p>
                <p className="text-sm text-stone-500">Signatures</p>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={240}>
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-white border border-stone-200 flex items-center justify-center shadow-sm">
                  <Clock size={24} className="text-stone-600" />
                </div>
                <p className="text-2xl font-semibold text-gray-900 mb-1">
                  <AnimatedCounter end={50} prefix="<" suffix="ms" duration={2000} />
                </p>
                <p className="text-sm text-stone-500">Verification</p>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={300}>
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-white border border-stone-200 flex items-center justify-center shadow-sm">
                  <Cpu size={24} className="text-stone-600" />
                </div>
                <p className="text-2xl font-semibold text-gray-900 mb-1">
                  <AnimatedCounter end={100} suffix="%" duration={2000} />
                </p>
                <p className="text-sm text-stone-500">Local proof generation</p>
              </div>
            </ScrollAnimation>
          </div>

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <ScrollAnimation animation="blur-in" delay={360}>
              <a
                href={config.links.docs + '/guide/quickstart'}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
              >
                Read the quickstart guide
                <ArrowRight size={16} />
              </a>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={360}>
              <a
                href={config.links.pypi}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-stone-300 text-stone-700 text-sm font-medium rounded-lg hover:bg-white transition-colors"
              >
                View on PyPI
              </a>
            </ScrollAnimation>
          </div>
        </div>
      </div>
    </section>
  );
}
