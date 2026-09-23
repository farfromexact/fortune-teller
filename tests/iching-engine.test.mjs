import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { resolveReading } from "../app/iching.ts";

test("actual resolver interprets bottom-to-top casts and preserves legacy records", () => {
  assert.equal(resolveReading([7, 8, 8, 8, 7, 8]).primary.name, "屯");
  assert.equal(resolveReading([7, 8, 8, 8, 7, 8], 1).primary.name, "蒙");
  const moving = resolveReading([9, 8, 8, 8, 7, 8]);
  assert.equal(moving.changed.name, "比");
  assert.deepEqual(moving.moving, [1]);
});

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
    const primary = [...values].reverse().map((line) => line === 7 || line === 9 ? "1" : "0").join("");
    const changed = [...values].reverse().map((line) => line === 6 || line === 7 ? "1" : "0").join("");
    const actual = resolveReading(values);
    assert.equal(actual.primary.binary, primary);
    assert.equal(actual.changed.binary, changed);
    assert.ok(binaries.has(primary), `missing primary ${primary}`);
    assert.ok(binaries.has(changed), `missing changed ${changed}`);
  }
});
