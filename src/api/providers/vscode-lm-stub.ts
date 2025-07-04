// Stub file to replace vscode-lm provider when Language Model API is not available
import { ApiHandler } from "../"
import { ApiHandlerOptions, ModelInfo } from "@shared/api"

/**
 * Stub implementation of VS Code Language Model provider
 * Used when the VS Code Language Model API is not available
 */
export class VsCodeLmHandler implements ApiHandler {
	private options: ApiHandlerOptions

	constructor(options: ApiHandlerOptions) {
		this.options = options
	}

	async *createMessage(systemPrompt: string, messages: any[]): AsyncGenerator<any> {
		throw new Error("VS Code Language Model API is not available in this VS Code version. Please use a different provider or update to a newer VS Code version.")
	}

	getModel(): { id: string; info: ModelInfo } {
		return {
			id: "vscode-lm-unavailable",
			info: {
				maxTokens: 0,
				contextWindow: 0,
				supportsImages: false,
				supportsPromptCache: false,
				inputPrice: 0,
				outputPrice: 0,
			}
		}
	}
}
