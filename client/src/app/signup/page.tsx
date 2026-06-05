import { redirect } from "next/navigation";

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ callbackUrl?: string }>;
}) {
  const params = await searchParams;
  const callbackUrl = params.callbackUrl?.startsWith("/")
    ? params.callbackUrl
    : "";
  const query = callbackUrl
    ? `?callbackUrl=${encodeURIComponent(callbackUrl)}`
    : "";
  redirect(`/login${query}`);
}
