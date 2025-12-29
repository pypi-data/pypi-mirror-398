import { Bot, Wind, Plane, Factory, FlaskConical, Activity, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ScrollAnimation } from './ScrollAnimation';

const useCases = [
  {
    icon: Bot,
    title: 'Robotics-as-a-Service',
    slug: 'robotics-as-a-service',
    description: 'Provide verifiable proof that your robots completed their assigned tasks. Enable trust in RaaS platforms with cryptographic execution records that customers can independently verify.'
  },
  {
    icon: Wind,
    title: 'Autonomous cleaning',
    slug: 'autonomous-cleaning',
    description: 'Document cleaning operations with tamper-proof evidence. Generate verifiable logs showing which areas were cleaned, when, and to what standard, ensuring accountability in automated facilities management.'
  },
  {
    icon: Plane,
    title: 'Drone inspections',
    slug: 'drone-inspections',
    description: 'Create immutable records of infrastructure inspections. Prove that drones followed approved flight paths, captured required imagery, and completed safety protocols without manual oversight.'
  },
  {
    icon: Factory,
    title: 'Industrial auditing',
    slug: 'industrial-auditing',
    description: 'Automate compliance verification with cryptographic audit trails. Demonstrate that automated systems performed required checks, measurements, and quality control procedures according to regulatory standards.'
  },
  {
    icon: FlaskConical,
    title: 'Research environments',
    slug: 'research-environments',
    description: 'Ensure reproducibility of automated experiments. Generate proofs that research robots executed protocols precisely as specified, enabling verification of experimental methodology and results.'
  },
  {
    icon: Activity,
    title: 'Simulation validation',
    slug: 'simulation-validation',
    description: 'Bridge the gap between simulation and reality. Prove that real-world robot behavior matches simulated models by comparing cryptographic proofs from both environments.'
  },
];

export function UseCases() {
  return (
    <section id="use-cases" className="border-t border-gray-100">
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-32">
        <ScrollAnimation animation="blur-in" delay={0}>
          <h2 className="text-2xl md:text-3xl font-medium mb-4 md:mb-6 tracking-tight">Use cases</h2>
          <p className="text-base md:text-lg text-gray-600 mb-12 md:mb-16 max-w-2xl">
            From industrial automation to research, proof of execution enables trust and accountability in autonomous systems across diverse applications.
          </p>
        </ScrollAnimation>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          {useCases.map((useCase, index) => {
            const Icon = useCase.icon;
            return (
              <ScrollAnimation key={useCase.title} animation="blur-in" delay={60 + index * 60} className="h-full">
                <Link 
                  to={`/use-cases/${useCase.slug}`}
                  className="group flex flex-col h-full border border-gray-200 rounded-xl p-6 hover:border-gray-300 hover:shadow-lg transition-all"
                >
                  <div className="mb-4 inline-flex items-center justify-center w-12 h-12 rounded-lg bg-gray-100 group-hover:bg-gray-900 transition-colors">
                    <Icon className="w-6 h-6 text-gray-900 group-hover:text-white transition-colors" />
                  </div>
                  <h3 className="text-lg font-medium mb-3 text-gray-900 flex items-center justify-between">
                    {useCase.title}
                    <ArrowUpRight size={18} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                  </h3>
                  <p className="text-gray-600 leading-relaxed flex-grow">{useCase.description}</p>
                </Link>
              </ScrollAnimation>
            );
          })}
        </div>
      </div>
    </section>
  );
}
