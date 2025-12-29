import { useEffect, useRef, useState, ReactNode } from 'react';

type AnimationType = 
  | 'fade-up' 
  | 'fade-down' 
  | 'fade-left' 
  | 'fade-right' 
  | 'scale-up' 
  | 'scale-down'
  | 'flip-up'
  | 'slide-left'
  | 'slide-right'
  | 'zoom-in'
  | 'blur-in';

interface ScrollAnimationProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  duration?: number;
  animation?: AnimationType;
  once?: boolean;
}

export function ScrollAnimation({ 
  children, 
  className = '', 
  delay = 0,
  duration = 900,
  animation = 'fade-up',
  once = true,
}: ScrollAnimationProps) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && (!hasAnimated.current || !once)) {
          setTimeout(() => {
            setIsVisible(true);
            hasAnimated.current = true;
          }, delay);
        } else if (!once && !entry.isIntersecting) {
          setIsVisible(false);
        }
      },
      {
        threshold: 0.05,
        rootMargin: '0px 0px -50px 0px',
      }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [delay, once]);

  const getAnimationClasses = () => {
    const base = `transition-all`;
    const easingClass = `ease-[cubic-bezier(0.25,0.1,0.25,1)]`;
    
    const animations = {
      'fade-up': isVisible 
        ? 'opacity-100 translate-y-0' 
        : 'opacity-0 translate-y-6',
      'fade-down': isVisible 
        ? 'opacity-100 translate-y-0' 
        : 'opacity-0 -translate-y-6',
      'fade-left': isVisible 
        ? 'opacity-100 translate-x-0' 
        : 'opacity-0 translate-x-6',
      'fade-right': isVisible 
        ? 'opacity-100 translate-x-0' 
        : 'opacity-0 -translate-x-6',
      'scale-up': isVisible 
        ? 'opacity-100 scale-100' 
        : 'opacity-0 scale-95',
      'scale-down': isVisible 
        ? 'opacity-100 scale-100' 
        : 'opacity-0 scale-105',
      'flip-up': isVisible 
        ? 'opacity-100 rotate-0' 
        : 'opacity-0 -rotate-3',
      'slide-left': isVisible 
        ? 'translate-x-0' 
        : 'translate-x-8',
      'slide-right': isVisible 
        ? 'translate-x-0' 
        : '-translate-x-8',
      'zoom-in': isVisible 
        ? 'opacity-100 scale-100' 
        : 'opacity-0 scale-90',
      'blur-in': isVisible 
        ? 'opacity-100 blur-0' 
        : 'opacity-0 blur-[8px]',
    };

    return `${base} ${easingClass} ${animations[animation]}`;
  };

  return (
    <div
      ref={ref}
      className={`${getAnimationClasses()} ${className}`}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  );
}

