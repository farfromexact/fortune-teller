import { getChatGPTUser } from "./chatgpt-auth";
import GuanbianApp from "./guanbian-app";

export const dynamic = "force-dynamic";

export default async function Home() {
  const user = await getChatGPTUser();
  return <GuanbianApp user={user ? { displayName: user.displayName } : null} />;
}
