import { useState, useEffect, useRef } from 'react';

interface LoadingScreenProps {
  imagesToPreload?: string[];
  minLoadTime?: number;
  maxLoadTime?: number;
}

// Check if initial loading has already completed (persists via sessionStorage)
const STORAGE_KEY = 'acto_images_loaded';

function checkIfAlreadyLoaded(): boolean {
  try {
    return sessionStorage.getItem(STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

function markAsLoaded(): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, 'true');
  } catch {
    // Ignore storage errors
  }
}

export function LoadingScreen({
  imagesToPreload = ['/hero.png'],
  minLoadTime = 300,
  maxLoadTime = 3000,
}: LoadingScreenProps) {
  const alreadyLoaded = checkIfAlreadyLoaded();
  
  // If already loaded once, don't show loading screen at all
  const [isLoading, setIsLoading] = useState(!alreadyLoaded);
  const [isVisible, setIsVisible] = useState(!alreadyLoaded);
  const loadingStarted = useRef(false);

  useEffect(() => {
    // Skip if already loaded or loading already started
    if (alreadyLoaded || loadingStarted.current) {
      return;
    }

    loadingStarted.current = true;
    let imagesLoaded = 0;
    let minTimeElapsed = false;
    let loadingComplete = false;

    const checkComplete = () => {
      if (loadingComplete) return;

      const allImagesLoaded = imagesLoaded >= imagesToPreload.length;
      
      if (allImagesLoaded && minTimeElapsed) {
        loadingComplete = true;
        markAsLoaded(); // Mark as globally complete in sessionStorage
        setIsLoading(false);
        // Wait for fade out animation before removing from DOM
        setTimeout(() => setIsVisible(false), 400);
      }
    };

    // Minimum load time for smooth UX
    setTimeout(() => {
      minTimeElapsed = true;
      checkComplete();
    }, minLoadTime);

    // Preload ALL images at once
    imagesToPreload.forEach((src) => {
      const img = new Image();
      img.src = src;

      const handleLoad = () => {
        imagesLoaded++;
        checkComplete();
      };

      img.onload = handleLoad;
      img.onerror = handleLoad; // Continue even if image fails

      // Handle already cached images
      if (img.complete) {
        handleLoad();
      }
    });

    // Fallback: max load time
    const fallbackTimer = setTimeout(() => {
      if (!loadingComplete) {
        loadingComplete = true;
        markAsLoaded();
        setIsLoading(false);
        setTimeout(() => setIsVisible(false), 400);
      }
    }, maxLoadTime);

    return () => clearTimeout(fallbackTimer);
  }, [imagesToPreload, minLoadTime, maxLoadTime]);

  // Don't render anything if not visible
  if (!isVisible) return null;

  return (
    <div className={`loading-screen ${!isLoading ? 'loading-screen--hidden' : ''}`}>
      <img src="/logo_w.png" alt="ACTO" className="loading-logo" />
      <div className="loading-spinner" />
      <div className="loading-text">Loading...</div>
    </div>
  );
}

