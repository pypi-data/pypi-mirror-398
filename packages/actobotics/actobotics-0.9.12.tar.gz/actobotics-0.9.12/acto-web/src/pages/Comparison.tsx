import { Check, X, Shield, Zap, Database, Link2, Clock, Lock, Cpu, Binary, ChevronRight } from 'lucide-react';
import { SEO } from '../components/SEO';
import { ScrollAnimation } from '../components/ScrollAnimation';
import { config } from '../config';

interface ComparisonFeature {
  feature: string;
  acto: boolean | string;
  traditional: boolean | string;
  blockchain: boolean | string;
}

const comparisonData: ComparisonFeature[] = [
  { feature: 'Tamper-proof proofs', acto: true, traditional: false, blockchain: true },
  { feature: 'Independent verification', acto: true, traditional: false, blockchain: true },
  { feature: 'Verification speed', acto: '<50ms', traditional: 'N/A', blockchain: '10-60s' },
  { feature: 'Proof generation', acto: '<5ms', traditional: 'Instant', blockchain: '30-60s' },
  { feature: 'Works offline', acto: false, traditional: true, blockchain: false },
  { feature: 'Access model', acto: '50k tokens', traditional: 'Free', blockchain: 'Gas fees' },
  { feature: 'Energy efficient', acto: true, traditional: true, blockchain: false },
  { feature: 'Real-time capable', acto: true, traditional: true, blockchain: false },
  { feature: 'Scalability', acto: '∞', traditional: '∞', blockchain: 'Limited' },
  { feature: 'Data privacy', acto: 'Private', traditional: 'Private', blockchain: 'Public' },
  { feature: 'Setup time', acto: '5 min', traditional: '5 min', blockchain: 'Days' },
];

export function Comparison() {
  return (
    <>
      <SEO
        title="ACTO vs Traditional Logging vs Blockchain"
        description="Compare ACTO's cryptographic proofs with traditional logging and blockchain solutions."
        url="https://actobotics.net/comparison"
      />
      <div className="min-h-screen bg-white">
        {/* Hero */}
        <section className="pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-40"
            style={{ backgroundImage: 'url(/hero4.png)' }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-white" />
          
          <div className="max-w-5xl mx-auto px-4 md:px-6 relative z-10">
            <ScrollAnimation animation="blur-in" delay={0}>
              <div className="flex items-center gap-3 mb-6">
                <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/30 to-transparent" />
                <span className="text-xs uppercase tracking-[0.3em] text-white/70 font-mono">Comparison</span>
                <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/30 to-transparent" />
              </div>
              <h1 className="text-4xl md:text-6xl font-light mb-8 tracking-tight text-white text-center">
                Choose your<br />
                <span className="font-medium">verification layer</span>
              </h1>
              <p className="text-lg text-white/80 leading-relaxed max-w-2xl mx-auto text-center font-light">
                Not all proofs are created equal. Compare the approaches and find what fits your needs.
              </p>
            </ScrollAnimation>
          </div>
        </section>

        {/* Visual Comparison */}
        <section className="py-20 md:py-28 relative">
          <div className="max-w-6xl mx-auto px-4 md:px-6">
            <div className="grid md:grid-cols-3 gap-6">
              {/* ACTO Card */}
              <ScrollAnimation animation="blur-in" delay={0}>
                <div className="group relative h-full">
                  <div className="absolute -inset-0.5 bg-gradient-to-b from-gray-900/20 to-transparent rounded-2xl blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <div className="relative border-2 border-gray-900 rounded-2xl p-8 h-full flex flex-col shadow-sm group-hover:shadow-lg transition-shadow duration-500 overflow-hidden">
                    {/* Background image */}
                    <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg1.png)' }} />
                    <div className="absolute inset-0 bg-white/85" />
                    {/* Content */}
                    <div className="relative z-10 flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 rounded-xl bg-gray-900 flex items-center justify-center">
                        <Shield className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-xl font-medium text-gray-900">ACTO</h3>
                        <p className="text-xs text-gray-900 font-mono uppercase tracking-wider">Recommended</p>
                      </div>
                    </div>
                    <p className="relative z-10 text-gray-600 text-sm leading-relaxed mb-6 flex-grow">
                      Cryptographic proofs with Ed25519 signatures. The sweet spot between security and practicality.
                    </p>
                    <div className="relative z-10 space-y-3 pt-6 border-t border-gray-200">
                      <div className="flex items-center gap-3 text-sm">
                        <Zap className="w-4 h-4 text-gray-900" />
                        <span className="text-gray-700">50ms verification</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <Lock className="w-4 h-4 text-gray-900" />
                        <span className="text-gray-700">Tamper-proof</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <Cpu className="w-4 h-4 text-gray-900" />
                        <span className="text-gray-700">Real-time capable</span>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollAnimation>

              {/* Traditional Card */}
              <ScrollAnimation animation="blur-in" delay={80}>
                <div className="relative h-full">
                  <div className="relative border border-gray-200 rounded-2xl p-8 h-full flex flex-col overflow-hidden">
                    {/* Background image */}
                    <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg2.png)' }} />
                    <div className="absolute inset-0 bg-white/85" />
                    {/* Content */}
                    <div className="relative z-10 flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 rounded-xl bg-gray-200 flex items-center justify-center">
                        <Database className="w-6 h-6 text-gray-500" />
                      </div>
                      <div>
                        <h3 className="text-xl font-medium text-gray-700">Traditional</h3>
                        <p className="text-xs text-gray-400 font-mono uppercase tracking-wider">Basic</p>
                      </div>
                    </div>
                    <p className="relative z-10 text-gray-500 text-sm leading-relaxed mb-6 flex-grow">
                      Simple logs and database entries. Easy to implement but provides no cryptographic guarantees.
                    </p>
                    <div className="relative z-10 space-y-3 pt-6 border-t border-gray-200">
                      <div className="flex items-center gap-3 text-sm">
                        <X className="w-4 h-4 text-red-400" />
                        <span className="text-gray-500">No verification</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <X className="w-4 h-4 text-red-400" />
                        <span className="text-gray-500">Easily manipulated</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <Check className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-500">Works offline</span>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollAnimation>

              {/* Blockchain Card */}
              <ScrollAnimation animation="blur-in" delay={160}>
                <div className="relative h-full">
                  <div className="relative border border-stone-200 rounded-2xl p-8 h-full flex flex-col overflow-hidden">
                    {/* Background image */}
                    <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg3.png)' }} />
                    <div className="absolute inset-0 bg-white/85" />
                    {/* Content */}
                    <div className="relative z-10 flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 rounded-xl bg-stone-300 flex items-center justify-center">
                        <Link2 className="w-6 h-6 text-stone-600" />
                      </div>
                      <div>
                        <h3 className="text-xl font-medium text-stone-700">Blockchain</h3>
                        <p className="text-xs text-stone-400 font-mono uppercase tracking-wider">Overkill</p>
                      </div>
                    </div>
                    <p className="relative z-10 text-stone-500 text-sm leading-relaxed mb-6 flex-grow">
                      Decentralized ledger technology. Maximum security but impractical for real-time robotics.
                    </p>
                    <div className="relative z-10 space-y-3 pt-6 border-t border-stone-200">
                      <div className="flex items-center gap-3 text-sm">
                        <Clock className="w-4 h-4 text-stone-400" />
                        <span className="text-stone-500">30-60s latency</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <Binary className="w-4 h-4 text-stone-400" />
                        <span className="text-stone-500">High gas fees</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <X className="w-4 h-4 text-red-400" />
                        <span className="text-stone-500">Not real-time</span>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollAnimation>
            </div>
          </div>
        </section>

        {/* Feature Matrix */}
        <section className="py-20 md:py-28 bg-gray-50">
          <div className="max-w-5xl mx-auto px-4 md:px-6">
            <ScrollAnimation animation="blur-in" delay={0}>
              <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-gray-900 text-center">
                Feature Matrix
              </h2>
              <p className="text-gray-500 text-center mb-12 text-sm">
                A detailed breakdown of capabilities
              </p>
            </ScrollAnimation>

            <ScrollAnimation animation="blur-in" delay={60}>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse bg-white rounded-xl overflow-hidden shadow-md border border-gray-200">
                  <thead>
                    <tr className="bg-gray-100 border-b-2 border-gray-200">
                      <th className="py-5 px-6 text-left text-sm font-semibold text-gray-700">Feature</th>
                      <th className="py-5 px-6 text-center text-sm font-semibold text-gray-900">ACTO</th>
                      <th className="py-5 px-6 text-center text-sm font-semibold text-gray-500">Traditional</th>
                      <th className="py-5 px-6 text-center text-sm font-semibold text-gray-500">Blockchain</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonData.map((row, index) => (
                      <tr 
                        key={index} 
                        className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                          index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                        }`}
                      >
                        <td className="py-4 px-6 text-sm font-medium text-gray-900">{row.feature}</td>
                        <td className="py-4 px-6 text-center">
                          {typeof row.acto === 'boolean' ? (
                            row.acto ? (
                              <div className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-green-100">
                                <Check className="w-4 h-4 text-green-600" />
                              </div>
                            ) : (
                              <div className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-red-50">
                                <X className="w-4 h-4 text-red-400" />
                              </div>
                            )
                          ) : (
                            <span className="text-sm font-semibold text-gray-900">{row.acto}</span>
                          )}
                        </td>
                        <td className="py-4 px-6 text-center">
                          {typeof row.traditional === 'boolean' ? (
                            row.traditional ? (
                              <div className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-green-50">
                                <Check className="w-4 h-4 text-green-500" />
                              </div>
                            ) : (
                              <div className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-red-50">
                                <X className="w-4 h-4 text-red-400" />
                              </div>
                            )
                          ) : (
                            <span className="text-sm text-gray-600">{row.traditional}</span>
                          )}
                        </td>
                        <td className="py-4 px-6 text-center">
                          {typeof row.blockchain === 'boolean' ? (
                            row.blockchain ? (
                              <div className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-green-50">
                                <Check className="w-4 h-4 text-green-500" />
                              </div>
                            ) : (
                              <div className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-red-50">
                                <X className="w-4 h-4 text-red-400" />
                              </div>
                            )
                          ) : (
                            <span className="text-sm text-gray-600">{row.blockchain}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ScrollAnimation>
          </div>
        </section>

        {/* Decision Guide */}
        <section className="py-20 md:py-28">
          <div className="max-w-4xl mx-auto px-4 md:px-6">
            <ScrollAnimation animation="blur-in" delay={0}>
              <h2 className="text-2xl md:text-3xl font-medium mb-12 tracking-tight text-gray-900 text-center">
                When to use what?
              </h2>
            </ScrollAnimation>

            <div className="space-y-4">
              <ScrollAnimation animation="blur-in" delay={60}>
                <div className="group bg-white border-2 border-gray-900 rounded-xl p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-gray-900 flex items-center justify-center flex-shrink-0 mt-1">
                      <Shield className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-3">Use ACTO when</h3>
                      <div className="grid sm:grid-cols-2 gap-x-8 gap-y-2">
                        {[
                          'Production systems need proof',
                          'Regulatory compliance required',
                          'Real-time verification critical',
                          'Independent verification needed',
                          'Reliable internet available',
                          'Web3/token model acceptable'
                        ].map((item, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm text-gray-600">
                            <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollAnimation>

              <ScrollAnimation animation="blur-in" delay={120}>
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1">
                      <Database className="w-5 h-5 text-gray-500" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-700 mb-3">Use Traditional Logging when</h3>
                      <div className="grid sm:grid-cols-2 gap-x-8 gap-y-2">
                        {[
                          'Development/testing phase',
                          'No compliance requirements',
                          'Internal use only',
                          'Trust is not a concern',
                          'Budget constraints exist',
                          'Quick prototyping needed'
                        ].map((item, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm text-gray-500">
                            <ChevronRight className="w-4 h-4 text-gray-300 flex-shrink-0" />
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollAnimation>

              <ScrollAnimation animation="blur-in" delay={180}>
                <div className="bg-stone-50 border border-stone-200 rounded-xl p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-stone-200 flex items-center justify-center flex-shrink-0 mt-1">
                      <Link2 className="w-5 h-5 text-stone-500" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-stone-700 mb-3">Use Blockchain when</h3>
                      <div className="grid sm:grid-cols-2 gap-x-8 gap-y-2">
                        {[
                          'Public auditability required',
                          'Decentralization is core',
                          'Cost/speed not concerns',
                          'Complex infra acceptable',
                          'Real-time not needed',
                          'Immutable history critical'
                        ].map((item, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm text-stone-500">
                            <ChevronRight className="w-4 h-4 text-stone-300 flex-shrink-0" />
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollAnimation>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 md:py-28 relative overflow-hidden">
          {/* Background Image */}
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat"
            style={{ backgroundImage: 'url(/bg1.png)' }}
          />
          {/* Dark Overlay */}
          <div className="absolute inset-0 bg-black/70" />
          
          <div className="relative max-w-3xl mx-auto px-4 md:px-6 text-center">
            <ScrollAnimation animation="blur-in" delay={0}>
              <h2 className="text-3xl md:text-4xl font-medium mb-6 tracking-tight text-white">
                Ready to verify?
              </h2>
              <p className="text-gray-300 mb-10 text-lg">
                Get started in minutes. No blockchain complexity.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a
                  href={config.links.docs}
                  className="group inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors"
                >
                  Read the Docs
                  <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </a>
                <a
                  href={config.links.dashboard}
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-white/30 text-white font-medium rounded-lg hover:bg-white/10 transition-colors"
                >
                  Get API Access
                </a>
              </div>
            </ScrollAnimation>
          </div>
        </section>
      </div>
    </>
  );
}
