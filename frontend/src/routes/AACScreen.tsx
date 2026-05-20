import { useEffect, useState } from 'react';
import { MessageSquare, Brain, MapPin, ShieldOff, Phone } from 'lucide-react';

type LucideComponent = React.ElementType;

const ICON_MAP: Record<string, LucideComponent> = {
  Brain,
  MapPin,
  ShieldOff,
  Phone,
  MessageSquare,
};

interface AACCard {
  id: string;
  icon: string;
  text_ru: string;
  text_en: string;
}

const FALLBACK_CARDS: AACCard[] = [
  { id: 'autism', icon: 'Brain',    text_ru: 'У меня аутизм. Я всё понимаю, но не могу говорить.', text_en: 'I have autism. I understand, but cannot speak.' },
  { id: 'quiet',  icon: 'MapPin',   text_ru: 'Помогите мне попасть в тихое место.',                 text_en: 'Please help me get to a quiet place.'         },
  { id: 'space',  icon: 'ShieldOff',text_ru: 'Не трогайте меня. Пожалуйста, отойдите.',             text_en: 'Do not touch me. Please step back.'           },
  { id: 'call',   icon: 'Phone',    text_ru: 'Позвоните моему близкому.',                            text_en: 'Please call my emergency contact.'            },
];

export default function AACScreen() {
  const [lang, setLang] = useState<'ru' | 'en'>('ru');
  const [active, setActive] = useState<string | null>(null);
  const [cards, setCards] = useState<AACCard[]>(FALLBACK_CARDS);

  useEffect(() => {
    fetch('/aac-cards.json')
      .then(r => r.json())
      .then((data: AACCard[]) => { if (Array.isArray(data) && data.length > 0) setCards(data); })
      .catch(() => {});
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '24px 16px 16px', minHeight: '100%' }}>
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <MessageSquare size={24} strokeWidth={2} style={{ color: 'var(--color-calm)' }} />
        <h1 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, color: 'var(--color-ink)', flex: 1 }}>
          ААК-карточки
        </h1>

        {/* Language toggle */}
        <div
          role="group"
          aria-label="Выбор языка карточек"
          style={{ display: 'flex', borderRadius: '0.5rem', overflow: 'hidden',
            border: '1.5px solid var(--color-border)' }}
        >
          {(['ru', 'en'] as const).map(l => (
            <button
              key={l}
              onClick={() => setLang(l)}
              style={{
                padding: '6px 12px',
                border: 'none',
                backgroundColor: lang === l ? 'var(--color-calm)' : 'var(--color-surface)',
                color: 'var(--color-ink)',
                fontSize: '0.8rem',
                fontWeight: lang === l ? 600 : 400,
                cursor: 'pointer',
                transition: 'background-color 200ms ease-in-out',
              }}
              aria-pressed={lang === l}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </header>

      {/* Cards grid 2×2 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {cards.map(({ id, icon, text_ru, text_en }) => {
          const Icon = ICON_MAP[icon] ?? Brain;
          const text = lang === 'ru' ? text_ru : text_en;
          const isActive = active === id;
          return (
            <button
              key={id}
              onClick={() => setActive(isActive ? null : id)}
              style={{
                minHeight: 120,
                padding: '16px 12px',
                backgroundColor: isActive ? '#EEF7F1' : 'var(--color-surface)',
                border: `2px solid ${isActive ? 'var(--color-calm)' : 'var(--color-border)'}`,
                borderRadius: '1rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'border-color 200ms ease-in-out, background-color 200ms ease-in-out',
              }}
              aria-pressed={isActive}
              aria-label={text}
            >
              <Icon
                size={40}
                strokeWidth={1.8}
                style={{ color: isActive ? 'var(--color-calm)' : 'var(--color-ink)', flexShrink: 0 }}
                aria-hidden="true"
              />
              <span style={{
                fontSize: '0.78rem',
                fontWeight: 400,
                color: 'var(--color-ink)',
                lineHeight: 1.5,
              }}>
                {text}
              </span>
            </button>
          );
        })}
      </div>

      {/* Emergency call */}
      <a
        href="tel:+79991234567"
        style={{
          minHeight: 64,
          width: '100%',
          backgroundColor: 'var(--color-alert)',
          color: '#FFFFFF',
          border: 'none',
          borderRadius: '1rem',
          fontSize: '1.05rem',
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          marginTop: 'auto',
          textDecoration: 'none',
          transition: 'opacity 200ms ease-in-out',
        }}
        aria-label="Вызвать близкого — экстренный контакт"
      >
        <Phone size={22} strokeWidth={2} aria-hidden="true" />
        Вызвать близкого
      </a>
    </div>
  );
}
