from tentacles.Meta.Keywords.matrix_library.RunAnalysis.AnalysisMode import (
    DefaultRunAnalysisMode,
)


async def script(ctx):
    return await DefaultRunAnalysisMode().run_analysis_script(ctx)
