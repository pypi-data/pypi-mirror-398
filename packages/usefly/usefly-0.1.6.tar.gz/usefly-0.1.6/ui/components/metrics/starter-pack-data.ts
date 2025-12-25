export interface StarterChart {
  id: string
  name: string
  description: string
  category: "Engagement" | "Conversion" | "Activation" | "Friction"
  whyItMatters: string
  eventsCollected: string[]
  howToMeasure: string
  chartType: "line" | "funnel" | "bar" | "pie"
  sampleData: {
    labels?: string[]
    values?: number[]
    steps?: { name: string; value: number; percentage: number }[]
    data?: Array<{ name: string; value: number }>
  }
}

export const STARTER_PACK_CHARTS: StarterChart[] = [
  {
    id: "dau_wau_mau",
    name: "DAU/WAU/MAU",
    description: "Track daily, weekly, and monthly active users over time",
    category: "Engagement",
    whyItMatters:
      "Understanding your active user base is fundamental to measuring product health and growth. DAU/WAU ratio indicates stickiness, while MAU shows overall reach.",
    eventsCollected: [
      "user_session_start",
      "user_activity",
      "page_view",
    ],
    howToMeasure:
      "Track unique users who perform any activity in 1 day (DAU), 7 days (WAU), or 30 days (MAU). DAU/MAU ratio > 20% indicates good stickiness.",
    chartType: "line",
    sampleData: {
      labels: ["Week 1", "Week 2", "Week 3", "Week 4"],
      values: [1200, 1450, 1680, 1820],
    },
  },
  {
    id: "conversion_funnel",
    name: "Conversion Funnel",
    description: "Track user progression through key conversion steps",
    category: "Conversion",
    whyItMatters:
      "Identify exactly where users drop off in your conversion flow. A single step with high drop-off reveals your biggest opportunity for improvement.",
    eventsCollected: [
      "funnel_step_entered",
      "funnel_step_completed",
      "conversion_goal_reached",
    ],
    howToMeasure:
      "Define your conversion steps (e.g., Landing → Sign Up → Onboarding → First Action). Track completion rate at each step. Industry average overall conversion: 2-5%.",
    chartType: "funnel",
    sampleData: {
      steps: [
        { name: "Landing Page", value: 10000, percentage: 100 },
        { name: "Sign Up Started", value: 3200, percentage: 32 },
        { name: "Account Created", value: 2400, percentage: 24 },
        { name: "Onboarding Complete", value: 1600, percentage: 16 },
        { name: "First Feature Used", value: 1200, percentage: 12 },
      ],
    },
  },
  {
    id: "time_to_value",
    name: "Time to Value",
    description: "Measure how quickly users reach their 'aha moment'",
    category: "Activation",
    whyItMatters:
      "Users who reach value faster are more likely to retain. If TTV is too long, you'll lose users before they understand your product's value.",
    eventsCollected: [
      "user_signed_up",
      "first_value_event",
      "aha_moment_reached",
    ],
    howToMeasure:
      "Define your 'aha moment' (first meaningful action). Measure time from sign-up to this event. Good TTV: < 5 minutes for simple products, < 24 hours for complex ones.",
    chartType: "bar",
    sampleData: {
      data: [
        { name: "< 5 min", value: 450 },
        { name: "5-15 min", value: 320 },
        { name: "15-30 min", value: 180 },
        { name: "30-60 min", value: 95 },
        { name: "> 1 hour", value: 155 },
      ],
    },
  },
  {
    id: "feature_adoption",
    name: "Feature Adoption Rate",
    description: "Track what % of users adopt your new feature",
    category: "Engagement",
    whyItMatters:
      "Low adoption means users either don't discover your feature or don't find it valuable. This directly impacts the ROI of your development efforts.",
    eventsCollected: [
      "feature_discovered",
      "feature_first_use",
      "feature_repeated_use",
    ],
    howToMeasure:
      "Track % of active users who used the feature at least once. Good adoption: >40% in first month. Also track power users (>5 uses) vs one-time users.",
    chartType: "line",
    sampleData: {
      labels: ["Week 1", "Week 2", "Week 3", "Week 4"],
      values: [12, 28, 45, 58],
    },
  },
  {
    id: "error_rate",
    name: "Error Rate",
    description: "Monitor friction points and errors users encounter",
    category: "Friction",
    whyItMatters:
      "High error rates directly correlate with user frustration and churn. Catching errors early prevents negative reviews and support tickets.",
    eventsCollected: [
      "error_occurred",
      "error_type",
      "user_stuck",
      "rage_click",
    ],
    howToMeasure:
      "Track errors per session and by error type. Healthy products: <2% error rate. Prioritize fixing errors that affect >5% of users or block critical flows.",
    chartType: "pie",
    sampleData: {
      data: [
        { name: "Form Validation", value: 145 },
        { name: "API Timeout", value: 89 },
        { name: "Page Load Error", value: 56 },
        { name: "Payment Failed", value: 34 },
        { name: "Other", value: 76 },
      ],
    },
  },
  {
    id: "session_success",
    name: "Session Success Rate",
    description: "Measure % of sessions where users complete their goal",
    category: "Conversion",
    whyItMatters:
      "Success rate indicates whether users can actually accomplish what they came to do. Low success = poor UX or unclear value prop.",
    eventsCollected: [
      "session_start",
      "goal_attempted",
      "goal_completed",
      "session_end",
    ],
    howToMeasure:
      "Define what 'success' means for your product (e.g., completing a purchase, sending a message). Track % of sessions with goal completion. Good benchmark: >60%.",
    chartType: "bar",
    sampleData: {
      data: [
        { name: "Successful", value: 6800 },
        { name: "Partial", value: 1900 },
        { name: "Abandoned", value: 1300 },
      ],
    },
  },
]
