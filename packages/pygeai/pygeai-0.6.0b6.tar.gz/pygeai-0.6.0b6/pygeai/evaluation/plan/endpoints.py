LIST_EVALUATION_PLANS = "evaluationPlanApi/evaluationPlans"  # GET -> Retrieves a list of all evaluation plans.
CREATE_EVALUATION_PLAN = "evaluationPlanApi/evaluationPlan"  # POST -> Creates a new evaluation plan.
GET_EVALUATION_PLAN = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}"  # GET -> Retrieves a specific evaluation plan by ID.
UPDATE_EVALUATION_PLAN = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}"  # PUT -> Updates a specific evaluation plan by ID.
DELETE_EVALUATION_PLAN = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}"  # DELETE -> Deletes a specific evaluation plan by ID.

LIST_EVALUATION_PLAN_SYSTEM_METRICS = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}/evaluationPlanSystemMetrics"  # GET -> Retrieves system metrics associated with a specific evaluation plan.
ADD_EVALUATION_PLAN_SYSTEM_METRIC = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}/evaluationPlanSystemMetric"  # POST -> Adds a system metric to a specific evaluation plan.
GET_EVALUATION_PLAN_SYSTEM_METRIC = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}/evaluationPlanSystemMetric/{systemMetricId}"  # GET -> Retrieves a specific system metric from an evaluation plan.
UPDATE_EVALUATION_PLAN_SYSTEM_METRIC = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}/evaluationPlanSystemMetric/{systemMetricId}"  # PUT -> Updates a specific system metric within an evaluation plan.
DELETE_EVALUATION_PLAN_SYSTEM_METRIC = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}/evaluationPlanSystemMetric/{systemMetricId}"  # DELETE -> Deletes a specific system metric from an evaluation plan.

LIST_SYSTEM_METRICS = "evaluationPlanApi/systemMetrics"  # GET -> Retrieves a list of all available system metrics.
GET_SYSTEM_METRIC = "evaluationPlanApi/systemMetric/{systemMetricId}"  # GET -> Retrieves a specific system metric by ID.

EXECUTE_EVALUATION_PLAN = "evaluationPlanApi/evaluationPlan/{evaluationPlanId}"  # POST -> Executes a specific evaluation plan.
