import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("ships the finished 观变 product surface", async () => {
  const [page, app, layout] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/guanbian-app.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  ]);
  assert.match(page, /GuanbianApp/);
  assert.match(app, /三枚铜钱 · 六次成卦/);
  assert.match(app, /变化档案/);
  assert.match(app, /经典依据/);
  assert.match(layout, /观变｜以易观时，以行验知/);
  assert.doesNotMatch(page + app + layout, /codex-preview|SkeletonPreview|Your site is taking shape/);
});
