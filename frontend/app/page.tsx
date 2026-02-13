'use client';

import { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { createAudit } from '@/lib/api-client';

function formatPhoneBR(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 11);
  if (digits.length <= 2) return digits;
  if (digits.length <= 7) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}

function isValidPhoneBR(value: string): boolean {
  const digits = value.replace(/\D/g, '');
  // Brazilian mobile: 2-digit DDD (11-99) + 9-digit number starting with 9
  return digits.length === 11 && digits[2] === '9';
}

export default function Home() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  );
}

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [businessName, setBusinessName] = useState('');
  const [location, setLocation] = useState('');
  const [whatsapp, setWhatsapp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Capture UTM params from Facebook ads
  const [utmParams, setUtmParams] = useState<{
    utm_source?: string;
    utm_medium?: string;
    utm_campaign?: string;
    utm_content?: string;
  }>({});

  useEffect(() => {
    setUtmParams({
      utm_source: searchParams.get('utm_source') || undefined,
      utm_medium: searchParams.get('utm_medium') || undefined,
      utm_campaign: searchParams.get('utm_campaign') || undefined,
      utm_content: searchParams.get('utm_content') || undefined,
    });
  }, [searchParams]);

  const handleWhatsappChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setWhatsapp(formatPhoneBR(e.target.value));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!businessName || !location) {
      setError('Por favor, preencha o nome da clínica e a cidade.');
      return;
    }

    if (!whatsapp.trim()) {
      setError('WhatsApp é obrigatório para receber seu diagnóstico.');
      return;
    }

    if (!isValidPhoneBR(whatsapp)) {
      setError(
        'Número de WhatsApp inválido. Use DDD + número (ex: 11 99999-1234).'
      );
      return;
    }

    setLoading(true);
    setError('');

    try {
      const audit = await createAudit({
        business_name: businessName,
        location,
        whatsapp: whatsapp.replace(/\D/g, ''),
        ...utmParams,
      });
      router.push(`/diagnostico/${audit.id}`);
    } catch (err: any) {
      console.error('Error creating audit:', err);
      setError(
        err.response?.data?.detail ||
          'Erro ao iniciar diagnóstico. Verifique os dados e tente novamente.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <span className="font-serif text-xl font-bold text-charcoal tracking-tight">
            AI Discovery Optimizer
          </span>
          <span className="text-sm text-muted-foreground">by LK Digital</span>
        </div>
      </header>

      {/* Hero */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h1 className="font-serif text-4xl sm:text-5xl font-bold text-charcoal mb-6 leading-tight">
            Quem domina sua região
            <br />
            <span className="text-gold">nas buscas com IA?</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Descubra em minutos como a inteligência artificial vê sua clínica,
            quem são seus concorrentes mais fortes e o que fazer para aparecer.
          </p>
        </div>

        {/* Form card */}
        <div className="max-w-xl mx-auto">
          <div className="bg-white rounded-2xl shadow-lg border border-border p-8">
            <div className="mb-6">
              <h2 className="font-serif text-2xl font-bold text-charcoal mb-1">
                Diagnóstico Competitivo Gratuito
              </h2>
              <p className="text-muted-foreground text-sm">
                Comparamos sua clínica com o Top 3 da sua região
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Business name */}
              <div>
                <label
                  htmlFor="business_name"
                  className="block text-sm font-medium text-charcoal mb-1.5"
                >
                  Nome da clínica *
                </label>
                <input
                  id="business_name"
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="Ex: Clínica Dental Sorriso"
                  className="w-full px-4 py-3 border border-border rounded-lg bg-cream/50 focus:ring-2 focus:ring-gold focus:border-transparent outline-none transition placeholder:text-muted-foreground/50"
                  disabled={loading}
                />
              </div>

              {/* City */}
              <div>
                <label
                  htmlFor="location"
                  className="block text-sm font-medium text-charcoal mb-1.5"
                >
                  Cidade *
                </label>
                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Ex: São Paulo"
                  className="w-full px-4 py-3 border border-border rounded-lg bg-cream/50 focus:ring-2 focus:ring-gold focus:border-transparent outline-none transition placeholder:text-muted-foreground/50"
                  disabled={loading}
                />
              </div>

              {/* WhatsApp (required) */}
              <div>
                <label
                  htmlFor="whatsapp"
                  className="block text-sm font-medium text-charcoal mb-1.5"
                >
                  WhatsApp *{' '}
                  <span className="text-muted-foreground font-normal">
                    (você receberá o resultado aqui)
                  </span>
                </label>
                <input
                  id="whatsapp"
                  type="tel"
                  value={whatsapp}
                  onChange={handleWhatsappChange}
                  placeholder="(11) 99999-1234"
                  className="w-full px-4 py-3 border border-border rounded-lg bg-cream/50 focus:ring-2 focus:ring-gold focus:border-transparent outline-none transition placeholder:text-muted-foreground/50"
                  disabled={loading}
                  required
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gold hover:bg-gold-dark text-white font-semibold py-4 px-6 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <svg
                      className="w-5 h-5 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Iniciando...
                  </>
                ) : (
                  'Receber Diagnóstico no WhatsApp'
                )}
              </button>
            </form>

            <p className="mt-5 text-xs text-muted-foreground text-center">
              100% gratuito. Resultado direto no seu WhatsApp em menos de 1 minuto.
            </p>
          </div>

          {/* Features */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="w-12 h-12 rounded-full bg-gold-light flex items-center justify-center mx-auto mb-3">
                <svg
                  className="w-6 h-6 text-gold-dark"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <h3 className="font-serif font-semibold text-charcoal mb-1">
                Análise com IA
              </h3>
              <p className="text-sm text-muted-foreground">
                Como o Google Gemini vê sua clínica agora
              </p>
            </div>

            <div>
              <div className="w-12 h-12 rounded-full bg-gold-light flex items-center justify-center mx-auto mb-3">
                <svg
                  className="w-6 h-6 text-gold-dark"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>
              <h3 className="font-serif font-semibold text-charcoal mb-1">
                Top 3 Concorrentes
              </h3>
              <p className="text-sm text-muted-foreground">
                Quem domina as buscas na sua cidade
              </p>
            </div>

            <div>
              <div className="w-12 h-12 rounded-full bg-gold-light flex items-center justify-center mx-auto mb-3">
                <svg
                  className="w-6 h-6 text-gold-dark"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="font-serif font-semibold text-charcoal mb-1">
                Resultado no WhatsApp
              </h3>
              <p className="text-sm text-muted-foreground">
                Receba seu diagnóstico direto no celular
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-white/80 backdrop-blur-sm mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-center text-muted-foreground text-sm">
            &copy; {new Date().getFullYear()} LK Digital. Todos os direitos
            reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}
