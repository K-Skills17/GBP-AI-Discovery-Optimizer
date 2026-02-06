'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createAudit } from '@/lib/api-client';
import { Loader2, Search, Sparkles } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [businessName, setBusinessName] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!businessName || !location) {
      setError('Por favor, preencha todos os campos');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const audit = await createAudit({
        business_name: businessName,
        location: location,
      });

      // Redirect to results page
      router.push(`/resultado/${audit.id}`);
    } catch (err: any) {
      console.error('Error creating audit:', err);
      setError(
        err.response?.data?.detail || 
        'Erro ao criar auditoria. Verifique se o negócio existe e tente novamente.'
      );
    } finally {
      setLoading(false);
    }
  };

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
            <span className="text-sm text-gray-600">by LK Digital</span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Como a IA do Google
            <br />
            <span className="text-blue-600">vê seu negócio?</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Descubra em minutos como a inteligência artificial percebe sua empresa
            e o que está impedindo você de aparecer nas buscas com IA.
          </p>
        </div>

        {/* Audit Form Card */}
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Auditoria Gratuita
              </h2>
              <p className="text-gray-600">
                Análise completa do seu perfil no Google Meu Negócio
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="business_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Nome do Negócio *
                </label>
                <input
                  id="business_name"
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="Ex: Clínica Dental Sorriso"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                  Cidade *
                </label>
                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Ex: São Paulo"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                  disabled={loading}
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analisando...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    Iniciar Auditoria Gratuita
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="flex items-start gap-3 text-sm text-gray-600">
                <Sparkles className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <p>
                  <strong className="text-gray-900">100% Gratuito.</strong> Receba em minutos
                  uma análise completa de como a IA do Google percebe seu negócio.
                </p>
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Search className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">Análise AI</h3>
              <p className="text-sm text-gray-600">
                Como o Gemini vê seu negócio agora
              </p>
            </div>

            <div className="text-center">
              <div className="bg-purple-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">Score de Descoberta</h3>
              <p className="text-sm text-gray-600">
                Métrica exclusiva de visibilidade AI
              </p>
            </div>

            <div className="text-center">
              <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">Ações Prioritárias</h3>
              <p className="text-sm text-gray-600">
                O que fazer para melhorar hoje
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-center text-gray-600 text-sm">
            © 2024 LK Digital. Todos os direitos reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}
