import { Bot, Activity, FolderTree, Clock, Cpu, Battery, HardDrive, ArrowRight } from 'lucide-react';
import { config } from '../config';
import { ScrollAnimation } from './ScrollAnimation';

const features = [
  {
    icon: Bot,
    title: 'Device Overview',
    description: 'See all your robots in one place. Track online/offline status, last activity, and total proof count per device. Quickly identify which robots need attention.',
  },
  {
    icon: FolderTree,
    title: 'Device Groups',
    description: 'Organize robots into logical groups like "Warehouse A", "Production Line 2", or "Test Fleet". Filter and manage devices by group for easier operations.',
  },
  {
    icon: Activity,
    title: 'Health Monitoring',
    description: 'Report and track CPU usage, memory consumption, and battery levels. Set up alerts when devices report critical health metrics.',
  },
  {
    icon: Clock,
    title: 'Activity History',
    description: 'View complete proof history per device. See when each robot was active, what tasks it executed, and verify the full audit trail.',
  },
];

const stats = [
  { icon: Bot, label: 'Active Devices', value: '24' },
  { icon: Cpu, label: 'Avg. CPU', value: '42%' },
  { icon: Battery, label: 'Avg. Battery', value: '78%' },
  { icon: HardDrive, label: 'Proofs Today', value: '1,247' },
];

export function FleetManagement() {
  return (
    <section className="border-t border-gray-100 relative">
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/hero3.png)' }}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-white/90 via-white/70 to-white/40" />
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-24 relative">
        <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center">
          {/* Left: Content */}
          <div>
            <ScrollAnimation animation="blur-in" delay={0}>
              <p className="text-sm text-gray-400 mb-4 tracking-wide uppercase">Fleet Management</p>
              <h2 className="text-3xl md:text-4xl font-medium mb-6 tracking-tight">
                Monitor your entire robot fleet
              </h2>
              <p className="text-gray-600 leading-relaxed mb-8">
                When you run dozens or hundreds of robots, you need visibility. ACTO's fleet management 
                gives you real-time overview of all your devices, their health status, and execution history. 
                Every proof submitted automatically updates your fleet dashboard.
              </p>
            </ScrollAnimation>

            <div className="space-y-6 mb-8">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <ScrollAnimation key={feature.title} animation="blur-in" delay={120 + index * 60}>
                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-10 h-10 bg-white border border-gray-200 rounded-lg flex items-center justify-center">
                        <Icon className="w-5 h-5 text-gray-700" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 mb-1">{feature.title}</h3>
                        <p className="text-sm text-gray-600 leading-relaxed">{feature.description}</p>
                      </div>
                    </div>
                  </ScrollAnimation>
                );
              })}
            </div>

            <ScrollAnimation animation="blur-in" delay={360}>
              <a
                href={config.links.dashboard}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
              >
                View your fleet
                <ArrowRight size={14} />
              </a>
            </ScrollAnimation>
          </div>

          {/* Right: Mock Dashboard */}
          <ScrollAnimation animation="blur-in" delay={180}>
            <div className="bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-900">Fleet Overview</h3>
                <span className="text-xs text-gray-500">Live</span>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-px bg-gray-100">
              {stats.map((stat) => {
                const Icon = stat.icon;
                return (
                  <div key={stat.label} className="bg-white p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4 text-gray-400" />
                      <span className="text-xs text-gray-500">{stat.label}</span>
                    </div>
                    <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                  </div>
                );
              })}
            </div>

            {/* Device List */}
            <div className="border-t border-gray-100">
              <div className="px-4 py-3 bg-gray-50/50 border-b border-gray-100">
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Recent Activity</span>
              </div>
              <div className="divide-y divide-gray-100">
                {[
                  { name: 'robot-alpha-01', status: 'online', task: 'pick-place-247', time: '2m ago' },
                  { name: 'robot-beta-03', status: 'online', task: 'inspection-089', time: '5m ago' },
                  { name: 'drone-warehouse-12', status: 'offline', task: 'patrol-night-02', time: '2h ago' },
                ].map((device) => (
                  <div key={device.name} className="px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${device.status === 'online' ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{device.name}</p>
                        <p className="text-xs text-gray-500">{device.task}</p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-400">{device.time}</span>
                  </div>
                ))}
              </div>
            </div>
            </div>
          </ScrollAnimation>
        </div>
      </div>
    </section>
  );
}

