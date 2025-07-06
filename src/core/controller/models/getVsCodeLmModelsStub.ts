import { Controller } from ".."
import { EmptyRequest } from "../../../shared/proto/common"
import { VsCodeLmModelsArray } from "../../../shared/proto/models"

/**
 * Stub implementation for VS Code LM models when API is not available
 * @param controller The controller instance
 * @param request Empty request
 * @returns Empty array of models
 */
export async function getVsCodeLmModelsStub(controller: Controller, request: EmptyRequest): Promise<VsCodeLmModelsArray> {
	// Return empty array as stub implementation
	return VsCodeLmModelsArray.create({ models: [] })
}
