import { Helmet } from 'react-helmet-async';

interface SEOProps {
  title?: string;
  description?: string;
  keywords?: string;
  image?: string;
  url?: string;
  type?: string;
}

export function SEO({
  title = 'ACTO - Proof of Execution for Robotics',
  description = 'Trust is good. Cryptographic proof is better. Turn every robotic action into undeniable, verifiable truth with ACTO\'s robotics-first proof-of-execution toolkit.',
  keywords = 'robotics, proof of execution, cryptographic proof, autonomous systems, web3, blockchain, verification, fleet management',
  image = 'https://actobotics.net/banner.png',
  url = 'https://actobotics.net',
  type = 'website',
}: SEOProps) {
  const fullTitle = title.includes('ACTO') ? title : `${title} | ACTO`;

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      
      {/* Open Graph / Facebook */}
      <meta property="og:type" content={type} />
      <meta property="og:url" content={url} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      
      {/* Twitter */}
      <meta property="twitter:card" content="summary_large_image" />
      <meta property="twitter:url" content={url} />
      <meta property="twitter:title" content={fullTitle} />
      <meta property="twitter:description" content={description} />
      <meta property="twitter:image" content={image} />
      <meta property="twitter:site" content="@actoboticsnet" />
      
      {/* Additional SEO */}
      <meta name="robots" content="index, follow" />
      <meta name="language" content="English" />
      <meta name="author" content="ACTO" />
      <link rel="canonical" href={url} />
    </Helmet>
  );
}

