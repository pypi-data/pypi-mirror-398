export function Privacy() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative py-24 md:py-32">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: 'url(/hero2.png)' }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-black/70" />
        <div className="max-w-4xl mx-auto px-4 md:px-6 relative z-10">
          <p className="text-sm text-gray-200 mb-4 tracking-wide uppercase">Legal</p>
          <h1 className="text-4xl md:text-5xl font-medium mb-4 tracking-tight text-white">Privacy Policy</h1>
          <p className="text-gray-300">Last updated: December 2025</p>
        </div>
      </section>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 md:px-6 py-16 md:py-24">

        <div className="prose prose-gray max-w-none">
          {/* Introduction */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">1. Introduction</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              ACTO ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, 
              use, disclose, and safeguard your information when you use our proof-of-execution platform, including our website 
              (actobotics.net), API services (api.actobotics.net), dashboard, SDK, and CLI tools (collectively, the "Services").
            </p>
            <p className="text-gray-600 leading-relaxed">
              By using our Services, you agree to the collection and use of information in accordance with this policy. 
              If you do not agree with our policies and practices, please do not use our Services.
            </p>
          </section>

          {/* Information We Collect */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">2. Information We Collect</h2>
            
            <h3 className="text-lg font-medium mb-3 text-gray-900">2.1 Information You Provide</h3>
            <ul className="list-disc pl-6 mb-6 text-gray-600 space-y-2">
              <li><strong>Wallet Addresses:</strong> When you connect your Solana wallet to access our dashboard, we collect your public wallet address for authentication and access control.</li>
              <li><strong>API Keys:</strong> We generate and store API keys associated with your wallet address to authenticate your API requests.</li>
              <li><strong>Robot and Device Information:</strong> Robot IDs, device names, and group assignments you configure in fleet management.</li>
              <li><strong>Proof Data:</strong> Cryptographic proofs you submit, including task IDs, timestamps, and associated metadata.</li>
              <li><strong>Telemetry Data:</strong> If you choose to submit telemetry bundles, we process sensor data, execution logs, and operational metrics.</li>
            </ul>

            <h3 className="text-lg font-medium mb-3 text-gray-900">2.2 Information Collected Automatically</h3>
            <ul className="list-disc pl-6 mb-6 text-gray-600 space-y-2">
              <li><strong>Usage Data:</strong> API request logs, including endpoints accessed, request timestamps, response times, and error codes.</li>
              <li><strong>Device Information:</strong> IP addresses, browser type, operating system, and device identifiers when accessing web services.</li>
              <li><strong>Analytics:</strong> Aggregated usage statistics to improve our Services.</li>
            </ul>

            <h3 className="text-lg font-medium mb-3 text-gray-900">2.3 Information We Do NOT Collect</h3>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Private Keys:</strong> We never collect, store, or have access to your wallet's private keys. Authentication is performed via cryptographic signature verification.</li>
              <li><strong>Raw Sensor Data:</strong> The SDK processes telemetry locally on your hardware. Only cryptographic hashes and proofs are transmitted to our servers.</li>
              <li><strong>Personal Identification:</strong> We do not require names, emails, or other personal identification information to use our Services.</li>
            </ul>
          </section>

          {/* How We Use Your Information */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">3. How We Use Your Information</h2>
            <p className="text-gray-600 leading-relaxed mb-4">We use the information we collect to:</p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Provide, maintain, and improve our Services</li>
              <li>Authenticate users and authorize access to protected resources</li>
              <li>Process, verify, and store cryptographic proofs</li>
              <li>Enable fleet management and device monitoring features</li>
              <li>Enforce token-gating requirements and access controls</li>
              <li>Monitor for security threats and prevent abuse</li>
              <li>Generate aggregated, anonymized analytics</li>
              <li>Communicate service updates and security notices</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          {/* Data Storage and Security */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">4. Data Storage and Security</h2>
            
            <h3 className="text-lg font-medium mb-3 text-gray-900">4.1 Storage Location</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              Your data is stored on secure servers hosted by Vercel and Neon (PostgreSQL). Our infrastructure is distributed 
              across multiple regions to ensure reliability and performance.
            </p>

            <h3 className="text-lg font-medium mb-3 text-gray-900">4.2 Security Measures</h3>
            <ul className="list-disc pl-6 mb-6 text-gray-600 space-y-2">
              <li><strong>Encryption:</strong> All data in transit is encrypted using TLS 1.3. Sensitive data at rest is encrypted using AES-256.</li>
              <li><strong>Authentication:</strong> We use Ed25519 cryptographic signatures and JWT tokens for secure authentication.</li>
              <li><strong>Access Controls:</strong> Role-based access control (RBAC) limits internal access to data on a need-to-know basis.</li>
              <li><strong>Audit Logging:</strong> All access to sensitive data is logged and monitored.</li>
              <li><strong>Regular Audits:</strong> We conduct regular security assessments and penetration testing.</li>
            </ul>

            <h3 className="text-lg font-medium mb-3 text-gray-900">4.3 Data Retention</h3>
            <p className="text-gray-600 leading-relaxed">
              Proof data is retained indefinitely to maintain the integrity of the verification system. API logs are retained 
              for 90 days. You may request deletion of your fleet management data at any time by contacting us.
            </p>
          </section>

          {/* Data Sharing */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">5. Data Sharing and Disclosure</h2>
            <p className="text-gray-600 leading-relaxed mb-4">We do not sell your personal information. We may share data in the following circumstances:</p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Service Providers:</strong> We use third-party services (Vercel, Neon, Helius) to host and operate our infrastructure. These providers are bound by confidentiality agreements.</li>
              <li><strong>Legal Requirements:</strong> We may disclose information if required by law, court order, or government request.</li>
              <li><strong>Security:</strong> We may share information to investigate fraud, security incidents, or violations of our Terms of Service.</li>
              <li><strong>Business Transfers:</strong> In the event of a merger, acquisition, or sale of assets, user data may be transferred to the acquiring entity.</li>
            </ul>
          </section>

          {/* Your Rights */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">6. Your Rights and Choices</h2>
            <p className="text-gray-600 leading-relaxed mb-4">Depending on your location, you may have the following rights:</p>
            <ul className="list-disc pl-6 mb-6 text-gray-600 space-y-2">
              <li><strong>Access:</strong> Request a copy of the data we hold about you.</li>
              <li><strong>Correction:</strong> Request correction of inaccurate data.</li>
              <li><strong>Deletion:</strong> Request deletion of your data (subject to legal retention requirements).</li>
              <li><strong>Portability:</strong> Request your data in a machine-readable format.</li>
              <li><strong>Objection:</strong> Object to certain processing activities.</li>
              <li><strong>Withdraw Consent:</strong> Withdraw consent where processing is based on consent.</li>
            </ul>
            <p className="text-gray-600 leading-relaxed">
              To exercise these rights, please contact us at privacy@actobotics.net. We will respond within 30 days.
            </p>
          </section>

          {/* Cookies */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">7. Cookies and Tracking</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Our website uses minimal cookies necessary for functionality:
            </p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Authentication Cookies:</strong> To maintain your session when logged into the dashboard.</li>
              <li><strong>Preference Cookies:</strong> To remember your settings and preferences.</li>
            </ul>
            <p className="text-gray-600 leading-relaxed mt-4">
              We do not use third-party tracking cookies or advertising cookies. We do not participate in cross-site tracking.
            </p>
          </section>

          {/* International Transfers */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">8. International Data Transfers</h2>
            <p className="text-gray-600 leading-relaxed">
              Our Services are operated globally. By using our Services, you consent to the transfer of your information to 
              countries outside your country of residence, which may have different data protection laws. We implement 
              appropriate safeguards, including Standard Contractual Clauses where required, to protect your data during 
              international transfers.
            </p>
          </section>

          {/* Children */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">9. Children's Privacy</h2>
            <p className="text-gray-600 leading-relaxed">
              Our Services are not intended for individuals under the age of 18. We do not knowingly collect personal 
              information from children. If we become aware that we have collected personal information from a child, 
              we will take steps to delete that information.
            </p>
          </section>

          {/* Changes */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">10. Changes to This Policy</h2>
            <p className="text-gray-600 leading-relaxed">
              We may update this Privacy Policy from time to time. We will notify you of any material changes by posting 
              the new policy on this page and updating the "Last updated" date. Your continued use of our Services after 
              any changes constitutes acceptance of the new policy.
            </p>
          </section>

          {/* Contact */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">11. Contact Us</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              If you have questions or concerns about this Privacy Policy or our data practices, please contact us:
            </p>
            <ul className="text-gray-600 space-y-2">
              <li><strong>Email:</strong> privacy@actobotics.net</li>
              <li><strong>GitHub:</strong> github.com/actobotics/ACTO/issues</li>
            </ul>
          </section>

          {/* GDPR */}
          <section className="mb-12">
            <h2 className="text-2xl font-medium mb-4 text-gray-900">12. Additional Information for EU/EEA Users</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              If you are located in the European Union or European Economic Area, you have additional rights under the 
              General Data Protection Regulation (GDPR):
            </p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Legal Basis:</strong> We process your data based on legitimate interests (providing and improving our Services), contract performance, and consent where applicable.</li>
              <li><strong>Data Protection Officer:</strong> You may contact our data protection team at dpo@actobotics.net.</li>
              <li><strong>Supervisory Authority:</strong> You have the right to lodge a complaint with your local data protection authority.</li>
            </ul>
          </section>

          {/* California */}
          <section>
            <h2 className="text-2xl font-medium mb-4 text-gray-900">13. Additional Information for California Residents</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Under the California Consumer Privacy Act (CCPA), California residents have specific rights regarding their personal information:
            </p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Right to Know:</strong> You can request information about the categories and specific pieces of personal information we have collected.</li>
              <li><strong>Right to Delete:</strong> You can request deletion of your personal information, subject to certain exceptions.</li>
              <li><strong>Right to Non-Discrimination:</strong> We will not discriminate against you for exercising your CCPA rights.</li>
              <li><strong>Do Not Sell:</strong> We do not sell personal information as defined under the CCPA.</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}

