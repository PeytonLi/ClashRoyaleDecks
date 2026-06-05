import Navbar from "../../components/Navbar";
import UnifiedAuthForm from "./UnifiedAuthForm";
import LoginBackground from "./LoginBackground";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ callbackUrl?: string }>;
}) {
  const params = await searchParams;
  const raw = params.callbackUrl ?? "";
  const callbackUrl =
    raw.startsWith("/") && !raw.startsWith("//") ? raw : "/recommend";
  const googleEnabled = Boolean(
    process.env.AUTH_GOOGLE_ID && process.env.AUTH_GOOGLE_SECRET,
  );

  return (
    <LoginBackground>
      <Navbar />
      <main className="page-frame flex grow items-center justify-center py-10">
        <UnifiedAuthForm
          callbackUrl={callbackUrl}
          googleEnabled={googleEnabled}
        />
      </main>
    </LoginBackground>
  );
}
