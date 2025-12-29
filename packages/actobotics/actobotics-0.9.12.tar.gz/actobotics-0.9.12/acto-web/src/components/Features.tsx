import { ScrollAnimation } from './ScrollAnimation';

export function Features() {
  return (
    <section className="border-t border-gray-100">
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-32">
        <div className="grid md:grid-cols-3 gap-12 md:gap-16">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div>
              <p className="text-sm text-gray-400 mb-4">01</p>
              <h3 className="text-lg font-medium mb-3">Capture the moment</h3>
              <p className="text-gray-500 leading-relaxed">
                Every sensor reading. Every movement. Sealed with cryptographic signatures the moment it happens.
              </p>
            </div>
          </ScrollAnimation>
          <ScrollAnimation animation="blur-in" delay={80}>
            <div>
              <p className="text-sm text-gray-400 mb-4">02</p>
              <h3 className="text-lg font-medium mb-3">Trust no one</h3>
              <p className="text-gray-500 leading-relaxed">
                Verification that doesn't rely on the operator's word. Anyone can check. No one can fake it.
              </p>
            </div>
          </ScrollAnimation>
          <ScrollAnimation animation="blur-in" delay={160}>
            <div>
              <p className="text-sm text-gray-400 mb-4">03</p>
              <h3 className="text-lg font-medium mb-3">Built for Web3</h3>
              <p className="text-gray-500 leading-relaxed">
                Your wallet is your identity. Token-gated access for committed users. Decentralized trust for autonomous machines.
              </p>
            </div>
          </ScrollAnimation>
        </div>
      </div>
    </section>
  );
}
