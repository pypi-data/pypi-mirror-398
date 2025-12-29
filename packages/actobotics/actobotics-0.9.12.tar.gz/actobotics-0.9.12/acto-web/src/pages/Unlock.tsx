import { useState } from 'react';
import { Lock, ArrowRight, AlertCircle, Github, X } from 'lucide-react';
import { FaXTwitter } from 'react-icons/fa6';

interface UnlockProps {
  onUnlock: () => void;
}

// Modal Component for Privacy and Terms
function Modal({ isOpen, onClose, title, children }: { isOpen: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-medium text-gray-900">{title}</h2>
          <button 
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors rounded-lg hover:bg-gray-100"
          >
            <X size={20} />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}

// Privacy Policy Content (Full Version)
function PrivacyContent() {
  return (
    <div className="prose prose-sm prose-gray max-w-none">
      <p className="text-xs text-gray-400 mb-6">Last updated: December 2025</p>
      
      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">1. Introduction</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          ACTO ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, 
          use, disclose, and safeguard your information when you use our proof-of-execution platform, including our website 
          (actobotics.net), API services (api.actobotics.net), dashboard, SDK, and CLI tools (collectively, the "Services").
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          By using our Services, you agree to the collection and use of information in accordance with this policy.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">2. Information We Collect</h3>
        <h4 className="text-sm font-medium mb-2 text-gray-800">2.1 Information You Provide</h4>
        <ul className="list-disc pl-5 mb-4 text-gray-600 text-sm space-y-1">
          <li><strong>Wallet Addresses:</strong> When you connect your Solana wallet to access our dashboard, we collect your public wallet address for authentication and access control.</li>
          <li><strong>API Keys:</strong> We generate and store API keys associated with your wallet address to authenticate your API requests.</li>
          <li><strong>Robot and Device Information:</strong> Robot IDs, device names, and group assignments you configure in fleet management.</li>
          <li><strong>Proof Data:</strong> Cryptographic proofs you submit, including task IDs, timestamps, and associated metadata.</li>
          <li><strong>Telemetry Data:</strong> If you choose to submit telemetry bundles, we process sensor data, execution logs, and operational metrics.</li>
        </ul>
        <h4 className="text-sm font-medium mb-2 text-gray-800">2.2 Information Collected Automatically</h4>
        <ul className="list-disc pl-5 mb-4 text-gray-600 text-sm space-y-1">
          <li><strong>Usage Data:</strong> API request logs, including endpoints accessed, request timestamps, response times, and error codes.</li>
          <li><strong>Device Information:</strong> IP addresses, browser type, operating system, and device identifiers when accessing web services.</li>
          <li><strong>Analytics:</strong> Aggregated usage statistics to improve our Services.</li>
        </ul>
        <h4 className="text-sm font-medium mb-2 text-gray-800">2.3 Information We Do NOT Collect</h4>
        <ul className="list-disc pl-5 text-gray-600 text-sm space-y-1">
          <li><strong>Private Keys:</strong> We never collect, store, or have access to your wallet's private keys.</li>
          <li><strong>Raw Sensor Data:</strong> The SDK processes telemetry locally on your hardware. Only cryptographic hashes and proofs are transmitted.</li>
          <li><strong>Personal Identification:</strong> We do not require names, emails, or other personal identification information.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">3. How We Use Your Information</h3>
        <ul className="list-disc pl-5 text-gray-600 text-sm space-y-1">
          <li>Provide, maintain, and improve our Services</li>
          <li>Authenticate users and authorize access to protected resources</li>
          <li>Process, verify, and store cryptographic proofs</li>
          <li>Enable fleet management and device monitoring features</li>
          <li>Enforce token-gating requirements and access controls</li>
          <li>Monitor for security threats and prevent abuse</li>
          <li>Generate aggregated, anonymized analytics</li>
          <li>Comply with legal obligations</li>
        </ul>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">4. Data Storage and Security</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          Your data is stored on secure servers hosted by Vercel and Neon (PostgreSQL). All data in transit is encrypted 
          using TLS 1.3. Sensitive data at rest is encrypted using AES-256. We use Ed25519 cryptographic signatures and 
          JWT tokens for secure authentication.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          Proof data is retained indefinitely to maintain the integrity of the verification system. API logs are retained 
          for 90 days. You may request deletion of your fleet management data at any time.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">5. Data Sharing and Disclosure</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">We do not sell your personal information. We may share data in the following circumstances:</p>
        <ul className="list-disc pl-5 text-gray-600 text-sm space-y-1">
          <li><strong>Service Providers:</strong> We use third-party services (Vercel, Neon, Helius) to host and operate our infrastructure.</li>
          <li><strong>Legal Requirements:</strong> We may disclose information if required by law, court order, or government request.</li>
          <li><strong>Security:</strong> We may share information to investigate fraud, security incidents, or violations of our Terms.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">6. Your Rights and Choices</h3>
        <ul className="list-disc pl-5 mb-4 text-gray-600 text-sm space-y-1">
          <li><strong>Access:</strong> Request a copy of the data we hold about you.</li>
          <li><strong>Correction:</strong> Request correction of inaccurate data.</li>
          <li><strong>Deletion:</strong> Request deletion of your data (subject to legal retention requirements).</li>
          <li><strong>Portability:</strong> Request your data in a machine-readable format.</li>
          <li><strong>Withdraw Consent:</strong> Withdraw consent where processing is based on consent.</li>
        </ul>
        <p className="text-gray-600 text-sm leading-relaxed">
          To exercise these rights, please contact us at privacy@actobotics.net.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">7. Cookies and Tracking</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          Our website uses minimal cookies necessary for functionality: authentication cookies to maintain your session 
          and preference cookies to remember your settings. We do not use third-party tracking cookies or advertising cookies.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">8. International Data Transfers</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          Our Services are operated globally. By using our Services, you consent to the transfer of your information to 
          countries outside your country of residence, which may have different data protection laws.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">9. Children's Privacy</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          Our Services are not intended for individuals under the age of 18. We do not knowingly collect personal 
          information from children.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">10. Changes to This Policy</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          We may update this Privacy Policy from time to time. We will notify you of any material changes by posting 
          the new policy on this page and updating the "Last updated" date.
        </p>
      </section>

      <section>
        <h3 className="text-lg font-medium mb-3 text-gray-900">11. Contact Us</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          If you have questions or concerns about this Privacy Policy, please contact us at privacy@actobotics.net 
          or via GitHub at github.com/actobotics/ACTO/issues.
        </p>
      </section>
    </div>
  );
}

// Terms of Service Content (Full Version)
function TermsContent() {
  return (
    <div className="prose prose-sm prose-gray max-w-none">
      <p className="text-xs text-gray-400 mb-6">Last updated: December 2025</p>
      
      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">1. Agreement to Terms</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          These Terms of Service ("Terms") constitute a legally binding agreement between you ("User," "you," or "your") 
          and ACTO ("Company," "we," "us," or "our") governing your access to and use of the ACTO platform, including 
          our website (actobotics.net), API services (api.actobotics.net), dashboard, Python SDK, CLI tools, and any 
          related services (collectively, the "Services").
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          By accessing or using our Services, you agree to be bound by these Terms. If you disagree with any part of 
          these Terms, you may not access the Services.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">2. Description of Services</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">ACTO provides a proof-of-execution platform for autonomous systems and robotics. Our Services include:</p>
        <ul className="list-disc pl-5 text-gray-600 text-sm space-y-1">
          <li><strong>Python SDK:</strong> Software development kit for generating cryptographic execution proofs locally on your hardware.</li>
          <li><strong>REST API:</strong> Cloud-hosted API for proof verification, submission, and registry services.</li>
          <li><strong>Dashboard:</strong> Web-based interface for managing API keys, viewing proofs, and monitoring robot fleets.</li>
          <li><strong>CLI Tools:</strong> Command-line interface for proof creation, key management, and API interaction.</li>
          <li><strong>Fleet Management:</strong> Tools for organizing, monitoring, and tracking multiple robotic devices.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">3. Eligibility</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">To use our Services, you must:</p>
        <ul className="list-disc pl-5 text-gray-600 text-sm space-y-1">
          <li>Be at least 18 years of age</li>
          <li>Have the legal capacity to enter into binding contracts</li>
          <li>Not be prohibited from using the Services under applicable law</li>
          <li>Have a valid Solana wallet for dashboard access (if using authenticated features)</li>
          <li>Hold the required ACTO token balance for API access (currently 50,000 ACTO tokens)</li>
        </ul>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">4. Account and Access</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          <strong>Wallet Authentication:</strong> Access to authenticated features requires connection of a Solana wallet. 
          You are solely responsible for maintaining the security of your wallet and private keys.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          <strong>API Keys:</strong> API keys are generated through the dashboard and are tied to your wallet address. 
          You must keep your API keys confidential and are responsible for all activity under your keys.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          <strong>Token Requirements:</strong> Access to certain API features requires holding a minimum balance of ACTO tokens. 
          Token requirements are verified on-chain and may be adjusted.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">5. Acceptable Use</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">You agree not to:</p>
        <ul className="list-disc pl-5 text-gray-600 text-sm space-y-1">
          <li>Use the Services for any unlawful purpose or in violation of any applicable laws</li>
          <li>Submit false, misleading, or fraudulent proofs or data</li>
          <li>Attempt to gain unauthorized access to any part of the Services</li>
          <li>Interfere with or disrupt the integrity or performance of the Services</li>
          <li>Reverse engineer, decompile, or disassemble any part of the Services (except as permitted by open-source licenses)</li>
          <li>Use automated systems to excessively load our infrastructure (rate limits apply)</li>
          <li>Resell or redistribute API access without authorization</li>
          <li>Circumvent token-gating or access control mechanisms</li>
        </ul>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">6. Intellectual Property</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          <strong>Our IP:</strong> The Services, including all content, features, and functionality, are owned by ACTO and 
          are protected by copyright, trademark, and other intellectual property laws.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          <strong>Open Source:</strong> The ACTO SDK and CLI are released under the MIT License. You may use, modify, and 
          distribute these components in accordance with the MIT License terms.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          <strong>Your Content:</strong> You retain ownership of all data, proofs, and content you submit to the Services.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">7. Privacy</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          Your use of the Services is also governed by our Privacy Policy, which is incorporated into these Terms by reference.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">8. Fees and Payment</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          The Services are currently provided free of charge to users who meet the token-gating requirements. 
          We reserve the right to introduce paid tiers or usage-based pricing in the future with reasonable notice.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          You are responsible for any costs incurred from third-party services, including Solana network transaction 
          fees, internet service charges, and hardware costs.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">9. Service Availability</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          We strive to maintain high availability but do not guarantee uninterrupted access. The Services may be 
          temporarily unavailable due to scheduled maintenance, emergency updates, factors beyond our control, or force majeure events.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">10. Disclaimers</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2 uppercase font-medium">
          THE SERVICES ARE PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR 
          IMPLIED, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
          PURPOSE, NON-INFRINGEMENT, AND TITLE.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          Cryptographic proofs generated by the Services are mathematical attestations based on the data provided. 
          They do not constitute legal proof, certification, or guarantee of real-world events.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">11. Limitation of Liability</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          TO THE MAXIMUM EXTENT PERMITTED BY LAW, ACTO SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, 
          CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, 
          OR OTHER INTANGIBLE LOSSES, RESULTING FROM YOUR USE OF THE SERVICES.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">12. Indemnification</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          You agree to defend, indemnify, and hold harmless ACTO and its officers, directors, employees, and agents 
          from any claims, damages, losses, liabilities, costs, and expenses arising from your use of the Services, 
          your violation of these Terms, or your violation of any rights of a third party.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">13. Termination</h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-2">
          You may stop using the Services at any time. We may suspend or terminate your access to the Services 
          immediately, without prior notice, for breach of these Terms, fraudulent activity, or at our sole discretion.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          Upon termination, your right to use the Services will immediately cease. Proofs already submitted to the 
          registry will remain accessible.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">14. Dispute Resolution</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          Before filing a formal dispute, you agree to contact us at legal@actobotics.net and attempt to resolve 
          the dispute informally for at least 30 days. Any dispute that cannot be resolved informally shall be 
          settled by binding arbitration.
        </p>
      </section>

      <section className="mb-8">
        <h3 className="text-lg font-medium mb-3 text-gray-900">15. General Provisions</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          These Terms, together with our Privacy Policy, constitute the entire agreement between you and ACTO 
          regarding the Services. If any provision is held invalid, the remaining provisions shall remain in effect. 
          You may not assign these Terms without our prior written consent.
        </p>
      </section>

      <section>
        <h3 className="text-lg font-medium mb-3 text-gray-900">16. Contact Information</h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          For questions about these Terms, please contact us at legal@actobotics.net or via GitHub at 
          github.com/actobotics/ACTO/issues.
        </p>
      </section>
    </div>
  );
}

export function Unlock({ onUnlock }: UnlockProps) {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showTerms, setShowTerms] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/unlock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();

      if (data.success) {
        // Store access in localStorage
        localStorage.setItem('site_access', 'granted');
        onUnlock();
      } else {
        setError('Invalid access code');
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative">
      {/* Background image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/hero.png)' }}
      />
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50" />

      <div className="relative z-10 w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <img src="/logo_w.png" alt="ACTO" className="h-10 mx-auto mb-4" />
          <p className="text-gray-300 text-sm">Early Access</p>
        </div>

        {/* Card */}
        <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-6">
            <div className="w-14 h-14 bg-stone-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Lock className="w-7 h-7 text-stone-600" />
            </div>
            <h1 className="text-xl font-medium text-gray-900 mb-2">Enter Access Code</h1>
            <p className="text-stone-500 text-sm">
              This site is currently in private beta.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Access code"
                className="w-full px-4 py-3 bg-stone-50 border border-stone-300 rounded-lg text-gray-900 placeholder-stone-400 focus:outline-none focus:border-stone-500 focus:ring-2 focus:ring-stone-200 transition-colors"
                autoFocus
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle size={16} />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !code}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Checking...' : 'Continue'}
              {!loading && <ArrowRight size={16} />}
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-center gap-4 mt-6">
          <a 
            href="https://x.com/actoboticsnet" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="X (Twitter)"
          >
            <FaXTwitter size={20} />
          </a>
          <a 
            href="https://github.com/actobotics" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="GitHub"
          >
            <Github size={20} />
          </a>
        </div>
        
        {/* Legal Links */}
        <div className="flex items-center justify-center gap-3 mt-4">
          <button 
            onClick={() => setShowPrivacy(true)}
            className="text-white/70 hover:text-white transition-colors text-xs"
          >
            Privacy
          </button>
          <span className="text-white/50">·</span>
          <button 
            onClick={() => setShowTerms(true)}
            className="text-white/70 hover:text-white transition-colors text-xs"
          >
            Terms
          </button>
        </div>
      </div>

      {/* Modals */}
      <Modal isOpen={showPrivacy} onClose={() => setShowPrivacy(false)} title="Privacy Policy">
        <PrivacyContent />
      </Modal>
      
      <Modal isOpen={showTerms} onClose={() => setShowTerms(false)} title="Terms of Service">
        <TermsContent />
      </Modal>
    </div>
  );
}

