import { desc, eq } from "drizzle-orm";
import { getDb } from "../../../db";
import { readings } from "../../../db/schema";
import { getChatGPTUser } from "../../chatgpt-auth";

const lineValues = new Set([6, 7, 8, 9]);

export async function GET() {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: "请先登录" }, { status: 401 });
  const rows = await getDb().select().from(readings).where(eq(readings.ownerEmail, user.email)).orderBy(desc(readings.createdAt)).limit(100);
  return Response.json(rows.map((row) => ({ ...row, lines: JSON.parse(row.linesJson) })));
}

export async function POST(request: Request) {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: "请先登录" }, { status: 401 });
  const body = await request.json() as Record<string, unknown>;
  const lines = Array.isArray(body.lines) ? body.lines.map(Number) : [];
  if (
    typeof body.id !== "string" ||
    typeof body.question !== "string" ||
    body.question.trim().length < 8 ||
    body.question.length > 180 ||
    lines.length !== 6 ||
    lines.some((line) => !lineValues.has(line))
  ) {
    return Response.json({ error: "记录格式不完整" }, { status: 400 });
  }
  await getDb().insert(readings).values({
    id: body.id.slice(0, 160),
    ownerEmail: user.email,
    question: body.question.trim(),
    linesJson: JSON.stringify(lines),
    action: typeof body.action === "string" ? body.action.slice(0, 300) : null,
    reviewDate: typeof body.reviewDate === "string" ? body.reviewDate : null,
    createdAt: typeof body.createdAt === "string" ? body.createdAt : new Date().toISOString(),
  }).onConflictDoNothing();
  return Response.json({ ok: true }, { status: 201 });
}
