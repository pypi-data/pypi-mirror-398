/**
 * Stale Check Automation Script
 * 
 * Checks if a work item has been inactive for too long and marks it as stale.
 */

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface Context {
  workItem: {
    id: string;
    title: string;
    description?: string;
    type: string;
    state: string;
    priority?: string;
    labels: string[];
    assignees: string[];
    properties: Record<string, unknown>;
    createdAt?: string;
    updatedAt?: string;
  };
  trigger: {
    type: string;
    timestamp: string;
    changes?: Record<string, { from: unknown; to: unknown }>;
  };
  config: Record<string, unknown>;
}

type Action =
  | { set: Record<string, unknown> }
  | { assign: string | string[] }
  | { unassign: string | string[] }
  | { add_label: string | string[] }
  | { remove_label: string | string[] }
  | { comment: string }
  | { notify: { channel?: string; to?: string; message: string } };

// =============================================================================
// AUTOMATION LOGIC
// =============================================================================

export default function run(ctx: Context): Action[] {
  const { workItem } = ctx;
  
  // Calculate days since last update
  const updatedAt = workItem.updatedAt || workItem.createdAt;
  if (!updatedAt) {
    return [];
  }
  
  const daysSinceUpdate = getDaysSince(updatedAt);
  
  // Items inactive for 30+ days -> move to backlog
  if (daysSinceUpdate > 30) {
    return [
      { add_label: "stale" },
      { set: { state: "backlog" } },
      { comment: `⚠️ This item has been inactive for ${Math.round(daysSinceUpdate)} days and has been moved to backlog.` },
      { notify: { 
        to: workItem.assignees[0], 
        message: `"${workItem.title}" is stale and moved to backlog` 
      }}
    ];
  }
  
  // Items inactive for 14+ days -> add stale label
  if (daysSinceUpdate > 14) {
    return [
      { add_label: "stale" },
      { comment: `⚠️ This item has been inactive for ${Math.round(daysSinceUpdate)} days.\n\nPlease update the status or close if no longer relevant.` }
    ];
  }
  
  // Item is active, no action needed
  return [];
}

// =============================================================================
// HELPERS
// =============================================================================

function getDaysSince(dateString: string): number {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  return diffMs / (1000 * 60 * 60 * 24);
}

