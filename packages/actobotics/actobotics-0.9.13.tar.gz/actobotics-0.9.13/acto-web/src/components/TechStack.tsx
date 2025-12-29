import { SiPython, SiFastapi, SiSolana, SiSqlite, SiJsonwebtokens } from 'react-icons/si';
import { TbApi, TbRobot } from 'react-icons/tb';
import { ComponentType } from 'react';

interface TechItem {
  name: string;
  url: string;
  logo?: string;
  icon?: ComponentType<{ className?: string }>;
}

const techStack: TechItem[] = [
  { name: 'Python SDK', url: 'https://python.org', logo: 'python.svg', icon: SiPython },
  { name: 'FastAPI', url: 'https://fastapi.tiangolo.com', logo: 'fastapi.svg', icon: SiFastapi },
  { name: 'Solana', url: 'https://solana.com', logo: 'solana.svg', icon: SiSolana },
  { name: 'Neon', url: 'https://neon.tech', logo: 'neon.svg', icon: TbApi },
  { name: 'SQLite', url: 'https://sqlite.org', logo: 'sqlite.svg', icon: SiSqlite },
  { name: 'JWT Auth', url: 'https://jwt.io', logo: 'jwt.svg', icon: SiJsonwebtokens },
  { name: 'Helius RPC', url: 'https://helius.dev', logo: 'helius.svg', icon: TbApi },
  { name: 'ROS 2', url: 'https://ros.org', logo: 'ros2.svg', icon: TbRobot },
  { name: 'REST API', url: 'https://restfulapi.net', logo: 'rest-api.png', icon: TbApi },
];

export function TechStack() {
  // Triple the array for seamless loop
  const items = [...techStack, ...techStack, ...techStack];

  return (
    <section className="py-16 bg-gray-50 overflow-hidden">
      <div className="relative">
        <div className="flex whitespace-nowrap animate-marquee">
          {items.map((tech, index) => {
            const Icon = tech.icon;
            return (
              <a
                key={index}
                href={tech.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-3 px-8 text-xl font-medium text-gray-900 font-serif hover:text-gray-600 transition-colors"
              >
                {tech.logo ? (
                  <img
                    src={`/logos/${tech.logo}`}
                    alt={tech.name}
                    className="w-6 h-6 object-contain"
                    onError={(e) => {
                      // Hide image on error, fallback icon will show
                      e.currentTarget.style.display = 'none';
                      e.currentTarget.nextElementSibling?.classList.remove('hidden');
                    }}
                  />
                ) : null}
                {Icon && (
                  <Icon className={`w-6 h-6 text-gray-900 ${tech.logo ? 'hidden' : ''}`} />
                )}
                {tech.name}
                <span className="mx-6 text-gray-400">•</span>
              </a>
            );
          })}
        </div>
      </div>
    </section>
  );
}
