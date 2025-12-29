import {
  Hero,
  Features,
  QuickInstall,
  Products,
  HowItWorks,
  FleetManagement,
  TechStack,
  UseCases,
  OpenSource,
  SEO,
} from '../components';

export function Home() {
  return (
    <>
      <SEO />
      <Hero />
      <Features />
      <QuickInstall />
      <Products />
      <HowItWorks />
      <FleetManagement />
      <TechStack />
      <UseCases />
      <OpenSource />
    </>
  );
}
