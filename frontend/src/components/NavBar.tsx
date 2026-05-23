import { Link } from 'react-router-dom';
import { Home, Wind, Map, MessageSquare, BarChart2 } from 'lucide-react';

interface NavBarProps {
  currentPath: string;
}

const NAV_ITEMS = [
  { path: '/',             icon: Home,          label: 'Главная' },
  { path: '/intervention', icon: Wind,          label: 'Помощь'  },
  { path: '/map',          icon: Map,           label: 'Карта'   },
  { path: '/aac',          icon: MessageSquare, label: 'ААК'     },
  { path: '/doctor',       icon: BarChart2,     label: 'Врач'    },
] as const;

export default function NavBar({ currentPath }: NavBarProps) {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 safe-bottom"
      style={{
        backgroundColor: 'var(--color-surface)',
        borderTop: '1px solid var(--color-border)',
      }}
    >
      <ul
        role="list"
        className="flex items-center justify-around h-16 px-1 m-0 p-0 list-none"
      >
        {NAV_ITEMS.map(({ path, icon: Icon, label }) => {
          const active = currentPath === path;
          return (
            <li key={path} className="flex-1">
              <Link
                to={path}
                aria-current={active ? 'page' : undefined}
                className="flex flex-col items-center justify-center gap-0.5 w-full rounded-xl"
                style={{
                  minHeight: 48,
                  textDecoration: 'none',
                  color: active ? 'var(--color-brand)' : 'var(--color-muted)',
                  fontWeight: active ? 600 : 400,
                  fontSize: '0.65rem',
                  transition: 'color 200ms ease-in-out',
                }}
              >
                <Icon
                  size={20}
                  strokeWidth={active ? 2.5 : 1.8}
                  aria-hidden="true"
                />
                <span>{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
