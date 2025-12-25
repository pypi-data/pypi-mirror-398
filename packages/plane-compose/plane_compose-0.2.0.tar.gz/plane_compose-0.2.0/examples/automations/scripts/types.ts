/**
 * Plane Automations - TypeScript Type Definitions
 * 
 * These types define the contract for automation scripts.
 * Import them in your scripts for full type safety and autocomplete.
 * 
 * Usage:
 *   import type { Context, Action } from "./types.ts";
 *   
 *   export default function run(ctx: Context): Action[] {
 *     // Your logic here
 *   }
 */

// =============================================================================
// CONTEXT - What your script receives
// =============================================================================

/**
 * The work item that triggered the automation.
 */
export interface WorkItem {
  /** Unique identifier */
  id: string;
  
  /** Title of the work item */
  title: string;
  
  /** Description (markdown) */
  description?: string;
  
  /** Work item type: bug, task, feature, etc. */
  type: string;
  
  /** Current state: backlog, todo, in_progress, done, etc. */
  state: string;
  
  /** Priority: none, low, medium, high, urgent */
  priority?: string;
  
  /** Array of label names */
  labels: string[];
  
  /** Array of assignee emails or IDs */
  assignees: string[];
  
  /** Custom properties */
  properties: Record<string, unknown>;
  
  /** ISO timestamp when created */
  createdAt?: string;
  
  /** ISO timestamp when last updated */
  updatedAt?: string;
  
  /** Start date (YYYY-MM-DD) */
  startDate?: string;
  
  /** Due date (YYYY-MM-DD) */
  dueDate?: string;
}

/**
 * Information about what triggered the automation.
 */
export interface Trigger {
  /** Event type: work_item.created, work_item.updated, etc. */
  type: string;
  
  /** ISO timestamp when event occurred */
  timestamp: string;
  
  /** Field changes (for update events) */
  changes?: Record<string, {
    from: unknown;
    to: unknown;
  }>;
}

/**
 * The full context passed to your automation script.
 */
export interface Context {
  /** The work item that triggered this automation */
  workItem: WorkItem;
  
  /** Information about the trigger event */
  trigger: Trigger;
  
  /** Project configuration from plane.yaml */
  config: Record<string, unknown>;
}

// =============================================================================
// ACTIONS - What your script returns
// =============================================================================

/**
 * Set fields on the work item.
 * 
 * Example:
 *   { set: { priority: "high", state: "in_progress" } }
 */
export interface SetAction {
  set: {
    state?: string;
    priority?: string;
    type?: string;
    start_date?: string;
    due_date?: string;
    properties?: Record<string, unknown>;
  };
}

/**
 * Assign work item to user(s).
 * 
 * Example:
 *   { assign: "alice@example.com" }
 *   { assign: ["alice@example.com", "bob@example.com"] }
 */
export interface AssignAction {
  assign: string | string[];
}

/**
 * Remove assignee(s) from work item.
 */
export interface UnassignAction {
  unassign: string | string[];
}

/**
 * Add label(s) to work item.
 * 
 * Example:
 *   { add_label: "urgent" }
 *   { add_label: ["urgent", "needs-review"] }
 */
export interface AddLabelAction {
  add_label: string | string[];
}

/**
 * Remove label(s) from work item.
 */
export interface RemoveLabelAction {
  remove_label: string | string[];
}

/**
 * Add a comment to the work item.
 * 
 * Example:
 *   { comment: "This was auto-triaged" }
 */
export interface CommentAction {
  comment: string;
}

/**
 * Send a notification.
 * 
 * Examples:
 *   { notify: { channel: "#alerts", message: "New critical bug!" } }
 *   { notify: { to: "manager@example.com", message: "Please review" } }
 */
export interface NotifyAction {
  notify: {
    /** Slack channel (e.g., "#alerts") */
    channel?: string;
    /** Email or user ID to notify */
    to?: string;
    /** Message content */
    message: string;
  };
}

/**
 * Create a new work item.
 * 
 * Example:
 *   { create: { type: "task", title: "Follow-up", parent: ctx.workItem.id } }
 */
export interface CreateAction {
  create: {
    type: string;
    title: string;
    description?: string;
    state?: string;
    priority?: string;
    labels?: string[];
    assignees?: string[];
    parent?: string;
  };
}

/**
 * Union of all possible actions.
 */
export type Action =
  | SetAction
  | AssignAction
  | UnassignAction
  | AddLabelAction
  | RemoveLabelAction
  | CommentAction
  | NotifyAction
  | CreateAction;

// =============================================================================
// SCRIPT SIGNATURE
// =============================================================================

/**
 * The function signature for automation scripts.
 * 
 * Your script should export a default function with this signature:
 * 
 *   export default function run(ctx: Context): Action[] {
 *     // Your logic here
 *     return [{ set: { priority: "high" } }];
 *   }
 * 
 * Or async:
 * 
 *   export default async function run(ctx: Context): Promise<Action[]> {
 *     // Your async logic here
 *     return [{ set: { priority: "high" } }];
 *   }
 */
export type AutomationScript = (ctx: Context) => Action[] | Promise<Action[]>;

