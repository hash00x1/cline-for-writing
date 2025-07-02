export type OpenAIReasoningEffort = "low" | "medium" | "high"

export interface ChatSettings {
        mode: "plan" | "act" | "research" | "write"
        preferredLanguage?: string
        openAIReasoningEffort?: OpenAIReasoningEffort
}

export type PartialChatSettings = Partial<ChatSettings>

export const DEFAULT_CHAT_SETTINGS: ChatSettings = {
	mode: "act",
	preferredLanguage: "English",
	openAIReasoningEffort: "medium",
}
