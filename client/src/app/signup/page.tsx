import Navbar from '../../components/Navbar';
import SignupForm from './SignupForm';

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ callbackUrl?: string }>;
}) {
  const params = await searchParams;
  const callbackUrl = params.callbackUrl?.startsWith('/') ? params.callbackUrl : '/recommend';
  const googleEnabled = Boolean(process.env.AUTH_GOOGLE_ID && process.env.AUTH_GOOGLE_SECRET);

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="page-frame flex grow items-center justify-center py-10">
        <SignupForm callbackUrl={callbackUrl} googleEnabled={googleEnabled} />
      </main>
    </div>
  );
}
