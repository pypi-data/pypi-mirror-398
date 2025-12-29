import { useState, ReactNode } from 'react';
import { ChevronDown } from 'lucide-react';
import { SEO } from '../components/SEO';
import { ScrollAnimation } from '../components/ScrollAnimation';
import { config } from '../config';

interface FAQItem {
  question: string;
  answer: string | ReactNode;
  category: string;
}

const faqData: FAQItem[] = [
  {
    category: 'General',
    question: 'What is ACTO?',
    answer: 'ACTO (Autonomous Cryptographic Task Operations) is a platform that enables autonomous systems to generate cryptographic proofs of their actions. Every task execution is signed with Ed25519 signatures, creating tamper-proof, independently verifiable records.'
  },
  {
    category: 'General',
    question: 'How does ACTO work?',
    answer: (
      <>
        <p className="mb-3">ACTO works in four steps:</p>
        <ol className="list-decimal list-inside space-y-2 ml-2">
          <li>Your robot executes a task and collects telemetry data</li>
          <li>The ACTO SDK generates a cryptographic hash of the execution data</li>
          <li>The hash is signed with the robot's private key using Ed25519</li>
          <li>The proof is submitted to our API for verification and storage</li>
        </ol>
        <p className="mt-3">Anyone can verify the proof using the robot's public key.</p>
      </>
    )
  },
  {
    category: 'General',
    question: 'What makes ACTO different from traditional logging?',
    answer: 'Traditional logs can be modified or deleted after the fact. ACTO proofs are cryptographically signed, making them mathematically impossible to forge or alter. Additionally, proofs can be verified independently without trusting the operator or ACTO.'
  },
  {
    category: 'Security',
    question: 'How secure is ACTO?',
    answer: 'ACTO uses Ed25519 cryptographic signatures, the same technology used in modern security systems. Proofs are generated locally on your robot, so sensitive data never leaves your system until you choose to submit it. The signature scheme is resistant to forgery and has been extensively peer-reviewed.'
  },
  {
    category: 'Security',
    question: 'What happens if a robot\'s private key is compromised?',
    answer: (
      <>
        <p className="mb-3">If a private key is compromised:</p>
        <ol className="list-decimal list-inside space-y-1 ml-2">
          <li>Immediately revoke it and generate a new key pair</li>
          <li>Mark the key as compromised in your system</li>
          <li>Past proofs remain valid and verifiable</li>
        </ol>
        <p className="mt-3">ACTO's dashboard allows you to manage multiple keys per robot and track key rotation.</p>
      </>
    )
  },
  {
    category: 'Security',
    question: 'Can ACTO proofs be faked?',
    answer: 'No. Ed25519 signatures are mathematically impossible to forge without the private key. Even with unlimited computing power, forging a signature would take longer than the age of the universe. This is why cryptographic proofs are more trustworthy than any traditional logging system.'
  },
  {
    category: 'Security',
    question: 'Where is my data stored?',
    answer: 'Your telemetry data is processed through our API to generate cryptographic proofs. The proof (hash + signature) is created via our service and stored in our registry. You control what data goes into the proof, and all proofs require token validation through your connected Solana wallet.'
  },
  {
    category: 'Technical',
    question: 'What programming languages are supported?',
    answer: 'Currently, we provide an official Python SDK (actobotics). The SDK works with Python 3.8+ and supports async/await. We also provide a REST API that can be used from any language. Community SDKs for other languages are in development.'
  },
  {
    category: 'Technical',
    question: 'Does ACTO work with ROS/ROS2?',
    answer: 'Yes! Our Python SDK can be integrated into ROS/ROS2 nodes. We\'re working on native ROS2 integration with dedicated message types and services. Follow us on X to stay updated on ROS integration progress.'
  },
  {
    category: 'Technical',
    question: 'What is the performance impact?',
    answer: 'Proof generation is extremely fast - typically under 5ms for a standard proof. Signature creation uses Ed25519, which is optimized for speed. Verification is even faster at under 1ms. The overhead is negligible for most robotic applications.'
  },
  {
    category: 'Technical',
    question: 'Can ACTO work offline?',
    answer: 'No, ACTO requires an internet connection. The proof generation and verification process requires token validation and runs through our API. Your robot needs connectivity to generate and verify proofs in real-time.'
  },
  {
    category: 'Technical',
    question: 'What data should I include in a proof?',
    answer: (
      <>
        <p className="mb-3">Include any data that proves task execution:</p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>Timestamps</li>
          <li>GPS coordinates</li>
          <li>Sensor readings</li>
          <li>Task parameters</li>
          <li>Success/failure status</li>
          <li>Any relevant metadata</li>
        </ul>
        <p className="mt-3">The more specific the data, the more valuable the proof. Our SDK provides helpers for common data types.</p>
      </>
    )
  },
  {
    category: 'Integration',
    question: 'How long does it take to integrate ACTO?',
    answer: (
      <>
        <p className="mb-3">Basic integration takes 15-30 minutes:</p>
        <ol className="list-decimal list-inside space-y-1 ml-2">
          <li>Install the SDK with pip</li>
          <li>Generate a key pair</li>
          <li>Start creating proofs</li>
        </ol>
        <p className="mt-3">Advanced features like fleet management and custom proof schemas can be added incrementally. Our quickstart guide walks you through the process.</p>
      </>
    )
  },
  {
    category: 'Integration',
    question: 'Do I need to modify my existing robot code?',
    answer: 'Integration is minimal. You add a few lines of code where you want to generate proofs - typically after task completion. The SDK is designed to be non-invasive and works alongside your existing logging and monitoring systems.'
  },
  {
    category: 'Integration',
    question: 'Can I use ACTO with my existing fleet management system?',
    answer: 'Yes! ACTO provides a REST API that integrates with any fleet management system. You can also use our dashboard as a standalone fleet management tool or integrate it with your existing systems via API.'
  },
  {
    category: 'Pricing',
    question: 'How much does ACTO cost?',
    answer: 'To use the ACTO ecosystem, you need to hold 50,000 ACTO tokens in your Solana wallet. This token-gated access ensures that only committed users can use the platform. The tokens remain in your wallet - they are not spent or consumed.'
  },
  {
    category: 'Pricing',
    question: 'What are ACTO tokens?',
    answer: 'ACTO tokens are Solana-based tokens that provide access to the ACTO ecosystem. Holding 50,000 ACTO tokens in your wallet grants you full access to the API, dashboard, and all features. The tokens can be purchased on Solana DEXs.'
  },
  {
    category: 'Pricing',
    question: 'Do I need to spend my tokens?',
    answer: 'No! The 50,000 ACTO tokens simply need to be held in your wallet. They are not consumed or spent when you use the platform. As long as your wallet holds the required tokens, you have full access to ACTO.'
  },
  {
    category: 'Use Cases',
    question: 'What industries use ACTO?',
    answer: (
      <>
        <p className="mb-3">ACTO is used in various industries:</p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>Robotics-as-a-Service</li>
          <li>Autonomous cleaning</li>
          <li>Drone inspections</li>
          <li>Industrial auditing</li>
          <li>Research environments</li>
          <li>Simulation validation</li>
        </ul>
        <p className="mt-3">Any industry where autonomous systems need to prove what they did can benefit from ACTO.</p>
      </>
    )
  },
  {
    category: 'Use Cases',
    question: 'Can ACTO help with regulatory compliance?',
    answer: 'Yes! Many industries require proof of task execution for compliance (FDA, ISO, etc.). ACTO\'s cryptographic proofs provide audit-ready evidence that satisfies regulatory requirements. Auditors can independently verify proofs without trusting your logs.'
  },
  {
    category: 'Use Cases',
    question: 'Is ACTO suitable for safety-critical applications?',
    answer: 'Yes. ACTO provides the highest level of assurance that tasks were executed as specified. However, ACTO is a verification layer - it doesn\'t replace safety systems. Use ACTO to prove that safety protocols were followed, not as a safety system itself.'
  },
  {
    category: 'Support',
    question: 'What support options are available?',
    answer: 'Support is provided through our X (Twitter) page where you can reach out to our team. We also offer comprehensive documentation including quickstart guides, API references, and integration examples. For urgent issues, contact us via X.'
  },
  {
    category: 'Support',
    question: 'Is ACTO open source?',
    answer: 'Yes! The Python SDK is fully open source under the MIT license. You can review, modify, and contribute to the code. The API and infrastructure are proprietary, but the verification logic is transparent and auditable.'
  },
  {
    category: 'Support',
    question: 'How can I contribute to ACTO?',
    answer: 'We welcome contributions! Check out our GitHub repository for open issues, feature requests, and contribution guidelines. You can contribute code, documentation, examples, or help other users in our Discord community.'
  }
];

const categories = ['All', ...Array.from(new Set(faqData.map(item => item.category)))];

export function FAQ() {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [openItems, setOpenItems] = useState<Set<number>>(new Set());

  const filteredFAQs = selectedCategory === 'All' 
    ? faqData 
    : faqData.filter(item => item.category === selectedCategory);

  const toggleItem = (index: number) => {
    const newOpenItems = new Set(openItems);
    if (newOpenItems.has(index)) {
      newOpenItems.delete(index);
    } else {
      newOpenItems.add(index);
    }
    setOpenItems(newOpenItems);
  };

  return (
    <>
      <SEO
        title="FAQ - Frequently Asked Questions"
        description="Find answers to common questions about ACTO, cryptographic proofs, integration, pricing, and more."
        url="https://actobotics.net/faq"
      />
      <div className="min-h-screen">
        {/* Hero */}
        <section className="pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
          {/* Background Image */}
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-40"
            style={{ backgroundImage: 'url(/hero3.png)' }}
          />
          {/* Fade to white overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-white" />
          
          <div className="max-w-4xl mx-auto px-4 md:px-6 text-center relative z-10">
            <ScrollAnimation animation="blur-in" delay={0}>
              <h1 className="text-4xl md:text-5xl font-medium mb-6 tracking-tight text-white">
                Frequently Asked Questions
              </h1>
              <p className="text-xl text-white/80 leading-relaxed">
                Everything you need to know about ACTO, cryptographic proofs, and verifiable autonomy.
              </p>
            </ScrollAnimation>
          </div>
        </section>

        {/* Category Filter */}
        <section className="sticky top-0 bg-white/95 backdrop-blur-sm z-40">
          <div className="max-w-4xl mx-auto px-4 md:px-6 py-4">
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                    selectedCategory === category
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Items */}
        <section className="py-16 md:py-24">
          <div className="max-w-4xl mx-auto px-4 md:px-6">
            <div className="space-y-4">
              {filteredFAQs.map((item, index) => {
                const isOpen = openItems.has(index);
                return (
                  <ScrollAnimation key={index} animation="blur-in" delay={Math.min(index * 30, 300)}>
                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleItem(index)}
                        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex-1 pr-4">
                          <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                            {item.category}
                          </span>
                          <h3 className="text-lg font-medium text-gray-900 mt-1">
                            {item.question}
                          </h3>
                        </div>
                        <ChevronDown
                          size={20}
                          className={`text-gray-400 flex-shrink-0 transition-transform duration-700 ease-in-out ${
                            isOpen ? 'rotate-180' : ''
                          }`}
                        />
                      </button>
                      <div 
                        className={`overflow-hidden transition-all duration-700 ease-in-out ${
                          isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                        }`}
                      >
                        <div className="px-6 pb-4 pt-2 text-gray-600 leading-relaxed border-t border-gray-100">
                          {item.answer}
                        </div>
                      </div>
                    </div>
                  </ScrollAnimation>
                );
              })}
            </div>
          </div>
        </section>

        {/* Still have questions CTA */}
        <section className="py-16 md:py-24 bg-gray-50 border-t border-gray-100">
          <div className="max-w-4xl mx-auto px-4 md:px-6 text-center">
            <ScrollAnimation animation="blur-in" delay={0}>
              <h2 className="text-2xl md:text-3xl font-medium mb-4 tracking-tight">
                Still have questions?
              </h2>
              <p className="text-lg text-gray-600 mb-8">
                Reach out to our team on X (Twitter) for support and updates.
              </p>
            </ScrollAnimation>
            <div className="flex justify-center">
              <ScrollAnimation animation="blur-in" delay={60}>
                <a
                  href={config.social.x}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 transition-colors"
                >
                  <svg width="18" height="18" viewBox="0 0 1200 1227" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                    <path d="M714.163 519.284L1160.89 0H1055.03L667.137 450.887L357.328 0H0L468.492 681.821L0 1226.37H105.866L515.491 750.218L842.672 1226.37H1200L714.137 519.284H714.163ZM569.165 687.828L521.697 619.934L144.011 79.6944H306.615L611.412 515.685L658.88 583.579L1055.08 1150.3H892.476L569.165 687.854V687.828Z"/>
                  </svg>
                  Follow us on X
                </a>
              </ScrollAnimation>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

