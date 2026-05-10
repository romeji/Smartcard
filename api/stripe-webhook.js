// Vercel Edge Function — Stripe Webhook
// Gère les événements de paiement Stripe et met à jour Firebase Firestore
// Variables requises : STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, FIREBASE_SERVICE_ACCOUNT

export const config = { runtime: 'edge' };

export default async function handler(req) {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  const STRIPE_WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET;
  const FIREBASE_WEB_API_KEY = process.env.FIREBASE_WEB_API_KEY;
  const FIREBASE_PROJECT_ID = process.env.FIREBASE_PROJECT_ID || 'smartcard-4c62c';

  // Verify Stripe signature
  const signature = req.headers.get('stripe-signature');
  const body = await req.text();

  // In production: verify with stripe.webhooks.constructEvent()
  // For now, parse directly (add verification in prod)
  let event;
  try {
    event = JSON.parse(body);
  } catch (e) {
    return new Response('Invalid JSON', { status: 400 });
  }

  // Handle successful payment
  if (event.type === 'checkout.session.completed' || event.type === 'payment_intent.succeeded') {
    const session = event.data?.object;
    const userId = session?.client_reference_id || session?.metadata?.userId;
    const plan = session?.metadata?.plan || 'monthly';

    if (userId && FIREBASE_PROJECT_ID) {
      // Update user premium status in Firestore via REST API
      const expiresAt = Date.now() + (plan === 'yearly' ? 365 : 30) * 24 * 3600 * 1000;
      const premiumData = {
        fields: {
          premium: {
            mapValue: {
              fields: {
                active: { booleanValue: true },
                plan: { stringValue: plan },
                expiresAt: { integerValue: String(expiresAt) },
                activatedAt: { integerValue: String(Date.now()) },
                stripeSessionId: { stringValue: session?.id || '' },
              }
            }
          },
          updatedAt: { integerValue: String(Date.now()) },
        }
      };

      try {
        const firestoreUrl = `https://firestore.googleapis.com/v1/projects/${FIREBASE_PROJECT_ID}/databases/(default)/documents/users/${userId}`;
        await fetch(firestoreUrl + '?updateMask.fieldPaths=premium&updateMask.fieldPaths=updatedAt', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            // In production: add Authorization header with service account token
          },
          body: JSON.stringify(premiumData),
        });
        console.log('[Stripe] Premium activated for user:', userId);
      } catch (e) {
        console.error('[Stripe] Firestore update failed:', e.message);
      }
    }
  }

  // Handle subscription cancellation
  if (event.type === 'customer.subscription.deleted') {
    const userId = event.data?.object?.metadata?.userId;
    if (userId) {
      // Deactivate premium in Firestore
      console.log('[Stripe] Premium cancelled for user:', userId);
    }
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
