'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

/**
 * Legacy resultado route — redirects to the new diagnostico page.
 */
export default function ResultadoRedirect() {
  const params = useParams();
  const router = useRouter();
  const auditId = params.auditId as string;

  useEffect(() => {
    if (auditId) {
      router.replace(`/diagnostico/${auditId}`);
    } else {
      router.replace('/');
    }
  }, [auditId, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-gray-500">Redirecionando...</p>
    </div>
  );
}
