import { Github, ArrowRight, Key } from 'lucide-react';
import { config } from '../config';

export function Hero() {
  return (
    <section className="min-h-screen flex items-center relative">
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/hero.png)' }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-black/70" />
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-20 md:py-32 relative z-10">
        <p className="text-sm text-gray-200 mb-6 md:mb-8 tracking-wide uppercase">Proof of Execution</p>
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-medium leading-[1.15] tracking-tight mb-6 md:mb-8 max-w-3xl text-white">
          Verify that robots<br />actually executed.
        </h1>
        <p className="text-lg md:text-xl text-gray-200 mb-8 md:mb-12 max-w-xl leading-relaxed">
          Trust is good. Cryptographic proof is better.<br />
          Turn every robotic action into undeniable, verifiable truth.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 md:gap-4">
          <a
            href={config.links.dashboard}
            className="group px-6 py-3 bg-white text-gray-900 text-sm font-medium rounded-md hover:bg-gray-100 transition-colors inline-flex items-center justify-center gap-2"
          >
            <Key size={16} />
            Get API Key
            <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
          </a>
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
      </div>
    </section>
  );
}
