import { useParams, Link } from 'react-router-dom';
import { Bot, Wind, Plane, Factory, FlaskConical, Activity, ArrowLeft, CheckCircle2, Shield, Zap, ArrowRight, Target, TrendingUp, Clock, MapPin, FileCheck, Microscope } from 'lucide-react';
import { SEO } from '../components/SEO';
import { ScrollAnimation } from '../components/ScrollAnimation';
import { config } from '../config';

// Hero image mapping for each use case
const heroImages: Record<string, string> = {
  'robotics-as-a-service': '/hero.png',
  'autonomous-cleaning': '/hero2.png',
  'drone-inspections': '/hero3.png',
  'industrial-auditing': '/hero4.png',
  'research-environments': '/hero.png',
  'simulation-validation': '/hero2.png',
};

const useCaseData: Record<string, {
  icon: any;
  title: string;
  tagline: string;
  description: string;
  challenge: string;
  solution: string;
  benefits: string[];
  features: { title: string; description: string; icon: any }[];
  example: { title: string; scenario: string; implementation: string };
  stats?: { value: string; label: string }[];
}> = {
  'robotics-as-a-service': {
    icon: Bot,
    title: 'Robotics-as-a-Service',
    tagline: 'Build trust in your RaaS platform with verifiable execution proofs',
    description: 'In the rapidly growing Robotics-as-a-Service market, trust is everything. Customers need to know that robots actually performed the tasks they paid for.',
    challenge: 'Traditional RaaS platforms rely on operator logs and self-reported metrics. Customers have no independent way to verify that tasks were completed as promised. This creates trust issues, disputes, and limits market growth.',
    solution: 'ACTO provides cryptographic proof of execution for every robot task. Each action is signed with the robot\'s private key, creating an immutable, independently verifiable record that customers can trust without relying on the operator.',
    benefits: [
      'Eliminate disputes with cryptographic proof of task completion',
      'Build customer trust with transparent, verifiable records',
      'Automate billing based on verified execution',
      'Enable pay-per-task models with confidence',
      'Reduce insurance costs with tamper-proof evidence',
      'Scale your platform with automated verification'
    ],
    features: [
      { title: 'Task Verification', description: 'Every task generates a signed proof with timestamps, location data, and execution parameters', icon: CheckCircle2 },
      { title: 'Customer Portal', description: 'Customers can independently verify proofs without trusting the operator', icon: Shield },
      { title: 'Real-time Tracking', description: 'Live proof generation and verification during task execution', icon: Zap }
    ],
    example: {
      title: 'Warehouse Picking Robot',
      scenario: 'A RaaS company operates picking robots in multiple warehouses. Customers pay per item picked.',
      implementation: 'Each pick operation generates a proof containing: item ID, timestamp, location, and robot signature. Customers verify proofs in real-time and are billed automatically based on verified picks. Disputes drop to near zero.'
    },
    stats: [
      { value: '99.7%', label: 'Dispute reduction' },
      { value: '3x', label: 'Faster billing' },
      { value: '40%', label: 'More customers' }
    ]
  },
  'autonomous-cleaning': {
    icon: Wind,
    title: 'Autonomous Cleaning',
    tagline: 'Prove cleaning operations with tamper-proof evidence',
    description: 'Automated cleaning robots need to demonstrate compliance with cleaning standards and schedules. Manual verification is expensive and doesn\'t scale.',
    challenge: 'Facility managers need proof that cleaning robots actually cleaned assigned areas to the required standard. Traditional logs can be manipulated, and manual spot-checks are time-consuming and incomplete.',
    solution: 'ACTO creates cryptographic proofs for each cleaning operation, including area covered, time spent, cleaning mode, and sensor readings. These proofs are immutable and independently verifiable.',
    benefits: [
      'Demonstrate compliance with cleaning standards',
      'Reduce manual inspection costs',
      'Provide evidence for health and safety audits',
      'Optimize cleaning schedules based on verified data',
      'Enable performance-based contracts',
      'Track cleaning quality over time'
    ],
    features: [
      { title: 'Area Coverage Proof', description: 'Cryptographic proof of which areas were cleaned and when', icon: CheckCircle2 },
      { title: 'Quality Metrics', description: 'Sensor data and cleaning parameters included in proofs', icon: Shield },
      { title: 'Compliance Reports', description: 'Automated generation of audit-ready compliance documentation', icon: Zap }
    ],
    example: {
      title: 'Hospital Floor Cleaning',
      scenario: 'A hospital uses autonomous cleaning robots for infection control. Strict cleaning schedules must be followed and documented.',
      implementation: 'Each cleaning cycle generates proofs with floor area, cleaning mode, disinfectant usage, and completion time. Health inspectors can verify compliance without manual checks. The hospital reduces infection rates and passes audits with cryptographic evidence.'
    }
  },
  'drone-inspections': {
    icon: Plane,
    title: 'Drone Inspections',
    tagline: 'Create immutable records of infrastructure inspections',
    description: 'Autonomous drones perform critical infrastructure inspections. Regulators and stakeholders need verifiable proof that inspections followed approved protocols.',
    challenge: 'Infrastructure owners must prove to regulators that inspections were completed according to specifications. Manual verification of flight paths and image capture is impractical. Liability concerns require bulletproof documentation.',
    solution: 'ACTO generates cryptographic proofs for every inspection flight, including GPS coordinates, altitude, images captured, and flight parameters. Proofs are tamper-proof and satisfy regulatory requirements.',
    benefits: [
      'Satisfy regulatory inspection requirements',
      'Reduce liability with verifiable documentation',
      'Automate compliance reporting',
      'Prove adherence to safety protocols',
      'Enable remote inspection verification',
      'Build stakeholder confidence'
    ],
    features: [
      { title: 'Flight Path Verification', description: 'Cryptographic proof of exact flight path and coverage', icon: CheckCircle2 },
      { title: 'Image Authentication', description: 'Prove images were captured at specific locations and times', icon: Shield },
      { title: 'Safety Compliance', description: 'Verify altitude limits, no-fly zones, and safety protocols', icon: Zap }
    ],
    example: {
      title: 'Bridge Inspection',
      scenario: 'A transportation authority uses drones to inspect bridge infrastructure. Regulators require proof that all critical areas were inspected.',
      implementation: 'Each inspection generates proofs with GPS coordinates, altitude, images captured, and inspection checklist completion. Regulators verify proofs remotely. The authority reduces inspection costs by 60% while improving compliance.'
    }
  },
  'industrial-auditing': {
    icon: Factory,
    title: 'Industrial Auditing',
    tagline: 'Automate compliance verification with cryptographic audit trails',
    description: 'Industrial facilities must demonstrate compliance with safety, quality, and environmental regulations. Automated systems need to prove they performed required checks.',
    challenge: 'Regulators require proof that automated quality control and safety systems actually performed required checks and measurements. Manual audit trails are expensive and prone to errors or manipulation.',
    solution: 'ACTO creates cryptographic proofs for every automated check, measurement, and quality control procedure. These proofs form an immutable audit trail that satisfies regulatory requirements.',
    benefits: [
      'Reduce audit preparation time and costs',
      'Eliminate manual audit trail creation',
      'Prove regulatory compliance automatically',
      'Enable real-time compliance monitoring',
      'Reduce risk of fines and shutdowns',
      'Improve quality control processes'
    ],
    features: [
      { title: 'Automated Audit Trails', description: 'Every check and measurement generates a cryptographic proof', icon: CheckCircle2 },
      { title: 'Regulatory Compliance', description: 'Proofs satisfy ISO, FDA, and other regulatory standards', icon: Shield },
      { title: 'Real-time Monitoring', description: 'Compliance officers can verify operations in real-time', icon: Zap }
    ],
    example: {
      title: 'Pharmaceutical Manufacturing',
      scenario: 'A pharmaceutical plant uses automated systems for quality control. FDA requires complete documentation of all quality checks.',
      implementation: 'Each quality control check generates a proof with measurement data, timestamps, and system signatures. FDA auditors verify proofs remotely. The plant passes audits with zero findings and reduces compliance costs by 40%.'
    }
  },
  'research-environments': {
    icon: FlaskConical,
    title: 'Research Environments',
    tagline: 'Ensure reproducibility of automated experiments',
    description: 'Research robots perform complex experiments that must be reproducible. The scientific community needs verifiable proof that protocols were followed exactly.',
    challenge: 'Reproducibility is a crisis in science. When robots perform experiments, researchers need to prove that protocols were executed precisely as specified. Traditional logs are insufficient for peer review and replication.',
    solution: 'ACTO generates cryptographic proofs of every experimental step, including parameters, timing, measurements, and environmental conditions. These proofs enable true reproducibility and satisfy peer review requirements.',
    benefits: [
      'Enable true experimental reproducibility',
      'Satisfy peer review requirements',
      'Prove protocol adherence',
      'Detect and prevent experimental errors',
      'Accelerate research validation',
      'Build confidence in automated research'
    ],
    features: [
      { title: 'Protocol Verification', description: 'Cryptographic proof that experimental protocols were followed exactly', icon: CheckCircle2 },
      { title: 'Data Integrity', description: 'Prove measurement data was collected without manipulation', icon: Shield },
      { title: 'Reproducibility', description: 'Enable other researchers to verify and replicate experiments', icon: Zap }
    ],
    example: {
      title: 'Drug Discovery Pipeline',
      scenario: 'A biotech company uses robotic systems for high-throughput screening. Regulatory approval requires proof of experimental integrity.',
      implementation: 'Each screening run generates proofs with compound IDs, concentrations, timing, and results. Regulators and peer reviewers verify proofs independently. The company accelerates FDA approval by 6 months with cryptographic evidence of experimental integrity.'
    }
  },
  'simulation-validation': {
    icon: Activity,
    title: 'Simulation Validation',
    tagline: 'Bridge the gap between simulation and reality',
    description: 'Robots are developed in simulation but must work in the real world. Proving that real-world behavior matches simulation is critical for safety and certification.',
    challenge: 'The sim-to-real gap is a major challenge in robotics. Developers need to prove that robots behave in the real world as they did in simulation. Manual comparison is impractical and subjective.',
    solution: 'ACTO generates cryptographic proofs from both simulated and real robots. These proofs can be compared mathematically to verify that real-world behavior matches simulation, enabling automated validation.',
    benefits: [
      'Automate sim-to-real validation',
      'Prove safety before real-world deployment',
      'Accelerate certification processes',
      'Detect behavioral differences early',
      'Enable continuous validation',
      'Reduce real-world testing costs'
    ],
    features: [
      { title: 'Behavior Comparison', description: 'Mathematically compare simulated and real-world proofs', icon: CheckCircle2 },
      { title: 'Safety Validation', description: 'Prove real-world behavior matches safe simulated behavior', icon: Shield },
      { title: 'Continuous Testing', description: 'Validate every deployment against simulation', icon: Zap }
    ],
    example: {
      title: 'Autonomous Vehicle Testing',
      scenario: 'An AV company tests vehicles in simulation before real-world deployment. Regulators require proof that real behavior matches simulation.',
      implementation: 'Both simulated and real vehicles generate proofs for identical scenarios. The company mathematically compares proofs to verify behavior matches. Regulators accept cryptographic proof of sim-to-real validation, accelerating certification.'
    }
  }
};

// Layout 1: Robotics-as-a-Service - Business/Stats focused
function RoboticsAsAServiceLayout({ useCase, slug }: { useCase: typeof useCaseData[string]; slug: string }) {
  const Icon = useCase.icon;
  return (
    <div className="min-h-screen">
      {/* Hero with Stats */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
        <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${heroImages[slug]})` }} />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-white" />
        
        <div className="max-w-6xl mx-auto px-4 md:px-6 relative z-10">
          <Link to="/#use-cases" className="inline-flex items-center gap-2 text-sm text-gray-300 hover:text-white mb-8 transition-colors">
            <ArrowLeft size={16} /> Back to Use Cases
          </Link>
          
          <div>
            <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center mb-6">
              <Icon className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-medium mb-6 tracking-tight text-white">{useCase.title}</h1>
            <p className="text-xl text-white/80 leading-relaxed max-w-2xl">{useCase.tagline}</p>
          </div>
        </div>
      </section>

      {/* Bento Grid Overview */}
      <section className="py-20 md:py-28">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <div className="grid md:grid-cols-3 gap-6">
            <ScrollAnimation animation="blur-in" delay={0} className="md:col-span-2">
              <div className="bg-gray-50 rounded-3xl p-8 h-full">
                <h2 className="text-2xl font-medium mb-4">The Opportunity</h2>
                <p className="text-gray-600 leading-relaxed text-lg">{useCase.description}</p>
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={100}>
              <div className="bg-black text-white rounded-3xl p-8 h-full flex flex-col justify-between">
                <Target className="w-10 h-10 mb-4 text-gray-400" />
                <div>
                  <h3 className="text-lg font-medium mb-2">Business Impact</h3>
                  <p className="text-gray-400 text-sm">Transform your RaaS platform with verifiable trust</p>
                </div>
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={150} className="h-full">
              <div className="bg-gray-100 border border-gray-200 rounded-3xl p-8 h-full flex flex-col">
                <h3 className="text-lg font-medium mb-3 text-gray-900">Challenge</h3>
                <p className="text-gray-600 text-sm leading-relaxed flex-grow">{useCase.challenge}</p>
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={200} className="md:col-span-2 h-full">
              <div className="bg-black text-white rounded-3xl p-8 h-full flex flex-col">
                <h3 className="text-lg font-medium mb-3">ACTO Solution</h3>
                <p className="text-gray-300 leading-relaxed flex-grow">{useCase.solution}</p>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Features as Cards */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-3xl font-medium mb-4 tracking-tight text-center">How It Works</h2>
            <p className="text-gray-500 text-center mb-12 max-w-2xl mx-auto">Three key capabilities that power your RaaS verification</p>
          </ScrollAnimation>
          
          <div className="grid md:grid-cols-3 gap-8">
            {useCase.features.map((feature, i) => {
              const FeatureIcon = feature.icon;
              const bgImages = ['/bg1.png', '/bg2.png', '/bg3.png'];
              return (
                <ScrollAnimation key={i} animation="blur-in" delay={100 + i * 100} className="h-full">
                  <div className="relative rounded-2xl p-8 h-full border border-gray-200 hover:shadow-xl transition-shadow overflow-hidden">
                    <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${bgImages[i]})` }} />
                    <div className="absolute inset-0 bg-white/70" />
                    <div className="relative z-10">
                      <div className="w-14 h-14 bg-black rounded-xl flex items-center justify-center mb-6">
                        <FeatureIcon className="w-7 h-7 text-white" />
                      </div>
                      <h3 className="text-xl font-medium mb-3">{feature.title}</h3>
                      <p className="text-gray-500 leading-relaxed">{feature.description}</p>
                    </div>
                  </div>
                </ScrollAnimation>
              );
            })}
          </div>
        </div>
      </section>

      {/* Benefits List */}
      <section className="py-20 md:py-28">
        <div className="max-w-4xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-3xl font-medium mb-12 tracking-tight">Why RaaS Companies Choose ACTO</h2>
          </ScrollAnimation>
          
          <div className="space-y-4">
            {useCase.benefits.map((benefit, i) => (
              <ScrollAnimation key={i} animation="blur-in" delay={60 + i * 40}>
                <div className="flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors group">
                  <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0 group-hover:bg-gray-200 transition-colors">
                    <CheckCircle2 size={18} className="text-gray-700" />
                  </div>
                  <p className="text-gray-700 text-lg">{benefit}</p>
                </div>
              </ScrollAnimation>
            ))}
          </div>
        </div>
      </section>

      {/* Case Study & CTA with background image and fade */}
      <section className="relative bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg1.png)' }}>
        {/* Gradient overlay - fades from white at top to dark at bottom */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-transparent to-black/70" />
        
        {/* Case Study */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-20 md:py-28 relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div className="text-sm font-mono text-gray-500 mb-4 text-center">CASE STUDY</div>
            <h2 className="text-3xl font-medium mb-8 text-center text-gray-900">{useCase.example.title}</h2>
            <p className="text-gray-600 text-lg mb-8 text-center">{useCase.example.scenario}</p>
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 text-left border border-gray-200 shadow-lg">
              <p className="text-gray-700 leading-relaxed">{useCase.example.implementation}</p>
            </div>
          </ScrollAnimation>
        </div>

        {/* CTA */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-16 md:py-24 text-center relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-white">
              Ready to get started?
            </h2>
            <p className="text-lg text-gray-200 mb-8 max-w-2xl mx-auto">
              Start building verifiable execution proofs for your autonomous systems today.
            </p>
          </ScrollAnimation>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <ScrollAnimation animation="blur-in" delay={60}>
              <a
                href={config.links.docs}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors"
              >
                Read Documentation
              </a>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <a
                href={config.links.dashboard}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/30 text-white font-medium rounded-lg hover:bg-white/10 transition-colors"
              >
                Get API Key
              </a>
            </ScrollAnimation>
          </div>
        </div>
      </section>
    </div>
  );
}

// Layout 2: Autonomous Cleaning - Clean/Checklist style
function AutonomousCleaningLayout({ useCase, slug }: { useCase: typeof useCaseData[string]; slug: string }) {
  const Icon = useCase.icon;
  return (
    <div className="min-h-screen bg-white">
      {/* Clean Hero */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
        <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${heroImages[slug]})` }} />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-white" />
        
        <div className="max-w-5xl mx-auto px-4 md:px-6 relative z-10 text-center">
          <Link to="/#use-cases" className="inline-flex items-center gap-2 text-sm text-gray-300 hover:text-white mb-8 transition-colors">
            <ArrowLeft size={16} /> Back to Use Cases
          </Link>
          
          <div className="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-3xl flex items-center justify-center mx-auto mb-8">
            <Icon className="w-10 h-10 text-white" />
          </div>
          
          <h1 className="text-4xl md:text-6xl font-light mb-6 tracking-tight text-white">
            {useCase.title.split(' ')[0]} <span className="font-medium">{useCase.title.split(' ').slice(1).join(' ')}</span>
          </h1>
          <p className="text-xl text-gray-200 max-w-2xl mx-auto">{useCase.tagline}</p>
        </div>
      </section>

      {/* Checklist Style Benefits */}
      <section className="py-20 md:py-28">
        <div className="max-w-5xl mx-auto px-4 md:px-6">
          <div className="grid lg:grid-cols-2 gap-16">
            <ScrollAnimation animation="blur-in" delay={0}>
              <h2 className="text-3xl font-medium mb-6 tracking-tight">Verified clean, every time</h2>
              <p className="text-gray-600 leading-relaxed mb-8">{useCase.description}</p>
              
              <div className="space-y-3">
                {useCase.benefits.slice(0, 4).map((benefit, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-md bg-gray-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <CheckCircle2 size={14} className="text-gray-700" />
                    </div>
                    <p className="text-gray-700">{benefit}</p>
                  </div>
                ))}
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={200}>
              <div className="bg-gray-50 rounded-3xl p-8 border border-gray-100">
                <h3 className="text-lg font-medium mb-4 text-gray-900">What gets proven</h3>
                <div className="space-y-4">
                  {['Floor area covered', 'Cleaning duration', 'Disinfectant levels', 'Sensor readings', 'Completion timestamp'].map((item, i) => (
                    <div key={i} className="flex items-center gap-3 text-gray-700">
                      <div className="w-2 h-2 rounded-full bg-gray-400" />
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Challenge & Solution Side by Side */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 md:px-6">
          <div className="grid md:grid-cols-2 gap-8">
            <ScrollAnimation animation="blur-in" delay={0}>
              <div className="bg-white rounded-2xl p-8 h-full border border-gray-200">
                <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center mb-4">
                  <span className="text-gray-600 font-bold">!</span>
                </div>
                <h3 className="text-xl font-medium mb-4 text-gray-900">The Problem</h3>
                <p className="text-gray-600 leading-relaxed">{useCase.challenge}</p>
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={100}>
              <div className="bg-black text-white rounded-2xl p-8 h-full">
                <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center mb-4">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-medium mb-4">The Solution</h3>
                <p className="text-gray-300 leading-relaxed">{useCase.solution}</p>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Features Horizontal */}
      <section className="py-20 md:py-28">
        <div className="max-w-5xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-3xl font-medium mb-12 tracking-tight text-center">Key Capabilities</h2>
          </ScrollAnimation>
          
          <div className="space-y-6">
            {useCase.features.map((feature, i) => {
              const FeatureIcon = feature.icon;
              // Background images for each feature box
              const bgImages = ['/bg2.png', '/bg3.png', '/bg4.png'];
              return (
                <ScrollAnimation key={i} animation="blur-in" delay={60 + i * 60}>
                  <div className="relative flex items-center gap-6 p-6 rounded-2xl overflow-hidden group">
                    {/* Background image */}
                    <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${bgImages[i]})` }} />
                    <div className="absolute inset-0 bg-white/80" />
                    {/* Content */}
                    <div className="relative z-10 w-16 h-16 bg-white rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm group-hover:shadow-md transition-shadow">
                      <FeatureIcon size={28} className="text-gray-700" />
                    </div>
                    <div className="relative z-10 flex-1">
                      <h3 className="text-lg font-medium mb-1">{feature.title}</h3>
                      <p className="text-gray-500">{feature.description}</p>
                    </div>
                  </div>
                </ScrollAnimation>
              );
            })}
          </div>
        </div>
      </section>

      {/* Example & CTA with background image and fade */}
      <section className="relative bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg2.png)' }}>
        {/* Gradient overlay - fades from white at top to dark at bottom */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-transparent to-black/70" />
        
        {/* Success Story */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-20 md:py-28 relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div className="text-gray-500 text-sm font-medium mb-4 text-center">SUCCESS STORY</div>
            <h2 className="text-3xl font-medium mb-8 text-center text-gray-900">{useCase.example.title}</h2>
            <p className="text-gray-600 text-lg leading-relaxed mb-8 text-center">{useCase.example.scenario}</p>
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 text-left border border-gray-200 shadow-lg">
              <p className="text-gray-700 leading-relaxed">{useCase.example.implementation}</p>
            </div>
          </ScrollAnimation>
        </div>

        {/* CTA */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-16 md:py-24 text-center relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-white">
              Ready to get started?
            </h2>
            <p className="text-lg text-gray-200 mb-8 max-w-2xl mx-auto">
              Start building verifiable execution proofs for your autonomous systems today.
            </p>
          </ScrollAnimation>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <ScrollAnimation animation="blur-in" delay={60}>
              <a
                href={config.links.docs}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors"
              >
                Read Documentation
              </a>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <a
                href={config.links.dashboard}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/30 text-white font-medium rounded-lg hover:bg-white/10 transition-colors"
              >
                Get API Key
              </a>
            </ScrollAnimation>
          </div>
        </div>
      </section>
    </div>
  );
}

// Layout 3: Drone Inspections - Technical/Data style
function DroneInspectionsLayout({ useCase, slug }: { useCase: typeof useCaseData[string]; slug: string }) {
  const Icon = useCase.icon;
  return (
    <div className="min-h-screen">
      {/* Tech Hero */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
        <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${heroImages[slug]})` }} />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-white" />
        
        <div className="max-w-6xl mx-auto px-4 md:px-6 relative z-10">
          <Link to="/#use-cases" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-8 transition-colors">
            <ArrowLeft size={16} /> Back to Use Cases
          </Link>
          
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center">
                <Icon className="w-6 h-6 text-gray-900" />
              </div>
              <span className="text-gray-400 font-mono text-sm">AERIAL VERIFICATION</span>
            </div>
            
            <h1 className="text-4xl md:text-5xl font-medium mb-6 tracking-tight text-white">{useCase.title}</h1>
            <p className="text-xl text-gray-300 max-w-2xl">{useCase.tagline}</p>
          </div>
        </div>
      </section>

      {/* Data Points */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-3xl font-medium mb-4 tracking-tight">What Gets Verified</h2>
            <p className="text-gray-500 mb-12 max-w-2xl">{useCase.description}</p>
          </ScrollAnimation>
          
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { icon: MapPin, label: 'Flight Path', value: 'GPS Coordinates', bg: '/bg1.png' },
              { icon: TrendingUp, label: 'Altitude', value: 'Real-time tracking', bg: '/bg2.png' },
              { icon: Clock, label: 'Timestamps', value: 'Sub-second precision', bg: '/bg3.png' },
              { icon: FileCheck, label: 'Protocol', value: 'Checklist completion', bg: '/bg4.png' }
            ].map((item, i) => (
              <ScrollAnimation key={i} animation="blur-in" delay={100 + i * 50}>
                <div className="relative rounded-xl p-6 border border-gray-200 text-center overflow-hidden">
                  <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${item.bg})` }} />
                  <div className="absolute inset-0 bg-white/70" />
                  <div className="relative z-10">
                    <item.icon className="w-8 h-8 text-gray-700 mx-auto mb-3" />
                    <div className="font-medium text-gray-900">{item.label}</div>
                    <div className="text-sm text-gray-500">{item.value}</div>
                  </div>
                </div>
              </ScrollAnimation>
            ))}
          </div>
        </div>
      </section>

      {/* Challenge Solution Split */}
      <section className="py-20 md:py-28">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <div className="grid lg:grid-cols-2 gap-12">
            <ScrollAnimation animation="blur-in" delay={0}>
              <div className="sticky top-32">
                <h2 className="text-3xl font-medium mb-6 tracking-tight">From Manual to Automated</h2>
                <div className="bg-gray-100 border-l-4 border-gray-400 rounded-r-xl p-6 mb-6">
                  <h3 className="font-medium text-gray-900 mb-2">Manual Verification</h3>
                  <p className="text-gray-600 text-sm">{useCase.challenge}</p>
                </div>
                <div className="bg-black border-l-4 border-white rounded-r-xl p-6">
                  <h3 className="font-medium text-white mb-2">ACTO Verification</h3>
                  <p className="text-gray-300 text-sm">{useCase.solution}</p>
                </div>
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={200}>
              <h3 className="text-xl font-medium mb-6">Key Benefits</h3>
              <div className="space-y-4">
                {useCase.benefits.map((benefit, i) => (
                  <div key={i} className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl">
                    <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                      <span className="text-gray-700 font-bold text-xs">{i + 1}</span>
                    </div>
                    <p className="text-gray-700">{benefit}</p>
                  </div>
                ))}
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Example & CTA with background image and fade */}
      <section className="relative bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg3.png)' }}>
        {/* Gradient overlay - fades from white at top to dark at bottom */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-transparent to-black/70" />
        
        {/* Real-World Implementation */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-20 md:py-28 relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div className="font-mono text-gray-500 text-sm mb-4 text-center">// REAL-WORLD IMPLEMENTATION</div>
            <h2 className="text-3xl font-medium mb-8 text-center text-gray-900">{useCase.example.title}</h2>
            
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 font-mono text-sm border border-gray-200 shadow-lg">
              <div className="text-gray-500 mb-4">// Scenario</div>
              <p className="text-gray-700 mb-6">{useCase.example.scenario}</p>
              <div className="text-gray-500 mb-4">// Implementation</div>
              <p className="text-gray-700">{useCase.example.implementation}</p>
            </div>
          </ScrollAnimation>
        </div>

        {/* CTA */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-16 md:py-24 text-center relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-white">
              Ready to get started?
            </h2>
            <p className="text-lg text-gray-200 mb-8 max-w-2xl mx-auto">
              Start building verifiable execution proofs for your autonomous systems today.
            </p>
          </ScrollAnimation>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <ScrollAnimation animation="blur-in" delay={60}>
              <a
                href={config.links.docs}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors"
              >
                Read Documentation
              </a>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <a
                href={config.links.dashboard}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/30 text-white font-medium rounded-lg hover:bg-white/10 transition-colors"
              >
                Get API Key
              </a>
            </ScrollAnimation>
          </div>
        </div>
      </section>
    </div>
  );
}

// Layout 4: Industrial Auditing - Corporate/Process style
function IndustrialAuditingLayout({ useCase, slug }: { useCase: typeof useCaseData[string]; slug: string }) {
  const Icon = useCase.icon;
  return (
    <div className="min-h-screen">
      {/* Corporate Hero */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
        <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${heroImages[slug]})` }} />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-white" />
        
        <div className="max-w-5xl mx-auto px-4 md:px-6 relative z-10">
          <Link to="/#use-cases" className="inline-flex items-center gap-2 text-sm text-gray-300 hover:text-white mb-8 transition-colors">
            <ArrowLeft size={16} /> Back to Use Cases
          </Link>
          
          <div className="flex items-center gap-4 mb-8">
            <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center">
              <Icon className="w-8 h-8 text-white" />
            </div>
            <div>
              <div className="text-gray-300 text-sm font-medium mb-1">COMPLIANCE AUTOMATION</div>
              <h1 className="text-4xl md:text-5xl font-medium tracking-tight text-white">{useCase.title}</h1>
            </div>
          </div>
          <p className="text-xl text-gray-200 max-w-3xl">{useCase.tagline}</p>
        </div>
      </section>

      {/* Compliance Badges */}
      <section className="py-12 border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-4 md:px-6">
          <div className="flex flex-wrap items-center justify-center gap-8">
            {['ISO 9001', 'FDA 21 CFR', 'SOC 2', 'GDPR'].map((cert, i) => (
              <ScrollAnimation key={i} animation="blur-in" delay={i * 50}>
                <div className="flex items-center gap-2 text-gray-500">
                  <Shield className="w-4 h-4" />
                  <span className="font-medium">{cert}</span>
                </div>
              </ScrollAnimation>
            ))}
          </div>
        </div>
      </section>

      {/* Overview */}
      <section className="py-20 md:py-28">
        <div className="max-w-5xl mx-auto px-4 md:px-6">
          <div className="grid lg:grid-cols-3 gap-8">
            <ScrollAnimation animation="blur-in" delay={0} className="lg:col-span-2">
              <h2 className="text-3xl font-medium mb-6 tracking-tight">Automated Compliance, Real Results</h2>
              <p className="text-gray-600 leading-relaxed text-lg mb-8">{useCase.description}</p>
              <p className="text-gray-600 leading-relaxed">{useCase.solution}</p>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={200}>
              <div className="relative border border-gray-200 rounded-2xl p-6 overflow-hidden">
                {/* Background image */}
                <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg4.png)' }} />
                <div className="absolute inset-0 bg-white/80" />
                {/* Content */}
                <div className="relative z-10">
                  <h3 className="font-medium text-gray-900 mb-4">The Challenge</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{useCase.challenge}</p>
                </div>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Features as Process */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-3xl font-medium mb-12 tracking-tight text-center">The Audit-Ready Process</h2>
          </ScrollAnimation>
          
          <div className="relative">
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-300 hidden md:block" />
            
            {useCase.features.map((feature, i) => {
              const FeatureIcon = feature.icon;
              return (
                <ScrollAnimation key={i} animation="blur-in" delay={100 + i * 100}>
                  <div className={`flex items-center gap-8 mb-12 ${i % 2 === 1 ? 'md:flex-row-reverse' : ''}`}>
                    <div className={`flex-1 ${i % 2 === 1 ? 'md:text-right' : ''}`}>
                      <h3 className="text-xl font-medium mb-2">{feature.title}</h3>
                      <p className="text-gray-500">{feature.description}</p>
                    </div>
                    <div className="w-14 h-14 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0 border-4 border-white shadow-lg relative z-10">
                      <FeatureIcon className="w-6 h-6 text-gray-700" />
                    </div>
                    <div className="flex-1 hidden md:block" />
                  </div>
                </ScrollAnimation>
              );
            })}
          </div>
        </div>
      </section>

      {/* Example & CTA with background image and fade */}
      <section className="relative bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg4.png)' }}>
        {/* Gradient overlay - fades from gray-50 at top to dark at bottom for seamless transition */}
        <div className="absolute inset-0 bg-gradient-to-b from-gray-50 via-transparent to-black/70" />
        
        {/* Case Study */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-20 md:py-28 relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div className="text-gray-500 text-sm font-medium mb-4 uppercase tracking-wider text-center">Case Study</div>
            <h2 className="text-3xl font-medium mb-8 text-center text-gray-900">{useCase.example.title}</h2>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-gray-200 shadow-lg">
                <h4 className="text-gray-500 text-sm font-medium mb-2">Scenario</h4>
                <p className="text-gray-700">{useCase.example.scenario}</p>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-gray-200 shadow-lg">
                <h4 className="text-gray-500 text-sm font-medium mb-2">Results</h4>
                <p className="text-gray-700">{useCase.example.implementation}</p>
              </div>
            </div>
          </ScrollAnimation>
        </div>

        {/* CTA */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-16 md:py-24 text-center relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-white">
              Ready to get started?
            </h2>
            <p className="text-lg text-gray-200 mb-8 max-w-2xl mx-auto">
              Start building verifiable execution proofs for your autonomous systems today.
            </p>
          </ScrollAnimation>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <ScrollAnimation animation="blur-in" delay={60}>
              <a
                href={config.links.docs}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors"
              >
                Read Documentation
              </a>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <a
                href={config.links.dashboard}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/30 text-white font-medium rounded-lg hover:bg-white/10 transition-colors"
              >
                Get API Key
              </a>
            </ScrollAnimation>
          </div>
        </div>
      </section>
    </div>
  );
}

// Layout 5: Research Environments - Academic style
function ResearchEnvironmentsLayout({ useCase, slug }: { useCase: typeof useCaseData[string]; slug: string }) {
  return (
    <div className="min-h-screen">
      {/* Academic Hero */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
        <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${heroImages[slug]})` }} />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-white" />
        
        <div className="max-w-4xl mx-auto px-4 md:px-6 relative z-10 text-center">
          <Link to="/#use-cases" className="inline-flex items-center gap-2 text-sm text-gray-300 hover:text-white mb-8 transition-colors">
            <ArrowLeft size={16} /> Back to Use Cases
          </Link>
          
          <h1 className="text-4xl md:text-5xl font-light mb-6 tracking-tight text-white">
            {useCase.title}
          </h1>
          <p className="text-xl text-gray-200 max-w-2xl mx-auto">{useCase.tagline}</p>
        </div>
      </section>

      {/* Abstract Style */}
      <section className="py-20 md:py-28">
        <div className="max-w-4xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div className="border-l-4 border-gray-900 pl-8 mb-12">
              <h2 className="text-sm font-medium text-gray-500 mb-2 uppercase tracking-wider">Abstract</h2>
              <p className="text-xl text-gray-700 leading-relaxed">{useCase.description}</p>
            </div>
          </ScrollAnimation>
          
          <div className="grid md:grid-cols-2 gap-12">
            <ScrollAnimation animation="blur-in" delay={100}>
              <div>
                <Microscope className="w-8 h-8 text-gray-700 mb-4" />
                <h3 className="text-lg font-medium mb-3">The Reproducibility Crisis</h3>
                <p className="text-gray-600 leading-relaxed">{useCase.challenge}</p>
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={200}>
              <div>
                <Shield className="w-8 h-8 text-gray-700 mb-4" />
                <h3 className="text-lg font-medium mb-3">Cryptographic Solution</h3>
                <p className="text-gray-600 leading-relaxed">{useCase.solution}</p>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Methods */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl font-medium mb-2">Methods</h2>
            <p className="text-gray-500 mb-12">How ACTO enables reproducible research</p>
          </ScrollAnimation>
          
          <div className="space-y-8">
            {useCase.features.map((feature, i) => {
              const FeatureIcon = feature.icon;
              // Background images for each method box
              const bgImages = ['/bg1.png', '/bg2.png', '/bg4.png'];
              return (
                <ScrollAnimation key={i} animation="blur-in" delay={100 + i * 100}>
                  <div className="relative rounded-xl p-8 shadow-sm border border-gray-100 overflow-hidden">
                    {/* Background image */}
                    <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${bgImages[i]})` }} />
                    <div className="absolute inset-0 bg-white/80" />
                    {/* Content */}
                    <div className="relative z-10 flex items-start gap-6">
                      <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm">
                        <FeatureIcon className="w-6 h-6 text-gray-700" />
                      </div>
                      <div>
                        <h3 className="text-xl font-medium mb-2">{feature.title}</h3>
                        <p className="text-gray-600">{feature.description}</p>
                      </div>
                    </div>
                  </div>
                </ScrollAnimation>
              );
            })}
          </div>
        </div>
      </section>

      {/* Results/Benefits */}
      <section className="py-20 md:py-28">
        <div className="max-w-4xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl font-medium mb-2">Results & Impact</h2>
            <p className="text-gray-500 mb-12">Measured benefits for research institutions</p>
          </ScrollAnimation>
          
          <div className="grid md:grid-cols-2 gap-4">
            {useCase.benefits.map((benefit, i) => (
              <ScrollAnimation key={i} animation="blur-in" delay={60 + i * 40}>
                <div className="flex items-start gap-3 p-4 border-l-2 border-gray-200 hover:border-gray-900 transition-colors bg-gray-50">
                  <CheckCircle2 size={18} className="text-gray-700 flex-shrink-0 mt-0.5" />
                  <p className="text-gray-700 text-sm">{benefit}</p>
                </div>
              </ScrollAnimation>
            ))}
          </div>
        </div>
      </section>

      {/* Example & CTA with background image and fade */}
      <section className="relative bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg1.png)' }}>
        {/* Gradient overlay - fades from white at top to dark at bottom */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-transparent to-black/70" />
        
        {/* Case Study */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-20 md:py-28 relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl font-medium mb-2 text-center text-gray-900">Case Study</h2>
            <h3 className="text-xl text-gray-600 mb-8 text-center">{useCase.example.title}</h3>
            
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 space-y-6 border border-gray-200 shadow-lg">
              <div>
                <h4 className="text-gray-500 text-sm font-medium mb-2">Background</h4>
                <p className="text-gray-700">{useCase.example.scenario}</p>
              </div>
              <div>
                <h4 className="text-gray-500 text-sm font-medium mb-2">Implementation & Outcomes</h4>
                <p className="text-gray-700">{useCase.example.implementation}</p>
              </div>
            </div>
          </ScrollAnimation>
        </div>

        {/* CTA */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-16 md:py-24 text-center relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-white">
              Ready to get started?
            </h2>
            <p className="text-lg text-gray-200 mb-8 max-w-2xl mx-auto">
              Start building verifiable execution proofs for your autonomous systems today.
            </p>
          </ScrollAnimation>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <ScrollAnimation animation="blur-in" delay={60}>
              <a
                href={config.links.docs}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors"
              >
                Read Documentation
              </a>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <a
                href={config.links.dashboard}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/30 text-white font-medium rounded-lg hover:bg-white/10 transition-colors"
              >
                Get API Key
              </a>
            </ScrollAnimation>
          </div>
        </div>
      </section>
    </div>
  );
}

// Layout 6: Simulation Validation - Comparison style
function SimulationValidationLayout({ useCase, slug }: { useCase: typeof useCaseData[string]; slug: string }) {
  return (
    <div className="min-h-screen">
      {/* Futuristic Hero */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
        <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${heroImages[slug]})` }} />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-white" />
        
        <div className="max-w-6xl mx-auto px-4 md:px-6 relative z-10">
          <Link to="/#use-cases" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-8 transition-colors">
            <ArrowLeft size={16} /> Back to Use Cases
          </Link>
          
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-medium mb-6 tracking-tight text-white">{useCase.title}</h1>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">{useCase.tagline}</p>
          </div>
        </div>
      </section>

      {/* Comparison Visual */}
      <section className="py-20 md:py-28">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-3xl font-medium mb-4 tracking-tight text-center">Bridging the Gap</h2>
            <p className="text-gray-500 text-center mb-12 max-w-2xl mx-auto">{useCase.description}</p>
          </ScrollAnimation>
          
          <div className="grid lg:grid-cols-3 gap-8 items-stretch">
            <ScrollAnimation animation="blur-in" delay={100} className="h-full">
              <div className="bg-gray-100 rounded-2xl p-8 h-full flex flex-col">
                <h3 className="text-lg font-medium mb-4">The Challenge</h3>
                <p className="text-gray-600 text-sm leading-relaxed flex-grow">{useCase.challenge}</p>
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={200} className="h-full">
              <div className="bg-black text-white rounded-2xl p-8 h-full flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center mb-4">
                  <ArrowRight className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-medium">ACTO Bridges</h3>
                <p className="text-gray-400 text-sm mt-2">Mathematical proof comparison</p>
              </div>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={300} className="h-full">
              <div className="bg-black text-white rounded-2xl p-8 h-full flex flex-col">
                <h3 className="text-lg font-medium mb-4">The Solution</h3>
                <p className="text-gray-300 text-sm leading-relaxed flex-grow">{useCase.solution}</p>
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 md:px-6">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-3xl font-medium mb-12 tracking-tight">Validation Capabilities</h2>
          </ScrollAnimation>
          
          <div className="grid md:grid-cols-3 gap-6">
            {useCase.features.map((feature, i) => {
              const FeatureIcon = feature.icon;
              // Background images for each capability box
              const bgImages = ['/bg1.png', '/bg2.png', '/bg4.png'];
              return (
                <ScrollAnimation key={i} animation="blur-in" delay={100 + i * 100} className="h-full">
                  <div className="relative rounded-2xl p-6 h-full border border-gray-200 group hover:border-gray-400 transition-colors overflow-hidden">
                    {/* Background image */}
                    <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url(${bgImages[i]})` }} />
                    <div className="absolute inset-0 bg-white/80" />
                    {/* Content */}
                    <div className="relative z-10">
                      <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4 shadow-sm group-hover:shadow-md transition-shadow">
                        <FeatureIcon className="w-6 h-6 text-gray-700" />
                      </div>
                      <h3 className="text-lg font-medium mb-2">{feature.title}</h3>
                      <p className="text-gray-500 text-sm">{feature.description}</p>
                    </div>
                  </div>
                </ScrollAnimation>
              );
            })}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 md:py-28">
        <div className="max-w-5xl mx-auto px-4 md:px-6">
          <div className="grid lg:grid-cols-2 gap-12">
            <ScrollAnimation animation="blur-in" delay={0}>
              <h2 className="text-3xl font-medium mb-6 tracking-tight">Why Teams Choose ACTO</h2>
              <p className="text-gray-600 mb-8">Accelerate your simulation-to-real pipeline with cryptographic validation</p>
            </ScrollAnimation>
            
            <ScrollAnimation animation="blur-in" delay={100}>
              <div className="space-y-3">
                {useCase.benefits.map((benefit, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="w-6 h-6 rounded-full bg-black flex items-center justify-center flex-shrink-0">
                      <CheckCircle2 size={14} className="text-white" />
                    </div>
                    <p className="text-gray-700">{benefit}</p>
                  </div>
                ))}
              </div>
            </ScrollAnimation>
          </div>
        </div>
      </section>

      {/* Example & CTA with background image and fade */}
      <section className="relative bg-cover bg-center bg-no-repeat" style={{ backgroundImage: 'url(/bg3.png)' }}>
        {/* Gradient overlay - fades from white at top to dark at bottom */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-transparent to-black/70" />
        
        {/* Implementation Example */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-20 md:py-28 relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <div className="text-gray-500 font-mono text-sm mb-4 text-center">// IMPLEMENTATION EXAMPLE</div>
            <h2 className="text-3xl font-medium mb-8 text-center text-gray-900">{useCase.example.title}</h2>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-gray-200 shadow-lg">
                <div className="text-gray-500 text-sm mb-2">Scenario</div>
                <p className="text-gray-700">{useCase.example.scenario}</p>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-gray-200 shadow-lg">
                <div className="text-gray-500 text-sm mb-2">Results</div>
                <p className="text-gray-700">{useCase.example.implementation}</p>
              </div>
            </div>
          </ScrollAnimation>
        </div>

        {/* CTA */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-16 md:py-24 text-center relative z-10">
          <ScrollAnimation animation="blur-in" delay={0}>
            <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight text-white">
              Ready to get started?
            </h2>
            <p className="text-lg text-gray-200 mb-8 max-w-2xl mx-auto">
              Start building verifiable execution proofs for your autonomous systems today.
            </p>
          </ScrollAnimation>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <ScrollAnimation animation="blur-in" delay={60}>
              <a
                href={config.links.docs}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors"
              >
                Read Documentation
              </a>
            </ScrollAnimation>
            <ScrollAnimation animation="blur-in" delay={120}>
              <a
                href={config.links.dashboard}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/30 text-white font-medium rounded-lg hover:bg-white/10 transition-colors"
              >
                Get API Key
              </a>
            </ScrollAnimation>
          </div>
        </div>
      </section>
    </div>
  );
}

export function UseCaseDetail() {
  const { slug } = useParams<{ slug: string }>();
  const useCase = slug ? useCaseData[slug] : null;

  if (!useCase) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-medium mb-4">Use Case Not Found</h1>
          <Link to="/" className="text-gray-600 hover:text-gray-900">
            Return to Home
          </Link>
        </div>
      </div>
    );
  }

  // Render different layout based on slug
  const layouts: Record<string, JSX.Element> = {
    'robotics-as-a-service': <RoboticsAsAServiceLayout useCase={useCase} slug={slug!} />,
    'autonomous-cleaning': <AutonomousCleaningLayout useCase={useCase} slug={slug!} />,
    'drone-inspections': <DroneInspectionsLayout useCase={useCase} slug={slug!} />,
    'industrial-auditing': <IndustrialAuditingLayout useCase={useCase} slug={slug!} />,
    'research-environments': <ResearchEnvironmentsLayout useCase={useCase} slug={slug!} />,
    'simulation-validation': <SimulationValidationLayout useCase={useCase} slug={slug!} />,
  };

  return (
    <>
      <SEO
        title={`${useCase.title} - ACTO Use Cases`}
        description={useCase.description}
        url={`https://actobotics.net/use-cases/${slug}`}
      />
      {layouts[slug!] || <RoboticsAsAServiceLayout useCase={useCase} slug={slug!} />}
    </>
  );
}
