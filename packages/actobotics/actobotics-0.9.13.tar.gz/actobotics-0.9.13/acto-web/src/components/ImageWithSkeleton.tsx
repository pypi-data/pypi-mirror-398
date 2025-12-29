import { useState, useEffect } from 'react';

interface ImageWithSkeletonProps {
  src: string;
  className?: string;
  skeletonClassName?: string;
}

export function ImageWithSkeleton({ 
  src, 
  className = '',
  skeletonClassName = ''
}: ImageWithSkeletonProps) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.src = src;
    img.onload = () => setLoaded(true);
    img.onerror = () => setError(true);
  }, [src]);

  if (error) {
    return null;
  }

  return (
    <>
      {!loaded && (
        <div className={`animate-pulse bg-gray-800/50 ${skeletonClassName}`} />
      )}
      <div
        className={`bg-cover bg-center bg-no-repeat transition-opacity duration-500 ${
          loaded ? 'opacity-100' : 'opacity-0'
        } ${className}`}
        style={{ backgroundImage: `url(${src})` }}
      />
    </>
  );
}

