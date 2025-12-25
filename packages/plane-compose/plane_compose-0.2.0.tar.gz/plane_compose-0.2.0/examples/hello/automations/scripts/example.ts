/**
 * Example Automation Script
 * 
 * This is a template showing how to write automation scripts.
 * Copy this file and modify it for your needs.
 */

import type { Context, Action } from "./types.ts";

/**
 * Main automation function.
 * 
 * @param ctx - The automation context with work item data
 * @returns Array of actions to execute
 */
export default function run(ctx: Context): Action[] {
  const { workItem, trigger, config } = ctx;
  
  console.error(`Processing: ${workItem.title}`);  // Logs go to stderr
  
  // Example: Escalate critical bugs
  if (workItem.type === "bug" && workItem.labels.includes("critical")) {
    return [
      { set: { priority: "urgent", state: "in_progress" } },
      { assign: "oncall@example.com" },
      { comment: "🚨 Auto-escalated: Critical bug detected" },
      { notify: { 
        channel: "#critical-bugs", 
        message: `Critical bug reported: ${workItem.title}` 
      }}
    ];
  }
  
  // Example: Auto-assign based on labels
  if (workItem.labels.includes("frontend") && workItem.assignees.length === 0) {
    return [
      { assign: "frontend-team@example.com" },
      { add_label: "team-frontend" }
    ];
  }
  
  // Example: Check for missing information
  if (!workItem.description || workItem.description.length < 20) {
    return [
      { add_label: "needs-details" },
      { comment: "Please add more details to help us understand the issue." }
    ];
  }
  
  // No actions needed
  return [];
}

// =============================================================================
// HELPER FUNCTIONS (Optional - add your own)
// =============================================================================

/**
 * Calculate days since a date.
 */
function daysSince(dateString: string): number {
  const date = new Date(dateString);
  const now = new Date();
  return (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);
}

/**
 * Check if current time is business hours.
 */
function isBusinessHours(): boolean {
  const hour = new Date().getHours();
  const day = new Date().getDay();
  return day >= 1 && day <= 5 && hour >= 9 && hour < 18;
}

