import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("knowledge layer contains all 64 unique King Wen hexagrams", async () => {
  const source = await readFile(new URL("../app/iching.ts", import.meta.url), "utf8");
  const pairs = [...source.matchAll(/\["[^"]+", "[^"]+", "([01]{6})",/g)].map((match) => match[1]);
  assert.equal(pairs.length, 64);
  assert.equal(new Set(pairs).size, 64);
  assert.ok(pairs.includes("111111"));
  assert.ok(pairs.includes("000000"));
});

test("all 4096 stable/moving line states resolve to a known primary and changed pattern", async () => {
  const source = await readFile(new URL("../app/iching.ts", import.meta.url), "utf8");
  const binaries = new Set([...source.matchAll(/\["[^"]+", "[^"]+", "([01]{6})",/g)].map((match) => match[1]));
  for (let state = 0; state < 4096; state++) {
    const values = Array.from({ length: 6 }, (_, index) => [6, 7, 8, 9][(state >> (index * 2)) & 3]);
    const primary = values.map((line) => line === 7 || line === 9 ? "1" : "0").join("");
    const changed = values.map((line) => line === 6 || line === 7 ? "1" : "0").join("");
    assert.ok(binaries.has(primary), `missing primary ${primary}`);
    assert.ok(binaries.has(changed), `missing changed ${changed}`);
  }
});
