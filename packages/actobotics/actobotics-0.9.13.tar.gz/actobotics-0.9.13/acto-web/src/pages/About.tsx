import { Shield, Zap, Eye, Lock, ArrowRight, CheckCircle2, AlertTriangle, TrendingUp, Bot, Factory, Truck, Plane } from 'lucide-react';
import { config } from '../config';
import { SEO } from '../components/SEO';
import { ScrollAnimation } from '../components/ScrollAnimation';
import { ParallaxSection } from '../components/ParallaxSection';
import { ImageWithSkeleton } from '../components/ImageWithSkeleton';

const timeline = [
  {
    year: '2024',
    title: 'The Idea',
    description: 'While working with autonomous systems, we realized: there\'s no standardized way to prove what a robot actually did.',
  },
  {
    year: '2024',
    title: 'First Version',
    description: 'Ed25519-based signatures, Python SDK, local proof generation. The foundation for verifiable autonomy.',
  },
  {
    year: '2025',
    title: 'Ecosystem Launch',
    description: 'Hosted API, dashboard, fleet management. From a tool to a platform for the entire robotics industry.',
  },
  {
    year: 'Soon',
    title: 'What\'s Next',
    description: 'ROS 2 integration, enhanced fleet analytics, enterprise features. The infrastructure for the autonomous future.',
  },
];

const useCases = [
  { icon: Truck, label: 'Delivery Robots', description: 'Proof of route, delivery, and handling' },
  { icon: Factory, label: 'Industrial Automation', description: 'Compliance records for production processes' },
  { icon: Bot, label: 'Service Robots', description: 'Documentation of every customer interaction' },
  { icon: Plane, label: 'Drones', description: 'Flight path verification and inspection reports' },
];

export function About() {
  return (
    <>
      <SEO
        title="About ACTO"
        description="ACTO is the infrastructure for verifiable autonomy. We enable autonomous systems to cryptographically prove what they did – independently, tamper-proof, in real-time."
        url="https://actobotics.net/about"
      />
      <div className="min-h-screen">
        {/* Hero Section */}
      <section className="min-h-screen flex items-center relative">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: 'url(/hero2.png)' }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-black/70" />
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-20 md:py-32 relative z-10">
          <p className="text-sm text-gray-300 mb-6 md:mb-8 tracking-wide uppercase">About ACTO</p>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-medium leading-[1.1] tracking-tight mb-8 max-w-4xl text-white">
            Machines do what they want.<br />
            <span className="text-gray-400">We make them prove it.</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-300 max-w-2xl leading-relaxed">
            ACTO is the infrastructure for verifiable autonomy. We enable autonomous systems to 
            cryptographically prove what they did – independently, tamper-proof, in real-time.
          </p>
        </div>
      </section>

      {/* The Problem */}
      <section className="py-16 md:py-24">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center">
            <div>
              <ScrollAnimation animation="blur-in" delay={0}>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 text-red-600 text-sm font-medium mb-6">
                  <AlertTriangle size={14} />
                  The Problem
                </div>
              </ScrollAnimation>
              <ScrollAnimation animation="blur-in" delay={60}>
                <h2 className="text-3xl md:text-4xl font-medium mb-6 tracking-tight">
                  Trust is good.<br />But what if you can't trust?
                </h2>
              </ScrollAnimation>
              <ScrollAnimation animation="blur-in" delay={120}>
                <div className="space-y-4 text-gray-600 leading-relaxed">
                  <p>
                    Autonomous systems are everywhere: delivery robots, production lines, drones, 
                    self-driving vehicles. They make millions of decisions – without human oversight.
                  </p>
                  <p>
                    <strong className="text-gray-900">The problem:</strong> How do we know they're doing 
                    what they should? Logs can be manipulated. Sensor data can be missing. 
                    The operator says "It worked" – but did it really?
                  </p>
                  <p>
                    In regulated industries, insurance claims, liability cases – 
                    "Trust me" is not an answer.
                  </p>
                </div>
              </ScrollAnimation>
            </div>
            <ScrollAnimation animation="blur-in" delay={180}>
              <div className="bg-gray-50 rounded-2xl p-8 md:p-10">
                <h3 className="text-lg font-medium mb-6 text-gray-900">Traditional approaches fail:</h3>
                <ul className="space-y-4">
                  <ScrollAnimation animation="blur-in" delay={240}>
                    <li className="flex gap-4">
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-100 flex items-center justify-center">
                        <span className="text-red-500 text-sm">✕</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">Centralized logs</p>
                        <p className="text-sm text-gray-500">Can be altered retroactively</p>
                      </div>
                    </li>
                  </ScrollAnimation>
                  <ScrollAnimation animation="blur-in" delay={300}>
                    <li className="flex gap-4">
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-100 flex items-center justify-center">
                        <span className="text-red-500 text-sm">✕</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">Manual verification</p>
                        <p className="text-sm text-gray-500">Doesn't scale with thousands of robots</p>
                      </div>
                    </li>
                  </ScrollAnimation>
                  <ScrollAnimation animation="blur-in" delay={360}>
                    <li className="flex gap-4">
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-100 flex items-center justify-center">
                        <span className="text-red-500 text-sm">✕</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">Camera surveillance</p>
                        <p className="text-sm text-gray-500">Privacy issues, storage costs, gaps</p>
                      </div>
                    </li>
                  </ScrollAnimation>
                  <ScrollAnimation animation="blur-in" delay={420}>
                    <li className="flex gap-4">
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-100 flex items-center justify-center">
                        <span className="text-red-500 text-sm">✕</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">Trusting the operator</p>
                        <p className="text-sm text-gray-500">No independent verification possible</p>
                      </div>
                    </li>
                  </ScrollAnimation>
                </ul>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* The Solution */}
      <section id="solution-section" className="py-16 md:py-24 relative overflow-hidden text-white">
        {/* Background Image with Parallax and Loading Skeleton */}
        <ParallaxSection speed={0.3} className="absolute inset-0">
          <ImageWithSkeleton 
            src="/code.png" 
            className="absolute inset-0"
            skeletonClassName="absolute inset-0"
          />
        </ParallaxSection>
        {/* Dark Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/85 via-black/80 to-black/85" />
        
        <div className="max-w-6xl mx-auto px-4 md:px-6 relative z-10">
          <div className="text-center mb-12 md:mb-16">
            <ScrollAnimation animation="blur-in" delay={0}>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-gray-300 text-sm font-medium mb-6">
                <CheckCircle2 size={14} />
                The Solution
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={60}>
              <h2 className="text-3xl md:text-4xl font-medium mb-6 tracking-tight">
                Cryptographic proofs.<br />Not words.
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto leading-relaxed">
                ACTO generates a cryptographic proof for every action of an autonomous system. 
                This proof is mathematically verifiable – by anyone, at any time.
              </p>
            </ScrollAnimation>
          </div>

          <div className="grid md:grid-cols-3 gap-6 md:gap-8">
            <ScrollAnimation animation="blur-in" delay={120}>
              <div className="group relative bg-black/50 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl hover:border-white/20 transition-all duration-300 overflow-hidden">
                <div className="relative z-10">
                  <div className="w-14 h-14 bg-gradient-to-br from-white/20 to-white/5 rounded-xl flex items-center justify-center mb-6 transition-transform duration-300">
                    <Lock size={26} className="text-white" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-xl font-medium mb-3 text-white">Ed25519 Signatures</h3>
                  <p className="text-gray-400 leading-relaxed">
                    Every proof is signed with the robot's private key. 
                    Forgery? Mathematically impossible.
                  </p>
                </div>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={200}>
              <div className="group relative bg-black/50 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl hover:border-white/20 transition-all duration-300 overflow-hidden">
                <div className="relative z-10">
                  <div className="w-14 h-14 bg-gradient-to-br from-white/20 to-white/5 rounded-xl flex items-center justify-center mb-6 transition-transform duration-300">
                    <Eye size={26} className="text-white" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-xl font-medium mb-3 text-white">Independent Verification</h3>
                  <p className="text-gray-400 leading-relaxed">
                    Anyone can verify a proof – without trusting the operator or us. 
                    Trustless by design.
                  </p>
                </div>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={280}>
              <div className="group relative bg-black/50 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl hover:border-white/20 transition-all duration-300 overflow-hidden">
                <div className="relative z-10">
                  <div className="w-14 h-14 bg-gradient-to-br from-white/20 to-white/5 rounded-xl flex items-center justify-center mb-6 transition-transform duration-300">
                    <Zap size={26} className="text-white" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-xl font-medium mb-3 text-white">Real-time Capable</h3>
                  <p className="text-gray-400 leading-relaxed">
                    Proof generation in milliseconds. Verification under 50ms. 
                    Built for the speed of autonomous systems.
                  </p>
                </div>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 md:py-24">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-12 tracking-tight">How it works</h2>
          </ScrollAnimation>
          <div className="grid md:grid-cols-4 gap-8">
            <ScrollAnimation animation="blur-in" delay={60}>
              <div className="relative">
                <div className="text-6xl font-light text-gray-200 mb-4">01</div>
                <h3 className="text-lg font-medium mb-2 text-gray-900">Capture telemetry</h3>
                <p className="text-gray-500 text-sm leading-relaxed">
                  The robot collects sensor data, movements, actions – everything that happens.
                </p>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <div className="relative">
                <div className="text-6xl font-light text-gray-200 mb-4">02</div>
                <h3 className="text-lg font-medium mb-2 text-gray-900">Sign locally</h3>
                <p className="text-gray-500 text-sm leading-relaxed">
                  The SDK creates a hash and signs it with the robot's private key.
                </p>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={180}>
              <div className="relative">
                <div className="text-6xl font-light text-gray-200 mb-4">03</div>
                <h3 className="text-lg font-medium mb-2 text-gray-900">Verify via API</h3>
                <p className="text-gray-500 text-sm leading-relaxed">
                  The proof is sent to the ACTO API and verified in under 50ms.
                </p>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={240}>
              <div className="relative">
                <div className="text-6xl font-light text-gray-200 mb-4">04</div>
                <h3 className="text-lg font-medium mb-2 text-gray-900">Store & retrieve</h3>
                <p className="text-gray-500 text-sm leading-relaxed">
                  Proofs are stored in the registry. Query by robot, task, or time range.
                </p>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section
        className="py-16 md:py-24 relative bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/bg2.png)' }}
      >
        {/* Gradient overlay - fades to white at top and bottom */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-white/30 to-white" />
        <div className="max-w-6xl mx-auto px-4 md:px-6 relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div className="text-center mb-12">
              <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight">Where ACTO could be used</h2>
              <p className="text-gray-500 max-w-xl mx-auto">
                Everywhere autonomous systems need to prove what they did.
              </p>
            </div>
          </ScrollAnimation>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {useCases.map((useCase, index) => {
              const Icon = useCase.icon;
              return (
                <ScrollAnimation key={useCase.label} animation="blur-in" delay={60 + index * 60}>
                  <div className="bg-white border border-gray-200 rounded-xl p-6 text-center hover:shadow-lg hover:border-gray-300 transition-all">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <Icon size={24} className="text-gray-700" />
                    </div>
                    <h3 className="font-medium text-gray-900 mb-2">{useCase.label}</h3>
                    <p className="text-sm text-gray-500">{useCase.description}</p>
                  </div>
                </ScrollAnimation>
              );
            })}
          </div>
        </div>
      </section>

      {/* Why Now */}
      <section className="py-16 md:py-24">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center">
            <div>
              <ScrollAnimation animation="blur-in" delay={0}>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-600 text-sm font-medium mb-6">
                  <TrendingUp size={14} />
                  Why Now
                </div>
              </ScrollAnimation>
              <ScrollAnimation animation="blur-in" delay={60}>
                <h2 className="text-3xl md:text-4xl font-medium mb-6 tracking-tight">
                  The autonomous revolution has begun.
                </h2>
              </ScrollAnimation>
              <ScrollAnimation animation="blur-in" delay={120}>
                <div className="space-y-4 text-gray-600 leading-relaxed">
                  <p>
                    By 2030, millions of autonomous robots will be deployed – in warehouses, 
                    on roads, in the air. The robotics market is growing over 20% annually.
                  </p>
                  <p>
                    <strong className="text-gray-900">But without verifiability, there's no trust.</strong> And 
                    without trust, no adoption in critical areas: healthcare, logistics, manufacturing.
                  </p>
                  <p>
                    ACTO is the infrastructure layer that closes this gap. We don't build 
                    robots – we build the trust they need.
                  </p>
                </div>
              </ScrollAnimation>
            </div>
            <div className="space-y-4">
              <ScrollAnimation animation="blur-in" delay={180}>
                <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
                  <p className="text-4xl font-medium text-gray-900 mb-2">$180B+</p>
                  <p className="text-gray-500">Expected robotics market by 2030</p>
                </div>
              </ScrollAnimation>
              <ScrollAnimation animation="blur-in" delay={240}>
                <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
                  <p className="text-4xl font-medium text-gray-900 mb-2">26%</p>
                  <p className="text-gray-500">Annual growth in autonomous systems</p>
                </div>
              </ScrollAnimation>
              <ScrollAnimation animation="blur-in" delay={300}>
                <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
                  <p className="text-4xl font-medium text-gray-900 mb-2">&lt;50ms</p>
                  <p className="text-gray-500">ACTO verification time</p>
                </div>
              </ScrollAnimation>
            </div>
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-16 md:py-24 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-12 tracking-tight">Our Journey</h2>
          </ScrollAnimation>
          <div className="grid md:grid-cols-4 gap-6">
            {timeline.map((item, index) => (
              <ScrollAnimation key={index} animation="blur-in" delay={60 + index * 80}>
                <div className="relative">
                  <div className="text-sm text-gray-400 mb-2 font-medium">{item.year}</div>
                  <h3 className="text-lg font-medium mb-2 text-gray-900">{item.title}</h3>
                  <p className="text-gray-500 text-sm leading-relaxed">{item.description}</p>
                </div>
              </ScrollAnimation>
            ))}
          </div>
        </div>
      </section>

      {/* Values & CTA */}
      <section
        className="relative bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/bg1.png)' }}
      >
        {/* Gradient overlay - fades from gray-50 at top */}
        <div className="absolute inset-0 bg-gradient-to-b from-gray-50 via-transparent to-black/60" />
        
        {/* What we stand for */}
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-24 relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-12 md:mb-16 tracking-tight">What we stand for</h2>
          </ScrollAnimation>
          <div className="grid md:grid-cols-2 gap-8 md:gap-12">
            <ScrollAnimation animation="blur-in" delay={60}>
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 rounded-lg bg-gray-900 flex items-center justify-center">
                    <Shield className="w-6 h-6 text-white" />
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium mb-2 text-gray-900">Cryptography over promises</h3>
                  <p className="text-gray-600 leading-relaxed">
                    Mathematical proofs are stronger than contracts. Our signatures cannot be forged, 
                    our proofs cannot be tampered with.
                  </p>
                </div>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={60}>
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 rounded-lg bg-gray-900 flex items-center justify-center">
                    <Eye className="w-6 h-6 text-white" />
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium mb-2 text-gray-900">Transparency through open source</h3>
                  <p className="text-gray-600 leading-relaxed">
                    Our SDK is fully open source. Anyone can review, understand, and improve the code. 
                    Trust requires transparency.
                  </p>
                </div>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 rounded-lg bg-gray-900 flex items-center justify-center">
                    <Zap className="w-6 h-6 text-white" />
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium mb-2 text-gray-900">Built for developers</h3>
                  <p className="text-gray-600 leading-relaxed">
                    One pip install, one API key, done. Integration in minutes, not weeks. 
                    Because good infrastructure is invisible.
                  </p>
                </div>
              </div>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <div className="flex gap-6">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 rounded-lg bg-gray-900 flex items-center justify-center">
                    <Lock className="w-6 h-6 text-white" />
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium mb-2 text-gray-900">Web3-native</h3>
                  <p className="text-gray-600 leading-relaxed">
                    Your wallet is your identity. Token-gated access ensures only committed users 
                    can use the platform. Connect with Phantom, Solflare, or other Solana wallets.
                  </p>
                </div>
              </div>
            </ScrollAnimation>
          </div>
        </div>

        {/* CTA */}
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-24 text-center relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-white">
              Ready for verifiable autonomy?
            </h2>
            <p className="text-lg text-white mb-8 max-w-2xl mx-auto">
              Start with the Python SDK or check out the documentation. 
              Questions? We're just a message away.
            </p>
          </ScrollAnimation>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <ScrollAnimation animation="blur-in" delay={120}>
              <a
                href={config.links.docs}
                className="group inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors"
              >
                Documentation
                <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
              </a>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <a
                href={config.links.dashboard}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/30 text-white font-medium rounded-lg hover:bg-white/10 transition-colors"
              >
                Open Dashboard
              </a>
            </ScrollAnimation>
          </div>
        </div>
      </section>
      </div>
    </>
  );
}
