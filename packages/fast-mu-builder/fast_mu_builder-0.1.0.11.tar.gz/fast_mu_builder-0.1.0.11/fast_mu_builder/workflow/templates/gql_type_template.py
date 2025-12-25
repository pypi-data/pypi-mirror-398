import strawberry

from fast_mu_builder.workflow.response import EvaluationStatusResponse

'''EVALUATION_RESPONSE'''
@strawberry.type
class _MODEL_EvaluationStatusResponse(EvaluationStatusResponse):
    pass