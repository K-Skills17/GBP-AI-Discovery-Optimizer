'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getAudit, type Audit } from '@/lib/api-client';
import { Loader2, AlertCircle, CheckCircle2, TrendingUp, MessageSquare, Camera, Sparkles } from 'lucide-react';
import { getScoreColor, getScoreLabel } from '@/lib/utils';

export default function ResultadoPage() {
  const params = useParams();
  const auditId = params.auditId as string;
  
  const [audit, setAudit] = useState<Audit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!auditId) return;

    const pollAudit = async () => {
      try {
        const data = await getAudit(auditId);
        setAudit(data);

        // If still processing, poll again
        if (data.status === 'pending' || data.status === 'processing') {
          setTimeout(pollAudit, 3000); // Poll every 3 seconds
        } else {
          setLoading(false);
        }
      } catch (err: any) {
        console.error('Error fetching audit:', err);
        setError('Erro ao carregar auditoria');
        setLoading(false);
      }
    };

    pollAudit();
  }, [auditId]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Erro</h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  if (loading || !audit || audit.status !== 'completed') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-12 max-w-md w-full text-center">
          <Loader2 className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-6" />
          <h2 className="text-2xl font-bold text-gray-900 mb-3">
            Analisando seu perfil...
          </h2>
          <p className="text-gray-600 mb-6">
            Estamos processando dados do Google Maps, avaliações e fazendo análise com IA.
            Isso pode levar até 2 minutos.
          </p>
          <div className="space-y-2 text-left">
            <div className="flex items-center gap-3 text-sm">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <span className="text-gray-700">Dados coletados</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              {audit?.status === 'processing' ? (
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
              )}
              <span className="text-gray-700">Análise de IA em andamento...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const score = audit.discovery_score || 0;
  const scoreLabel = getScoreLabel(score);
  const scoreColor = getScoreColor(score);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">
                AI Discovery Optimizer
              </span>
            </div>
            <a 
              href="/"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Nova Auditoria
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Score Hero */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 mb-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Resultado da Auditoria
            </h1>
            <p className="text-gray-600">
              Análise completa de como a IA vê seu negócio
            </p>
          </div>

          <div className="flex flex-col items-center">
            <div 
              className="w-48 h-48 rounded-full flex items-center justify-center mb-6 relative"
              style={{
                background: `conic-gradient(${scoreColor} ${score * 3.6}deg, #e5e7eb 0deg)`
              }}
            >
              <div className="w-40 h-40 bg-white rounded-full flex flex-col items-center justify-center">
                <div className="text-5xl font-bold" style={{ color: scoreColor }}>
                  {score}
                </div>
                <div className="text-sm text-gray-600">pontos</div>
              </div>
            </div>

            <div className="text-center">
              <div 
                className="inline-block px-4 py-2 rounded-full text-lg font-bold mb-2"
                style={{ backgroundColor: scoreColor + '20', color: scoreColor }}
              >
                {scoreLabel}
              </div>
              <p className="text-gray-600 max-w-md">
                {audit.ai_summary?.ai_summary || 'Análise em processamento'}
              </p>
            </div>
          </div>
        </div>

        {/* AI Perception */}
        {audit.ai_summary && (
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6">
            <div className="flex items-start gap-4 mb-6">
              <div className="bg-purple-100 p-3 rounded-lg">
                <Sparkles className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Como a IA vê você
                </h2>
                <p className="text-gray-600">
                  Percepção do Gemini sobre seu negócio
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Público-alvo identificado:</h3>
                <p className="text-gray-700">{audit.ai_summary.target_audience}</p>
              </div>

              {audit.ai_summary.key_attributes.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Atributos identificados:</h3>
                  <div className="flex flex-wrap gap-2">
                    {audit.ai_summary.key_attributes.map((attr, idx) => (
                      <span 
                        key={idx}
                        className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                      >
                        {attr}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {audit.ai_summary.missing_signals.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Informações faltantes:</h3>
                  <ul className="space-y-1">
                    {audit.ai_summary.missing_signals.map((signal, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-gray-700">
                        <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                        {signal}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {audit.recommendations && audit.recommendations.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6">
            <div className="flex items-start gap-4 mb-6">
              <div className="bg-green-100 p-3 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Ações Prioritárias
                </h2>
                <p className="text-gray-600">
                  Implemente estas mudanças para melhorar seu score
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {audit.recommendations.map((rec, idx) => (
                <div 
                  key={idx}
                  className="border-l-4 pl-4 py-2"
                  style={{
                    borderColor: rec.priority === 'high' ? '#ef4444' : rec.priority === 'medium' ? '#f59e0b' : '#6b7280'
                  }}
                >
                  <div className="flex items-start justify-between mb-1">
                    <h3 className="font-semibold text-gray-900">{rec.action}</h3>
                    <span className="text-sm font-bold text-green-600">{rec.impact}</span>
                  </div>
                  <div className="flex gap-3 text-sm text-gray-600">
                    <span className="capitalize">Prioridade: {rec.priority === 'high' ? 'Alta' : rec.priority === 'medium' ? 'Média' : 'Baixa'}</span>
                    <span>•</span>
                    <span className="capitalize">Esforço: {rec.effort === 'low' ? 'Baixo' : rec.effort === 'medium' ? 'Médio' : 'Alto'}</span>
                  </div>
                  {rec.template && (
                    <div className="mt-2 bg-gray-50 p-3 rounded text-sm text-gray-700 italic">
                      💡 Modelo: "{rec.template}"
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-lg p-8 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">
            Quer implementar essas otimizações?
          </h2>
          <p className="text-lg mb-6 opacity-90">
            Nossa equipe pode fazer tudo isso para você e monitorar seus resultados mensalmente.
          </p>
          <a 
            href="https://wa.me/5511999999999?text=Olá! Vi minha auditoria AI Discovery e quero otimizar meu perfil"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-white text-blue-600 font-bold py-4 px-8 rounded-lg hover:bg-gray-100 transition"
          >
            Falar com Especialista
          </a>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-center text-gray-600 text-sm">
            © 2024 LK Digital. Todos os direitos reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}
