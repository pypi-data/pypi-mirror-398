import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { Navigation, Footer, Logo, LoadingScreen, ScrollToTop, ScrollRestoration } from './components';
import { Home, About, Privacy, Terms, Unlock, NotFound, UseCaseDetail, FAQ, Comparison } from './pages';

// ============================================
// ACCESS CONTROL - Set to false to disable
// ============================================
const ACCESS_REQUIRED = true;
// ============================================

function App() {
  const [hasAccess, setHasAccess] = useState(!ACCESS_REQUIRED);

  useEffect(() => {
    // Check localStorage for access
    if (ACCESS_REQUIRED) {
      const access = localStorage.getItem('site_access');
      if (access === 'granted') {
        setHasAccess(true);
      }
    }
  }, []);

  const handleUnlock = () => {
    setHasAccess(true);
  };

  // Show unlock page if access required and not granted
  if (ACCESS_REQUIRED && !hasAccess) {
    return <Unlock onUnlock={handleUnlock} />;
  }

  return (
    <HelmetProvider>
      <BrowserRouter>
        <ScrollRestoration />
        <LoadingScreen imagesToPreload={['/hero.png', '/hero2.png', '/hero3.png', '/hero4.png', '/bg1.png', '/bg2.png', '/bg3.png', '/bg4.png']} />
        <div className="min-h-screen bg-white text-gray-900">
          <Logo />
          <Navigation />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/about" element={<About />} />
              <Route path="/faq" element={<FAQ />} />
              <Route path="/comparison" element={<Comparison />} />
              <Route path="/use-cases/:slug" element={<UseCaseDetail />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/terms" element={<Terms />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Footer />
          <ScrollToTop />
        </div>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
