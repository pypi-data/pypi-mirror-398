import { ScrollAnimation } from './ScrollAnimation';

const steps = [
  {
    number: '01',
    title: 'Robot executes task',
    description: 'Physical operation in the real world.',
  },
  {
    number: '02',
    title: 'Data collection',
    description: 'Telemetry and logs captured during execution.',
  },
  {
    number: '03',
    title: 'Proof generation',
    description: 'Deterministic cryptographic proof created.',
  },
  {
    number: '04',
    title: 'Verification',
    description: 'Local or network-based proof verification.',
  },
];

export function HowItWorks() {
  return (
    <section>
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-32">
        <div className="grid md:grid-cols-2 gap-12 md:gap-24">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div>
              <h2 className="text-2xl md:text-3xl font-medium mb-4 md:mb-6 tracking-tight">How it works</h2>
              <p className="text-gray-500 leading-relaxed">
                Four steps from task execution to verifiable proof.
              </p>
            </div>
          </ScrollAnimation>
          <div className="space-y-8 md:space-y-10">
            {steps.map((step, index) => (
              <ScrollAnimation key={step.number} animation="blur-in" delay={60 + index * 60}>
                <div className="flex gap-4 md:gap-6">
                  <p className="text-sm text-gray-300 font-medium w-8 flex-shrink-0">{step.number}</p>
                  <div>
                    <p className="font-medium mb-1">{step.title}</p>
                    <p className="text-sm text-gray-500">{step.description}</p>
                  </div>
                </div>
              </ScrollAnimation>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
