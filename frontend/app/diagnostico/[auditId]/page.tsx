'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { getAudit, sendWhatsApp, getReportDownloadUrl, type Audit } from '@/lib/api-client';
import { getScoreColor, getScoreLabel } from '@/lib/utils';

/* ------------------------------------------------------------------ */
/* Facebook Pixel helper (safe if pixel not loaded)                    */
/* ------------------------------------------------------------------ */

function fbTrack(event: string, data?: Record<string, unknown>) {
  if (typeof window !== 'undefined' && typeof (window as any).fbq === 'function') {
    (window as any).fbq('track', event, data);
  }
}

/* ------------------------------------------------------------------ */
/* Micro-engagement progress steps                                     */
/* ------------------------------------------------------------------ */

const BASE_STEPS = [
  { label: 'Localizando sua clínica...', durationMs: 2000 },
  { label: 'Identificando seus principais concorrentes...', durationMs: 4000 },
  { label: 'Analisando presença no Google...', durationMs: 6000 },
  { label: 'Consultando inteligência artificial...', durationMs: 10000 },
  { label: 'Comparando com o Top 3 da sua região...', durationMs: 6000 },
];
const WHATSAPP_STEP = { label: 'Enviando resultado para seu WhatsApp...', durationMs: 4000 };
const PDF_STEP = { label: 'Preparando seu relatório para download...', durationMs: 4000 };

const MIN_DISPLAY_MS = 45000; // minimum 45 seconds even if backend is faster

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={3}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 13l4 4L19 7" strokeDasharray="24" className="animate-checkDraw" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/* Main page component                                                 */
/* ------------------------------------------------------------------ */

export default function DiagnosticoPage() {
  const params = useParams();
  const auditId = params.auditId as string;

  const [audit, setAudit] = useState<Audit | null>(null);
  const [error, setError] = useState('');

  // Progress UI state
  const [currentStep, setCurrentStep] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [backendDone, setBackendDone] = useState(false);
  const [progressStarted] = useState(() => Date.now());

  // WhatsApp retry state
  const [resending, setResending] = useState(false);
  const [resendResult, setResendResult] = useState<'success' | 'error' | null>(null);

  // Build steps list based on whether WhatsApp was provided
  const hasWhatsApp = !!audit?.whatsapp_number;
  const STEPS = [...BASE_STEPS, hasWhatsApp ? WHATSAPP_STEP : PDF_STEP];

  // ---- Poll backend ----
  const pollAudit = useCallback(async () => {
    try {
      const data = await getAudit(auditId);
      setAudit(data);
      if (data.status === 'completed' || data.status === 'failed') {
        setBackendDone(true);
        // Fire FB Pixel Lead event on completion
        if (data.status === 'completed') {
          fbTrack('Lead', {
            content_name: 'Diagnostic Audit',
            content_category: 'audit_completed',
          });
        }
      } else {
        setTimeout(pollAudit, 3000);
      }
    } catch {
      setError('Erro ao carregar diagnóstico.');
    }
  }, [auditId]);

  useEffect(() => {
    if (auditId) pollAudit();
  }, [auditId, pollAudit]);

  // ---- Timed progress steps ----
  useEffect(() => {
    let elapsed = 0;
    const timers: NodeJS.Timeout[] = [];

    STEPS.forEach((step, idx) => {
      elapsed += step.durationMs;
      timers.push(setTimeout(() => setCurrentStep(idx + 1), elapsed));
    });

    return () => timers.forEach(clearTimeout);
  }, []);

  // ---- Show results after BOTH conditions met: backend done + minimum time passed ----
  useEffect(() => {
    if (!backendDone) return;

    const elapsed = Date.now() - progressStarted;
    const remaining = Math.max(MIN_DISPLAY_MS - elapsed, 0);

    const timer = setTimeout(() => {
      setCurrentStep(STEPS.length);
      setTimeout(() => setShowResults(true), 800); // small pause after last check
    }, remaining);

    return () => clearTimeout(timer);
  }, [backendDone, progressStarted]);

  // ---- WhatsApp resend handler ----
  const handleResendWhatsApp = async () => {
    setResending(true);
    setResendResult(null);
    try {
      const result = await sendWhatsApp(auditId);
      setResendResult(result.success ? 'success' : 'error');
      // Refresh audit data to update whatsapp_sent status
      const data = await getAudit(auditId);
      setAudit(data);
    } catch {
      setResendResult('error');
    } finally {
      setResending(false);
    }
  };

  // ---- Error state ----
  if (error || (audit?.status === 'failed')) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="font-serif text-2xl font-bold text-charcoal mb-2">Erro</h2>
          <p className="text-muted-foreground">{error || audit?.error_message || 'Ocorreu um erro inesperado.'}</p>
          <a href="/" className="inline-block mt-6 text-gold hover:text-gold-dark font-medium">
            Tentar novamente
          </a>
        </div>
      </div>
    );
  }

  // ---- Progress / micro-engagement screen ----
  if (!showResults) {
    const progress = Math.min((currentStep / STEPS.length) * 100, 100);

    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-10 max-w-lg w-full">
          <div className="text-center mb-8">
            <span className="font-serif text-xl font-bold text-charcoal">AI Discovery Optimizer</span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-gold-light rounded-full mb-8 overflow-hidden">
            <div
              className="h-full bg-gold rounded-full transition-all duration-700 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Steps */}
          <div className="space-y-4">
            {STEPS.map((step, idx) => {
              const done = currentStep > idx;
              const active = currentStep === idx;
              return (
                <div
                  key={idx}
                  className={`flex items-center gap-3 transition-opacity duration-300 ${
                    done || active ? 'opacity-100' : 'opacity-30'
                  }`}
                >
                  {done ? (
                    <div className="w-6 h-6 rounded-full bg-gold flex items-center justify-center flex-shrink-0">
                      <CheckIcon className="w-4 h-4 text-white" />
                    </div>
                  ) : active ? (
                    <div className="w-6 h-6 rounded-full border-2 border-gold flex items-center justify-center flex-shrink-0">
                      <div className="w-2 h-2 rounded-full bg-gold animate-pulseGold" />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full border-2 border-border flex-shrink-0" />
                  )}
                  <span
                    className={`text-sm ${
                      done ? 'text-charcoal' : active ? 'text-charcoal font-medium' : 'text-muted-foreground'
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>

          {currentStep >= STEPS.length && !showResults && (
            <div className="mt-8 text-center animate-fadeInSlide">
              <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
                <CheckIcon className="w-6 h-6 text-green-600" />
              </div>
              <p className="font-serif text-lg font-bold text-charcoal">Pronto!</p>
              <p className="text-sm text-muted-foreground mt-1">
                {audit?.whatsapp_number
                  ? `Seu diagnóstico foi enviado para o WhatsApp (${audit.whatsapp_number})`
                  : 'Seu diagnóstico está pronto para download!'}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ---- Results screen ----
  if (!audit || audit.status !== 'completed') return null;

  const score = audit.discovery_score || 0;
  const scoreLabel = getScoreLabel(score);
  const scoreColor = getScoreColor(score);
  const comp = audit.competitor_analysis || {} as any;
  const competitors: any[] = comp.competitors || [];
  const matrix = comp.comparison_matrix || {};
  const biz = matrix.your_business || {};
  const gaps: any[] = comp.gaps || [];

  const medalEmoji = ['', '', ''];

  // WhatsApp delivery status
  const wasSent = audit.whatsapp_sent;
  const waError = audit.whatsapp_error;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <span className="font-serif text-xl font-bold text-charcoal">AI Discovery Optimizer</span>
          <a href="/" className="text-sm text-gold hover:text-gold-dark font-medium">Novo Diagnóstico</a>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
        {/* WhatsApp delivery notice */}
        {wasSent && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center text-sm text-green-800">
            Seu diagnóstico foi enviado para o WhatsApp ({audit.whatsapp_number}).
            <br />
            <strong>Fique atento ao WhatsApp. Nosso especialista vai te explicar os resultados em seguida.</strong>
          </div>
        )}

        {/* WhatsApp error — show retry button */}
        {!wasSent && waError && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-center text-sm text-yellow-800">
            <p className="mb-2">
              Não conseguimos enviar o diagnóstico para o WhatsApp ({audit.whatsapp_number}).
            </p>
            <button
              onClick={handleResendWhatsApp}
              disabled={resending}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium transition disabled:opacity-50"
            >
              {resending ? 'Reenviando...' : 'Reenviar para WhatsApp'}
            </button>
            {resendResult === 'success' && (
              <p className="mt-2 text-green-700 font-medium">Enviado com sucesso!</p>
            )}
            {resendResult === 'error' && (
              <p className="mt-2 text-red-700 font-medium">Falha ao reenviar. Tente novamente.</p>
            )}
          </div>
        )}

        {/* WhatsApp not sent yet but no error (still pending) */}
        {audit.whatsapp_number && !wasSent && !waError && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-center text-sm text-blue-800">
            Enviando diagnóstico para o WhatsApp ({audit.whatsapp_number})...
            <br />
            <span className="text-xs">O resultado também está disponível abaixo.</span>
          </div>
        )}

        {/* Score hero */}
        <div className="bg-white rounded-2xl shadow-lg border border-border p-8 text-center">
          <h1 className="font-serif text-3xl font-bold text-charcoal mb-2">Diagnóstico Competitivo</h1>
          <p className="text-muted-foreground mb-6">Análise completa da sua posição no mercado</p>

          <div className="flex flex-wrap justify-center gap-3 mb-8">
            <a
              href={getReportDownloadUrl(auditId, 'pdf')}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium transition"
            >
              Baixar PDF
            </a>
            <a
              href={getReportDownloadUrl(auditId, 'text')}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-charcoal text-white rounded-lg hover:bg-charcoal/80 text-sm font-medium transition"
            >
              Baixar texto
            </a>
          </div>

          {/* Score gauge */}
          <div className="flex flex-col items-center">
            <div
              className="w-44 h-44 rounded-full flex items-center justify-center mb-4 relative"
              style={{
                background: `conic-gradient(${scoreColor} ${score * 3.6}deg, hsl(var(--border)) 0deg)`,
              }}
            >
              <div className="w-36 h-36 bg-white rounded-full flex flex-col items-center justify-center">
                <span className="text-5xl font-bold" style={{ color: scoreColor }}>{score}</span>
                <span className="text-xs text-muted-foreground">de 100</span>
              </div>
            </div>
            <span
              className="inline-block px-4 py-1.5 rounded-full text-sm font-bold"
              style={{ backgroundColor: scoreColor + '20', color: scoreColor }}
            >
              {scoreLabel}
            </span>
          </div>
        </div>

        {/* Section 1: Quem domina sua região */}
        {competitors.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg border border-border p-8">
            <h2 className="font-serif text-2xl font-bold text-charcoal mb-6">
              1. Quem domina sua região
            </h2>
            <div className="space-y-4">
              {competitors.slice(0, 3).map((c: any, i: number) => (
                <div key={i} className="flex items-start gap-4 p-4 rounded-xl bg-cream/50 border border-border">
                  <span className="text-2xl flex-shrink-0">{medalEmoji[i] || `#${i + 1}`}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-serif font-bold text-charcoal">{c.name}</span>
                      {c.ai_mentioned && (
                        <span className="text-xs bg-gold-light text-gold-dark px-2 py-0.5 rounded-full font-medium">
                          IA recomenda
                        </span>
                      )}
                    </div>
                    <div className="flex gap-4 mt-1 text-sm text-muted-foreground">
                      <span>&#11088; {c.rating || 'N/A'}</span>
                      <span>{c.total_reviews || 0} avaliações</span>
                      <span>{c.photos_count || 0} fotos</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Section 2: Onde sua clínica está */}
        {biz.name && (
          <div className="bg-white rounded-2xl shadow-lg border border-border p-8">
            <h2 className="font-serif text-2xl font-bold text-charcoal mb-6">
              2. Onde sua clínica está
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Nota', value: biz.rating ?? 'N/A', comp: matrix.competitor_average?.rating },
                { label: 'Avaliações', value: biz.total_reviews ?? 0, comp: matrix.competitor_average?.total_reviews },
                { label: 'Fotos', value: biz.photos_count ?? 0, comp: matrix.competitor_average?.photos_count },
                { label: 'Site', value: biz.has_website ? 'Sim' : 'Não', comp: null },
              ].map((item, i) => {
                const behind =
                  item.comp != null &&
                  typeof item.value === 'number' &&
                  item.value < item.comp;
                return (
                  <div key={i} className="text-center p-4 rounded-xl bg-cream/50 border border-border">
                    <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
                    <p className={`text-2xl font-bold ${behind ? 'text-red-500' : 'text-charcoal'}`}>
                      {item.value}
                    </p>
                    {item.comp != null && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Média: {item.comp}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Section 3: O que separa você do Top 3 */}
        {gaps.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg border border-border p-8">
            <h2 className="font-serif text-2xl font-bold text-charcoal mb-6">
              3. O que separa você do Top 3
            </h2>
            <div className="space-y-3">
              {gaps.slice(0, 4).map((gap: any, i: number) => (
                <div
                  key={i}
                  className={`p-4 rounded-xl border-l-4 ${
                    gap.severity === 'high'
                      ? 'border-l-red-500 bg-red-50/50'
                      : 'border-l-yellow-500 bg-yellow-50/50'
                  }`}
                >
                  <p className="text-sm text-charcoal font-medium">{gap.message}</p>
                  {gap.action && (
                    <p className="text-xs text-muted-foreground mt-1">{gap.action}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Perception */}
        {audit.ai_summary && (
          <div className="bg-white rounded-2xl shadow-lg border border-border p-8">
            <h2 className="font-serif text-2xl font-bold text-charcoal mb-4">Como a IA vê você</h2>
            <p className="text-muted-foreground mb-4">{audit.ai_summary.ai_summary}</p>

            {audit.ai_summary.key_attributes?.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-medium text-charcoal mb-2">Atributos identificados:</p>
                <div className="flex flex-wrap gap-2">
                  {audit.ai_summary.key_attributes.map((attr: string, idx: number) => (
                    <span key={idx} className="px-3 py-1 bg-gold-light text-gold-dark rounded-full text-sm">
                      {attr}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {audit.ai_summary.missing_signals?.length > 0 && (
              <div>
                <p className="text-sm font-medium text-charcoal mb-2">Informações faltantes:</p>
                <ul className="space-y-1">
                  {audit.ai_summary.missing_signals.map((s: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className="text-yellow-500 mt-0.5">&#9888;</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Recommendations */}
        {audit.recommendations && audit.recommendations.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg border border-border p-8">
            <h2 className="font-serif text-2xl font-bold text-charcoal mb-6">Ações Prioritárias</h2>
            <div className="space-y-3">
              {audit.recommendations.map((rec: any, idx: number) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border-l-4"
                  style={{
                    borderColor:
                      rec.priority === 'high' ? '#ef4444' : rec.priority === 'medium' ? '#f59e0b' : '#9ca3af',
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium text-charcoal">{rec.action}</p>
                    <span className="text-xs font-bold text-green-600 whitespace-nowrap">{rec.impact}</span>
                  </div>
                  {rec.detail && (
                    <p className="text-xs text-muted-foreground mt-1">{rec.detail}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <div className="bg-charcoal rounded-2xl shadow-lg p-8 text-center text-white">
          <h2 className="font-serif text-3xl font-bold mb-4">
            Quer fechar essas lacunas?
          </h2>
          <p className="text-lg mb-6 opacity-80">
            Nosso especialista pode implementar todas essas otimizações e monitorar seus resultados.
          </p>
          <a
            href="https://wa.me/5511999999999?text=Olá! Vi meu diagnóstico competitivo e quero otimizar minha clínica"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-gold hover:bg-gold-dark text-white font-bold py-4 px-8 rounded-lg transition"
          >
            Falar com Especialista
          </a>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-white/80 backdrop-blur-sm mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-center text-muted-foreground text-sm">
            &copy; {new Date().getFullYear()} LK Digital. Todos os direitos reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}
