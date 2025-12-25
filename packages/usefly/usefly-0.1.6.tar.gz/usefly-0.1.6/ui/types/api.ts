/**
 * TypeScript types for Usefly API responses
 * These mirror the Python Pydantic models for type safety
 */

/**
 * Test Scenario
 * Defines test setup and personas
 */
export interface UserJourneyTask {
  number: number;
  starting_url: string;
  goal: string;
  steps: string;
  persona: string;
  stop?: string;
}

export interface TasksMetadata {
  total_tasks: number;
  total_generated?: number;
  total_selected?: number;
  selected_task_numbers?: number[];
  persona_distribution: Record<string, number>;
  generated_at?: string;
  last_generated?: string;
  generation_history?: Array<{
    timestamp: string;
    prompt_type: string;
    num_generated: number;
    custom_prompt_used: boolean;
  }>;
  error?: string;
}

export interface DiscoveredUrl {
  url: string;
  url_decoded?: string;
}

export interface Scenario {
  id: string;
  name: string;
  website_url: string;
  personas: string[];
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  description?: string;
  metrics?: string[];
  email?: string;
  tasks?: UserJourneyTask[];
  tasks_metadata?: TasksMetadata;
  discovered_urls?: DiscoveredUrl[];
  crawler_final_result?: any;
  crawler_extracted_content?: any;
  selected_task_indices?: number[];
}

export interface CreateScenarioRequest {
  name: string;
  website_url: string;
  personas?: string[];
  description?: string;
  metrics?: string[];
  email?: string;
  tasks?: UserJourneyTask[];
  selected_task_indices?: number[];
  tasks_metadata?: TasksMetadata;
  discovered_urls?: DiscoveredUrl[];
  crawler_final_result?: string;
  crawler_extracted_content?: string;
}

/**
 * System Configuration
 * Global settings for the application
 */
export interface SystemConfig {
  id: number;
  provider: string;
  model_name: string;
  api_key: string;
  use_thinking: boolean;
  max_steps: number;
  max_browser_workers: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface UpdateSystemConfigRequest {
  provider: string;
  model_name: string;
  api_key: string;
  use_thinking: boolean;
  max_steps: number;
  max_browser_workers: number;
}

/**
 * System Configuration Status
 * Lightweight check for config status
 */
export interface SystemConfigStatus {
  configured: boolean;
  missing_fields: string[];
}

/**
 * Crawler Analysis
 * Website crawling and analysis
 */
export interface CrawlerAnalysisRequest {
  scenario_id: string;  // NOW REQUIRED - must be an existing scenario
  website_url: string;
  description?: string;
  name?: string;
  metrics?: string[];
  email?: string;
}

export interface CrawlerAnalysisResponse {
  run_id: string;
  scenario_id: string;
  output_path?: string;
  status: string;
  duration?: number;
  steps?: number;
  error?: string;
  crawler_summary?: string;
  crawler_extracted_content: string;
  tasks?: UserJourneyTask[];
  tasks_metadata?: TasksMetadata;
}

/**
 * Friction Point
 * Represents a point where the user encountered friction
 */
export interface FrictionPoint {
  step: string;
  type: string;
  duration: number;
}

/**
 * Metrics Data
 * Contains performance metrics for an agent run
 */
export interface MetricsData {
  time_to_value?: {
    minutes: number;
    steps: number;
  };
  onboarding?: {
    completed: boolean;
  };
  feature_adoption?: {
    adopted: boolean;
  };
}

/**
 * Persona Run
 * Represents a single persona execution
 */
export interface PersonaRun {
  id: string;
  config_id: string;
  report_id?: string;
  persona_type: string;
  is_done: boolean;
  timestamp: string; // ISO datetime
  duration_seconds?: number; // seconds
  platform: string;
  error_type?: string; // Error type for failed runs
  steps_completed: number;
  total_steps: number;
  final_result?: string;
  judgement_data: any;
  task_description?: string;
  task_goal?: string;
  task_steps?: string;
  task_url?: string;
  events: any[];
}

export interface CreatePersonaRunRequest {
  config_id: string;
  report_id?: string;
  persona_type: string;
  is_done?: boolean;
  timestamp: string;
  duration_seconds?: number;
  platform?: string;
  error_type?: string;
  steps_completed?: number;
  total_steps?: number;
  journey_path?: string[];
  final_result?: string;
  judgement_data?: any;
  task_description?: string;
  task_goal?: string;
  task_steps?: string;
  task_url?: string;
  events?: any[];
}

/**
 * Friction Reason
 * Individual friction reason with count
 */
export interface FrictionReason {
  reason: string;
  count: number;
}

/**
 * Sankey Node
 * Represents a page in the journey with optional friction metadata
 */
export interface SankeyNode {
  name: string;
  visits: number;
  event_count?: number;
  friction_count?: number;
  friction_reasons?: FrictionReason[];
  friction_impact?: number;
  example_run_ids?: string[];
}

/**
 * Sankey Link
 * Represents a transition between pages
 */
export interface SankeyLink {
  source: number;
  target: number;
  value: number;
}

/**
 * Sankey Data
 * Complete sankey diagram data for journey visualization
 */
export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

/**
 * Metrics Summary
 * Aggregated metrics across multiple agent runs
 */
export interface MetricsSummary {
  total_runs: number;
  sucessfull_runs: number;
  failed_runs: number;
  error_runs: number;
  success_rate: number;
  avg_duration_seconds: number;
  avg_steps: number;
}

/**
 * Report List Item
 * Summary of a report for the report selector
 */
export interface ReportListItem {
  report_id: string;
  scenario_id: string;
  scenario_name: string;
  run_count: number;
  first_run: string;  // ISO datetime
  last_run: string;   // ISO datetime
}

/**
 * Report Aggregate
 * Full aggregated data for a specific report
 */
export interface ReportAggregate {
  report_id: string;
  scenario_id: string;
  scenario_name: string;
  run_count: number;
  metrics_summary: MetricsSummary;
  journey_sankey: SankeyData;
}

export interface PersonaExecutionResponse {
  run_id: string;
  scenario_id: string;
  report_id: string;
  task_count: number;
  status: string;
  message: string;
}

/**
 * Task Progress Status
 * Progress status for a single task within a run
 */
export interface TaskProgressStatus {
  task_index: number;
  persona: string;
  status: "pending" | "running" | "completed" | "failed";
  current_step: number;
  max_steps: number;
  current_action?: string;
  current_url?: string;
  started_at?: string;
  error?: string;
}

/**
 * Run Status Response
 * Enhanced run status with per-task progress
 */
export interface RunStatusResponse {
  run_id: string;
  scenario_id: string;
  scenario_name?: string;
  run_type: "persona_run" | "scenario_analysis";
  status: "in_progress" | "completed" | "partial_failure" | "failed";
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  agent_run_ids: string[];
  task_progress: TaskProgressStatus[];
  started_at?: string;
  logs: string[];
}

/**
 * Active Executions Response
 * Response containing all active executions
 */
export interface ActiveExecutionsResponse {
  executions: RunStatusResponse[];
  total_count: number;
}

/**
 * API Response Types
 */
export interface ApiResponse<T> {
  data: T;
  error?: string;
}

export interface ApiListResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface GenerateMoreTasksRequest {
  num_tasks: number;
  prompt_type: "original" | "friction";
  custom_prompt?: string;
}

export interface GenerateMoreTasksResponse {
  scenario_id: string;
  new_tasks: UserJourneyTask[];
  total_tasks: number;
  tasks_metadata: TasksMetadata;
  message: string;
}

export interface AsyncAnalysisResponse {
  run_id: string;
  scenario_id: string;
  status: string;
  message: string;
}

/**
 * Insights and Friction Data
 */
export interface FrictionHotspotItem {
  location: string;
  reason: string;
  count: number;
  impact_percentage: number;
  example_run_ids: string[];
}
