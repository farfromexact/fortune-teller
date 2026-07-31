CREATE TABLE `readings` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_email` text NOT NULL,
	`question` text NOT NULL,
	`lines_json` text NOT NULL,
	`action` text,
	`review_date` text,
	`reflection` text,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `readings_owner_created_idx` ON `readings` (`owner_email`,`created_at`);