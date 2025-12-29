export function Terms() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative py-24 md:py-32">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: 'url(/hero.png)' }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-black/70" />
        <div className="max-w-4xl mx-auto px-4 md:px-6 relative z-10">
          <p className="text-sm text-gray-200 mb-4 tracking-wide uppercase">Legal</p>
          <h1 className="text-4xl md:text-5xl font-medium mb-4 tracking-tight text-white">Terms of Service</h1>
          <p className="text-gray-300">Last updated: December 2025</p>
        </div>
      </section>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 md:px-6 py-16 md:py-24">

        <div className="prose prose-gray max-w-none">
          {/* Introduction */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">1. Agreement to Terms</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              These Terms of Service ("Terms") constitute a legally binding agreement between you ("User," "you," or "your") 
              and ACTO ("Company," "we," "us," or "our") governing your access to and use of the ACTO platform, including 
              our website (actobotics.net), API services (api.actobotics.net), dashboard, Python SDK, CLI tools, and any 
              related services (collectively, the "Services").
            </p>
            <p className="text-gray-600 leading-relaxed mb-4">
              By accessing or using our Services, you agree to be bound by these Terms. If you disagree with any part of 
              these Terms, you may not access the Services.
            </p>
            <p className="text-gray-600 leading-relaxed">
              We reserve the right to modify these Terms at any time. We will provide notice of material changes by updating 
              the "Last updated" date. Your continued use of the Services after such modifications constitutes acceptance 
              of the updated Terms.
            </p>
          </section>

          {/* Description of Services */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">2. Description of Services</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              ACTO provides a proof-of-execution platform for autonomous systems and robotics. Our Services include:
            </p>
            <ul className="list-disc pl-6 mb-4 text-gray-600 space-y-2">
              <li><strong>Python SDK:</strong> Software development kit for generating cryptographic execution proofs locally on your hardware.</li>
              <li><strong>REST API:</strong> Cloud-hosted API for proof verification, submission, and registry services.</li>
              <li><strong>Dashboard:</strong> Web-based interface for managing API keys, viewing proofs, and monitoring robot fleets.</li>
              <li><strong>CLI Tools:</strong> Command-line interface for proof creation, key management, and API interaction.</li>
              <li><strong>Fleet Management:</strong> Tools for organizing, monitoring, and tracking multiple robotic devices.</li>
            </ul>
            <p className="text-gray-600 leading-relaxed">
              The Services are designed for professional use in robotics, automation, and industrial applications. 
              They are not intended for consumer applications.
            </p>
          </section>

          {/* Eligibility */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">3. Eligibility</h2>
            <p className="text-gray-600 leading-relaxed mb-4">To use our Services, you must:</p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Be at least 18 years of age</li>
              <li>Have the legal capacity to enter into binding contracts</li>
              <li>Not be prohibited from using the Services under applicable law</li>
              <li>Have a valid Solana wallet for dashboard access (if using authenticated features)</li>
              <li>Hold the required ACTO token balance for API access (currently 50,000 ACTO tokens)</li>
            </ul>
          </section>

          {/* Account and Access */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">4. Account and Access</h2>
            
            <h3 className="text-lg font-medium mb-3 text-gray-900">4.1 Wallet Authentication</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              Access to authenticated features requires connection of a Solana wallet. You are solely responsible for 
              maintaining the security of your wallet and private keys. We are not liable for any loss resulting from 
              unauthorized access to your wallet.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">4.2 API Keys</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              API keys are generated through the dashboard and are tied to your wallet address. You must keep your API 
              keys confidential and are responsible for all activity under your keys. Notify us immediately if you 
              suspect unauthorized use of your API keys.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">4.3 Token Requirements</h3>
            <p className="text-gray-600 leading-relaxed">
              Access to certain API features requires holding a minimum balance of ACTO tokens. Token requirements are 
              verified on-chain and may be adjusted. We are not responsible for token price fluctuations or your ability 
              to acquire tokens.
            </p>
          </section>

          {/* Acceptable Use */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">5. Acceptable Use</h2>
            <p className="text-gray-600 leading-relaxed mb-4">You agree not to:</p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Use the Services for any unlawful purpose or in violation of any applicable laws</li>
              <li>Submit false, misleading, or fraudulent proofs or data</li>
              <li>Attempt to gain unauthorized access to any part of the Services</li>
              <li>Interfere with or disrupt the integrity or performance of the Services</li>
              <li>Reverse engineer, decompile, or disassemble any part of the Services (except as permitted by open-source licenses)</li>
              <li>Use automated systems to excessively load our infrastructure (rate limits apply)</li>
              <li>Resell or redistribute API access without authorization</li>
              <li>Use the Services to harm, threaten, or harass others</li>
              <li>Circumvent token-gating or access control mechanisms</li>
              <li>Submit malicious code, viruses, or harmful data</li>
            </ul>
          </section>

          {/* Intellectual Property */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">6. Intellectual Property</h2>
            
            <h3 className="text-lg font-medium mb-3 text-gray-900">6.1 Our Intellectual Property</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              The Services, including all content, features, and functionality, are owned by ACTO and are protected by 
              copyright, trademark, and other intellectual property laws. The ACTO name, logo, and branding are 
              trademarks of ACTO.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">6.2 Open Source Components</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              The ACTO SDK and CLI are released under the MIT License. You may use, modify, and distribute these 
              components in accordance with the MIT License terms. The server software and API are not open source.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">6.3 Your Content</h3>
            <p className="text-gray-600 leading-relaxed">
              You retain ownership of all data, proofs, and content you submit to the Services. By submitting content, 
              you grant us a non-exclusive, worldwide, royalty-free license to store, process, and display your content 
              as necessary to provide the Services.
            </p>
          </section>

          {/* Privacy */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">7. Privacy</h2>
            <p className="text-gray-600 leading-relaxed">
              Your use of the Services is also governed by our Privacy Policy, which is incorporated into these Terms 
              by reference. Please review our <a href="/privacy" className="text-gray-900 underline">Privacy Policy</a> to 
              understand how we collect, use, and protect your information.
            </p>
          </section>

          {/* Fees and Payment */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">8. Fees and Payment</h2>
            
            <h3 className="text-lg font-medium mb-3 text-gray-900">8.1 Current Pricing</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              The Services are currently provided free of charge to users who meet the token-gating requirements. 
              We reserve the right to introduce paid tiers or usage-based pricing in the future with reasonable notice.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">8.2 Token Requirements</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              Access requires holding ACTO tokens. The required token amount may change. We do not provide refunds 
              for tokens purchased, and we are not responsible for token value fluctuations.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">8.3 Third-Party Costs</h3>
            <p className="text-gray-600 leading-relaxed">
              You are responsible for any costs incurred from third-party services, including Solana network transaction 
              fees, internet service charges, and hardware costs.
            </p>
          </section>

          {/* Service Availability */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">9. Service Availability</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              We strive to maintain high availability but do not guarantee uninterrupted access. The Services may be 
              temporarily unavailable due to:
            </p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Scheduled maintenance (we will provide advance notice when possible)</li>
              <li>Emergency maintenance or security updates</li>
              <li>Factors beyond our control (network outages, third-party service failures)</li>
              <li>Force majeure events</li>
            </ul>
          </section>

          {/* Disclaimers */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">10. Disclaimers</h2>
            <p className="text-gray-600 leading-relaxed mb-4 uppercase text-sm font-medium">
              THE SERVICES ARE PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR 
              IMPLIED, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
              PURPOSE, NON-INFRINGEMENT, AND TITLE.
            </p>
            <p className="text-gray-600 leading-relaxed mb-4">We do not warrant that:</p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>The Services will meet your specific requirements</li>
              <li>The Services will be uninterrupted, timely, secure, or error-free</li>
              <li>The results obtained from using the Services will be accurate or reliable</li>
              <li>Any errors in the Services will be corrected</li>
            </ul>
            <p className="text-gray-600 leading-relaxed mt-4">
              Cryptographic proofs generated by the Services are mathematical attestations based on the data provided. 
              They do not constitute legal proof, certification, or guarantee of real-world events. You are responsible 
              for determining the suitability of proofs for your specific use case.
            </p>
          </section>

          {/* Limitation of Liability */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">11. Limitation of Liability</h2>
            <p className="text-gray-600 leading-relaxed mb-4 uppercase text-sm font-medium">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, IN NO EVENT SHALL ACTO, ITS DIRECTORS, EMPLOYEES, PARTNERS, 
              AGENTS, SUPPLIERS, OR AFFILIATES BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR 
              PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER 
              INTANGIBLE LOSSES, RESULTING FROM:
            </p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Your access to or use of (or inability to access or use) the Services</li>
              <li>Any conduct or content of any third party on the Services</li>
              <li>Any content obtained from the Services</li>
              <li>Unauthorized access, use, or alteration of your transmissions or content</li>
              <li>Loss of cryptocurrency, tokens, or wallet access</li>
              <li>Errors in proof generation or verification</li>
              <li>Reliance on proofs for business or legal purposes</li>
            </ul>
            <p className="text-gray-600 leading-relaxed mt-4">
              Our total liability for any claims arising from these Terms or your use of the Services shall not exceed 
              the amount you paid us (if any) in the twelve (12) months preceding the claim.
            </p>
          </section>

          {/* Indemnification */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">12. Indemnification</h2>
            <p className="text-gray-600 leading-relaxed">
              You agree to defend, indemnify, and hold harmless ACTO and its officers, directors, employees, and agents 
              from any claims, damages, losses, liabilities, costs, and expenses (including reasonable attorneys' fees) 
              arising from: (a) your use of the Services; (b) your violation of these Terms; (c) your violation of any 
              rights of a third party; or (d) your content or data submitted to the Services.
            </p>
          </section>

          {/* Termination */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">13. Termination</h2>
            
            <h3 className="text-lg font-medium mb-3 text-gray-900">13.1 Termination by You</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              You may stop using the Services at any time. You may request deletion of your data by contacting us.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">13.2 Termination by Us</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              We may suspend or terminate your access to the Services immediately, without prior notice, for any reason, 
              including but not limited to: (a) breach of these Terms; (b) fraudulent or illegal activity; (c) failure 
              to meet token requirements; or (d) at our sole discretion.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">13.3 Effect of Termination</h3>
            <p className="text-gray-600 leading-relaxed">
              Upon termination, your right to use the Services will immediately cease. Provisions that by their nature 
              should survive termination will survive, including ownership provisions, warranty disclaimers, indemnity, 
              and limitations of liability. Proofs already submitted to the registry will remain accessible.
            </p>
          </section>

          {/* Dispute Resolution */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">14. Dispute Resolution</h2>
            
            <h3 className="text-lg font-medium mb-3 text-gray-900">14.1 Informal Resolution</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              Before filing a formal dispute, you agree to contact us at legal@actobotics.net and attempt to resolve 
              the dispute informally for at least 30 days.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">14.2 Arbitration</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              Any dispute arising from these Terms or the Services that cannot be resolved informally shall be settled 
              by binding arbitration. The arbitration shall be conducted in English, and the arbitrator's decision 
              shall be final and binding.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">14.3 Class Action Waiver</h3>
            <p className="text-gray-600 leading-relaxed">
              You agree that any dispute resolution proceedings will be conducted only on an individual basis and not 
              in a class, consolidated, or representative action.
            </p>
          </section>

          {/* General */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">15. General Provisions</h2>
            
            <h3 className="text-lg font-medium mb-3 text-gray-900">15.1 Entire Agreement</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              These Terms, together with our Privacy Policy, constitute the entire agreement between you and ACTO 
              regarding the Services and supersede all prior agreements.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">15.2 Severability</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              If any provision of these Terms is held to be invalid or unenforceable, such provision shall be struck 
              and the remaining provisions shall remain in effect.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">15.3 Waiver</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              Our failure to enforce any right or provision of these Terms will not be considered a waiver of those rights.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">15.4 Assignment</h3>
            <p className="text-gray-600 leading-relaxed">
              You may not assign or transfer these Terms without our prior written consent. We may assign our rights 
              and obligations under these Terms without restriction.
            </p>
          </section>

          {/* Contact */}
          <section>
            <h2 className="text-2xl font-medium mb-4 text-gray-900">16. Contact Information</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              For questions about these Terms, please contact us:
            </p>
            <ul className="text-gray-600 space-y-2">
              <li><strong>Email:</strong> legal@actobotics.net</li>
              <li><strong>GitHub:</strong> github.com/actobotics/ACTO/issues</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}

