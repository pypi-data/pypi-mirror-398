import { Github, ArrowRight, Code2, Shield, Users, Scale, ExternalLink } from 'lucide-react';
import { config } from '../config';
import { ScrollAnimation } from './ScrollAnimation';

const highlights = [
  {
    icon: Code2,
    title: 'Fully Auditable',
    description: 'Every line of proof generation and verification logic is open for inspection.',
  },
  {
    icon: Shield,
    title: 'Security First',
    description: 'Cryptographic implementations reviewed and tested. No hidden backdoors.',
  },
  {
    icon: Users,
    title: 'Community Driven',
    description: 'Built with contributions from robotics engineers and security researchers.',
  },
  {
    icon: Scale,
    title: 'MIT Licensed',
    description: 'Use it freely in commercial and personal projects. No strings attached.',
  },
];

const stats = [
  { label: 'Python SDK', value: 'actobotics' },
  { label: 'License', value: 'MIT' },
  { label: 'API', value: 'REST' },
];

export function OpenSource() {
  return (
    <section className="relative overflow-hidden">
      {/* Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/hero4.png)' }}
      />
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/55 via-black/45 to-black/55" />

      <div className="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-24 relative z-10">
        {/* Header */}
        <ScrollAnimation animation="blur-in" delay={0}>
          <div className="text-center mb-12 md:mb-16">
            <p className="text-sm text-gray-300 mb-4 tracking-wide uppercase">Transparency</p>
            <h2 className="text-3xl md:text-4xl font-medium mb-4 tracking-tight text-white">
              Open Source. Open Trust.
            </h2>
            <p className="text-gray-300 max-w-2xl mx-auto leading-relaxed">
              Trust shouldn't be a black box. Our SDK, verification logic, and protocol specifications 
              are fully open source – because verifiable systems require verifiable code.
            </p>
          </div>
        </ScrollAnimation>

        {/* Highlights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12 md:mb-16">
          {highlights.map((item, index) => {
            const Icon = item.icon;
            return (
              <ScrollAnimation key={item.title} animation="blur-in" delay={60 + index * 60}>
                <div
                  className="bg-white/95 backdrop-blur-sm border border-white/20 rounded-xl p-6 hover:bg-white hover:shadow-lg transition-all"
                >
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
                    <Icon size={20} className="text-gray-700" />
                  </div>
                  <h3 className="font-medium text-gray-900 mb-2">{item.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{item.description}</p>
                </div>
              </ScrollAnimation>
            );
          })}
        </div>

        {/* CTA Card */}
        <ScrollAnimation animation="blur-in" delay={300}>
          <div className="bg-neutral-800 rounded-2xl p-8 md:p-12 text-white">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            {/* Left: Text */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <Github size={28} />
                <span className="text-xl font-medium">actobotics/ACTO</span>
              </div>
              <p className="text-gray-400 leading-relaxed max-w-lg mb-6 lg:mb-0">
                Clone, fork, or contribute. The entire codebase – from Ed25519 signing to 
                API verification – is available for review, modification, and improvement.
              </p>
            </div>

            {/* Right: Stats + Button */}
            <div className="flex flex-col gap-6">
              {/* Mini Stats */}
              <div className="flex gap-6 lg:gap-8">
                {stats.map((stat) => (
                  <div key={stat.label}>
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{stat.label}</p>
                    <p className="text-white font-medium">{stat.value}</p>
                  </div>
                ))}
              </div>

              {/* Buttons */}
              <div className="flex flex-wrap gap-3">
                <a
                  href={config.links.repository}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group px-6 py-3 bg-white text-gray-900 text-sm font-medium rounded-lg hover:bg-gray-100 transition-colors inline-flex items-center gap-2"
                >
                  <Github size={16} />
                  View on GitHub
                  <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                </a>
                <a
                  href={config.links.pypi}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 border border-neutral-600 text-white text-sm font-medium rounded-lg hover:bg-neutral-700 transition-colors inline-flex items-center gap-2"
                >
                  <ExternalLink size={16} />
                  PyPI Package
                </a>
              </div>
            </div>
          </div>
          </div>
        </ScrollAnimation>
      </div>
    </section>
  );
}
