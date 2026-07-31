import { index, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const readings = sqliteTable("readings", {
  id: text("id").primaryKey(),
  ownerEmail: text("owner_email").notNull(),
  question: text("question").notNull(),
  linesJson: text("lines_json").notNull(),
  action: text("action"),
  reviewDate: text("review_date"),
  reflection: text("reflection"),
  createdAt: text("created_at").notNull(),
}, (table) => [
  index("readings_owner_created_idx").on(table.ownerEmail, table.createdAt),
]);
