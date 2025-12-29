import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export function Logo() {
  const [logoColor, setLogoColor] = useState<'white' | 'black'>('white');

  useEffect(() => {
    const handleScroll = () => {
      const heroSection = document.querySelector('section');
      const solutionSection = document.getElementById('solution-section');
      
      // Check if we're in the dark solution section
      if (solutionSection) {
        const rect = solutionSection.getBoundingClientRect();
        const isInSolutionSection = rect.top <= 100 && rect.bottom >= 100;
        
        if (isInSolutionSection) {
          setLogoColor('white');
          return;
        }
      }
      
      // Default behavior: white logo in hero, black logo after hero
      if (heroSection) {
        const heroBottom = heroSection.offsetHeight;
        setLogoColor(window.scrollY > heroBottom - 100 ? 'black' : 'white');
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll();

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <Link to="/" className="fixed top-4 left-4 md:top-8 md:left-8 z-50">
      <img
        src={logoColor === 'white' ? '/logo_w.png' : '/logo_b.png'}
        alt="Logo"
        className="h-8 md:h-12 w-auto transition-opacity duration-300"
      />
    </Link>
  );
}
