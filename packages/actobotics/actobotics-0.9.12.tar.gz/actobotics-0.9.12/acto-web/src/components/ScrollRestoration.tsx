import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * ScrollRestoration - Scrolls to top on route change
 * Ensures user starts at the top when navigating to a new page
 */
export function ScrollRestoration() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}

